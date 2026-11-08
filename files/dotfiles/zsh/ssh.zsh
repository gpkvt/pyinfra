# Add SSH keys to keychain
find ~/.ssh -type f -regextype egrep -regex '.*/id_[^.]+$' | xargs /usr/bin/keychain --nogui
source ~/.keychain/$(hostname)-sh
