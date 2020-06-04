#! /bin/bash

# (c) Kazansky137 - Thu Jun  4 20:25:47 UTC 2020

  debug=0

  function usage()
  { echo $0 [-h] [-f] [-d] -i icao dated_file.txt{.gz}
    exit
  }

  arg_prfd=""
  arg_icao=""

  while getopts "hfdpi:" option; do
    case "${option}" in
        h)
            usage
            ;;
        f)
            force=1
            ;;
        d)
            arg_prfd="-d"
            ;;
        p)
            profile=1
            ;;
        i)
            icao=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
  done
  shift "$((OPTIND-1))"

  if [ ! $icao ]; then
    usage
    exit 1
  fi

  in_file=$1

  if [ ! -r $in_file ]; then
    echo $0: file $in_file not readable
    exit 1
  fi

  echo Processing file $in_file

  in_name=$(basename $in_file)

  regname="^[[:alnum:]]+"
  regtime="[0-9]{6}-[0-9]{6}"

  if [[ $in_name =~ ($regname)-($regtime).txt$ ]]; then
    source="cat $in_file"
  elif [[ $in_name =~ ($regname)-($regtime).txt.gz$ ]]; then
    source="gzip -dcf $in_file"
  else
    echo $0: bad filename structure
    exit 1
  fi

# Various output files
  runfile=log-${BASH_REMATCH[2]}-$icao.txt
  txtfile=msg-${BASH_REMATCH[2]}-$icao.txt
  prdfile=prd-${BASH_REMATCH[2]}-$icao.bin

if [ ! $force ]; then
    if [ -e $runfile ]; then
        echo $0: file $runfile is already existing
        exit 1
    fi

    if [ -e $txtfile ]; then
        echo $0: file $txtfile is already existing
        exit 1
    fi

    if [ -e $prdfile ]; then
        echo $0: file $prdfile is already existing
        exit 1
    fi
fi

if [ $profile ]; then
    arg_prfd="--profile=$prdfile"
fi

# Environment variable for nice justified colored output
  export TERM_COLS=$(tput cols)

  $source | (./discover.py --file --output=raw --icao=$icao \
    $arg_prfd > $txtfile ) 2> $runfile

  touch -r $in_file $runfile $txtfile
  
  if [ $profile ]; then
    touch -r $in_file $prdfile
  fi

exit
