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

from MaKaC.common.general import *

from MaKaC.webinterface.rh import fileAccess

# We have to use a function different from "index" as when serving URLs like
#   http://foo.com/indico/getFile.py?id=1 which were outputing a PDF file were
#   causing troubles with IE; everything seems to work fine when we use URLs not
#   ending in ".py"; we couldn't find any documentation regarding this issue
#   so, for the moment, we decided to change the request handler so everything
#   works fine, even if the resulting URL is not very nice.

def access(req, **params):
    return fileAccess.RHFileAccess( req ).process( params )

def accessKey(req, **params):
    return fileAccess.RHFileAccessStoreAccessKey( req ).process( params )

def wmv(req, **params):
    return fileAccess.RHVideoWmvAccess( req ).process( params )

def flash(req, **params):
    return fileAccess.RHVideoFlashAccess( req ).process( params )
