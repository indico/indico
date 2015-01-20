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

from indico.core.db import DBMgr
from MaKaC.conference import ConferenceHolder
from indico.util.console import conferenceHolderIterator

dbi = DBMgr.getInstance()
dbi.startRequest()

ENCODINGS = ['Windows-1252', 'iso-8859-1', 'latin1']

def fix(getter, setter):
    txt = getter()
    print "fixing... ",
    for encoding in ENCODINGS:
        try:
            utxt = txt.decode(encoding)
            print encoding
            setter(utxt.encode('utf-8'))
            return
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
    print "error! %s" % repr(txt)

with dbi.transaction() as conn:
    i = 0
    for level, conf in conferenceHolderIterator(ConferenceHolder(), deepness='event', verbose=False):
        try:
            conf.getTitle().decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            print '\r%s title' % conf
            fix(conf.getTitle, conf.setTitle)

        try:
            conf.getDescription().decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            print '\r%s description' % conf
            fix(conf.getDescription, conf.setDescription)

        if i % 999 == 0:
            dbi.commit()
        i += 1
