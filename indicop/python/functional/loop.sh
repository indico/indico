#!/bin/bash
echo '--------------------- NEW RUN -------------------' >> selog.txt
for a in `seq 20`
do
  echo "===================== pass $a ====================="
  sudo PYTHONPATH=/home/jeremy/cds-indico/indico/ nosetests -v >> selog.txt 2>&1
done
