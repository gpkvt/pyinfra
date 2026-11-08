# Show tasks
if nc -zw1 192.168.42.100 53589; then
  /usr/bin/task sync
fi
/usr/bin/task list
