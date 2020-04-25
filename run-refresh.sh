:

# (c) Kazansky137 - Sat Apr 25 15:38:50 UTC 2020

  pid=$(ps xu | grep ./flights-2-txt.py | grep -v grep | awk '{print $2;}')
  kill -1 $pid

exit
