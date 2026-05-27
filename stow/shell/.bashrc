case $- in
  *i*) ;;
  *) return ;;
esac

[[ -r "/opt/homebrew/etc/profile.d/bash_completion.sh" ]] && . "/opt/homebrew/etc/profile.d/bash_completion.sh"
[[ -r "/opt/homebrew/share/bash-completion/completions/git" ]] && . "/opt/homebrew/share/bash-completion/completions/git"
[[ -r "/opt/homebrew/etc/bash_completion.d/aws_completer" ]] && . "/opt/homebrew/etc/bash_completion.d/aws_completer"

if [[ -z "$CLAUDECODE" && -s "$HOME/.scm_breeze/scm_breeze.sh" ]]; then
  . "$HOME/.scm_breeze/scm_breeze.sh"
fi

export NVM_DIR="$HOME/.nvm"
[[ -s "/opt/homebrew/opt/nvm/nvm.sh" ]] && . "/opt/homebrew/opt/nvm/nvm.sh"
[[ -s "$NVM_DIR/nvm.sh" ]] && . "$NVM_DIR/nvm.sh"
[[ -s "$NVM_DIR/bash_completion" ]] && . "$NVM_DIR/bash_completion"

[[ -s "$HOME/.rvm/scripts/rvm" ]] && . "$HOME/.rvm/scripts/rvm"
[[ -s "$HOME/.fzf.bash" ]] && . "$HOME/.fzf.bash"
[[ -s "$HOME/.asdf/asdf.sh" ]] && . "$HOME/.asdf/asdf.sh"
[[ -s "$HOME/.iterm2_shell_integration.bash" ]] && . "$HOME/.iterm2_shell_integration.bash"
[[ -s "$HOME/.cargo/env" ]] && . "$HOME/.cargo/env"

if command -v direnv >/dev/null 2>&1; then
  eval "$(direnv hook bash)"
fi

export BUN_INSTALL="$HOME/.bun"
export PNPM_HOME="$HOME/Library/pnpm"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$BUN_INSTALL/bin:$PNPM_HOME:$PATH"

set_prompt() {
  history -n
  history -a

  local prompt="\W"
  if type "__git_ps1" >/dev/null 2>&1; then
    prompt="$prompt$(__git_ps1 " \[\e[32m\](%s)\[\e[0m\]")"
  fi
  if [[ -n "$VIRTUAL_ENV" ]]; then
    prompt="$prompt \[\e[34m\]{${VIRTUAL_ENV##*/}}\[\e[0m\]"
  fi
  if [[ -n "$ACTIVE_PROFILE" ]]; then
    prompt="\[\e[31m\]($ACTIVE_PROFILE) \[\e[0m\]$prompt"
  fi
  PS1="$prompt\$ "
}

PROMPT_COMMAND=set_prompt
