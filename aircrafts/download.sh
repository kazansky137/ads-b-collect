#! /bin/bash

# (c) Kazansky137 - Sun Jun 14 17:41:22 CEST 2020

# 14  7 * * * $HOME/ads-b-collect/aircrafts/download.sh

  set -x

  (  curl -O https://opensky-network.org/datasets/metadata/aircraftDatabase.csv
     curl -O https://opensky-network.org/datasets/metadata/doc8643AircraftTypes.csv
     curl -O https://opensky-network.org/datasets/metadata/doc8643Manufacturers.csv
     ls -l *.csv
  ) | mail -s "[/adsb] download" info@belradar24.be

exit
