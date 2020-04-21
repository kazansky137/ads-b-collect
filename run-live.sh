:

# (c) Kazansky137 - Tue Apr 21 17:00:21 UTC 2020

# Input messages source
  src1090="10.0.0.97 30002 raw"
# src1090="10.0.0.28 30002 raw"

# Various output files
  outfile=messages-$(date -u +%y%m%d-%H%M%S).txt
  flgfile=flights-$(date -u +%y%m%d-%H%M%S).txt
  runfile=log-$(date -u +%y%m%d-%H%M%S).txt
  touch $runfile

# Environment variable for nice justified colored output
  export TERM_COLS=$(tput cols)

  ./collect-2-txt.py $src1090 2>> $runfile | \
		tee $outfile | ./flights-2-txt.py > $flgfile 2>> $runfile &
  
  sleep 1
  head $runfile
  echo "Please run : tail -f $runfile"

exit
