function dnames-fn {
    for ID in `docker ps | awk '{print $1}' | grep -v 'CONTAINER'`
    do
	docker inspect $ID | grep Name | head -1 | awk '{print $2}' | sed 's/,//g' | sed 's%/%%g' | sed 's/"//g'
    done
}

function dip-fn {
    echo "IP addresses of all named running containers"

    for DOC in `dnames-fn`
    do
        IP=`docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' "$DOC"`
        OUT+=$DOC'\t'$IP'\n'
    done
    echo -e $OUT | column -t
    unset OUT
}

function dex-fn {
    docker exec -it $1 ${2:-bash}
}

function di-fn {
    docker inspect $1
}

function dl-fn {
    docker logs -f $1
}

function drun-fn {
    docker run -it $1 $2
}

function dcr-fn {
    docker compose run $@
}

function dsr-fn {
    docker stop $1;docker rm $1
}

function drmc-fn {
       docker rm $(docker ps --all -q -f status=exited)
}

function drmid-fn {
       imgs=$(docker images -q -f dangling=true)
       [ ! -z "$imgs" ] && docker rmi "$imgs" || echo "no dangling images."
}

# in order to do things like dex $(dlab label) sh
function dlab {
       docker ps --filter="label=$1" --format="{{.ID}}"
}

function dc-fn {
        docker compose $*
}

alias dc=dc-fn
alias dcu="docker compose up -d"
alias dcd="docker compose down"
alias dcr=dcr-fn
alias dex=dex-fn
alias di=di-fn
alias dim="docker images"
alias dip=dip-fn
alias dl=dl-fn
alias dnames=dnames-fn
alias dps="docker ps"
alias dpsa="docker ps -a"
alias drmc=drmc-fn
alias drmid=drmid-fn
alias drun=drun-fn
alias dsp="docker system prune --all"
alias dsr=dsr-fn

function current_branch() {
  ref=$(git symbolic-ref HEAD 2> /dev/null) || return
  echo ${ref#refs/heads/}
}

function current_repository() {

  ref=$(git symbolic-ref HEAD 2> /dev/null) || return
  echo $(git remote -v | cut -d':' -f 2)
}

alias g='git'
alias gst='git status'
alias gup='git fetch && git rebase'
alias gc='git commit -a -v'
alias gco='git checkout'
alias gcm='git checkout master'
alias gb='git branch'
alias gba='git branch -a'
alias gcount='git shortlog -sn'
alias gcp='git cherry-pick'
alias glg='git log --stat --max-count=5'
alias glgg='git log --graph --max-count=5'
alias gss='git status -s'
alias ga='git add -A'
alias gm='git merge'
alias grh='git reset HEAD'
alias grhh='git reset HEAD --hard'
alias gl='git pull origin $(current_branch)'
alias gp='git push origin $(current_branch)'
alias gpnp='git pull origin $(current_branch) && git push origin $(current_branch)'

alias ls='ls --color=never'
alias ll='ls -lah --color=never'
alias grep='grep --color=auto'
alias a='tmux attach'
alias bat='batcat'
alias rep='reptyr'
alias tools="echo \"${tools}\""
unalias duf 2> /dev/null

alias tt='function _tt(){ timetagger start "$*" };_tt'
alias ts='timetagger status'
alias te='timetagger stop'
alias ta='timetagger app'

alias cat='bat -pp'
