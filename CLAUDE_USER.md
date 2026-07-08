# Plan: run Claude Code as an isolated `claude-agent` macOS user

## Goal

Stop a confused or prompt-injected Claude session from reading my secrets at a
**structural** layer (OS identity + filesystem permissions), not via a
command-name blocklist. A blocklist is trivially defeated (rename the binary,
build the name from string parts, call the C Security.framework API via
`ctypes`, write a custom Mach client). Identity isolation defeats all of those
at once.

## Two secret vectors this closes

1. **macOS keychain via `securityd`.** Keychain secrets are not read from disk —
   they are extracted by IPC to the `securityd` daemon over a Mach port. The
   on-disk keychain file is encrypted ciphertext. So `denyRead` on
   `/Library/Keychains` is useless, and the only structural choke point is
   *which keychain `securityd` serves the calling process* — which is determined
   by the **user identity**. A separate user gets its own (empty) login
   keychain. Confirmed empirically: from inside the current sandbox,
   `security list-keychains` and `security find-generic-password` reach
   `securityd` fine — the built-in sandbox does NOT block keychain IPC.

2. **Injected AWS credentials in the environment.** Today `claude` launches via
   `aws-vault exec bedrock-dev -- claude`, so short-term Bedrock STS creds are written
   into the process env and inherited by every subprocess (`printenv` leaks them
   with no prompt). Under the new model the agent still needs the Bedrock creds
   to call the model, but it gets ONLY those — never the long-term creds, which
   stay in my login keychain and never cross the boundary.

## Why a network-egress allowlist is not enough on its own

Anthropic's own docs: files Claude reads "are transmitted to the Anthropic API
or your configured provider with or without a sandbox." A read is a leak over
the one channel that must be allowed. So the defense has to prevent the READ,
which is what user isolation does.

## Decisions locked in

- **Scope:** ALL `claude` sessions run as `claude-agent` (single hardened path).
- **Repo access:** ACL granting `claude-agent` rwx on `~/code`, with my home
  locked to `700` so secrets are untraversable.
- **No `srt`:** the whole-process Seatbelt wrap (`slaude`) is work-in-progress and
  not used. Only Claude Code's built-in Bash sandbox is in play. `sudo -u` does
  NOT apply Seatbelt, and Claude Code applies its own `sandbox-exec` per Bash
  command — so the inner sandbox stays **ON**, no nesting conflict.
- **Account:** non-admin (not in the `admin` group). Keep it **visible** during
  setup so I can log in as it to debug MCP OAuth; hide it later if desired.
  Hidden vs visible is cosmetic only — no security effect.

## Target launch flow

```
me (terminal) → aws-vault exec bedrock-dev          [keychain read happens HERE, as me]
                  → mints short-term Bedrock creds
                    → sudo -u claude-agent --preserve-env=<bedrock vars only>
                      → claude   [as claude-agent: empty keychain, only Bedrock creds,
                                  built-in Bash sandbox ON]
```

`aws-vault` stays OUTSIDE the boundary (keychain/SSO works as me, before the
identity switch). `sudo` crosses the identity boundary. `--preserve-env` passes
through ONLY the short-lived Bedrock creds.

---

## Phase 1 — Identity + filesystem boundary (the security core)

All steps need `sudo`/admin and run OUTSIDE the sandbox — run them in a terminal
(or via `!`).

1. **Create a non-admin user** (no interactive login, reached only via `sudo -u`):
   ```
   sudo sysadminctl -addUser claude-agent -fullName "Claude Agent" -password -
   ```
   (Omit `-admin` so it cannot sudo back to root. Leave it visible for now; to
   hide later: `sudo dscl . create /Users/claude-agent IsHidden 1`.)

2. **Lock home so `staff`-group traversal can't reach secrets.** My home is
   currently `750 staff`, and every macOS user is in `staff` by default — so
   today `claude-agent` would get group access. `700` removes it:
   ```
   chmod 700 /Users/mattias.johansson
   ```

3. **Grant `claude-agent` a path to the repos only** (ACLs evaluate before POSIX
   mode, so they punch through the `700`):
   ```
   # traverse-only on home: reach ~/code without listing/reading anything else
   chmod +a "claude-agent allow search" /Users/mattias.johansson

   # full rwx + inheritance on the work tree
   chmod -R +a "claude-agent allow list,search,add_file,add_subdirectory,delete_child,readattr,writeattr,readextattr,writeextattr,readsecurity,read,write,execute,delete,file_inherit,directory_inherit" /Users/mattias.johansson/code
   ```
   `search` (not `list`) on home means the agent can `cd` into `~/code` but
   cannot enumerate or enter `~/.aws`, `~/.ssh`, `~/Library`.

4. **Verify secrets are self-protected** (must confirm — not yet checked from
   inside the sandbox):
   ```
   ls -lde ~/.aws ~/.ssh ~/Library/Keychains
   ```
   Each must be owner-only, owner `mattias.johansson`, NO `claude-agent` ACL.
   Tighten if needed:
   ```
   chmod 700 ~/.aws ~/.ssh
   ```

5. **Prove the boundary before trusting it:**
   ```
   sudo -u claude-agent cat ~/.aws/credentials                      # must: Permission denied
   sudo -u claude-agent security find-generic-password -s aws-vault # must: not found / denied
   sudo -u claude-agent ls /Users/mattias.johansson/code            # must: succeed
   ```

---

## Phase 2 — Make `claude-agent` usable (bulk of "All sessions")

6. **Install Claude for the agent** (per-user install; run as the agent):
   ```
   sudo -u claude-agent -i   # then run the claude installer in that shell
   ```

7. **Give the agent my config without my secrets.** Dotfiles are stowed from
   `~/code/bashconfig/stow` (which the agent can read). Stow the same packages
   into the agent's home:
   ```
   sudo -u claude-agent -i
   # in agent shell:
   stow -d /Users/mattias.johansson/code/bashconfig/stow -t ~ claude shell
   ```

8. **Fix hard-coded hook paths.** `settings.json` hooks reference
   `/Users/mattias.johansson/.claude/hooks/...`, which is the wrong home under
   the agent. Change hook commands to `python3 $HOME/.claude/hooks/...` (hook
   commands run through a shell, so `$HOME` expands per-user).

9. **Fix sandbox `allowRead`/`allowWrite` paths.** The built-in sandbox config
   lists `~/code`; under `claude-agent` that resolves to
   `/Users/claude-agent/code` (nonexistent). The shared repos are at
   `/Users/mattias.johansson/code` — use the ABSOLUTE path in the agent's
   `settings.json` sandbox entries, not `~/code`. Same for any other entry that
   actually lives in my home, not the agent's.

10. **Redo MCP OAuth as the agent.** First-time browser handshake fails
    in-sandbox. Authenticate Slack/Notion/etc. once as `claude-agent` under plain
    `claude` (no sandbox); the saved token in the agent's `~/.claude.json` then
    works inside.

---

## Phase 3 — Launcher + cut over

11. **Sudoers `NOPASSWD` rule** so launch needs no password each time
    (`sudo visudo -f /etc/sudoers.d/claude-agent`):
    ```
    mattias.johansson ALL=(claude-agent) NOPASSWD: /Users/claude-agent/.local/bin/claude
    ```
    (Adjust path to the agent's actual claude binary.)

12. **Rewrite the `claude` function** in `stow/shell/.bash_profile_funnel`:
    ```bash
    claude () {
        CLAUDE_CODE_USE_BEDROCK=1 \
        CLAUDE_CODE_ENABLE_AUTO_MODE=1 \
        ANTHROPIC_MODEL="eu.anthropic.claude-opus-4-8[1m]" \
        ANTHROPIC_DEFAULT_OPUS_MODEL="eu.anthropic.claude-opus-4-8[1m]" \
        ANTHROPIC_DEFAULT_HAIKU_MODEL="eu.anthropic.claude-haiku-4-5-20251001-v1:0" \
        aws-vault exec bedrock-dev -- sudo -u claude-agent \
          --preserve-env=AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY,AWS_SESSION_TOKEN,AWS_REGION,CLAUDE_CODE_USE_BEDROCK,CLAUDE_CODE_ENABLE_AUTO_MODE,ANTHROPIC_MODEL,ANTHROPIC_DEFAULT_OPUS_MODEL,ANTHROPIC_DEFAULT_HAIKU_MODEL \
          claude "${@}"
    }
    ```

---

## What this protects — and what it does not

- **Closed:** the agent cannot reach my login keychain (different user, empty
  keychain) or my `~/.aws` / `~/.ssh` files — by OS identity + filesystem perms,
  not by any name list. Renamed binaries, `ctypes`, and custom Mach clients all
  hit an empty keychain.
- **Bounded, not eliminated:** the agent still holds the short-term Bedrock STS
  creds in its env — it needs them to call the model. Pair with scoping
  `bedrock-dev` to Bedrock-only (or `AWS_BEARER_TOKEN_BEDROCK`, which structurally
  cannot reach other AWS services and expires in <=12h) so even that can't pivot.
- **Shared `~/code`:** both users read/write it, so a hostile agent could corrupt
  my working tree (not my secrets, not the remote git history). That is the cost
  of the seamless ACL option.

## Open items to verify on the live box

- Exact path of the agent's `claude` binary (for the sudoers rule).
- Whether `~/Library/Keychains` and `~/.aws`/`~/.ssh` are already owner-only
  (Phase 1 step 4) — assumed, not yet confirmed.
- That the built-in Bash sandbox applies normally under `sudo -u` (expected;
  `sudo` does not apply Seatbelt and Claude Code applies its own per command).
