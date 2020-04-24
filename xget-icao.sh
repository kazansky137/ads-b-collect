:

# (c) Kazansky137 - Fri Apr 24 19:28:54 CEST 2020

output=xout-icao-0.txt
tmpfile=/tmp/xget-$$.tmp

(	for file in $(find . -mtime -15 -name messages-20\*); do
 		echo $file >&2
 		gzip -dcf $file | cut -d" " -f3
 	done
) | sort | uniq | egrep -v "Resource|000000" > $tmpfile

(	for code in $(cat $tmpfile); do
		grep -q $code config/icao-tail.txt
		if [ $? -eq 0 ]; then
			continue
		fi
		grep -iw $code aircrafts/aircraftDatabase.csv | cut -d"," -f1-2 |\
			grep -v \"""\" | sed -e 's/"//g' -e 's/,/ : /' |\
			tr '[:lower:]' '[:upper:]'
	done
) | tee $output

exit
