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

from __future__ import unicode_literals

from io import BytesIO

from flask import session, request, jsonify
from pytz import timezone
from sqlalchemy.orm import load_only, noload, joinedload, subqueryload
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import ContributionPersonLink, AuthorType
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.contributions.util import (get_contributions_with_user_as_submitter,
                                                      serialize_contribution_for_ical, ContributionDisplayReporter)
from indico.modules.events.contributions.views import WPMyContributions, WPContributions, WPAuthorList, WPSpeakerList
from indico.modules.events.layout.util import is_menu_entry_enabled
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.util import get_base_ical_parameters
from indico.modules.events.views import WPEventDisplay
from indico.web.flask.util import send_file, jsonify_data
from indico.web.http_api.metadata.serializer import Serializer

from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.PDFinterface.conference import ContribToPDF, ContribsToPDF
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


def _get_persons(event, condition):
    """Queries event persons linked to contributions in the event, filtered using the condition provided."""
    return (event.persons.filter(EventPerson.contribution_links.any(
                                    db.and_(condition,
                                            ContributionPersonLink.contribution.has(~Contribution.is_deleted))))
            .options(joinedload('contribution_links').joinedload('contribution'))
            .order_by(db.func.lower(EventPerson.last_name)))


class RHContributionDisplayBase(RHConferenceBaseDisplay):
    CSRF_ENABLED = True

    normalize_url_spec = {
        'locators': {
            lambda self: self.contrib
        }
    }

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        if not self.contrib.can_access(session.user):
            raise Forbidden

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.contrib = Contribution.get_one(request.view_args['contrib_id'], is_deleted=False)


class RHDisplayProtectionBase(RHConferenceBaseDisplay):
    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        if not is_menu_entry_enabled(self.MENU_ENTRY_NAME, self.event_new):
            self._forbidden_if_not_admin()


class RHMyContributions(RHDisplayProtectionBase):
    """Display list of current user contributions"""

    MENU_ENTRY_NAME = 'my_contributions'

    def _process(self):
        contributions = get_contributions_with_user_as_submitter(self.event_new, session.user)
        return WPMyContributions.render_template('display/user_contribution_list.html', self._conf,
                                                 event=self.event_new, contributions=contributions)


class RHContributionList(RHDisplayProtectionBase):
    """Display list of event contributions"""

    MENU_ENTRY_NAME = 'contributions'

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.contribs = self.event_new.contributions
        self.reporter = ContributionDisplayReporter(event=self.event_new)

    def _process(self):
        tz = timezone(DisplayTZ(session.user, self._conf).getDisplayTZ())
        return WPContributions.render_template('display/contribution_list.html', self._conf, event=self.event_new,
                                               timezone=tz, **self.reporter.get_contrib_report_kwargs())


class RHContributionDisplay(RHContributionDisplayBase):
    """Display page with contribution details """

    def _process(self):
        ical_params = get_base_ical_parameters(session.user, self.event_new, 'contributions')
        return WPContributions.render_template('display/contribution_display.html', self._conf,
                                               contribution=self.contrib, event=self.event_new, **ical_params)


class RHAuthorList(RHDisplayProtectionBase):

    MENU_ENTRY_NAME = 'author_index'

    def _process(self):
        authors = _get_persons(self.event_new, ContributionPersonLink.author_type != AuthorType.none)
        return WPAuthorList.render_template('display/author_list.html', self._conf,
                                            authors=authors, event=self.event_new)


class RHSpeakerList(RHDisplayProtectionBase):

    MENU_ENTRY_NAME = 'speaker_index'

    def _process(self):
        speakers = _get_persons(self.event_new, ContributionPersonLink.is_speaker)
        return WPSpeakerList.render_template('display/speaker_list.html', self._conf,
                                             speakers=speakers, event=self.event_new)


class RHContributionAuthor(RHContributionDisplayBase):
    """Display info about an author"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.author
        }
    }

    def _checkProtection(self):
        RHContributionDisplayBase._checkProtection(self)
        if (not is_menu_entry_enabled('author_index', self.event_new) and
                not is_menu_entry_enabled('contributions', self.event_new)):
            self._forbidden_if_not_admin()

    def _checkParams(self, params):
        RHContributionDisplayBase._checkParams(self, params)
        self.author = (ContributionPersonLink.find_one(ContributionPersonLink.author_type != AuthorType.none,
                                                       id=request.view_args['person_id'],
                                                       contribution=self.contrib))

    def _process(self):
        author_contribs = (Contribution.query.with_parent(self.event_new)
                           .join(ContributionPersonLink)
                           .options(noload('*'))
                           .options(joinedload('event_new'))
                           .options(load_only('id', 'title'))
                           .filter(ContributionPersonLink.id == self.author.id,
                                   ContributionPersonLink.author_type != AuthorType.none)
                           .all())
        return WPEventDisplay.render_template('person_display.html', self._conf,
                                              author=self.author, contribs=author_contribs)


class RHContributionExportToPDF(RHContributionDisplayBase):
    def _process(self):
        pdf = ContribToPDF(self.contrib)
        return send_file('contribution.pdf', pdf.generate(), 'application/pdf')


class RHContributionsExportToPDF(RHContributionList):
    def _process(self):
        contribs = self.reporter.get_contrib_report_kwargs()['contribs']
        pdf = ContribsToPDF(self._conf, contribs)
        return send_file('contributions.pdf', pdf.generate(), 'application/pdf')


class RHContributionExportToICAL(RHContributionDisplayBase):
    """Export contribution to ICS"""

    def _process(self):
        data = {'results': serialize_contribution_for_ical(self.contrib)}
        serializer = Serializer.create('ics')
        return send_file('contribution.ics', BytesIO(serializer(data)), 'text/calendar')


class RHContributionReport(RHContributionList):
    """Display dialog with filters"""

    def _process(self):
        return RH._process(self)

    def _process_GET(self):
        return WPContributions.render_template('contrib_report_filter.html', self._conf, event=self.event_new,
                                               filters=self.reporter.report_config['filters'],
                                               filterable_items=self.reporter.filterable_items)

    def _process_POST(self):
        self.reporter.store_filters()
        return jsonify_data(**self.reporter.render_contribution_list())


class RHContributionListStaticURL(RHContributionList):
    """Generate static URL for the current set of filters"""

    def _process(self):
        return jsonify(url=self.reporter.generate_static_url())


class RHSubcontributionDisplay(RHConferenceBaseDisplay):
    normalize_url_spec = {
        'locators': {
            lambda self: self.subcontrib
        }
    }

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        if not self.subcontrib.can_access(session.user):
            raise Forbidden

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.subcontrib = SubContribution.get_one(request.view_args['subcontrib_id'], is_deleted=False)

    def _process(self):
        return WPContributions.render_template('display/subcontribution_display.html', self._conf, event=self.event_new,
                                               subcontrib=self.subcontrib)
