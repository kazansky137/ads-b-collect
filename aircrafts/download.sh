#! /bin/bash

# (c) Kazansky137 - Tue Sep  1 13:41:19 CEST 2020

# 15 19 * * * $HOME/ADS-B/00-prod-collect/aircrafts/download.sh

# set -x
  cd $HOME/ADS-B/00-prod-collect/aircrafts
  BASE=https://opensky-network.org/datasets/metadata

  (  curl -s -O $BASE/aircraftDatabase.csv
     curl -s -O $BASE/doc8643AircraftTypes.csv
     curl -s -O $BASE/doc8643Manufacturers.csv
     ls -l *.csv
     scp -rp aircraftDatabase.csv \
		nina@10.0.0.32:iCloud/Documents/Belradar24/20-aircraft-db/
  ) | mail -s "[/adsb] download" info@belradar24.be

exit
