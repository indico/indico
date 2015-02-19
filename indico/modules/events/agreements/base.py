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

from flask import render_template

from indico.modules.events.agreements.models.agreements import Agreement
from indico.util.decorators import classproperty
from indico.web.flask.templating import get_overridable_template_name


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
    def handle_accepted(cls, agreement):
        """Handles logic on agreement accepted"""
        pass  # pragma: no cover

    @classmethod
    def handle_rejected(cls, agreement):
        """Handles logic on agreement rejected"""
        pass  # pragma: no cover

    @classmethod
    def handle_reset(cls, agreement):
        """Handles logic on agreement reset"""
        pass  # pragma: no cover

    @classmethod
    def iter_people(cls, event):
        """Yields :class:`AgreementPersonInfo` required to sign agreements"""
        raise NotImplementedError  # pragma: no cover
