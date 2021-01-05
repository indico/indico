# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

"""
Conversion functions for fossils
"""

from collections import defaultdict

import pytz

from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence


class Conversion(object):
    @classmethod
    def datetime(cls, dt, tz=None, convert=False):
        if dt:
            if tz:
                if isinstance(tz, basestring):
                    tz = pytz.timezone(tz)
                date = dt.astimezone(tz)
            else:
                date = dt
            if convert:
                return {'date': str(date.date()), 'time': str(date.time()), 'tz': str(date.tzinfo)}
            else:
                return date
        else:
            return None

    @classmethod
    def reservationsList(cls, resvs):
        res = defaultdict(list)
        for resv in resvs:
            occurrences = (resv.occurrences
                           .filter(ReservationOccurrence.is_valid)
                           .options(ReservationOccurrence.NO_RESERVATION_USER_STRATEGY))
            res[resv.room.full_name] += [{'startDateTime': cls.datetime(occ.start_dt),
                                          'endDateTime': cls.datetime(occ.end_dt)}
                                         for occ in occurrences]
        return res
