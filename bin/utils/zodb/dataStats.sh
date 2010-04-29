#!/bin/bash

while getopts "hb:f:e:" opt; do
  case $opt in
    b)
      BACKUP_PATH=$OPTARG
      ;;
    f)
      DATA_PATH=$OPTARG
      ;;
    e)
      EMAIL=$OPTARG
      ;;
    h)
      echo "usage: dataStats.sh -b /backup/path -f /tmp/Data.fs -e john@doe.com"
      echo ""
      echo "    -h   show this help message and exit"
      echo "    -b   the backup directory path"
      echo "    -f   where you want to restore the Data.fs"
      echo "    -e   the email address to which send the reports"
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

if [ -z $DATA_PATH ] || [ -z $EMAIL ] || [ -z $BACKUP_PATH ]; then
    echo "All parameters are mandatory. Use -h for details"
    exit 1
fi

repozo -Rv -r $BACKUP_PATH -o $DATA_PATH

#---- [1/6] Objects_stats ------------
SUBJECT="[ZODB-Stats] Objects_stats"
ELEMENTS_TO_DISPLAY=100
python objects_stats.py -f $DATA_PATH -n $ELEMENTS_TO_DISPLAY > "/tmp/objects_stats.txt"
EMAILMESSAGE="/tmp/objects_stats.txt"
mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
rm "/tmp/objects_stats.txt"


#---- [2/6] Class_stats ------------
SUBJECT="[ZODB-Stats] Class_stats"
ELEMENTS_TO_DISPLAY=100
python class_stats.py -f $DATA_PATH -n $ELEMENTS_TO_DISPLAY > "/tmp/class_stats.txt"
EMAILMESSAGE="/tmp/class_stats.txt"
mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
rm "/tmp/class_stats.txt"


#---- [3/6] Transactions_stats ------------
SUBJECT="[ZODB-Stats] Transactions_stats"
DAYS=7
python transactions_stats.py -f $DATA_PATH -a $DAYS > "/tmp/transactions_stats.txt"
EMAILMESSAGE="/tmp/transactions_stats.txt"
mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
rm "/tmp/transactions_stats.txt"


#---- [4/6] Simple consistency checker ------------
SUBJECT="[ZODB-Stats] Consistency Checker"
python fstest.py $DATA_PATH > "/tmp/cchecker.txt"

#If the file is empy -> no error detected
if [ `ls -l "/tmp/cchecker.txt" | awk '{print $5}'` -eq 0 ]
then
    echo "No error detected" | mail -s "$SUBJECT" "$EMAIL"
else
    EMAILMESSAGE="/tmp/cchecker.txt"
    mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
fi;

rm "/tmp/cchecker.txt"


#---- [5/6] Amount of data added per day ------------
SUBJECT="[ZODB-Stats] Amount of data per day"
DAYS=7
python sizeIncreasing_stats.py -d $DAYS $DATA_PATH > "/tmp/data.txt"
EMAILMESSAGE="/tmp/data.txt"
mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
rm "/tmp/data.txt"


#---- [6/6] Most used classes ------------
SUBJECT="[ZODB-Stats] Most modified classes during last two days"
DAYS=2
python mostUsedClasses.py -d $DAYS $DATA_PATH > "/tmp/used.txt"
EMAILMESSAGE="/tmp/used.txt"
mail -s "$SUBJECT" "$EMAIL" < $EMAILMESSAGE
rm "/tmp/used.txt"


#Remove the Data.fs
rm $DATA_PATH