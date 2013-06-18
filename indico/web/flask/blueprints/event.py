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

from flask import Blueprint, redirect, url_for
from werkzeug.exceptions import NotFound

from MaKaC.common import DBMgr
from MaKaC.errors import NoReportError
from MaKaC.webinterface.urlHandlers import UHConferenceDisplay
import MaKaC.webinterface.rh.categoryDisplay as categoryDisplay
import MaKaC.webinterface.rh.conferenceDisplay as conferenceDisplay
from indico.web.flask.util import rh_as_view


def _redirect_simple_event(**kwargs):
    # simple_event is confusing so we always use "lecture" in the URL
    return redirect(url_for('.conferenceCreation', event_type='lecture', **kwargs))


def _event_or_shorturl(confId, shorturl_namespace=False):
    from MaKaC.conference import ConferenceHolder
    from MaKaC.common.url import ShortURLMapper

    with DBMgr.getInstance().global_connection():
        ch = ConferenceHolder()
        su = ShortURLMapper()
        if ch.hasKey(confId):
            if shorturl_namespace:
                url = UHConferenceDisplay.getURL(ch.getById(confId))
                func = lambda: redirect(url)
            else:
                func = lambda: conferenceDisplay.RHConferenceDisplay(None).process({'confId': confId})
        elif su.hasKey(confId):
            url = UHConferenceDisplay.getURL(su.getById(confId))
            func = lambda: redirect(url)
        else:
            if '/' in confId and not shorturl_namespace:
                # Most likely NOT an attempt to retrieve an event with an invalid short url
                raise NotFound()
            raise NotFound(
                _("The specified event with id or tag \"%s\" does not exist or has been deleted") % confId)

    return func()


event = Blueprint('event', __name__, url_prefix='/event')
event_shorturl = Blueprint('event_shorturl', __name__)


# Short URLs
event_shorturl.add_url_rule('/e/<path:confId>', view_func=_event_or_shorturl, strict_slashes=False,
                            defaults={'shorturl_namespace': True})


# conferenceCreation.py
event.add_url_rule('/create/simple_event', view_func=_redirect_simple_event)
event.add_url_rule('/create/simple_event/<categId>', view_func=_redirect_simple_event)
event.add_url_rule('/create/<any(lecture,meeting,conference):event_type>', 'conferenceCreation',
                   rh_as_view(categoryDisplay.RHConferenceCreation))
event.add_url_rule('/create/<any(lecture,meeting,conference):event_type>/<categId>', 'conferenceCreation',
                   rh_as_view(categoryDisplay.RHConferenceCreation))
event.add_url_rule('/create/save', 'conferenceCreation-createConference',
                   rh_as_view(categoryDisplay.RHConferencePerformCreation), methods=('POST',))

# conferenceDisplay.py
event.add_url_rule('/<path:confId>/', 'conferenceDisplay', _event_or_shorturl)
event.add_url_rule('/<confId>/next', 'conferenceDisplay-next', rh_as_view(conferenceDisplay.RHRelativeEvent),
                   defaults={'which': 'next'})
event.add_url_rule('/<confId>/prev', 'conferenceDisplay-prev', rh_as_view(conferenceDisplay.RHRelativeEvent),
                   defaults={'which': 'prev'})
