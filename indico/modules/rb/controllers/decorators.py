# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

from functools import wraps

from flask import request

from indico.core.errors import IndicoError, NotFoundError
from indico.util.i18n import _

from ..models.locations import Location


def double_wraps(f):
    @wraps(f)
    def wrapper(*args, **kw):
        if len(args) == 1 and not kw and callable(args[0]):
            return f(args[0])
        else:
            return lambda original: f(original, *args, **kw)
    return wrapper


@double_wraps
def requires_location(f,
                      parameter_name='roomLocation',
                      attribute_name='_location',
                      request_attribute='view_args'):
    @wraps(f)
    def wrapper(*args, **kw):
        if not args:
            raise IndicoError(_('Wrong usage of location decorator'))

        location_name = getattr(request, request_attribute).get(parameter_name, None)
        location = Location.getLocationByName(location_name)
        if location:
            setattr(args[0], attribute_name, location)
        else:
            raise NotFoundError(_('There is no location named: {0}').format(location_name))
        return f(*args, **kw)
    return wrapper


@double_wraps
def requires_room(f,
                  parameter_name='roomID',
                  attribute_name='_room',
                  location_attribute_name='_location',
                  request_attribute='view_args'):
    @wraps(f)
    def wrapper(*args, **kw):
        try:
            location = getattr(args[0], location_attribute_name)
        except (AttributeError, IndexError):
            raise IndicoError(_('Wrong usage of room decorator'))

        room_id = getattr(request, request_attribute).get(parameter_name, None)
        room = location.getRoomById(room_id)
        if room:
            setattr(args[0], attribute_name, room)
        else:
            raise NotFoundError(_('There is no room at \'{1}\' with id: {0}').format(room_id, location.name))
        return f(*args, **kw)
    return wrapper
