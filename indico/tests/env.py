# -*- coding: utf-8 -*-
##
## $Id: testFileSubmission.py,v 1.2 2008/04/24 16:59:58 jose Exp $
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

# pylint: disable-msg=C0103,C0111

"""
This module contains a basic setup for unit tests that
should be included from each file
"""

from MaKaC.common import DBMgr

def setup_module():
    DBMgr.getInstance().startRequest()

def teardown_module():
    DBMgr.getInstance().abort()
    DBMgr.getInstance().endRequest()
