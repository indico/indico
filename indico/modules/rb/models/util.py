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

from functools import wraps

from indico.core.errors import IndicoError


def unimplemented(exceptions=(Exception,), message='Unimplemented'):
    def _unimplemented(func):
        @wraps(func)
        def _wrapper(*args, **kw):
            try:
                return func(*args, **kw)
            except exceptions:
                raise IndicoError(str(message))

        return _wrapper

    return _unimplemented


def proxy_to_reservation_if_last_valid_occurrence(f):
    """Forwards a method call to `self.reservation` if there is only one occurrence."""
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if not kwargs.pop('propagate', True):
            return f(self, *args, **kwargs)
        resv_func = getattr(self.reservation, f.__name__)
        if not self.reservation.is_repeating:
            return resv_func(*args, **kwargs)
        valid_occurrences = self.reservation.occurrences.filter_by(is_valid=True).limit(2).all()
        if len(valid_occurrences) == 1 and valid_occurrences[0] == self:
            # If we ever use this outside ReservationOccurrence we can probably get rid of the ==self check
            return resv_func(*args, **kwargs)
        return f(self, *args, **kwargs)

    return wrapper
