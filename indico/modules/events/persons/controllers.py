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

import itertools
from collections import defaultdict

from flask import request, flash
from sqlalchemy.orm import joinedload, contains_eager

from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.notifications import make_email, send_email
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.persons.forms import EmailEventPersonsForm
from indico.modules.events.persons.views import WPManagePersons
from indico.util.i18n import ngettext, _
from indico.web.flask.util import url_for, jsonify_data
from indico.web.util import jsonify_form
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHPersonsList(RHConferenceModifBase):
    def _process(self):
        contribution_strategy = joinedload('contribution_links')
        contribution_strategy.joinedload('contribution')
        contribution_strategy.joinedload('person').joinedload('user')
        subcontribution_strategy = joinedload('subcontribution_links')
        subcontribution_strategy.joinedload('subcontribution')
        subcontribution_strategy.joinedload('person').joinedload('user')
        session_block_strategy = joinedload('session_block_links')
        session_block_strategy.joinedload('session_block')
        session_block_strategy.joinedload('person').joinedload('user')
        event_strategy = joinedload('event_links')
        event_strategy.joinedload('person').joinedload('user')

        event_persons_query = (self.event_new.persons.options(event_strategy, contribution_strategy,
                                                              subcontribution_strategy, session_block_strategy)
                               .all())
        persons = defaultdict(lambda: {'session_blocks': defaultdict(dict), 'contributions': defaultdict(dict),
                                       'subcontributions': defaultdict(dict), 'roles': defaultdict(dict)})

        event_principal_query = (EventPrincipal.query.with_parent(self.event_new)
                                 .filter(EventPrincipal.type == PrincipalType.email,
                                         EventPrincipal.has_management_role('submit')))

        contrib_principal_query = (ContributionPrincipal.find(Contribution.event_new == self.event_new,
                                                              ContributionPrincipal.type == PrincipalType.email,
                                                              ContributionPrincipal.has_management_role('submit'))
                                   .join(Contribution)
                                   .options(contains_eager('contribution')))

        session_principal_query = (SessionPrincipal.find(Session.event_new == self.event_new,
                                                         SessionPrincipal.type == PrincipalType.email,
                                                         SessionPrincipal.has_management_role())
                                   .join(Session).options(joinedload('session').joinedload('acl_entries')))

        chairpersons = {link.person for link in self.event_new.person_links}

        for event_person in event_persons_query:
            data = persons[event_person.email or event_person.id]

            data['person'] = event_person
            data['roles']['chairperson'] = event_person in chairpersons

            for person_link in event_person.session_block_links:
                if person_link.session_block.session.is_deleted:
                    continue

                data['session_blocks'][person_link.session_block_id] = {'title': person_link.session_block.full_title}
                data['roles']['convener'] = True

            for person_link in event_person.contribution_links:
                if not person_link.is_speaker:
                    continue
                contrib = person_link.contribution
                if contrib.is_deleted:
                    continue

                url = url_for('contributions.manage_contributions', self.event_new, selected=contrib.friendly_id)
                data['contributions'][contrib.id] = {'title': contrib.title, 'url': url}
                data['roles']['speaker'] = True

            for person_link in event_person.subcontribution_links:
                subcontrib = person_link.subcontribution
                contrib = subcontrib.contribution
                if subcontrib.is_deleted or contrib.is_deleted:
                    continue

                url = url_for('contributions.manage_contributions', self.event_new, selected=contrib.friendly_id)
                data['subcontributions'][subcontrib.id] = {'title': '{} ({})'.format(contrib.title, subcontrib.title),
                                                           'url': url}
                data['roles']['speaker'] = True

        # Some EventPersons will have no roles since they were connected to deleted things
        persons = {email: data for email, data in persons.viewitems() if
                   any(data['roles'].viewvalues())}

        num_no_account = 0
        for principal in itertools.chain(event_principal_query, contrib_principal_query, session_principal_query):
            if principal.email not in persons:
                continue
            if not persons[principal.email].get('no_account'):
                persons[principal.email]['roles']['no_account'] = True
                num_no_account += 1

        person_list = sorted(persons.viewvalues(), key=lambda x: x['person'].get_full_name(last_name_first=True).lower())

        return WPManagePersons.render_template('management/person_list.html', self._conf, event=self.event_new,
                                               persons=person_list, num_no_account=num_no_account)


class RHEmailEventPersons(RHConferenceModifBase):
    """Send emails to selected EventPersons"""

    def _checkParams(self, params):
        self._doNotSanitizeFields.append('from_address')
        RHConferenceModifBase._checkParams(self, params)

    def _process(self):
        person_ids = request.form.getlist('person_id')
        recipients = {p.email for p in self._find_event_persons(person_ids) if p.email}
        form = EmailEventPersonsForm(person_id=person_ids, recipients=', '.join(recipients))
        if form.validate_on_submit():
            for recipient in recipients:
                email = make_email(to_list=recipient, from_address=form.from_address.data,
                                   subject=form.subject.data, body=form.body.data, html=True)
                send_email(email, self.event_new, 'Event Persons')
            num = len(recipients)
            flash(ngettext('Your email has been sent.', '{} emails have been sent.', num).format(num))
            return jsonify_data()
        return jsonify_form(form, submit=_('Send'))

    def _find_event_persons(self, person_ids):
        return (self.event_new.persons
                .filter(EventPerson.id.in_(person_ids), EventPerson.email != '')
                .all())
