# -*- coding: utf-8 -*-
##
## $id$
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

from indico.core.extpoint import Component
from indico.core.extpoint.events import ITimetableContributor
from MaKaC.plugins.base import Observable
import zope.interface

class ImporterContributor(Component, Observable):
    """
    Adds interface extension to event's timetable modification websites.
    """

    zope.interface.implements(ITimetableContributor)

    @classmethod
    def includeTimetableJSFiles(cls, obj, params = {}):
        """
        Includes additional javascript file.
        """
        params['paths'].append("importer/js/importer.js")

    @classmethod
    def includeTimetableCSSFiles(cls, obj, params = {}):
        """
        Includes additional Css files.
        """
        params['paths'].append("importer/importer.css")

    @classmethod
    def customTimetableLinks(cls, obj, params = {}):
        """
        Inserts an "Import" link in a timetable header.
        """
        params.update({"Import" : "createImporterDialog"})