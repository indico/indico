# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import itertools
from collections import OrderedDict, defaultdict

from flask import flash, redirect, request, session
from sqlalchemy.orm import contains_eager, joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.notifications import make_email, send_email
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.models.roles import EventRole
from indico.modules.events.persons.forms import EmailEventPersonsForm, EventPersonForm
from indico.modules.events.persons.operations import update_person
from indico.modules.events.persons.views import WPManagePersons
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.users import User
from indico.util.date_time import now_utc
from indico.util.i18n import _, ngettext
from indico.util.placeholders import replace_placeholders
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import jsonify_data, url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_form


BUILTIN_ROLES = {'chairperson': {'name': 'Chairperson', 'code': 'CHR', 'color': 'f7b076',
                                 'css': 'background-color: #f7b076 !important; border-color: #f7b076 !important'},
                 'author': {'name': 'Author', 'code': 'AUT', 'color': '6582e8',
                            'css': 'background-color: #6582e8 !important; border-color: #6582e8 !important'},
                 'convener': {'name': 'Convener', 'code': 'CON', 'color': 'ce69e0',
                              'css': 'background-color: #ce69e0 !important; border-color: #ce69e0 !important'},
                 'speaker': {'name': 'Speaker', 'code': 'SPK', 'color': '53c7ad',
                             'css': 'background-color: #53c7ad !important; border-color: #53c7ad !important'}}


class RHPersonsBase(RHManageEventBase):
    def generate_abstracts_data(self, person_link):
        return {'title': person_link.abstract.verbose_title,
                'url': url_for('abstracts.display_abstract', person_link.abstract, management=True)}

    def generate_sessions_data(self, person_link):
        return {'title': person_link.session_block.full_title}

    def generate_contributions_data(self, person_link):
        return {'title': person_link.contribution.title,
                'url': url_for('contributions.manage_contributions', self.event,
                               selected=person_link.contribution.friendly_id)}

    def generate_subcontributions_data(self, person_link):
        return {'title': '{} ({})'.format(person_link.subcontribution.contribution.title,
                                          person_link.subcontribution.title),
                'url': url_for('contributions.manage_contributions', self.event,
                               selected=person_link.subcontribution.friendly_id)}

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
        persons = defaultdict(lambda: {'roles': OrderedDict(),
                                       'registrations': [],
                                       'has_event_person': True,
                                       'id_field_name': 'person_id'})

        _reg_person_join = db.or_((EventPerson.user_id == Registration.user_id),
                                  db.and_(EventPerson.user_id.is_(None),
                                          Registration.user_id.is_(None),
                                          EventPerson.email == Registration.email))
        event_persons_query = (db.session.query(EventPerson, Registration)
                               .filter(EventPerson.event_id == self.event.id)
                               .outerjoin(Registration, (Registration.event_id == self.event.id) & _reg_person_join)
                               .options(abstract_strategy,
                                        event_strategy,
                                        contribution_strategy,
                                        subcontribution_strategy,
                                        session_block_strategy)
                               .all())

        event_user_roles = defaultdict(set)
        for event_role in self.event.roles:
            for user in event_role.members:
                event_user_roles[user].add(event_role)

        event_person_users = set()
        for event_person, registration in event_persons_query:
            data = persons[event_person.email or event_person.id]
            if registration:
                data['registrations'].append(registration)
            data['person'] = event_person
            if event_person in chairpersons:
                data['roles']['chairperson'] = BUILTIN_ROLES['chairperson'].copy()

            if self.event.type == 'lecture':
                continue

            if self.event.has_feature('abstracts'):
                abstracts = {person_link.abstract_id: self.generate_abstracts_data(person_link)
                             for person_link in event_person.abstract_links if not person_link.abstract.is_deleted}

                if abstracts:
                    data['roles']['author'] = BUILTIN_ROLES['author'].copy()
                    data['roles']['author']['elements'] = abstracts

            session_blocks = {person_link.session_block_id: self.generate_sessions_data(person_link)
                              for person_link in event_person.session_block_links
                              if not person_link.session_block.session.is_deleted}

            if session_blocks:
                data['roles']['convener'] = BUILTIN_ROLES['convener'].copy()
                data['roles']['convener']['elements'] = session_blocks

            contributions = {person_link.contribution.id: self.generate_contributions_data(person_link)
                             for person_link in event_person.contribution_links
                             if person_link.is_speaker and not person_link.contribution.is_deleted}

            subcontributions = {person_link.subcontribution.id: self.generate_subcontributions_data(person_link)
                                for person_link in event_person.subcontribution_links
                                if not person_link.subcontribution.is_deleted and
                                not person_link.subcontribution.contribution.is_deleted}

            if contributions or subcontributions:
                data['roles']['speaker'] = BUILTIN_ROLES['speaker'].copy()
                data['roles']['speaker']['elements'] = dict(contributions, **subcontributions)

            event_user_roles_data = {}
            for role in event_user_roles[event_person.user]:
                event_user_roles_data['custom_{}'.format(role.id)] = {'name': role.name, 'code': role.code,
                                                                      'css': role.css}
            event_user_roles_data = OrderedDict(sorted(event_user_roles_data.items(), key=lambda t: t[1]['code']))
            data['roles'] = OrderedDict(data['roles'].items() + event_user_roles_data.items())

            event_person_users.add(event_person.user)

        internal_role_users = defaultdict(lambda: {'roles': OrderedDict(),
                                                   'person': [],
                                                   'has_event_person': False,
                                                   'id_field_name': 'user_id'})
        for user, roles in event_user_roles.viewitems():
            if user in event_person_users:
                continue
            for role in roles:
                user_metadata = internal_role_users[user.email]
                user_metadata['person'] = user
                user_metadata['roles']['custom_{}'.format(role.id)] = {'name': role.name, 'code': role.code,
                                                                       'css': role.css}
            user_metadata['roles'] = OrderedDict(sorted(user_metadata['roles'].items(), key=lambda x: x[1]['code']))

        # Some EventPersons will have no roles since they were connected to deleted things
        persons = {email: data for email, data in persons.viewitems() if any(data['roles'].viewvalues())}
        persons = dict(persons, **internal_role_users)
        return persons


class RHPersonsList(RHPersonsBase):
    def _process(self):
        event_principal_query = (EventPrincipal.query.with_parent(self.event)
                                 .filter(EventPrincipal.type == PrincipalType.email,
                                         EventPrincipal.has_management_permission('submit')))

        contrib_principal_query = (ContributionPrincipal.find(Contribution.event == self.event,
                                                              ContributionPrincipal.type == PrincipalType.email,
                                                              ContributionPrincipal.has_management_permission('submit'))
                                   .join(Contribution)
                                   .options(contains_eager('contribution')))

        session_principal_query = (SessionPrincipal.find(Session.event == self.event,
                                                         SessionPrincipal.type == PrincipalType.email,
                                                         SessionPrincipal.has_management_permission())
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
        custom_roles = {'custom_{}'.format(r.id): {'name': r.name, 'code': r.code, 'color': r.color}
                        for r in self.event.roles}
        return WPManagePersons.render_template('management/person_list.html', self.event, persons=person_list,
                                               num_no_account=num_no_account, builtin_roles=BUILTIN_ROLES,
                                               custom_roles=custom_roles)


class RHEmailEventPersons(RHManageEventBase):
    """Send emails to selected EventPersons."""

    def _process_args(self):
        self.no_account = request.args.get('no_account') == '1'
        RHManageEventBase._process_args(self)

    def _process(self):
        person_ids = request.form.getlist('person_id')
        user_ids = request.form.getlist('user_id')
        role_ids = request.form.getlist('role_id')
        recipients = set(self._find_event_persons(person_ids, request.args.get('not_invited_only') == '1'))
        recipients |= set(self._find_users(user_ids))
        recipients |= set(self._find_role_members(role_ids))
        if self.no_account:
            tpl = get_template_module('events/persons/emails/invitation.html', event=self.event)
            disabled_until_change = False
        else:
            tpl = get_template_module('events/persons/emails/generic.html', event=self.event)
            disabled_until_change = True
        form = EmailEventPersonsForm(person_id=person_ids, user_id=user_ids,
                                     recipients=sorted(x.email for x in recipients), body=tpl.get_html_body(),
                                     subject=tpl.get_subject(), register_link=self.no_account, event=self.event)
        if form.validate_on_submit():
            self._send_emails(form, recipients)
            num = len(recipients)
            flash(ngettext('Your email has been sent.', '{} emails have been sent.', num).format(num))
            return jsonify_data()
        return jsonify_form(form, disabled_until_change=disabled_until_change, submit=_('Send'), back=_('Cancel'))

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

    def _find_role_members(self, role_ids):
        if not role_ids:
            return []
        query = (EventRole.query.with_parent(self.event)
                 .filter(EventRole.id.in_(role_ids))
                 .options(joinedload('members')))
        return itertools.chain.from_iterable(role.members for role in query)


class RHGrantSubmissionRights(RHManageEventBase):
    """Grant submission rights to all contribution speakers."""

    def _process(self):
        count = 0
        for cont in self.event.contributions:
            speakers = cont.speakers[:]
            for subcontrib in cont.subcontributions:
                speakers += subcontrib.speakers
            for speaker in speakers:
                principal = speaker.person.principal
                if principal:
                    cont.update_principal(principal, add_permissions={'submit'})
                    count += 1
        self.event.log(EventLogRealm.management, EventLogKind.positive, 'Protection',
                       'Contribution speakers have been granted with submission rights', session.user)
        flash(ngettext('Submission rights have been granted to one speaker',
                       'Submission rights have been granted to {} speakers', count).format(count))
        return redirect(url_for('.person_list', self.event))


class RHGrantModificationRights(RHManageEventBase):
    """Grant session modification rights to all session conveners."""

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
    """Revoke submission rights."""

    def _process(self):
        count = 0
        for cont in self.event.contributions:
            for entry in set(cont.acl_entries):
                cont.update_principal(entry.principal, del_permissions={'submit'})
                count += 1
        for entry in set(self.event.acl_entries):
            self.event.update_principal(entry.principal, del_permissions={'submit'})
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
            return jsonify_data(html=tpl.render_person_row(person_data, bool(self.event.registration_forms)))
        return jsonify_form(form)
