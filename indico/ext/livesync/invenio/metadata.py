# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

"""
Metadata generation

This module is UNFINISHED

"""

# system libs
#from pymarc import Record, Field, marcxml

# plugin imports
from indico.ext.livesync.metadata import MetadataWrapper, MetadataGenerator

# legacy import
from MaKaC import conference
from MaKaC.fossils.conference import IConferenceFossil
from MaKaC.webinterface import urlHandlers

### These classes should be used instead of the current MARCXML generator

class IMARCFossil(IConferenceFossil):
    # TODO: finish this
    pass


class MARCGenerator(MetadataGenerator):

    def _getISODateTime(self, dt):
        """
        ISO8601 Date/time
        """
        return "%sZ" % dt.isoformat()

    def _getFullId(self, obj, separator=[':',':']):

        if type(separator) == str:
            separator = [separator]*2

        if isinstance(obj, conference.Conference):
            oid = obj.getId()
        elif isinstance(obj, conference.Contribution):
            oid = "%s%s%s"%(obj.getConference().getId(),separator[0],obj.getId())
        elif isinstance(obj, conference.SubContribution):
            oid = "%s%s%s%s%s"%(obj.getConference().getId(), separator[0], obj.getContribution().getId(), separator[1], obj.getId())
        else:
            oid = obj.getId()
        return oid

    def _getRecordCollection(self, obj):
        if obj.hasAnyProtection():
            return "INDICOSEARCH.PRIVATE"
        else:
            return "INDICOSEARCH.PUBLIC"

    def generate(self, obj):

        # Empty MARC record
        record = Record()

        record.add_field(Field(tag = '245', indicators = ('',''),
                               subfields = ['a', obj.getTitle()]))

        subfields = ['a', obj.getTitle(),
                     '9', self._getISODateTime(obj.getStartDate()),
                     'Z', self._getISODateTime(obj.getEndDate()),
                     'g', self._getFullId(obj)]

        for l in obj.getLocationList():
            location = ""
            if l.getName() != "":
                location = obj.getLocation().getName()
            if l.getAddress() != "":
                location = location + ", " + obj.getLocation().getAddress()

            if obj.getRoom():
                roomName = self._getRoom(obj.getRoom(), l)
                location = location + ", " + roomName

            if location:
                subfields += ['c', location]

        record.add_field(Field(tag = '111', indicators = ('',''),
                               subfields = subfields))

        record.add_field(Field(tag = '518', indicators = ('',''),
                         subfields = ['d', self._getISODateTime(obj.getStartDate())]))

        record.add_field(Field(tag = '520', indicators = ('a',''),
                         subfields = ['d', obj.getDescription()]))

        for path in obj.getCategoriesPath():
            record.add_field(Field(tag = '650', indicators = ('','7'),
                             subfields = ['a', ':'.join(path)]))

        keywords = obj.getKeywords()
        keywords = keywords.replace("\r\n", "\n")

        subfields = []
        for keyword in keywords.split("\n"):
            subfields += ['a', keyword]

        record.add_field(Field(tag = '653', indicators = ('1',''), subfields = subfields))

        record.add_field(Field(tag = '650', indicators = ('2','7'),
                         subfields = ['a', obj.getVerboseType()]))

        record.add_field(Field(tag = '856', indicators = ('4',''),
                         subfields = ['u',
                                      str(urlHandlers.UHConferenceDisplay.getURL(obj)),
                                      'y', 'Event details']))

        record.add_field(Field(tag = '961', indicators = ('',''), subfields = [
            'c', self._getISODateTime(obj.getCreationDate()),
            'x', self._getISODateTime(obj.getModificationDate())
            ]))

        record.add_field(Field(tag = '970', indicators = ('',''),
                         subfields = ['a', 'INDICO.%s' % self._getFullId(obj)]))

        record.add_field(Field(tag = '970', indicators = ('',''),
                         subfields = ['a', self._getRecordCollection(obj)]))


        return self._serialize(record)


class MARC21Generator(MARCGenerator):

    def _serialize(self, record):
        return record.as_marc()


class MARCXMLGenerator(MARCGenerator):

    def _serialize(self, record):
        return marcxml.record_to_xml(record)

###
