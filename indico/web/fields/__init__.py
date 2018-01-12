# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.core import signals
from indico.util.signals import named_objects_from_signal
from indico.web.fields.base import BaseField


__all__ = ('BaseField', 'get_field_definitions')


def get_field_definitions(for_):
    """Gets a dict containing all field definitions

    :param for_: The identifier/object passed to the `get_fields`
                 signal to identify which fields to get.
    """
    return named_objects_from_signal(signals.get_fields.send(for_), plugin_attr='plugin')
