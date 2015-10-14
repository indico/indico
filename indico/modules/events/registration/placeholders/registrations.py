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

from markupsafe import Markup, escape

from indico.util.i18n import _
from indico.util.placeholders import Placeholder
from indico.util.string import to_unicode
from indico.web.flask.util import url_for


class FirstNamePlaceholder(Placeholder):
    name = 'first_name'
    description = _("First name of the person")

    @classmethod
    def render(cls, registration):
        return registration.first_name


class LastNamePlaceholder(Placeholder):
    name = 'last_name'
    description = _("Last name of the person")

    @classmethod
    def render(cls, registration):
        return registration.last_name


class EventTitlePlaceholder(Placeholder):
    name = 'event_title'
    description = _("The title of the event")

    @classmethod
    def render(cls, registration):
        return registration.registration_form.event.title


class EventLinkPlaceholder(Placeholder):
    name = 'event_link'
    description = _("Link to the event")

    @classmethod
    def render(cls, registration):
        event = registration.registration_form.event
        return Markup('<a href="{url}" title="{title}">{url}</a>'.format(url=event.getURL(),
                                                                         title=escape(to_unicode(event.title))))


class IDPlaceholder(Placeholder):
    name = 'id'
    description = _("The ID of the registration")

    @classmethod
    def render(cls, registration):
        return registration.friendly_id


class LinkPlaceholder(Placeholder):
    name = 'link'
    description = _("The link to the registration details")

    @classmethod
    def render(cls, registration):
        url = url_for('.display_regform_summary', registration.registration_form, token=registration.uuid,
                      _external=True)
        return Markup('<a href="{url}">{url}</a>'.format(url=url))
