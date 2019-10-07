# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from markupsafe import Markup, escape

from indico.modules.auth.util import url_for_register
from indico.util.i18n import _
from indico.util.placeholders import Placeholder


# XXX: `person` may be either an `EventPerson` or a `User`


class FirstNamePlaceholder(Placeholder):
    name = 'first_name'
    description = _("First name of the person")

    @classmethod
    def render(cls, person, event, **kwargs):
        return person.first_name


class LastNamePlaceholder(Placeholder):
    name = 'last_name'
    description = _("Last name of the person")

    @classmethod
    def render(cls, person, event, **kwargs):
        return person.last_name


class EmailPlaceholder(Placeholder):
    name = 'email'
    description = _("Email of the person")

    @classmethod
    def render(cls, person, event, **kwargs):
        return person.email


class EventTitlePlaceholder(Placeholder):
    name = 'event_title'
    description = _("The title of the event")

    @classmethod
    def render(cls, person, event, **kwargs):
        return event.title


class EventLinkPlaceholder(Placeholder):
    name = 'event_link'
    description = _("Link to the event")

    @classmethod
    def render(cls, person, event, **kwargs):
        return Markup('<a href="{url}" title="{title}">{url}</a>').format(url=event.short_external_url,
                                                                          title=event.title)


class RegisterLinkPlaceholder(Placeholder):
    name = 'register_link'
    description = _("The link for the registration page")

    @classmethod
    def render(cls, person, event, **kwargs):
        url = url_for_register(event.url, email=person.email)
        return Markup('<a href="{url}">{url}</a>').format(url=url)
