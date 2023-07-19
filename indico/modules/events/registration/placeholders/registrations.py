# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from markupsafe import Markup

from indico.modules.events.registration.models.items import PersonalDataType
from indico.util.i18n import _
from indico.util.placeholders import ParametrizedPlaceholder, Placeholder
from indico.web.flask.util import url_for


class FirstNamePlaceholder(Placeholder):
    name = 'first_name'
    description = _('First name of the person')

    @classmethod
    def render(cls, regform, registration):
        return registration.first_name


class LastNamePlaceholder(Placeholder):
    name = 'last_name'
    description = _('Last name of the person')

    @classmethod
    def render(cls, regform, registration):
        return registration.last_name


class EventTitlePlaceholder(Placeholder):
    name = 'event_title'
    description = _('The title of the event')

    @classmethod
    def render(cls, regform, registration):
        return registration.registration_form.event.title


class EventLinkPlaceholder(ParametrizedPlaceholder):
    name = 'event_link'
    param_friendly_name = 'link title'

    @classmethod
    def render(cls, param, regform, registration):
        event = registration.registration_form.event
        return Markup('<a href="{url}" title="{title}">{text}</a>').format(url=event.short_external_url,
                                                                           title=event.title,
                                                                           text=(param or event.short_external_url))

    @classmethod
    def iter_param_info(cls, regform, registration, **kwargs):
        yield None, _('Link to the event')
        yield 'custom-text', _('Custom link text instead of the full URL')


class IDPlaceholder(Placeholder):
    name = 'id'
    description = _('The ID of the registration')

    @classmethod
    def render(cls, regform, registration):
        return registration.friendly_id


class LinkPlaceholder(Placeholder):
    name = 'link'
    description = _('The link to the registration details')

    @classmethod
    def render(cls, regform, registration):
        url = url_for('.display_regform', registration.registration_form, token=registration.uuid, _external=True)
        return Markup('<a href="{url}">{url}</a>').format(url=url)


class RejectionReasonPlaceholder(Placeholder):
    name = 'rejection_reason'
    description = _('The reason why the registration was rejected')

    @classmethod
    def render(cls, regform, registration):
        return registration.rejection_reason


class FieldPlaceholder(ParametrizedPlaceholder):
    name = 'field'
    description = None
    param_required = True
    param_restricted = True
    advanced = True

    @classmethod
    def render(cls, param, regform, registration):
        if ':' in param:
            field_id, key = param.split(':', 1)
        else:
            field_id = param
            key = None
        data = registration.data_by_field.get(int(field_id))
        if data is None:
            return ''
        rv = data.field_data.field.field_impl.render_placeholder(data, key)
        if isinstance(rv, list):
            rv = ', '.join(rv)
        return rv or '-'

    @classmethod
    def iter_param_info(cls, regform, registration):
        own_placeholder_types = {PersonalDataType.email, PersonalDataType.first_name, PersonalDataType.last_name}
        for field in sorted(regform.active_fields, key=lambda x: (x.parent.position, x.position)):
            if field.personal_data_type in own_placeholder_types:
                continue
            for key, description in field.field_impl.iter_placeholder_info():
                name = str(field.id) if key is None else f'{field.id}:{key}'
                yield name, description
