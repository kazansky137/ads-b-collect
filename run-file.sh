#! /bin/bash

# (c) Kazansky137 - Thu Jun  4 20:25:47 UTC 2020

  debug=0

  function usage()
  { echo $0 [-h] [-f] [-d] dated_file.txt{.gz}
    exit
  }

  args_prd=""
  args_prf=""

  while getopts "hfdp" option; do
    case "${option}" in
        h)
            usage
            ;;
        f)
            force=1
            ;;
        d)
            args_prd="-d"
            args_prf="-d"
            ;;
        p)
            profile=1
			;;
        *)
            usage
            ;;
    esac
  done
  shift "$((OPTIND-1))"

  in_file=$1

  if [ ! -r $in_file ]; then
    echo $0: file $in_file not readable
    exit 1
  fi

  echo Processing file $in_file

  in_name=$(basename $in_file)

  regname="^[[:alnum:]]+"
  regtime="[0-9]{6}-[0-9]{6}"
  regicao="[0-9A-Z]{6}"

  if [[ $in_name =~ ($regname)-($regtime)((-$regicao)*).txt$ ]]; then
    source="cat $in_file"
  elif [[ $in_name =~ ($regname)-($regtime)((-$regicao)*).txt.gz$ ]]; then
    source="gzip -dcf $in_file"
  else
    echo $0: bad filename structure
    exit 1
  fi

# Various output files
  flgfile=flg-${BASH_REMATCH[2]}${BASH_REMATCH[3]}.txt
  runfile=log-${BASH_REMATCH[2]}${BASH_REMATCH[3]}.txt
  txtfile=txt-${BASH_REMATCH[2]}${BASH_REMATCH[3]}.txt 
  prffile=prf-${BASH_REMATCH[2]}${BASH_REMATCH[3]}.bin
  prdfile=prd-${BASH_REMATCH[2]}${BASH_REMATCH[3]}.bin

if [ ! $force ]; then
	if [ -e $flgfile ]; then
  		echo $0: file $flgfile is already existing
  		exit 1
	fi

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

	if [ -e $prffile ]; then
  		echo $0: file $prffile is already existing
 	 	exit 1
    fi
fi

if [ $profile ]; then
	args_prd=$args_prd" --profile=$prdfile"
	args_prf=$args_prf" --profile=$prffile"
fi

# Environment variable for nice justified colored output
  export TERM_COLS=$(tput cols)

  $source | (./discover.py --file $args_prd | tee $txtfile | \
             ./flights-2-txt.py --file $args_prf > $flgfile) 2> $runfile
touch -r $in_file $flgfile $runfile $txtfile
  
if [ $profile ]; then
	touch -r $in_file $prffile $prdfile
fi

exit
