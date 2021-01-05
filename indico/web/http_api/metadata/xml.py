# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from datetime import datetime

import dateutil.parser
from lxml import etree
from pytz import timezone, utc

from indico.core.logger import Logger
from indico.util.string import to_unicode
from indico.web.http_api.metadata.serializer import Serializer


def _deserialize_date(date_dict):
    dt = datetime.combine(dateutil.parser.parse(date_dict['date']).date(),
                          dateutil.parser.parse(date_dict['time']).time())
    return timezone(date_dict['tz']).localize(dt).astimezone(utc)


class XMLSerializer(Serializer):
    """
    Receive a fossil (or a collection of them) and converts them to XML.
    """

    _mime = 'text/xml'

    def __init__(self, query_params, pretty=False, **kwargs):
        self._typeMap = kwargs.pop('typeMap', {})
        super(XMLSerializer, self).__init__(query_params, pretty, **kwargs)

    def _convert(self, value, _control_char_re=re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')):
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (int, long, float, bool)):
            return str(value)
        else:
            value = to_unicode(value) if isinstance(value, str) else value
            if isinstance(value, basestring):
                # Get rid of control chars breaking XML conversion
                value = _control_char_re.sub(u'', value)
            return value

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
            if k in ['_fossil', '_type', 'id']:
                continue
            if isinstance(k, (int, float)) or (isinstance(k, basestring) and k.isdigit()):
                elem = etree.SubElement(felement, 'entry', {'key': unicode(k)})
            else:
                elem = etree.SubElement(felement, k)
            if isinstance(v, dict) and set(v.viewkeys()) == {'date', 'time', 'tz'}:
                v = _deserialize_date(v)
            if isinstance(v, (list, tuple)):
                onlyDicts = all(isinstance(subv, dict) for subv in v)
                if onlyDicts:
                    for subv in v:
                        elem.append(self._xmlForFossil(subv))
                else:
                    for subv in v:
                        if isinstance(subv, dict):
                            elem.append(self._xmlForFossil(subv))
                        else:
                            subelem = etree.SubElement(elem, 'item')
                            subelem.text = self._convert(subv)
            elif isinstance(v, dict):
                elem.append(self._xmlForFossil(v))
            else:
                txt = self._convert(v)
                try:
                    elem.text = txt
                except Exception:
                    Logger.get('xmlSerializer').exception('Setting XML text value failed (id: %s, value %r)', id, txt)

        return felement

    def _execute(self, fossil, xml_declaration=True):
        if isinstance(fossil, list):
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
