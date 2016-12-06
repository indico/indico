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

from indico.modules.events.papers.settings import paper_reviewing_settings
from indico.modules.events.settings import EventSettingProperty
from indico.util.date_time import now_utc
from indico.util.string import return_ascii


class CallForPapers(object):
    """Proxy class to facilitate access to the call for papers settings"""

    def __init__(self, event):
        self.event = event

    @return_ascii
    def __repr__(self):
        return '<CallForPapers({}, start_dt={}, end_dt={})>'.format(self.event.id, self.start_dt, self.end_dt)

    start_dt = EventSettingProperty(paper_reviewing_settings, 'start_dt')
    end_dt = EventSettingProperty(paper_reviewing_settings, 'end_dt')
    content_reviewing_enabled = EventSettingProperty(paper_reviewing_settings, 'content_reviewing_enabled')
    layout_reviewing_enabled = EventSettingProperty(paper_reviewing_settings, 'layout_reviewing_enabled')

    @property
    def has_started(self):
        return self.start_dt is not None and self.start_dt <= now_utc()

    @property
    def has_ended(self):
        return self.end_dt is not None and self.end_dt <= now_utc()

    @property
    def is_open(self):
        return self.has_started and not self.has_ended

    def schedule(self, start_dt, end_dt):
        paper_reviewing_settings.set_multi(self.event, {
            'start_dt': start_dt,
            'end_dt': end_dt
        })

    def open(self):
        if self.has_ended:
            paper_reviewing_settings.set(self.event, 'end_dt', None)
        else:
            paper_reviewing_settings.set(self.event, 'start_dt', now_utc(False))

    def close(self):
        paper_reviewing_settings.set(self.event, 'end_dt', now_utc(False))

    def set_reviewing_state(self, reviewing_type, enable):
        if reviewing_type == 'content':
            paper_reviewing_settings.set(self.event, 'content_reviewing_enabled', enable)
        elif reviewing_type == 'layout':
            paper_reviewing_settings.set(self.event, 'layout_reviewing_enabled', enable)
