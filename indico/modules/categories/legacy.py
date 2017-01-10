# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from lxml import etree


class XMLCategorySerializer(object):
    def __init__(self, category):
        self.category = category

    def serialize_category(self):
        xml = self._serialize_category()
        return etree.tostring(xml, pretty_print=True)

    def _serialize_category(self):
        response = etree.Element('response')
        response.append(self._serialize_category_info(self.category))
        return response

    def _serialize_category_info(self, category):
        category_info = etree.Element('categInfo')
        etree.SubElement(category_info, 'title').text = category.title
        etree.SubElement(category_info, 'id').text = str(category.id)
        return category_info
