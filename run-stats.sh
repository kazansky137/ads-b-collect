:

# (c) Kazansky137 - Tue Apr 21 17:00:21 UTC 2020

  pid=$(ps u | grep ./collect-2-txt.py | grep -v grep | awk '{print $2;}')
  kill -1 $pid

exit
