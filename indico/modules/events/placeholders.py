# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from markupsafe import Markup

from indico.util.date_time import format_date, format_time
from indico.util.i18n import _
from indico.util.placeholders import ParametrizedPlaceholder, Placeholder


class EventTitlePlaceholder(Placeholder):
    name = 'event_title'
    description = _('The title of the event')

    @classmethod
    def render(cls, event, **kwargs):
        return event.title


class EventStartDatePlaceholder(Placeholder):
    name = 'event_start_date'
    description = _('Event start date')

    @classmethod
    def render(cls, event, **kwargs):
        return format_date(event.start_dt_local)


class EventStartTimePlaceholder(Placeholder):
    name = 'event_start_time'
    description = _('Event start time')

    @classmethod
    def render(cls, event, **kwargs):
        return format_time(event.start_dt_local)


class EventLinkPlaceholder(ParametrizedPlaceholder):
    name = 'event_link'
    param_friendly_name = 'link title'

    @classmethod
    def render(cls, param, event, **kwargs):
        return Markup('<a href="{url}" title="{title}">{text}</a>').format(url=event.short_external_url,
                                                                           title=event.title,
                                                                           text=(param or event.short_external_url))

    @classmethod
    def iter_param_info(cls, **kwargs):
        yield None, _('Link to the event')
        yield 'custom-text', _('Custom link text instead of the full URL')
