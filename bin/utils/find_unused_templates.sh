# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

which ag >/dev/null 2>&1
if [ "$?" -ne "0" ]; then
    echo 'ag (the silver searcher) not found'
    exit 1
fi

echo 'Searching for potentially unused templates.'
echo 'This will take a long time. Why not get some cookies in the meantime?'
echo
find indico/legacy/webinterface/tpls/ -maxdepth 1 -name '*.tpl' -exec sh -c 'TPL=$(basename {} .tpl); ag -c --nofilename --silent --ignore indico/translations/ --ignore ext_modules/ $TPL > /dev/null || echo "UNUSED: $TPL"' \;
