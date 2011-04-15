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

class Serializer(object):

    def __init__(self, pretty=False):
        self.pretty = pretty

    @classmethod
    def create(cls, dformat, **kwargs):
        """
        A serializer factory
        """

        from indico.util.metadata.html import HTML4Serializer
        from indico.util.metadata.json import JSONSerializer
        from indico.util.metadata.xml import XMLSerializer

        registry = {'json': JSONSerializer,
                    'xml': XMLSerializer,
                    'html': HTML4Serializer}

        serializer = registry.get(dformat)

        if serializer:
            return serializer(**kwargs)
        else:
            raise Exception("Serializer for '%s' does not exist!" % dformat)
