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

from collections import defaultdict

from sqlalchemy.orm import joinedload

from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.persons.views import WPManagePersons, WPManagePendingPersons
from indico.web.flask.util import url_for
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHPersonsList(RHConferenceModifBase):
    def _process(self):
        event_persons_query = (self.event_new.persons
                               .options(joinedload('event_links'), joinedload('contribution_links'),
                                        joinedload('subcontribution_links'), joinedload('session_block_links'))
                               .all())
        persons = defaultdict(lambda: {'session_blocks': defaultdict(dict), 'contributions': defaultdict(dict),
                                       'subcontributions': defaultdict(dict)})
        for event_person in event_persons_query:
            if event_person.is_principal_pending:
                continue
            data = persons[event_person]
            for person_link in event_person.session_block_links:
                data['session_blocks'][person_link.session_block_id] = {'title': person_link.session_block.full_title}
            for person_link in event_person.contribution_links:
                if not person_link.is_speaker:
                    continue
                contribution = person_link.contribution
                url = url_for('contributions.manage_contributions', self.event_new, selected=contribution.friendly_id)
                data['contributions'][contribution.id] = {'title': contribution.title, 'url': url}
            for person_link in event_person.subcontribution_links:
                subcontribution = person_link.subcontribution
                data['subcontributions'][subcontribution.id] = {'title': subcontribution.title}
        return WPManagePersons.render_template('management/person_list.html', self._conf, event=self.event_new,
                                               persons=persons)


class RHPendingPersonsList(RHConferenceModifBase):
    def _process(self):
        pending_persons = defaultdict(lambda: {'event_chairperson': False, 'contributions': {}, 'sessions': {},
                                               'subcontributions': {}})
        event_principals = (EventPrincipal.query.with_parent(self.event_new)
                            .filter(EventPrincipal.type == PrincipalType.email,
                                    EventPrincipal.has_management_role('submit')))
        for event_principal in event_principals:
            event_person = EventPerson.find_one(email=event_principal.principal.email)
            pending_persons[event_person]['event_chairperson'] = True
        for contribution in self.event_new.contributions:
            for contrib_pr in contribution.person_links:
                if contrib_pr.is_submitter and contrib_pr.person.is_principal_pending:
                    url = url_for('contributions.manage_contributions', self.event_new,
                                  selected=contribution.friendly_id)
                    event_person = contrib_pr.person
                    data = pending_persons[event_person]
                    data['contributions'][contribution.id] = {'title': contribution.title, 'url': url}
            for subc in contribution.subcontributions:
                for link in subc.person_links:
                    if link.person.is_principal_pending:
                        event_person = link.person
                        data = pending_persons[event_person]
                        data['subcontributions'][subc.id] = {'title': subc.title}
        for sess in self.event_new.sessions:
            for sess_pr in sess.acl_entries:
                sess_person = EventPerson.find_one(email=sess_pr.principal.email)
                if sess_pr.has_management_role() and sess_person.is_principal_pending:
                    data = pending_persons[sess_person]
                    data['sessions'][sess.id] = {'title': sess.title}
        return WPManagePendingPersons.render_template('management/pending_person_list.html', self._conf,
                                                      event=self.event_new, pending_persons=pending_persons)
