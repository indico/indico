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

from indico.ext.importer.recordConverter import RecordConverter, StandardConversion
from MaKaC.webinterface.common.tools import strip_ml_tags

class InvenioRecordConverterBase(RecordConverter):
    """
    Base class of every Invenio record converter. Data in Invenio records is always stored
    in the list (e.g. author's name is stored as ["Joe Doe"]), so defaultConversion method
    simply takes the first element form a list.
    """

    @staticmethod
    def defaultConversionMethod(attr):
        return attr[0]

class InvenioAuthorConverter(InvenioRecordConverterBase):
    """
    Converts author name, surname and affiliation.
    """

    conversion = [
                  ("a", "firstName", lambda x: x[0].split(" ")[0]),
                  ("a", "familyName", lambda x: " ".join(x[0].split(" ")[1:])),
                  ("u", "affiliation"),
                  ]

class InvenioPlaceTimeConverter111(InvenioRecordConverterBase):
    """
    Extracts event's place and start/end time. Used for entry 111 in MARC 21.
    """

    conversion = [
                  ("9", "startDateTime", StandardConversion.dateTime),
                  ("z", "endDateTime", StandardConversion.dateTime),
                  ("c", "place"),
                  ]

class InvenioPlaceTimeConverter518(InvenioRecordConverterBase):
    """
    Extracts event's place and start/end time. Used for entry 518 in MARC 21.
    """

    conversion = [
                  ("d", "startDateTime", StandardConversion.dateTime),
                  ("h", "endDateTime", StandardConversion.dateTime),
                  ("r", "place"),
                  ]

class InvenioLinkConverter(InvenioRecordConverterBase):
    """
    Extracts link to the event.
    """

    conversion = [
                  ("y", "name"),
                  ("u", "url"),
                  ]

class InvenioRecordConverter(InvenioRecordConverterBase):
    """
    Main converter class. Converts record from InvenioConverter in format readable by a plugin.
    """

    conversion = [
                  ("088","reportNumbers", lambda x: [number for number in x[0]['a'][0].split(" ") if number != "(Confidential)"]),
                  ("100","primaryAuthor", lambda x: x[0] if "Primary Author" in x[0].get("e",[]) else {}, InvenioAuthorConverter),
                  ("100","speaker", lambda x: x[0] if "Speaker" in x[0].get("e",[]) else {}, InvenioAuthorConverter),
                  ("111", "*append*", None, InvenioPlaceTimeConverter111),
                  ("245","title", lambda x: x[0]['a'][0]),
                  ("518", "*append*", None, InvenioPlaceTimeConverter518),
                  ("520", "summary", lambda x: strip_ml_tags(x[0]['a'][0])),
                  ("700","secondaryAuthor", None, InvenioAuthorConverter),
                  ("61124","meetingName", lambda x: str(x[0]['a'][0])),
                  ("8564","materials", lambda x: x, InvenioLinkConverter),
                  ]

