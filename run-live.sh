:

# (c) Kazansky137 - Sun May  3 19:40:32 UTC 2020

# Various output files
  outfile=messages-$(date -u +%y%m%d-%H%M%S).txt
  flgfile=flights-$(date -u +%y%m%d-%H%M%S).txt
  runfile=log-$(date -u +%y%m%d-%H%M%S).txt
  txtfile=txt-$(date -u +%y%m%d-%H%M%S).txt
  touch $runfile

# Environment variable for nice justified colored output
  export TERM_COLS=$(tput cols)

  ./collect-2-txt.py 2>> $runfile | \
		tee $outfile | (./discover.py | tee $txtfile | \
			./flights-2-txt.py --sms=1 > $flgfile) 2>> $runfile &
  
  sleep 2
  head $runfile
  echo "Please run : tail -f $runfile"

exit
