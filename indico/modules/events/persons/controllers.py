# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import flash, redirect, request, session
from sqlalchemy.orm import contains_eager, joinedload

from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.notifications import make_email, send_email
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.persons.forms import EmailEventPersonsForm, EventPersonForm
from indico.modules.events.persons.operations import update_person
from indico.modules.events.persons.views import WPManagePersons
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.users import User
from indico.util.date_time import now_utc
from indico.util.i18n import _, ngettext
from indico.util.placeholders import replace_placeholders
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import jsonify_data, url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_form, jsonify_template


class RHPersonsBase(RHManageEventBase):
    def get_persons(self):
        abstract_strategy = joinedload('abstract_links')
        abstract_strategy.joinedload('abstract')
        abstract_strategy.joinedload('person').joinedload('user')
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

        chairpersons = {link.person for link in self.event.person_links}
        persons = defaultdict(lambda: {'session_blocks': defaultdict(dict),
                                       'contributions': defaultdict(dict),
                                       'subcontributions': defaultdict(dict),
                                       'abstracts': defaultdict(dict),
                                       'roles': defaultdict(lambda: False)})

        event_persons_query = (self.event.persons
                               .options(abstract_strategy,
                                        event_strategy,
                                        contribution_strategy,
                                        subcontribution_strategy,
                                        session_block_strategy)
                               .all())

        for event_person in event_persons_query:
            data = persons[event_person.email or event_person.id]

            data['person'] = event_person
            data['roles']['chairperson'] = event_person in chairpersons

            for person_link in event_person.abstract_links:
                if person_link.abstract.is_deleted:
                    continue

                url = url_for('abstracts.display_abstract', person_link.abstract, management=True)
                data['abstracts'][person_link.abstract_id] = {'title': person_link.abstract.verbose_title, 'url': url}
                data['roles']['author'] = True

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

                url = url_for('contributions.manage_contributions', self.event, selected=contrib.friendly_id)
                data['contributions'][contrib.id] = {'title': contrib.title, 'url': url}
                data['roles']['speaker'] = True

            for person_link in event_person.subcontribution_links:
                subcontrib = person_link.subcontribution
                contrib = subcontrib.contribution
                if subcontrib.is_deleted or contrib.is_deleted:
                    continue

                url = url_for('contributions.manage_contributions', self.event, selected=contrib.friendly_id)
                data['subcontributions'][subcontrib.id] = {'title': '{} ({})'.format(contrib.title, subcontrib.title),
                                                           'url': url}
                data['roles']['speaker'] = True

        # Some EventPersons will have no roles since they were connected to deleted things
        persons = {email: data for email, data in persons.viewitems() if any(data['roles'].viewvalues())}
        return persons


class RHPersonsList(RHPersonsBase):
    def _process(self):
        event_principal_query = (EventPrincipal.query.with_parent(self.event)
                                 .filter(EventPrincipal.type == PrincipalType.email,
                                         EventPrincipal.has_management_role('submit')))

        contrib_principal_query = (ContributionPrincipal.find(Contribution.event == self.event,
                                                              ContributionPrincipal.type == PrincipalType.email,
                                                              ContributionPrincipal.has_management_role('submit'))
                                   .join(Contribution)
                                   .options(contains_eager('contribution')))

        session_principal_query = (SessionPrincipal.find(Session.event == self.event,
                                                         SessionPrincipal.type == PrincipalType.email,
                                                         SessionPrincipal.has_management_role())
                                   .join(Session).options(joinedload('session').joinedload('acl_entries')))

        persons = self.get_persons()
        person_list = sorted(persons.viewvalues(), key=lambda x: x['person'].display_full_name.lower())

        num_no_account = 0
        for principal in itertools.chain(event_principal_query, contrib_principal_query, session_principal_query):
            if principal.email not in persons:
                continue
            if not persons[principal.email].get('no_account'):
                persons[principal.email]['roles']['no_account'] = True
                num_no_account += 1

        return WPManagePersons.render_template('management/person_list.html', self.event,
                                               persons=person_list, num_no_account=num_no_account)


class RHEmailEventPersons(RHManageEventBase):
    """Send emails to selected EventPersons"""

    NOT_SANITIZED_FIELDS = {'from_address'}

    def _process_args(self):
        self.no_account = request.args.get('no_account') == '1'
        RHManageEventBase._process_args(self)

    def _process(self):
        person_ids = request.form.getlist('person_id')
        user_ids = request.form.getlist('user_id')
        recipients = set(self._find_event_persons(person_ids, request.args.get('not_invited_only') == '1'))
        recipients |= set(self._find_users(user_ids))
        if self.no_account:
            tpl = get_template_module('events/persons/emails/invitation.html', event=self.event)
            disabled_until_change = False
        else:
            tpl = get_template_module('events/persons/emails/generic.html', event=self.event)
            disabled_until_change = True
        form = EmailEventPersonsForm(person_id=person_ids, user_id=user_ids,
                                     recipients=[x.email for x in recipients], body=tpl.get_html_body(),
                                     subject=tpl.get_subject(), register_link=self.no_account, event=self.event)
        if form.validate_on_submit():
            self._send_emails(form, recipients)
            num = len(recipients)
            flash(ngettext('Your email has been sent.', '{} emails have been sent.', num).format(num))
            return jsonify_data()
        return jsonify_template('events/persons/email_dialog.html', form=form,
                                disabled_until_change=disabled_until_change)

    def _send_emails(self, form, recipients):
        for recipient in recipients:
            if self.no_account and isinstance(recipient, EventPerson):
                recipient.invited_dt = now_utc()
            email_body = replace_placeholders('event-persons-email', form.body.data, person=recipient,
                                              event=self.event, register_link=self.no_account)
            email_subject = replace_placeholders('event-persons-email', form.subject.data, person=recipient,
                                                 event=self.event, register_link=self.no_account)
            tpl = get_template_module('emails/custom.html', subject=email_subject, body=email_body)
            bcc = [session.user.email] if form.copy_for_sender.data else []
            email = make_email(to_list=recipient.email, bcc_list=bcc, from_address=form.from_address.data,
                               template=tpl, html=True)
            send_email(email, self.event, 'Event Persons')

    def _find_event_persons(self, person_ids, not_invited_only):
        if not person_ids:
            return []
        query = self.event.persons
        query = query.filter(EventPerson.id.in_(person_ids), EventPerson.email != '')
        if not_invited_only:
            query = query.filter(EventPerson.invited_dt.is_(None))
        return query.all()

    def _find_users(self, user_ids):
        if not user_ids:
            return []
        return User.query.filter(User.id.in_(user_ids), User.email != '').all()


class RHGrantSubmissionRights(RHManageEventBase):
    """Grants submission rights to all contribution speakers"""

    def _process(self):
        count = 0
        for cont in self.event.contributions:
            speakers = cont.speakers[:]
            for subcontrib in cont.subcontributions:
                speakers += subcontrib.speakers
            for speaker in speakers:
                principal = speaker.person.principal
                if principal:
                    cont.update_principal(principal, add_roles={'submit'})
                    count += 1
        self.event.log(EventLogRealm.management, EventLogKind.positive, 'Protection',
                       'Contribution speakers have been granted with submission rights', session.user)
        flash(ngettext('Submission rights have been granted to one speaker',
                       'Submission rights have been granted to {} speakers', count).format(count))
        return redirect(url_for('.person_list', self.event))


class RHGrantModificationRights(RHManageEventBase):
    """Grants session modification rights to all session conveners"""

    def _process(self):
        count = 0
        for sess in self.event.sessions:
            for convener in sess.conveners:
                principal = convener.person.principal
                if principal:
                    sess.update_principal(principal, full_access=True)
                    count += 1
        self.event.log(EventLogRealm.management, EventLogKind.positive, 'Protection',
                       'Modification rights have been granted to all session conveners', session.user)
        flash(ngettext('Session modification rights have been granted to one session convener',
                       'Session modification rights have been granted to {} session conveners', count).format(count))
        return redirect(url_for('.person_list', self.event))


class RHRevokeSubmissionRights(RHManageEventBase):
    """Revokes submission rights"""

    def _process(self):
        count = 0
        for cont in self.event.contributions:
            for entry in set(cont.acl_entries):
                cont.update_principal(entry.principal, del_roles={'submit'})
                count += 1
        for entry in set(self.event.acl_entries):
            self.event.update_principal(entry.principal, del_roles={'submit'})
            count += 1
        self.event.log(EventLogRealm.management, EventLogKind.negative, 'Protection',
                       'Submission privileges have been revoked from event submitters', session.user)
        flash(ngettext('Submission rights have been revoked from one user',
                       'Submission rights have been revoked from {} users', count).format(count))
        return redirect(url_for('.person_list', self.event))


class RHEditEventPerson(RHPersonsBase):
    def _process_args(self):
        RHPersonsBase._process_args(self)
        self.person = EventPerson.query.with_parent(self.event).filter_by(id=request.view_args['person_id']).one()

    def _process(self):
        form = EventPersonForm(obj=FormDefaults(self.person, skip_attrs={'title'}, title=self.person._title))
        if form.validate_on_submit():
            update_person(self.person, form.data)
            person_data = self.get_persons()[self.person.email or self.person.id]
            tpl = get_template_module('events/persons/management/_person_list_row.html')
            return jsonify_data(html=tpl.render_person_row(person_data))
        return jsonify_form(form)
