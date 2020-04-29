#! /bin/bash

# (c) Kazansky137 - Wed Apr 29 20:21:45 UTC 2020

  if [ $# -ne 1 ]; then
    echo Usage: $0 file.txt[.gz]
    exit 1
  fi

  in_file=$1

  if [ ! -r $in_file ]; then
    echo $0: file $in_file not readable
    exit 1
  fi

  echo Processing file $in_file

  in_name=$(basename $in_file)

  regname="^[[:alnum:]-]+"

  if [[ $in_name =~ ($regname).txt$ ]]; then
    source="cat $in_file"
  elif [[ $in_name =~ ($regname).txt.gz$ ]]; then
    source="gzip -dcf $in_file"
  else
    echo $0: bad filename structure
    exit 1
  fi

# Various output files
  chk=${BASH_REMATCH[1]}-checks.txt
  runfile=${BASH_REMATCH[1]}-log.txt

# Environment variable for nice justified colored output
  export TERM_COLS=$(tput cols)

  $source | awk '{print $2, $3'} | ./discover.py > $chk 2> $runfile
  touch -r $in_file  $chk  $runfile
  
exit
