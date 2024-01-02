# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
    description = _('First name of the person')

    @classmethod
    def render(cls, person, event, **kwargs):
        return person.first_name


class LastNamePlaceholder(Placeholder):
    name = 'last_name'
    description = _('Last name of the person')

    @classmethod
    def render(cls, person, event, **kwargs):
        return person.last_name


class EmailPlaceholder(Placeholder):
    name = 'email'
    description = _('Email of the person')

    @classmethod
    def render(cls, person, event, **kwargs):
        return person.email


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
    description = _('The link for the registration page')

    @classmethod
    def render(cls, person, event, **kwargs):
        url = url_for_register(event.url, email=person.email)
        return Markup('<a href="{url}">{url}</a>').format(url=url)


class ContributionIDPlaceholder(Placeholder):
    name = 'contribution_id'
    description = _('The ID of the contribution')

    @classmethod
    def render(cls, contribution, **kwargs):
        return str(contribution.friendly_id)


class ContributionTitlePlaceholder(Placeholder):
    name = 'contribution_title'
    description = _('The title of the contribution')

    @classmethod
    def render(cls, contribution, **kwargs):
        return str(contribution.title)


class ContributionCodePlaceholder(Placeholder):
    name = 'contribution_code'
    description = _('The program code of the contribution')

    @classmethod
    def render(cls, contribution, **kwargs):
        return str(contribution.code)


class AbstractIDPlaceholder(Placeholder):
    name = 'abstract_id'
    description = _('The ID of the abstract')

    @classmethod
    def render(cls, abstract, **kwargs):
        return str(abstract.friendly_id)


class AbstractTitlePlaceholder(Placeholder):
    name = 'abstract_title'
    description = _('The title of the abstract')

    @classmethod
    def render(cls, abstract, **kwargs):
        return str(abstract.title)
