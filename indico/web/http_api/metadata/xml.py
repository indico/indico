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

# external library imports
from lxml import etree
from datetime import datetime

# module imports
from indico.web.http_api.metadata.serializer import Serializer
from MaKaC.common.logger import Logger


class XMLSerializer(Serializer):

    """
    Receives a fossil (or a collection of them) and converts them to XML
    """

    _mime = 'text/xml'

    def __init__(self, pretty=False, **kwargs):
        self._typeMap = kwargs.pop('typeMap', {})
        super(XMLSerializer, self).__init__(pretty, **kwargs)

    def _convert(self, value):
        if type(value) == datetime:
            return value.isoformat()
        elif type(value) in (int, float, bool):
            return str(value)
        else:
            return value.decode('utf-8') if type(value) == str else value

    def _xmlForFossil(self, fossil, doc=None):
        attribs = {}
        id = None
        if '_fossil' in fossil:
            attribs['fossil'] = fossil['_fossil']
        if 'id' in fossil:
            id = attribs['id'] = str(fossil['id'])

        if '_type' in fossil:
            typeName = self._typeMap.get(fossil['_type'], fossil['_type'])
        else:
            typeName = 'collection'
        felement = etree.Element(typeName.lower(),
                                 attrib=attribs)
        if doc:
            doc.getroot().append(felement)

        for k, v in fossil.iteritems():
            if k not in ['_fossil', '_type', 'id']:
                elem = etree.SubElement(felement, k)
                if type(v) == list:
                    onlyDicts = all(type(subv) == dict for subv in v)
                    if onlyDicts:
                        for subv in v:
                            elem.append(self._xmlForFossil(subv))
                    else:
                        for subv in v:
                            if type(subv) == dict:
                                elem.append(self._xmlForFossil(subv))
                            else:
                                subelem = etree.SubElement(elem, 'item')
                                subelem.text = self._convert(subv)
                elif type(v) == dict:
                    elem.append(self._xmlForFossil(v))
                else:
                    txt = self._convert(v)
                    try:
                        elem.text = txt
                    except Exception, e:
                        Logger.get('xmlSerializer').error('Setting XML text value failed: %s (id: %s)' % (e, id))


        return felement

    def _execute(self, fossil, xml_declaration=True):
        if type(fossil) == list:
            # collection of fossils
            doc = etree.ElementTree(etree.Element("collection"))
            for elem in fossil:
                self._xmlForFossil(elem, doc)
            result = doc
        else:
            result = self._xmlForFossil(fossil)

        return etree.tostring(result, pretty_print=self.pretty,
                              xml_declaration=xml_declaration, encoding='utf-8')


Serializer.register('xml', XMLSerializer)
