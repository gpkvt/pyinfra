# Use modern completion system
autoload -Uz compinit
compinit
zstyle ':completion:*' menu select

fpath=(~/.dotfiles/zsh/zsh-completions $fpath)
