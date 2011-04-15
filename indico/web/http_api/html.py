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

# python stdlib imports
import os
from collections import OrderedDict

# module imports
from indico.util.metadata.serializer import Serializer

# legacy indico imports
from MaKaC.common.TemplateExec import render


class HTML4Serializer(Serializer):
    def __call__(self, fossils):
        if type(fossils) != list:
            fossils = [fossils]

        orderedFossils = OrderedDict()

        for fossil in fossils:
            orderedFossils.setdefault(fossil['startDate'].date(), []).append(fossil)

        return render(os.path.join(os.path.dirname(__file__), 'html4.tpl'),
                      {'fossils': orderedFossils})
