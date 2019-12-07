:

# (c) Kazansky137 - Sat Dec  7 22:53:15 CET 2019

# Input messages source
  src1090="10.0.0.28 30002 raw"

# Various output files
  outfile=messages-$(date -u +%y%m%d-%H%M%S).txt
  flgfile=flights-$(date -u +%y%m%d-%H%M%S).txt
  runfile=log-$(date -u +%y%m%d-%H%M%S).txt
  touch $runfile

  ./collect-2-txt.py $src1090 2>> $runfile | \
		tee $outfile | ./flights-2-txt.py > $flgfile 2>> $runfile &
  
  echo "Please run : tail -f $runfile"

exit
