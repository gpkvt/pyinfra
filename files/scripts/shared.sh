#!/bin/bash

echo "Use 'tmux -S /tmp/tmux_shared new-session -s shared' to start a new shared session."
echo "Change group ownership: 'chgrp tmuxshared /tmp/tmux_shared'"
echo "Execute 'tmux -S /tmp/shared attach -t shared' to join in, use '-r' for read-only mode."
