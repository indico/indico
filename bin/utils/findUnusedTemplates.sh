# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

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
