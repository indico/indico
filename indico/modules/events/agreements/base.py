# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import render_template

from indico.modules.events.agreements.models.agreements import Agreement
from indico.util.decorators import classproperty
from indico.web.flask.templating import get_overridable_template_name
from MaKaC.accessControl import AccessWrapper


class AgreementDefinitionBase(object):
    """AgreementDefinition base class"""

    #: unique name of the agreement definition
    name = None
    #: readable name of the agreement definition
    title = None
    #: optional and short description of the agreement definition
    description = None
    #: url to obtain the paper version of the agreement form
    paper_form_url = None
    #: template of the agreement form - agreement definition name by default
    template_name = None
    #: plugin containing this agreement definition - assigned automatically
    plugin = None

    @classproperty
    @classmethod
    def locator(cls):
        return {'definition': cls.name}

    @classmethod
    def can_access_api(cls, user, event):
        """Checks if a user can list the agreements for an event."""
        return event.canModify(AccessWrapper(user))

    @classmethod
    def extend_api_data(cls, event, person, agreement, data):  # pragma: no cover
        """Extends the data returned in the HTTP API.

        :param event: the event
        :param person: the :class:`AgreementPersonInfo`
        :param agreement: the :class:`Agreement` if available
        :param data: a dict containing the default data for the agreement
        """
        pass

    @classmethod
    def render_form(cls, agreement, form, **kwargs):
        template_name = cls.template_name or '{}.html'.format(cls.name.replace('-', '_'))
        tpl = get_overridable_template_name(template_name, cls.plugin, 'events/agreements/')
        return render_template(tpl, agreement=agreement, form=form, **kwargs)

    @classmethod
    def get_people(cls, event):
        """Returns a dictionary of :class:`AgreementPersonInfo` required to sign agreements"""
        people = cls.iter_people(event)
        if people is None:
            return {}
        return {p.identifier: p for p in people}

    @classmethod
    def get_people_not_notified(cls, event):
        """Returns a dictionary of :class:`AgreementPersonInfo` yet to be notified"""
        people = cls.get_people(event)
        sent_agreements = {a.identifier for a in Agreement.find(event_id=event.getId(), type=cls.name)}
        return {k: v for k, v in people.items() if v.identifier not in sent_agreements}

    @classmethod
    def render_data(cls, event, data):  # pragma: no cover
        """Returns extra data to display in the agreement list

        If you want a column to be rendered as HTML, use a :class:`~markupsafe.Markup`
        object instead of a plain string.

        :param event: The event containing the agreements
        :param data: The data from the :class:`AgreementPersonInfo`
        :return: List of extra columns for a row
        """
        return None

    @classmethod
    def handle_accepted(cls, agreement):  # pragma: no cover
        """Handles logic on agreement accepted"""
        pass

    @classmethod
    def handle_rejected(cls, agreement):  # pragma: no cover
        """Handles logic on agreement rejected"""
        pass

    @classmethod
    def handle_reset(cls, agreement):  # pragma: no cover
        """Handles logic on agreement reset"""
        pass

    @classmethod
    def iter_people(cls, event):  # pragma: no cover
        """Yields :class:`AgreementPersonInfo` required to sign agreements"""
        raise NotImplementedError
