# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
