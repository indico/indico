# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import redirect, request, url_for
from flask import current_app as app
from werkzeug.exceptions import NotFound

from indico.core.db import DBMgr
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.util.i18n import _
from indico.util.string import is_legacy_id
from indico.web.flask.blueprints.event.display import event
from MaKaC.webinterface.rh import conferenceDisplay
from MaKaC.webinterface.urlHandlers import UHConferenceDisplay


def _event_or_shorturl(confId, shorturl_namespace=False, ovw=False):
    from MaKaC.conference import ConferenceHolder
    from MaKaC.common.url import ShortURLMapper

    func = None
    with DBMgr.getInstance().global_connection():
        ch = ConferenceHolder()
        su = ShortURLMapper()
        if ch.hasKey(confId):
            # For obvious reasons an event id always comes first.
            # If it's used within the short url namespace we redirect to the event namespace, otherwise
            # we call the RH to display the event
            if shorturl_namespace:
                url = UHConferenceDisplay.getURL(ch.getById(confId))
                func = lambda: redirect(url)
            else:
                params = request.args.to_dict()
                params['confId'] = confId
                if ovw:
                    params['ovw'] = 'True'
                func = lambda: conferenceDisplay.RHConferenceDisplay().process(params)
        elif (shorturl_namespace or app.config['INDICO_COMPAT_ROUTES']) and su.hasKey(confId):
            if shorturl_namespace:
                # Correct namespace => redirect to the event
                url = UHConferenceDisplay.getURL(su.getById(confId))
                func = lambda: redirect(url)
            else:
                # Old event namespace => 301-redirect to the new shorturl first to get Google etc. to update it
                url = url_for('.shorturl', confId=confId)
                func = lambda: redirect(url, 301)
        elif is_legacy_id(confId):
            mapping = LegacyEventMapping.find_first(legacy_event_id=confId)
            if mapping is not None:
                url = url_for('event.conferenceDisplay', confId=mapping.event_id)
                func = lambda: redirect(url, 301)

    if func is None:
        raise NotFound(_('The specified event with id or tag "{}" does not exist or has been deleted').format(confId))
    return func()


# Routes supporting shorturls
# /e/ accepts slashes, /event/ doesn't - this is intended. We do not want to support slashes in the old namespace
# since it's a major pain in the ass to do so (and its route would eat anything that's usually a 404)
event.add_url_rule('!/e/<path:confId>', 'shorturl', _event_or_shorturl, strict_slashes=False,
                   defaults={'shorturl_namespace': True})
event.add_url_rule('!/event/<confId>/', 'conferenceDisplay', _event_or_shorturl)

# Event overview
event.add_url_rule('/overview', 'conferenceDisplay-overview', _event_or_shorturl, defaults={'ovw': True})

# Event access
event.add_url_rule('/accesskey', 'conferenceDisplay-accessKey', conferenceDisplay.RHConferenceAccessKey,
                   methods=('GET', 'POST'))

# Machine-readable formats
event.add_url_rule('/event.marc.xml', 'conferenceDisplay-marcxml', conferenceDisplay.RHConferenceToMarcXML)
event.add_url_rule('/event.xml', 'conferenceDisplay-xml', conferenceDisplay.RHConferenceToXML)
