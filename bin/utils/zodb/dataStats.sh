# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

#!/bin/bash

# Absolute path to this script.
SCRIPT=$(readlink -f $0)

# Absolute directory's path this script
SCRIPTPATH=`dirname $SCRIPT`

while getopts "hb:t:e:" opt; do
  case $opt in
    b)
      BACKUP_PATH=$OPTARG
      ;;
    t)
      case $OPTARG in
          */)
            TMP_PATH=$OPTARG
            DATA_PATH=$OPTARG"Data.fs"
            ;;
          *)
            TMP_PATH=/$OPTARG
            DATA_PATH=$OPTARG"/Data.fs"
            ;;
      esac
      ;;
    e)
      EMAIL=$OPTARG
      ;;
    h)
      echo "usage: dataStats.sh -b /backup/path -t /tmp/ -e john@doe.com"
      echo ""
      echo "    -h   show this help message and exit"
      echo "    -b   the backup directory path"
      echo "    -t   a temporary directory"
      echo "    -e   the email address to which send the reports. If you want multiple recipients, use quotes and commas, i.e. -e 'john@doe.com, john@smith.com'"
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

if [ -z $TMP_PATH ] || [ -z $EMAIL ] || [ -z $BACKUP_PATH ]; then
    echo "All parameters are mandatory. Use -h for details"
    exit 1
fi

repozo -Rv -r $BACKUP_PATH -o $DATA_PATH

#---- [1/6] Objects_stats ------------
SUBJECT="[ZODB-Stats] Objects_stats"
ELEMENTS_TO_DISPLAY=100
python $SCRIPTPATH/objects_stats.py -f $DATA_PATH -n $ELEMENTS_TO_DISPLAY > TMP_PATH"objects_stats.txt"
EMAILMESSAGE=TMP_PATH"objects_stats.txt"
mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
rm TMP_PATH"objects_stats.txt"


#---- [2/6] Class_stats ------------
SUBJECT="[ZODB-Stats] Class_stats"
ELEMENTS_TO_DISPLAY=100
python $SCRIPTPATH/class_stats.py -f $DATA_PATH -n $ELEMENTS_TO_DISPLAY > TMP_PATH"class_stats.txt"
EMAILMESSAGE=TMP_PATH"class_stats.txt"
mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
rm TMP_PATH"class_stats.txt"


#---- [3/6] Transactions_stats ------------
SUBJECT="[ZODB-Stats] Transactions_stats"
DAYS=7
python $SCRIPTPATH/transactions_stats.py -f $DATA_PATH -a $DAYS > TMP_PATH"transactions_stats.txt"
EMAILMESSAGE=TMP_PATH"transactions_stats.txt"
mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
rm TMP_PATH"transactions_stats.txt"


#---- [4/6] Simple consistency checker ------------
SUBJECT="[ZODB-Stats] Consistency Checker"
python $SCRIPTPATH/fstest.py $DATA_PATH > TMP_PATH"cchecker.txt"

#If the file is empy -> no error detected
if [ `ls -l TMP_PATH"cchecker.txt" | awk '{print $5}'` -eq 0 ]
then
    echo "No error detected" | mail -s "$SUBJECT" "$EMAIL"
else
    EMAILMESSAGE=TMP_PATH"cchecker.txt"
    mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
fi;

rm TMP_PATH"cchecker.txt"


#---- [5/6] Amount of data added per day ------------
SUBJECT="[ZODB-Stats] Amount of data per day"
DAYS=7
python $SCRIPTPATH/sizeIncreasing_stats.py -d $DAYS $DATA_PATH > TMP_PATH"data.txt"
EMAILMESSAGE=TMP_PATH"data.txt"
mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
rm TMP_PATH"data.txt"


#---- [6/6] Most used classes ------------
SUBJECT="[ZODB-Stats] Most modified classes during last two days"
DAYS=2
python $SCRIPTPATH/mostUsedClasses.py -d $DAYS $DATA_PATH > TMP_PATH"used.txt"
EMAILMESSAGE=TMP_PATH"used.txt"
mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
rm TMP_PATH"used.txt"


#Remove the Data.fs
rm $DATA_PATH