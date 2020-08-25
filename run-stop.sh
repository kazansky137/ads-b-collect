:

# (c) Kazansky137 - Tue Aug 25 20:17:44 UTC 2020

  
  pid=$(ps xu | grep ./collect-2-txt.py | grep -v grep | awk '{print $2;}')
  kill -2 $pid

  lstfile=last-log
  rm -f $lstfile

exit
