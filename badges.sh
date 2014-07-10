#! /bin/sh

COV=$(coverage report | tail -n 1 | rev | cut -f 1 -d " " | rev)

if [[ $COV < '50%' ]] ; then
  COLOUR=red;
elif [[ $COV < '75%' ]] ; then
  COLOUR=orange ;
elif [[ $COV < '90%' ]] ; then
  COLOUR=yellow ;
else
  COLOUR=brightgreen ;
fi

curl -# http://img.shields.io/badge/coverage-$COV-$COLOUR.svg > coverage-status.svg