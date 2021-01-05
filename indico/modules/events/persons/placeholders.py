# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from markupsafe import Markup

from indico.modules.auth.util import url_for_register
from indico.modules.events.contributions.util import get_contributions_for_person
from indico.modules.events.models.persons import EventPerson
from indico.modules.users.models.users import User
from indico.util.i18n import _
from indico.util.placeholders import ParametrizedPlaceholder, Placeholder
from indico.web.flask.templating import get_template_module


# XXX: `person` may be either an `EventPerson` or a `User`; the latter happens
# when emailing role members or people from peer reviewing teams)


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


class ContributionsPlaceholder(ParametrizedPlaceholder):
    name = 'contributions'
    param_required = False
    param_restricted = True

    @classmethod
    def iter_param_info(cls, person, event, **kwargs):
        yield None, _("The person's contributions")
        yield 'speakers', _("The person's contributions where they are a speaker")

    @classmethod
    def render(cls, param, person, event, **kwargs):
        if isinstance(person, User):
            person = EventPerson.query.with_parent(event).filter_by(user_id=person.id).first()
            if person is None:
                return ''
        tpl = get_template_module('events/persons/emails/_contributions.html')
        html = tpl.render_contribution_list(
            get_contributions_for_person(event, person, only_speakers=(param == 'speakers')),
            event.timezone
        )
        return Markup(html)


class RegisterLinkPlaceholder(Placeholder):
    name = 'register_link'
    description = _("The link for the registration page")

    @classmethod
    def render(cls, person, event, **kwargs):
        url = url_for_register(event.url, email=person.email)
        return Markup('<a href="{url}">{url}</a>').format(url=url)
