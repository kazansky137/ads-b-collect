#! /bin/bash

# (c) Kazansky137 - Mon Aug 24 20:01:20 CEST 2020

# 14  7 * * * $HOME/ads-b-collect/aircrafts/download.sh

# set -x

  cd $HOME/ads-b-collect/aircrafts
  BASE=https://opensky-network.org/datasets/metadata

  (  curl -s -O $BASE/aircraftDatabase.csv
     curl -s -O $BASE/doc8643AircraftTypes.csv
     curl -s -O $BASE/doc8643Manufacturers.csv
     ls -l *.csv
     scp -rp aircraftDatabase.csv \
		nina@10.0.0.32:iCloud/Documents/Belradar24/20-aircraft-db/
  ) | mail -s "[/adsb] download" info@belradar24.be

exit
