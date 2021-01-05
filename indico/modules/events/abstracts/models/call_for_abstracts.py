# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy.descriptions import RENDER_MODE_WRAPPER_MAP
from indico.modules.events.abstracts.settings import abstracts_reviewing_settings, abstracts_settings
from indico.modules.events.settings import EventSettingProperty
from indico.util.date_time import now_utc
from indico.util.string import return_ascii


class CallForAbstracts(object):
    """Proxy class to facilitate access to the call for abstracts settings."""

    def __init__(self, event):
        self.event = event

    @return_ascii
    def __repr__(self):
        return '<CallForAbstracts({}, start_dt={}, end_dt={})>'.format(self.event.id, self.start_dt, self.end_dt)

    start_dt = EventSettingProperty(abstracts_settings, 'start_dt')
    end_dt = EventSettingProperty(abstracts_settings, 'end_dt')
    modification_end_dt = EventSettingProperty(abstracts_settings, 'modification_end_dt')
    allow_attachments = EventSettingProperty(abstracts_settings, 'allow_attachments')
    allow_comments = EventSettingProperty(abstracts_reviewing_settings, 'allow_comments')
    allow_contributors_in_comments = EventSettingProperty(abstracts_reviewing_settings,
                                                          'allow_contributors_in_comments')
    allow_convener_judgment = EventSettingProperty(abstracts_reviewing_settings, 'allow_convener_judgment')
    allow_editing = EventSettingProperty(abstracts_settings, 'allow_editing')
    contribution_submitters = EventSettingProperty(abstracts_settings, 'contribution_submitters')
    submission_instructions = EventSettingProperty(abstracts_settings, 'submission_instructions')
    reviewing_instructions = EventSettingProperty(abstracts_reviewing_settings, 'reviewing_instructions')
    judgment_instructions = EventSettingProperty(abstracts_reviewing_settings, 'judgment_instructions')

    @property
    def has_started(self):
        return self.start_dt is not None and self.start_dt <= now_utc()

    @property
    def has_ended(self):
        return self.end_dt is not None and self.end_dt <= now_utc()

    @property
    def is_scheduled(self):
        return self.start_dt is not None

    @property
    def is_open(self):
        return self.has_started and not self.has_ended

    @property
    def modification_ended(self):
        return self.modification_end_dt is not None and self.modification_end_dt <= now_utc()

    @property
    def rating_range(self):
        return tuple(abstracts_reviewing_settings.get(self.event, key) for key in ('scale_lower', 'scale_upper'))

    @property
    def announcement(self):
        announcement = abstracts_settings.get(self.event, 'announcement')
        render_mode = abstracts_settings.get(self.event, 'announcement_render_mode')
        return RENDER_MODE_WRAPPER_MAP[render_mode](announcement)

    def can_submit_abstracts(self, user):
        return self.is_open or abstracts_settings.acls.contains_user(self.event, 'authorized_submitters', user)

    def can_edit_abstracts(self, user):
        modification_end = self.modification_end_dt
        return self.can_submit_abstracts(user) or (modification_end is not None and modification_end > now_utc())

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
            abstracts_settings.set(self.event, 'start_dt', now)
