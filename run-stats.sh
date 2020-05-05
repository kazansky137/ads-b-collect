:

# (c) Kazansky137 - Tue May  5 20:38:51 UTC 2020

  pid=$(ps xu | grep ./collect-2-txt.py | grep -v grep | awk '{print $2;}')
  if [ ! -z $pid ]; then
    kill -1 $pid
  fi

  pid=$(ps xu | grep ./discover.py | grep -v grep | awk '{print $2;}')
  if [ ! -z $pid ]; then
    kill -1 $pid
  fi

exit
