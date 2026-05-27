export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

if [[ -z "$INTELLIJ_ENVIRONMENT_READER" ]]; then
  stty stop undef 2>/dev/null
  stty start undef 2>/dev/null
fi

shopt -s histappend
export HISTCONTROL=ignoreboth
export HISTFILESIZE=
export HISTSIZE=9999999
export HISTTIMEFORMAT="%d/%m/%y %T "

export PATH="/opt/homebrew/bin:$HOME/bin:$HOME/bin/scripts:$HOME/code/futils/bin:$PATH"
export PATH="$PATH:$HOME/code/apl-inspired-filters/target/release:$HOME/Library/Python/3.14/bin"

export EDITOR=vim
export MAVEN_OPTS="-Xmx1536m -Xms128m -XX:+HeapDumpOnOutOfMemoryError"
export ANT_OPTS=-Xmx1024m
export BC_LINE_LENGTH=200000000
export AWS_SDK_JS_SUPPRESS_MAINTENANCE_MODE_MESSAGE=1

# Disable npm lifecycle scripts by default; opt in per command with npm_config_ignore_scripts=false.
export npm_config_ignore_scripts=true

[[ -f "$HOME/.bashrc" ]] && . "$HOME/.bashrc"

enable-profile() {
  local instance=${1:?missing profile}
  local credentials
  unset AWS_REGION AWS_DEFAULT_REGION
  credentials=$(aws-vault export "$instance" --format=export-env) || return 1
  eval "$credentials"
  export ACTIVE_PROFILE="$instance"
}

notes() {
  if [[ $# -eq 0 ]]; then
    tail -n 20 "$HOME/Documents/notes/main.md"
  else
    rg -C5 "$@" "$HOME/Documents/notes/"
  fi
}

todo() {
  if [[ $# -eq 0 ]]; then
    vim "$HOME/Documents/notes/todos"
  else
    printf '%s\n' "$*" >>"$HOME/Documents/notes/todos"
  fi
}

todos() {
  echo "=== explicit todos ==="
  sed 's/^/- /' "$HOME/Documents/notes/todos"
  echo
  echo "=== found in notes ==="
  rg TODO "$HOME/Documents/notes"
}

aws-regions() {
  cat <<'HERE'
us-east-1       US East (N. Virginia)
us-east-2       US East (Ohio)
us-west-1       US West (N. California)
us-west-2       US West (Oregon)
eu-north-1      Europe (Stockholm)
eu-west-1       Europe (Ireland)
eu-west-2       Europe (London)
eu-west-3       Europe (Paris)
eu-central-1    Europe (Frankfurt)
eu-central-2    Europe (Zurich)
ap-south-1      Asia Pacific (Mumbai)
ap-southeast-1  Asia Pacific (Singapore)
ap-southeast-2  Asia Pacific (Sydney)
ap-northeast-1  Asia Pacific (Tokyo)
ca-central-1    Canada (Central)
sa-east-1       South America (Sao Paulo)
HERE
}

json-structure() {
  jq '[path(..)|map(if type=="number" then "[]" else tostring end)|join(".")|split(".[]")|join("[]")]|unique|map("."+.)|.[]'
}

aws-logs() {
  local group=$1
  if [[ -z "$group" ]]; then
    group=$(aws logs describe-log-groups | jq -r '.logGroups[].logGroupName' | fzf)
  fi
  aws logs tail --since 1h --follow "$group"
}

summary() {
  local query
  query=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(" ".join(sys.argv[1:])))' "$@")
  curl -s "https://api.duckduckgo.com/?format=json&q=$query" | jq -r .Abstract | fold -s -w 72
}

git-pretty-format() {
  echo "%h, %H      (abbr) commit hash"
  echo "%p, %P      (abbr) parent hashes"
  echo "%[ac][ne]   author/committer name/email"
  echo "%[ac][Is]   author/committer date (short/ISO)"
  echo "%[fs]       (sanitized) subject"
  echo "%[bB]       body (raw)"
  echo "For more placeholders, see man git-log."
}

git-hot() {
  local i=1
  local ref
  for ref in $(git for-each-ref --count=20 --sort=-committerdate refs/remotes/ --format='%(refname:short)'); do
    echo "  [$i] $ref"
    declare -g "e$((i++))=${ref#*/}"
  done
}

git-commit-message-completion() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return
  fi

  local branch ticket
  branch=$(git rev-parse --abbrev-ref HEAD)
  ticket=$(echo "$branch" | grep -Eo '^[[:alpha:]]+-[0-9]+')
  if [[ -n "$ticket" ]]; then
    ticket="$ticket: "
  fi

  COMPREPLY=("-m '$ticket")
  compopt -o nospace 2>/dev/null
}

pd() {
  local when=${1:-$(date)}
  gdate -d "$when" '+%A %Y %m %d %H %M %S %z %s'
}

allcerts() {
  if [[ $# -eq 0 ]]; then
    openssl crl2pkcs7 -nocrl -certfile /dev/stdin | openssl pkcs7 -print_certs -text -noout
  else
    openssl crl2pkcs7 -nocrl -certfile "$1" | openssl pkcs7 -print_certs -text -noout
  fi
}

getcert() {
  local server=${1:?missing servername}
  </dev/null openssl s_client -connect "$server:443" | openssl x509 -noout -text
}

retry() {
  until "$@"; do
    sleep 1
  done
}

show() {
  vimcat "$(command -v "$1")"
}

c() {
  cd "$HOME/code/$({ echo .; ls "$HOME/code"; } | fzf)" || return
}

kube-get-contexts() {
  kubectl config get-contexts
}

kube-get-pods() {
  kubectl get pods --namespace "${1:-default}"
}

kube-get-pods-all-ns() {
  kubectl get pods --all-namespaces
}

alias av=aws-vault
alias noprofile='unset ACTIVE_PROFILE ${!AWS_*}'
alias b=booger
alias fabric=fabric-ai
alias to-human-number='numfmt --to=iec-i --suffix=B'
alias histogram='sort | uniq -c | sort -rn'
alias f=fzf
alias fzfp="fzf --preview 'bat --style=numbers --color=always --line-range :500 {}'"
alias stripansi="sed -e 's/\x1b\[[0-9;]*m//g'"
alias uuid=uuidgen
alias asciibanner=figlet
alias banner=figlet
alias markdown-render='npx termd'
alias snippets=tldr
alias vimtodo="vim ~/Documents/notes/todos"
alias td=todo
alias chars='grep -o .'
alias upper='tr [:lower:] [:upper:]'
alias lower='tr [:upper:] [:lower:]'
alias d='date "+%Y-%m-%d"'
alias vecka='date +"%U"'
alias nowrap='less -SE'
alias hl='grep --color -e'
alias serve='python3 -m http.server'
alias mkpasswd='openssl rand -base64 48'
alias v='test -d venv || python3 -m venv venv && . venv/bin/activate'
alias t='tree --gitfile ~/.gitignore_global --gitignore -L 3'
alias ll='ls -lhSA'
alias l=ll
alias gcom='git checkout main 2>/dev/null || git checkout master'
alias gdm='git diff origin/main || git diff origin/master'
alias gmm='git merge origin/main || git merge origin/master'
alias gg='git grep -iEI'
alias gh='git-hot'
alias gn='git next'
alias gp='git prev'
alias gitauthors='git log --pretty=format:%an | sort | uniq -c | sort -rn'
alias gitbranches='git branch -a --sort=-committerdate --color -v | head'
alias git-diff-ignore-whitespace='git diff --word-diff-regex=[^[:space:]]'
alias k=kubectl
alias kgc='kube-get-contexts'
alias kgp='kube-get-pods'
alias kgpa='kube-get-pods-all-ns'
alias ka='kubectl apply -f'
alias kattach='kubectl attach -it'
alias ke='kubectl exec -it'
alias kd='kubectl describe pod'
alias kk='kubectl delete pod'
alias kl='kubectl logs'
alias kuc='kubectl config use-context'
alias ss=shellcheck
alias cert='openssl x509 -noout -text'
alias whatismyip='dig -4 @resolver1.opendns.com myip.opendns.com +short'
alias whatismyipgoogle='dig TXT +short o-o.myaddr.l.google.com @ns1.google.com'
alias dns-cache-clear='sudo killall -HUP mDNSResponder'

complete -C aws_completer aws 2>/dev/null
complete -F _longopt curl 2>/dev/null
complete -o bashdefault -F git-commit-message-completion gc 2>/dev/null

export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && . "$HOME/.sdkman/bin/sdkman-init.sh"

[[ -f "$HOME/.bash_profile_funnel" ]] && . "$HOME/.bash_profile_funnel"
