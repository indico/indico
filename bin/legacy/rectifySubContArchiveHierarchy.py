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

# This script is used to rectify the folder hierarchy on the filesystem for the
# subcontributions materials. Currently a subcontribution resource is in a
# folder which is itself directly located in the conference folder. This script
# corrects this and creates a folder for the subcontribution in which are put
# all the resources'folders. This subcontribution folder is put in the
# contribution folder.

# Folder hierarchy:
#
# Before:                             After:
#
# 2005                                2005
# |                                   |
# C0511                               C0511
# |_______________                    |
# |     |        |                    c86
# c86   sc4.r0   sc4.r1               |___________
# |_____                              |     |    |
# |    |                              sc4   r0   r1
# r0   r1                             |_____
#                                     |    |
#                                     r0   r1

import os
import sys
import shutil
from indico.core.db import DBMgr
from MaKaC import conference
from MaKaC.conference import LocalFile

def main():
    ch=conference.ConferenceHolder()
    dbm=DBMgr.getInstance()
    dbm.startRequest()
    rep = dbm.getDBConnection().root()['local_repositories']['main']
    for c in ch.getList():
        for ct in c.getContributionList():
            for sc in ct.getSubContributionList():
                for m in sc.getAllMaterialList():
                    for r in m.getResourceList():
                        if isinstance(r, LocalFile):
                            moveFile(r, rep)
    dbm.endRequest()

def moveFile(res, repository):
    id = res.getRepositoryId()
    conf = res.getConference()
    cont = res.getContribution()
    subcont = res.getSubContribution()
    year = str(conf.getCreationDate().year)
    oldInterPath = os.path.join(year, "C%s"%conf.getId())
    interPath = os.path.join(oldInterPath, "c%s"%cont.getId(), "sc%s"%subcont.getId())
    try:
        destPath = os.path.join( repository.getRepositoryPath(), interPath, id )
        oldDestPath = os.path.join( repository.getRepositoryPath(), oldInterPath, id )
        os.makedirs( destPath.decode('utf-8') )
        destPath = os.path.join( destPath, res.getFileName() )
        relativePath = os.path.join( interPath, id, res.getFileName())
        shutil.move( res.getFilePath(), destPath.decode('utf-8','replace').encode(sys.getfilesystemencoding(),'replace') )
        os.rmdir(oldDestPath.decode('utf-8'))
        repository.getFiles()[id] = relativePath
        res.notifyModification()
        print "File \"%s\" (%s) moved."%(res.getFileName(), os.path.join(conf.getId(), cont.getId(), subcont.getId()))
    except IOError, e:
        print "Couldn't move file \"%s\" (%s) (%s)."%(res.getFileName(), os.path.join(conf.getId(), cont.getId(), subcont.getId()), e)
    except OSError, e:
        print "Error while moving file \"%s\" (%s) (%s)."%(res.getFileName(), os.path.join(conf.getId(), cont.getId(), subcont.getId()), e)

if __name__ == "__main__":
    main()
