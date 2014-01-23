# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

import os
import sys
## TO BE CHANGED:
#sys.path.append('C:/Documents and Settings/smilenko/My Documents/project/indico/code/code')
from distutils import sysconfig
from datetime import datetime
from indico.core.config import Config

# The folder that contains the current database file.
currentPath = Config.getInstance().getCurrentDBDir()

# The folder that contains the database backups.
backupsPath = Config.getInstance().getDBBackupsDir()

# Name of the database file.
dataFile = "data.fs"

python = os.path.join(sysconfig.get_config_vars()["exec_prefix"], "python")
## TO BE CHANGED:
repozo = "C:/Python23/Scripts/repozo.py"

def main():
    tmp = set(os.listdir(backupsPath))
    name = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    os.system("%s %s %s %s %s %s %s %s %s"%(python, repozo, "-B", "-f",\
    "\"%s\""%os.path.join(currentPath, dataFile), "-F", "-z", "-r",\
    "\"%s\""%backupsPath))
    names = set(os.listdir(backupsPath))
    names.difference_update(tmp)
    for n in names:
        os.rename(os.path.join(backupsPath, n), os.path.join(backupsPath,\
        "".join([name, os.path.splitext(n)[1]])))

if __name__ == '__main__':
    main()
