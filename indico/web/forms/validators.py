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

from wtforms.validators import StopValidation


class UsedIf(object):
    """
    Make a WTF field "used" if a given condition evaluates to True.
    If the field is not used, validation stops.
    """
    def __init__(self, condition):
        self.condition = condition

    def __call__(self, form, field):
        if self.condition in (True, False):
            if not self.condition:
                field.errors[:] = []
                raise StopValidation()
        elif not self.condition(form, field):
            field.errors[:] = []
            raise StopValidation()


class UsedIfChecked(UsedIf):
    def __init__(self, field_name):
        def _condition(form, field):
            return form._fields.get(field_name).data

        super(UsedIfChecked, self).__init__(_condition)
