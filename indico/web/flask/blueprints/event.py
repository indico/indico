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

from flask import Blueprint, redirect, url_for, request
from werkzeug.exceptions import NotFound

from MaKaC.common import DBMgr
from MaKaC.webinterface.urlHandlers import UHConferenceDisplay
import MaKaC.webinterface.rh.categoryDisplay as categoryDisplay
import MaKaC.webinterface.rh.conferenceDisplay as conferenceDisplay
import MaKaC.webinterface.rh.CFADisplay as CFADisplay
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
            # https://github.com/mitsuhiko/werkzeug/issues/397
            # It only causes problems when someone tries to POST to an URL that is not supposed to accept POST
            # requests but getting a proper 405 error in that case is very nice. When the problem in werkzeug is
            # fixed this workaround can be removed and strict_slashes re-enabled for the /<path:confId>/ rule.
            no_trailing_slash = str(request.url)[-1] != '/'
            if shorturl_namespace or no_trailing_slash:
                url = UHConferenceDisplay.getURL(ch.getById(confId))
                func = lambda: redirect(url, 301 if no_trailing_slash else 302)
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
event.add_url_rule('/<path:confId>/', 'conferenceDisplay', _event_or_shorturl, strict_slashes=False)
event.add_url_rule('/<confId>/next', 'conferenceDisplay-next', rh_as_view(conferenceDisplay.RHRelativeEvent),
                   defaults={'which': 'next'})
event.add_url_rule('/<confId>/prev', 'conferenceDisplay-prev', rh_as_view(conferenceDisplay.RHRelativeEvent),
                   defaults={'which': 'prev'})
# conferenceProgram.py
event.add_url_rule('/<confId>/program', 'conferenceProgram', rh_as_view(conferenceDisplay.RHConferenceProgram))
event.add_url_rule('/<confId>/program.pdf', 'conferenceProgram-pdf',
                   rh_as_view(conferenceDisplay.RHConferenceProgramPDF))
# conferenceCFA.py
event.add_url_rule('/<confId>/call-for-abstracts/', 'conferenceCFA', rh_as_view(CFADisplay.RHConferenceCFA))
# userAbstracts.py
event.add_url_rule('/<confId>/call-for-abstracts/my-abstracts', 'userAbstracts', rh_as_view(CFADisplay.RHUserAbstracts))
event.add_url_rule('/<confId>/call-for-abstracts/my-abstracts.pdf', 'userAbstracts-pdf',
                   rh_as_view(CFADisplay.RHUserAbstractsPDF))
# abstractSubmission.py
event.add_url_rule('/<confId>/call-for-abstracts/submit', 'abstractSubmission',
                   rh_as_view(CFADisplay.RHAbstractSubmission), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/submitted', 'abstractSubmission-confirmation',
                   rh_as_view(CFADisplay.RHAbstractSubmissionConfirmation))
# Routes for abstractModify.py
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/modify', 'abstractModify',
                   rh_as_view(CFADisplay.RHAbstractModify), methods=('GET', 'POST'))
# Routes for abstractDisplay.py
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/', 'abstractDisplay',
                   rh_as_view(CFADisplay.RHAbstractDisplay))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/file/<resId>', 'abstractDisplay-getAttachedFile',
                   rh_as_view(CFADisplay.RHGetAttachedFile))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/Abstract.pdf', 'abstractDisplay-pdf',
                   rh_as_view(CFADisplay.RHAbstractDisplayPDF))
# Routes for abstractWithdraw.py
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/withdraw', 'abstractWithdraw',
                   rh_as_view(CFADisplay.RHAbstractWithdraw), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/call-for-abstracts/<abstractId>/recover', 'abstractWithdraw-recover',
                   rh_as_view(CFADisplay.RHAbstractRecovery), methods=('GET', 'POST'))
# conferenceTimeTable.py
event.add_url_rule('/<confId>/timetable/', 'conferenceTimeTable', rh_as_view(conferenceDisplay.RHConferenceTimeTable))
event.add_url_rule('/<confId>/timetable/pdf', 'conferenceTimeTable-customizePdf',
                   rh_as_view(conferenceDisplay.RHTimeTableCustomizePDF))
event.add_url_rule('/<confId>/timetable/timetable.pdf', 'conferenceTimeTable-pdf',
                   rh_as_view(conferenceDisplay.RHTimeTablePDF), methods=('GET', 'POST'))
# contributionListDisplay.py
event.add_url_rule('/<confId>/contributions', 'contributionListDisplay',
                   rh_as_view(conferenceDisplay.RHContributionList))
event.add_url_rule('/<confId>/contributions.pdf', 'contributionListDisplay-contributionsToPDF',
                   rh_as_view(conferenceDisplay.RHContributionListToPDF), methods=('POST',))
# confAuthorIndex.py
event.add_url_rule('/<confId>/authors', 'confAuthorIndex', rh_as_view(conferenceDisplay.RHAuthorIndex))
# confSpeakerIndex.py
event.add_url_rule('/<confId>/speakers', 'confSpeakerIndex', rh_as_view(conferenceDisplay.RHSpeakerIndex))
