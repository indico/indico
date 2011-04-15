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

# external library imports
from lxml import etree
from datetime import datetime

# module imports
from indico.util.metadata.serializer import Serializer


class XMLSerializer(Serializer):

    """
    Receives a fossil (or a collection of them) and converts them to XML
    """

    _mime = 'text/xml'

    def _convert(self, value):
        if type(value) == datetime:
            return value.isoformat()
        else:
            return value.decode('utf-8') if type(value) == str else value

    def _xmlForFossil(self, fossil, doc=None):
        attribs = {'fossil': fossil['_fossil']}
        if 'id' in fossil:
            attribs['id'] = fossil['id']

        felement = etree.Element(fossil['_type'].lower(),
                                 attrib=attribs)
        if doc:
            doc.getroot().append(felement)

        for k, v in fossil.iteritems():
            if k not in ['_fossil', '_type', 'id']:
                elem = etree.SubElement(felement, k)
                try:
                    elem.text = self._convert(v)
                except:
                    raise Exception((attribs['id'], self._convert(v)))

    def __call__(self, fossil):
        xml_declaration = False
        if type(fossil) == list:
            # collection of fossils
            doc = etree.ElementTree(etree.Element("collection"))
            for elem in fossil:
                self._xmlForFossil(elem, doc)
            result = doc
            xml_declaration = True
        else:
            result = self._xmlForFossil(fossil)

        return etree.tostring(result, pretty_print=self.pretty,
                              xml_declaration=xml_declaration, encoding='utf-8')


Serializer.register('xml', XMLSerializer)
