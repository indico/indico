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


### These classes should be used instead of the current MARCXML generator

class IMARCFossil(IConferenceFossil):
    # TODO: finish this
    pass


class _future_MARCGenerator(MetadataGenerator):

    _fossilMappings = {
        conference.Conference: [
            ('245', ('',''), {'a': 'title'}),
            ('111', ('',''), {'a': 'title',
                              'c': 'location',
                              '9': 'xmlStartDate',
                              'Z': 'xmlEndDate'})
            # ...
            # TODO: finish this
            ]
        }

    def _generateFields(self, object):
        fossil = object.fossilize(IMARCFossil)
        for field in self._fossilMappings[object.__class__]:
            pass
            # generate

    def generate(self, object):

        metadata = self._generateFields(object)

        # Empty MARC record
        record = Record()

        for tag, indicators, subfields in metadata:
            record.add_field(tag = tag, indicators = indicators, subfields = subfields)

        return self._serialize(record)


class _future_MARC21Generator(_future_MARCGenerator):

    def _serialize(self, record):
        return record.as_marc()


class _future_MARCXMLGenerator(_future_MARCGenerator):

    def _serialize(self, record):
        return marcxml.record_to_xml(record)

###
