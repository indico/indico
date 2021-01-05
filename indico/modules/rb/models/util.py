# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import wraps


def proxy_to_reservation_if_last_valid_occurrence(f):
    """Forward a method call to `self.reservation` if there is only one occurrence."""
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
        if not kwargs.pop('propagate', True):
            return f(self, *args, **kwargs)
        resv_func = getattr(self.reservation, f.__name__)
        if not self.reservation.is_repeating:
            return resv_func(*args, **kwargs)
        criteria = (ReservationOccurrence.is_valid, ReservationOccurrence.is_within_cancel_grace_period)
        valid_occurrences = self.reservation.occurrences.filter(*criteria).limit(2).all()
        if len(valid_occurrences) == 1 and valid_occurrences[0] == self:
            # If we ever use this outside ReservationOccurrence we can probably get rid of the ==self check
            return resv_func(*args, **kwargs)
        return f(self, *args, **kwargs)

    return wrapper
