# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import re

from indico.core.config import Config
from indico.core.db import db
from indico.modules.events import LegacyEventMapping
from indico.modules.events.models.events import Event
from indico.util.i18n import _
from indico.web.flask.util import endpoint_for_url


class UtilsConference:
    @staticmethod
    def validateShortURL(tag, target):
        if tag.isdigit():
            raise ValueError(_("Short URL tag is a number: '%s'. Please add at least one non-digit.") % tag)
        if not re.match(r'^[a-zA-Z0-9/._-]+$', tag) or '//' in tag:
            raise ValueError(
                _("Short URL tag contains invalid chars: '%s'. Please select another one.") % tag)
        if tag[0] == '/' or tag[-1] == '/':
            raise ValueError(
                _("Short URL tag may not begin/end with a slash: '%s'. Please select another one.") % tag)
        conflict = (Event.query
                    .filter(db.func.lower(Event.url_shortcut) == tag.lower(),
                            ~Event.is_deleted,
                            Event.id != int(target.id))
                    .has_rows())
        if conflict:
            raise ValueError(_("Short URL tag already used: '%s'. Please select another one.") % tag)
        if LegacyEventMapping.query.filter_by(legacy_event_id=tag).has_rows():
            # Reject existing event ids. It'd be EXTREMELY confusing and broken to allow such a shorturl
            # Non-legacy event IDs are already covered by the `isdigit` check above.
            raise ValueError(_("Short URL tag is a legacy event id: '%s'. Please select another one.") % tag)
        ep = endpoint_for_url(Config.getInstance().getShortEventURL() + tag)
        if not ep or ep[0] != 'event.shorturl':
            # URL does not match the shorturl rule or collides with an existing rule that does does not
            # know about shorturls.
            # This shouldn't happen anymore with the /e/ namespace but we keep the check just to be safe
            raise ValueError(
                _("Short URL tag conflicts with an URL used by Indico: '%s'. Please select another one.") % tag)
