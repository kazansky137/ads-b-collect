:

# (c) Kazansky137 - Wed Apr 29 20:21:45 UTC 2020

  pid=$(ps xu | grep ./collect-2-txt.py | grep -v grep | awk '{print $2;}')
  kill -1 $pid

  pid=$(ps xu | grep ./discover.py | grep -v grep | awk '{print $2;}')
  kill -1 $pid

exit
