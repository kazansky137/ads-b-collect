:

# (c) Kazansky137 - Sat Apr 25 21:38:06 UTC 2020

  pid=$(ps xu | grep ./collect-2-txt.py | grep -v grep | awk '{print $2;}')
  kill -1 $pid

exit
