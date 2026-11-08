#!/bin/bash

session="checkmail"

tmux new-session -d -s ${session}

window=1
tmux rename-window -t ${session}:${window} 'maillog'
tmux select-window -t ${session}:${window}

tmux send-keys 'clear;ssh proxy1 "clear;tail /var/log/mail.log -f"' C-m
tmux select-pane -T 'mail.log 1'
tmux split-window -v
tmux select-pane -T 'mail.log 2'
tmux send-keys 'clear;ssh proxy2 "clear;tail /var/log/mail.log -f"' C-m

window=2
tmux new-window -t ${session}:${window}
tmux select-window -t ${session}:${window}
tmux rename-window -t ${session}:${window} 'mailq'

tmux send-keys 'clear;ssh proxy1' C-m 'clear;mailq' C-m
tmux select-pane -T 'proxy1'
tmux split-window -v
tmux select-pane -T 'proxy2'
tmux send-keys 'clear;ssh proxy2' C-m 'clear;mailq' C-m

window=3
tmux new-window -t ${session}:${window}
tmux select-window -t ${session}:${window}
tmux rename-window -t ${session}:${window} 'salt'
tmux send-keys 'clear;ssh salt' C-m
tmux select-pane -T 'salt'

tmux select-window -t ${session}:2
tmux attach-session -t ${session}
