:

# (c) Kazansky137 - Sat May  9 21:27:18 UTC 2020

  progs="./collect-2-txt.py|./discover.py"
  pids=$(ps xu | egrep $progs | grep -v grep | awk '{print $2;}')

  for pid in $pids; do
    kill -1 $pid
  done

exit
