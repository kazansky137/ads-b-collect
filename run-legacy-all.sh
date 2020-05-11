:

# (c) Kazansky137 - Mon May 11 20:45:32 UTC 2020

for file in $(ls archives/messages*); do
	echo $file
	./run-file.sh $file
done

exit
