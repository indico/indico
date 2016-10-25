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

from indico.modules.events.abstracts.settings import abstracts_settings, abstracts_reviewing_settings
from indico.util.date_time import now_utc
from indico.util.string import return_ascii


class CallForAbstracts(object):
    """Proxy class to facilitate access to the call for abstracts settings"""

    def __init__(self, event):
        self.event = event

    @return_ascii
    def __repr__(self):
        return '<CallForAbstracts({}, start_dt={}, end_dt={})>'.format(self.event.id, self.start_dt, self.end_dt)

    @property
    def allow_convener_judgment(self):
        return abstracts_reviewing_settings.get(self.event, 'allow_convener_judgment')

    @property
    def has_started(self):
        return self.start_dt is not None and self.start_dt <= now_utc()

    @property
    def has_ended(self):
        return self.end_dt is not None and self.end_dt <= now_utc()

    @property
    def modification_ended(self):
        return self.modification_end_dt is not None and self.modification_end_dt <= now_utc()

    @property
    def start_dt(self):
        return abstracts_settings.get(self.event, 'start_dt')

    @property
    def end_dt(self):
        return abstracts_settings.get(self.event, 'end_dt')

    @property
    def modification_end_dt(self):
        return abstracts_settings.get(self.event, 'modification_end_dt') or self.end_dt

    @property
    def rating_range(self):
        return tuple(abstracts_reviewing_settings.get(self.event, key) for key in ('scale_lower', 'scale_upper'))

    def schedule(self, start_dt, end_dt, modification_end_dt):
        abstracts_settings.set_multi(self.event, {
            'start_dt': start_dt,
            'end_dt': end_dt,
            'modification_end_dt': modification_end_dt
        })

    def open(self):
        if self.has_ended:
            abstracts_settings.set_multi(self.event, {
                'end_dt': None,
                'modification_end_dt': None
            })
        else:
            abstracts_settings.set(self.event, 'start_dt', now_utc(False))

    def close(self):
        now = now_utc(False)
        abstracts_settings.set(self.event, 'end_dt', now)
        if not self.has_started:
            abstracts_settings.set(self.event_new, 'start_dt', now)
