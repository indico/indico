# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from flask import redirect, request
from werkzeug.exceptions import NotFound

from MaKaC.common import DBMgr
from MaKaC.webinterface.rh import conferenceDisplay
from MaKaC.webinterface.urlHandlers import UHConferenceDisplay
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.display import event


def _event_or_shorturl(confId, shorturl_namespace=False, ovw=False):
    from MaKaC.conference import ConferenceHolder
    from MaKaC.common.url import ShortURLMapper

    with DBMgr.getInstance().global_connection():
        ch = ConferenceHolder()
        su = ShortURLMapper()
        if ch.hasKey(confId):
            # https://github.com/mitsuhiko/werkzeug/issues/397
            # It only causes problems when someone tries to POST to an URL that is not supposed to accept POST
            # requests but getting a proper 405 error in that case is very nice. When the problem in werkzeug is
            # fixed this workaround can be removed and strict_slashes re-enabled for the /<path:confId>/ rule.
            no_trailing_slash = request.base_url[-1] != '/'
            if shorturl_namespace or (no_trailing_slash and not ovw):
                url = UHConferenceDisplay.getURL(ch.getById(confId))
                func = lambda: redirect(url, 301 if no_trailing_slash else 302)
            else:
                params = request.args.to_dict()
                params['confId'] = confId
                if ovw:
                    params['ovw'] = 'True'
                func = lambda: conferenceDisplay.RHConferenceDisplay(None).process(params)
        elif su.hasKey(confId):
            url = UHConferenceDisplay.getURL(su.getById(confId))
            func = lambda: redirect(url)
        else:
            if '/' in confId and not shorturl_namespace:
                # Most likely NOT an attempt to retrieve an event with an invalid short url
                raise NotFound()
            raise NotFound(
                _('The specified event with id or tag "%s" does not exist or has been deleted') % confId)

    return func()


# Event home page and short urls
event.add_url_rule('!/e/<path:confId>', view_func=_event_or_shorturl, strict_slashes=False,
                   defaults={'shorturl_namespace': True})
event.add_url_rule('/<path:confId>/', 'conferenceDisplay', _event_or_shorturl, strict_slashes=False)
event.add_url_rule('/<confId>/overview', 'conferenceDisplay-overview', _event_or_shorturl, defaults={'ovw': True})
event.add_url_rule('/<confId>/next', 'conferenceDisplay-next', rh_as_view(conferenceDisplay.RHRelativeEvent),
                   defaults={'which': 'next'})
event.add_url_rule('/<confId>/prev', 'conferenceDisplay-prev', rh_as_view(conferenceDisplay.RHRelativeEvent),
                   defaults={'which': 'prev'})

# Event access
event.add_url_rule('/<confId>/accesskey', 'conferenceDisplay-accessKey',
                   rh_as_view(conferenceDisplay.RHConferenceAccessKey), methods=('GET', 'POST'))

# Event layout
event.add_url_rule('/<confId>/style.css', 'conferenceDisplay-getCSS', rh_as_view(conferenceDisplay.RHConferenceGetCSS))
event.add_url_rule('/<confId>/logo', 'conferenceDisplay-getLogo',
                   rh_as_view(conferenceDisplay.RHConferenceGetLogo), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/picture/<picId>.<picExt>', 'conferenceDisplay-getPic',
                   rh_as_view(conferenceDisplay.RHConferenceGetPic))

# Machine-readable formats
event.add_url_rule('/<confId>/event.ics', 'conferenceDisplay-ical', rh_as_view(conferenceDisplay.RHConferenceToiCal))
event.add_url_rule('/<confId>/event.marc.xml', 'conferenceDisplay-marcxml',
                   rh_as_view(conferenceDisplay.RHConferenceToMarcXML))
event.add_url_rule('/<confId>/event.xml', 'conferenceDisplay-xml', rh_as_view(conferenceDisplay.RHConferenceToXML))
