# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.util.string import RichMarkup


class DescriptionMixin(object):
    """Mixin to add an html-enabled description column"""

    @declared_attr
    def _description(cls):
        return db.Column(
            'description',
            db.Text,
            nullable=False,
            default=''
        )

    @hybrid_property
    def description(self):
        return RichMarkup(self._description)

    @description.setter
    def description(self, value):
        self._description = value

    @description.expression
    def description(cls):
        return cls._description
