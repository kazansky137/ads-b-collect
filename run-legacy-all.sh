:

# (c) Kazansky137 - Thu May 14 17:29:37 UTC 2020

for file in $(ls archives/messages*); do
	./run-file.sh $* $file
done

exit
