:

# (c) Kazansky137 - Sat Apr 18 16:37:51 UTC 2020

  pid=$(ps xu | grep ./collect-2-txt.py | grep -v grep | awk '{print $2;}')
  kill -2 $pid

exit
