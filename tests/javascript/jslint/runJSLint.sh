#!/bin/bash

RHINO=rhino
folderNames=( 'Admin' 'Collaboration' 'Core' 'Display' 'Legacy' 'Management' 'MaterialEditor' 'Timetable' )

for folderName in ${folderNames[@]}
do
  echo "----------->Scanning folder $folderName"
  for file in `find /home/jeremy/cds-indico/indico/htdocs/js/indico/$folderName -name '*.js'`;
  do
   echo File ${file}:
   $RHINO jslint.js $file
  done
done
