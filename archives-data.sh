:

# (c) Kazansky137 - Wed Nov 11 19:39:47 CET 2020

  host=sdsrv1
  rdir=ADS-B/data-sdosint1

  for file in $(find . -maxdepth 1 -type f -name \*.txt); do
    if [ $(lsof $file 2> /dev/null | wc -l) -eq 0 ] ; then
        echo Moving $file to sdsrv1:ADS-B/data-sdosint1
        gzip -v9 $file
  		if [ $(hostname -s) == $host ]; then
        	mv $file.gz $HOME/$rdir
		else
			scp -p $file.gz $host:$rdir
        	rm $file.gz
		fi
    else
        echo File $file busy
    fi
  done

exit
