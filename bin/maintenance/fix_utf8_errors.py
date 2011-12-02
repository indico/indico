# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Fixes possible encoding errors caused by older DB data
"""

from MaKaC.common import DBMgr
from MaKaC.conference import ConferenceHolder
from indico.util.console import conferenceHolderIterator


def fix_prop(c, name):
    getter = getattr(c, 'get' + name)
    try:
        getter().decode('utf-8')
    except UnicodeDecodeError:
        print c.getId(), name
        getattr(c, 'set' + name)(getter().decode('latin1').encode('utf-8'))


def fix_everything(dbi):
    i = 0
    for level, c in conferenceHolderIterator(ConferenceHolder(), deepness='event'):
        fix_prop(c, 'Title')
        fix_prop(c, 'Description')

        for spk in c.getChairList():
            fix_prop(spk, 'Affiliation')
            fix_prop(spk, 'FamilyName')
            fix_prop(spk, 'FirstName')

    if i % 999 == 0:
        dbi.commit()
    i += 1


if __name__ == '__main__':
    dbi = DBMgr.getInstance()
    dbi.startRequest()

    fix_everything(dbi)

    dbi.endRequest()
