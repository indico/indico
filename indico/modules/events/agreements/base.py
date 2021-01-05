# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from hashlib import sha1

from flask import render_template

from indico.modules.events.agreements.models.agreements import Agreement
from indico.modules.events.settings import EventSettingsProxy
from indico.util.caching import make_hashable, memoize_request
from indico.util.decorators import cached_classproperty, classproperty
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.web.flask.templating import get_overridable_template_name, get_template_module


class AgreementPersonInfo(object):
    def __init__(self, name=None, email=None, user=None, data=None):
        if user:
            if not name:
                name = user.full_name
            if not email:
                email = user.email
        if not name:
            raise ValueError('name is missing')
        self.name = name
        # Note: If you have persons with no email, you *MUST* have data that uniquely identifies such persons
        self.email = email or None
        self.user = user
        self.data = data

    @return_ascii
    def __repr__(self):
        return '<AgreementPersonInfo({}, {}, {})>'.format(self.name, self.email, self.identifier)

    @property
    def identifier(self):
        data_string = None
        if self.data:
            data_string = '-'.join('{}={}'.format(k, make_hashable(v)) for k, v in sorted(self.data.viewitems()))
        identifier = '{}:{}'.format(self.email, data_string or None)
        return sha1(identifier).hexdigest()


class AgreementDefinitionBase(object):
    """Base class for agreement definitions."""

    #: unique name of the agreement definition
    name = None
    #: readable name of the agreement definition
    title = None
    #: optional and short description of the agreement definition
    description = None
    #: url to obtain the paper version of the agreement form
    paper_form_url = None
    #: template of the agreement form - agreement definition name by default
    form_template_name = None
    #: template of the email body - emails/agreement_default_body.html by default
    email_body_template_name = None
    #: plugin containing this agreement definition - assigned automatically
    plugin = None
    #: default settings for an event
    default_event_settings = {'manager_notifications_enabled': True}
    #: default message to display when the agreement definition type is disabled
    disabled_reason = _('No signatures needed.')

    @classproperty
    @classmethod
    def locator(cls):
        return {'definition': cls.name}

    @cached_classproperty
    @classmethod
    def event_settings(cls):
        return EventSettingsProxy('agreement_{}'.format(cls.name), cls.default_event_settings)

    @classmethod
    def can_access_api(cls, user, event):
        """Check if a user can list the agreements for an event."""
        return event.can_manage(user)

    @classmethod
    def extend_api_data(cls, event, person, agreement, data):  # pragma: no cover
        """Extend the data returned in the HTTP API.

        :param event: the event
        :param person: the :class:`AgreementPersonInfo`
        :param agreement: the :class:`Agreement` if available
        :param data: a dict containing the default data for the agreement
        """
        pass

    @classmethod
    def get_email_body_template(cls, event, **kwargs):
        """
        Return the template of the email body for this agreement definition.
        """
        template_name = cls.email_body_template_name or 'emails/agreement_default_body.html'
        template_path = get_overridable_template_name(template_name, cls.plugin, 'events/agreements/')
        return get_template_module(template_path, event=event)

    @classmethod
    @memoize_request
    def get_people(cls, event):
        """
        Return a dictionary of :class:`AgreementPersonInfo` required to sign agreements.
        """
        people = cls.iter_people(event)
        if people is None:
            return {}
        return {p.identifier: p for p in people}

    @classmethod
    def get_people_not_notified(cls, event):
        """
        Return a dictionary of :class:`AgreementPersonInfo` yet to be notified.
        """
        people = cls.get_people(event)
        sent_agreements = {a.identifier for a in event.agreements.filter_by(type=cls.name)}
        return {k: v for k, v in people.items() if v.identifier not in sent_agreements}

    @classmethod
    def get_stats_for_signed_agreements(cls, event):
        """Return a digest of signed agreements on an event.

        :param event: the event
        :return: (everybody_signed, num_accepted, num_rejected)
        """
        people = cls.get_people(event)
        identifiers = [p.identifier for p in people.itervalues()]
        query = event.agreements.filter(Agreement.type == cls.name, Agreement.identifier.in_(identifiers))
        num_accepted = query.filter(Agreement.accepted).count()
        num_rejected = query.filter(Agreement.rejected).count()
        everybody_signed = len(people) == (num_accepted + num_rejected)
        return everybody_signed, num_accepted, num_rejected

    @classmethod
    def is_active(cls, event):
        """Check if the agreement type is active for a given event."""
        return bool(cls.get_people(event))

    @classmethod
    def is_agreement_orphan(cls, event, agreement):
        """Check if the agreement no longer has a corresponding person info record."""
        return agreement.identifier not in cls.get_people(event)

    @classmethod
    def render_form(cls, agreement, form, **kwargs):
        template_name = cls.form_template_name or '{}.html'.format(cls.name.replace('-', '_'))
        template_path = get_overridable_template_name(template_name, cls.plugin, 'events/agreements/')
        return render_template(template_path, agreement=agreement, form=form, **kwargs)

    @classmethod
    def render_data(cls, event, data):  # pragma: no cover
        """Return extra data to display in the agreement list.

        If you want a column to be rendered as HTML, use a :class:`~markupsafe.Markup`
        object instead of a plain string.

        :param event: The event containing the agreements
        :param data: The data from the :class:`AgreementPersonInfo`
        :return: List of extra columns for a row
        """
        return None

    @classmethod
    def handle_accepted(cls, agreement):  # pragma: no cover
        """Handle logic on agreement accepted."""
        pass

    @classmethod
    def handle_rejected(cls, agreement):  # pragma: no cover
        """Handle logic on agreement rejected."""
        pass

    @classmethod
    def handle_reset(cls, agreement):  # pragma: no cover
        """Handle logic on agreement reset."""
        pass

    @classmethod
    def iter_people(cls, event):  # pragma: no cover
        """Yield :class:`AgreementPersonInfo` required to sign agreements."""
        raise NotImplementedError
