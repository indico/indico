# -*- coding: utf-8 -*-
##
## $Id: contribution.py,v 1.39 2009/06/25 15:21:49 dmartinc Exp $
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
from MaKaC.common.fossilize import IFossil
from MaKaC.webinterface.common.tools import escape_html

class ICausedErrorFossil(IFossil):

    def getMessage(self):
        pass
    getMessage.convert = escape_html

    def getCode(self):
        pass

    def getInner(self):
        pass

    def getType(self):
        pass

class INoReportErrorFossil(ICausedErrorFossil):

    def getTitle(self):
        """
        A title for the error message - will be shown on the client side
        """

    def getExplanation(self):
        """
        Additional error information (can be shown on the client side)
        """

class IWarningFossil(IFossil):

    def getTitle(self):
        """ Title of the Warning """

    def getProblems(self):
        """ Content of the Warning """
    getProblems.name = "content"

class IResultWithWarningFossil(IFossil):

    def getResult(self):
        """ Result """

    def getWarning(self):
        """ Warning """
    getWarning.result = IWarningFossil

    def hasWarning(self):
        """ Whether the result has a Warning or not """
