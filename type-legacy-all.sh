#! /bin/bash

# (c) Kazansky137 - Sat May  9 21:27:18 UTC 2020

# Set magic characters to legacy BR24 message files.
#
# %MBR24-1.0
# 1573159410.465846062 8D484F18202CC378C4A820DEF36F 484F18 Heavy KLM81J__
#	RE='[0-9]{10}.[0-9]{9}' - Nfields=4,5
# 
# %MBR24-2.0
# VH 1587934610.940519571 8D7816349911C31BB004063F8FAB 781634 500 64.0 0
#	RE='[A-Z]{2}' - Nfields=5,6,7
#
# %MBR24-3.0
# 1588529721.211116791 5DA5B7690170D7
#	RE='[0-9]{10}.[0-9]{9}' - Nfields=2

# set -x

  function usage()
  {	echo $0 [-h] [-f] -l location
	exit
  }

  function add_type()
  {	tmp=tmp-$(basename $1 .gz)
	echo $2 $3 > $tmp
 	gzip -dcf $1 | tail -n +$4 >> $tmp
 	gzip -v9 $tmp
 	touch -r $1 $tmp.gz
 	dir=$(dirname $1)
 	name=$(basename $1 .gz)
 	rm -f $1
 	mv $tmp.gz $dir/$name.gz
  }

  while getopts "hfl:" option; do
	case "${option}" in
		h)
			usage
			;;
		f)
			force=1
			;;
		l)
			location=${OPTARG}
			;;
		*)
			usage
			;;
	esac
  done
  shift $((OPTIND-1))

  if [ -z "${location}" ]; then
		usage
  fi

  if [ ! $force ]; then
	echo Do not force
  fi

  files="find archives -type f -name messages\* | sort"

  for file in $(eval $files); do
	echo $file

	line=$(gzip -dcf $file | head -1)
	first=$(echo $line |  awk '{print $1;}')
	nfields=$(echo $line | awk '{print NF;}')
	offset=1

	re0='MBR24-[0-3].0'
	re1='[0-9]{10}.[0-9]{9}'
	re2='[A-Z]{2}'

	if [[ "$first" =~ $re0 ]]   && [ $nfields -ge 1 ]; then
  		if [ ! $force ]; then
			echo "Already typed - skipping"
			continue
  		else
			echo "Already typed - overwrite"
			offset=2
		fi
    fi

	line=$(gzip -dcf $file | tail -n +$offset | head -1)
	first=$(echo $line | awk '{print $1;}')
	nfields=$(echo $line | awk '{print NF;}')

	if [[ "$first" =~ $re1 ]] && [ $nfields -ge 4 ]; then
		magic=%MBR24-1.0
	elif [[ "$first" =~ $re2 ]] && [ $nfields -ge 5 ]; then
		magic=%MBR24-2.0
	elif [[ "$first" =~ $re1 ]] && [ $nfields -eq 2 ]; then
		magic=%MBR24-3.0
	else
		magic=%MBR24-0.0
		continue
	fi
 	add_type $file $magic $location $offset
  done

exit
