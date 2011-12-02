#!/bin/bash

which ack >/dev/null 2>&1
if [ "$?" -ne "0" ]; then
    echo 'ack not found; get it from http://betterthangrep.com/'
    echo 'you can easily install it using this command: sudo wget -O /usr/local/bin/ack http://betterthangrep.com/ack-standalone'
    exit 1
fi

echo 'Searching for potentially unused templates.'
echo 'This will take a long time. Why not get some cookies in the meantime?'
echo
find indico/MaKaC/webinterface/tpls/ -maxdepth 1 -name '*.tpl' -exec sh -c 'TPL=$(basename {} .tpl); ack -ch $TPL > /dev/null && echo "USED: $TPL" || echo "UNUSED: $TPL"' \;
