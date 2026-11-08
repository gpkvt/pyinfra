#!/bin/bash
sudo ufw disable
flatpak kill io.github.hepp3n.kdeconnect
sleep 3
sudo ufw enable
