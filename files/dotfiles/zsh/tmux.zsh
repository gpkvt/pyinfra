# Start tmux
# if [ -z ${TMUX} ]; then tmux; fi

# activate tmux powerline
if [ ! -z ${TMUX} ]; then
  tmux set-option -g status-left "#{tmux_mode_indicator}#(~/.tmux/plugins/tmux-powerline/powerline.sh left)"
  ~/.tmux/plugins/tmux-mode-indicator/mode_indicator.tmux
  #~/.tmux/plugins/tmux-powerline/main.tmux
fi
