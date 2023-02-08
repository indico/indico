# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from markupsafe import Markup

from indico.util.i18n import _
from indico.util.placeholders import Placeholder


class EventTitlePlaceholder(Placeholder):
    name = 'event_title'
    description = _('The title of the event')

    @classmethod
    def render(cls, event, **kwargs):
        return event.title


class EventLinkPlaceholder(Placeholder):
    name = 'event_link'
    description = _('Link to the event')

    @classmethod
    def render(cls, event, **kwargs):
        return Markup('<a href="{url}" title="{title}">{url}</a>').format(url=event.short_external_url,
                                                                          title=event.title)
