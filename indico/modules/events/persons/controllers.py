# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import itertools
from collections import defaultdict

from flask import flash, jsonify, redirect, request, session
from marshmallow import fields
from sqlalchemy import and_, or_
from sqlalchemy.orm import contains_eager, joinedload
from webargs import validate
from webargs.flaskparser import abort
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.unaccent import unaccent_match
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.notifications import make_email, send_email
from indico.modules.events import EventLogRealm
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.controllers.base import EditEventSettingsMixin, RHAuthenticatedEventBase
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.models.roles import EventRole
from indico.modules.events.persons import logger, persons_settings
from indico.modules.events.persons.forms import ManagePersonListsForm
from indico.modules.events.persons.operations import update_person
from indico.modules.events.persons.schemas import EventPersonSchema, EventPersonUpdateSchema
from indico.modules.events.persons.views import WPManagePersons
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.logs import LogKind
from indico.modules.users.models.affiliations import Affiliation
from indico.util.date_time import now_utc
from indico.util.i18n import _, ngettext
from indico.util.marshmallow import LowercaseString, no_relative_urls, not_empty, validate_with_message
from indico.util.placeholders import get_sorted_placeholders, replace_placeholders
from indico.util.user import principal_from_identifier
from indico.web.args import use_args, use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import jsonify_data, url_for


BUILTIN_ROLES = {'chairperson': {'name': _('Chairperson'), 'code': 'CHR', 'color': 'f7b076',
                                 'css': 'background-color: #f7b076 !important; border-color: #f7b076 !important'},
                 'author': {'name': _('Author'), 'code': 'AUT', 'color': '6582e8',
                            'css': 'background-color: #6582e8 !important; border-color: #6582e8 !important'},
                 'convener': {'name': _('Convener'), 'code': 'CON', 'color': 'ce69e0',
                              'css': 'background-color: #ce69e0 !important; border-color: #ce69e0 !important'},
                 'speaker': {'name': _('Speaker'), 'code': 'SPK', 'color': '53c7ad',
                             'css': 'background-color: #53c7ad !important; border-color: #53c7ad !important'},
                 'lecture_speaker': {'name': _('Speaker'), 'code': 'SPK', 'color': '53c7ad',
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
        return {'title': f'{person_link.subcontribution.contribution.title} ({person_link.subcontribution.title})',
                'url': url_for('contributions.manage_contributions', self.event,
                               selected=person_link.subcontribution.contribution.friendly_id)}

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
        persons = defaultdict(lambda: {'roles': {},
                                       'registrations': [],
                                       'has_event_person': True,
                                       'id_field_name': 'person_id'})

        _reg_person_join = db.or_((EventPerson.user_id == Registration.user_id),
                                  db.and_(EventPerson.user_id.is_(None),
                                          Registration.user_id.is_(None),
                                          EventPerson.email == Registration.email))
        event_persons_query = (db.session.query(EventPerson, Registration)
                               .filter(EventPerson.event_id == self.event.id)
                               .outerjoin(Registration, db.and_(
                                   Registration.event_id == self.event.id,
                                   Registration.registration_form.has(~RegistrationForm.is_deleted),
                                   _reg_person_join
                               ))
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
            if registration and registration.is_active:
                data['registrations'].append(registration)
            data['person'] = event_person
            if event_person in chairpersons:
                if self.event.type != 'lecture':
                    data['roles']['chairperson'] = BUILTIN_ROLES['chairperson'].copy()
                else:
                    data['roles']['lecture_speaker'] = BUILTIN_ROLES['lecture_speaker'].copy()

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
                data['roles']['speaker']['elements'] = contributions | subcontributions

            author_contributions = {person_link.contribution.id: self.generate_contributions_data(person_link)
                                    for person_link in event_person.contribution_links
                                    if person_link.is_author and not person_link.contribution.is_deleted}

            if author_contributions:
                data['roles']['author'] = BUILTIN_ROLES['author'].copy()
                data['roles']['author']['elements'] = author_contributions

            event_user_roles_data = {}
            for role in event_user_roles[event_person.user]:
                event_user_roles_data[f'custom_{role.id}'] = {'name': role.name, 'code': role.code, 'css': role.css}
            event_user_roles_data = dict(sorted(event_user_roles_data.items(), key=lambda t: t[1]['code']))
            data['roles'] |= event_user_roles_data

            event_person_users.add(event_person.user)

        internal_role_users = defaultdict(lambda: {'roles': {},
                                                   'person': [],
                                                   'registrations': [],
                                                   'has_event_person': False,
                                                   'id_field_name': 'user_id'})
        for user, roles in event_user_roles.items():
            if user in event_person_users:
                continue
            for role in roles:
                user_metadata = internal_role_users[user.email]
                user_metadata['person'] = user
                user_metadata['roles'][f'custom_{role.id}'] = {'name': role.name, 'code': role.code, 'css': role.css}
            user_metadata['roles'] = dict(sorted(user_metadata['roles'].items(), key=lambda x: x[1]['code']))

        regs = (Registration.query
                .with_parent(self.event)
                .join(Registration.registration_form)
                .filter(Registration.user_id.in_(data['person'].id for data in internal_role_users.values()),
                        Registration.is_active, ~RegistrationForm.is_deleted)
                .all())
        for reg in regs:
            internal_role_users[reg.user.email]['registrations'].append(reg)

        persons |= internal_role_users
        # Some EventPersons will have no built-in roles since they were connected to deleted things
        builtin_roles = set(BUILTIN_ROLES)
        for person in persons:
            roles = set(persons[person]['roles'].keys())
            if not roles:
                persons[person]['roles']['no_roles'] = True
            if not roles & builtin_roles:
                persons[person]['roles']['no_builtin_roles'] = True
        return persons


class RHPersonsList(RHPersonsBase):
    def _process(self):
        event_principal_query = (EventPrincipal.query.with_parent(self.event)
                                 .filter(EventPrincipal.type == PrincipalType.email,
                                         EventPrincipal.has_management_permission('submit')))

        contrib_principal_query = (ContributionPrincipal.query
                                   .filter(Contribution.event == self.event,
                                           ContributionPrincipal.type == PrincipalType.email,
                                           ContributionPrincipal.has_management_permission('submit'))
                                   .join(Contribution)
                                   .options(contains_eager('contribution')))

        session_principal_query = (SessionPrincipal.query
                                   .filter(Session.event == self.event,
                                           SessionPrincipal.type == PrincipalType.email,
                                           SessionPrincipal.has_management_permission())
                                   .join(Session)
                                   .options(joinedload('session').joinedload('acl_entries')))

        persons = self.get_persons()
        person_list = sorted(persons.values(), key=lambda x: x['person'].display_full_name.lower())

        num_no_account = 0
        for principal in itertools.chain(event_principal_query, contrib_principal_query, session_principal_query):
            if principal.email not in persons:
                continue
            if not persons[principal.email].get('no_account'):
                persons[principal.email]['roles']['no_account'] = True
                num_no_account += 1
        custom_roles = {f'custom_{r.id}': {'name': r.name, 'code': r.code, 'color': r.color}
                        for r in self.event.roles}
        for person_data in persons.values():
            if not person_data['registrations']:
                person_data['roles']['no_registration'] = True
        return WPManagePersons.render_template('management/person_list.html', self.event, persons=person_list,
                                               num_no_account=num_no_account, builtin_roles=BUILTIN_ROLES,
                                               custom_roles=custom_roles, person_schema=EventPersonSchema(),
                                               has_predefined_affiliations=Affiliation.query.has_rows())


class RHEmailEventPersonsBase(RHManageEventBase):
    """Send emails to selected EventPersons."""

    PERMISSION = 'contributions'

    @use_kwargs({
        'role_id': fields.List(fields.Integer(), load_default=lambda: []),
        'persons': fields.List(fields.String(), load_default=lambda: []),
        'not_invited_only': fields.Bool(load_default=None),
        'no_account': fields.Bool(load_default=False),
    })
    def _process_args(self, role_id, persons, not_invited_only, no_account):
        RHManageEventBase._process_args(self)
        principals = [principal_from_identifier(identifier, allow_event_persons=True, event_id=self.event.id)
                      for identifier in persons]
        if not_invited_only:
            self.recipients = {p for p in principals if p.invited_dt is None}
        else:
            self.recipients = set(principals)
        self.recipients |= set(self._find_role_members(role_id))
        self.no_account = no_account

    def _find_role_members(self, role_ids):
        if not role_ids:
            return []
        query = (EventRole.query.with_parent(self.event)
                 .filter(EventRole.id.in_(role_ids))
                 .options(joinedload('members')))
        return itertools.chain.from_iterable(role.members for role in query)


class RHEmailEventPersonsPreview(RHEmailEventPersonsBase):
    """Preview an email with EventPersons associated placeholders."""

    @use_kwargs({
        'body': fields.String(required=True),
        'subject': fields.String(required=True),
    })
    def _process(self, body, subject):
        person = next(iter(self.recipients)) if self.recipients else session.user
        email_body = replace_placeholders('event-persons-email', body, event=self.event, person=person,
                                          register_link=self.no_account)
        email_subject = replace_placeholders('event-persons-email', subject, event=self.event, person=person,
                                             register_link=self.no_account)
        tpl = get_template_module('events/persons/emails/custom_email.html', email_subject=email_subject,
                                  email_body=email_body)
        return jsonify(subject=tpl.get_subject(), body=tpl.get_body())


class RHAPIEmailEventPersonsMetadata(RHEmailEventPersonsBase):
    def _process(self):
        with self.event.force_event_locale():
            if self.no_account:
                tpl = get_template_module('events/persons/emails/invitation.html', event=self.event)
            else:
                tpl = get_template_module('events/persons/emails/generic.html', event=self.event)
            body = tpl.get_html_body()
            subject = tpl.get_subject()
        placeholders = get_sorted_placeholders('event-persons-email', event=None, person=None,
                                               register_link=self.no_account)
        return jsonify({
            'senders': list(self.event.get_allowed_sender_emails().items()),
            'recipients': sorted(x.email for x in self.recipients),
            'body': body,
            'subject': subject,
            'placeholders': [p.serialize(event=None, person=None) for p in placeholders],
        })


class RHAPIEmailEventPersonsSend(RHEmailEventPersonsBase):
    @use_kwargs({
        'from_address': fields.String(required=True, validate=not_empty),
        'body': fields.String(required=True, validate=[not_empty, no_relative_urls]),
        'subject': fields.String(required=True, validate=not_empty),
        'bcc_addresses': fields.List(LowercaseString(validate=validate.Email())),
        'copy_for_sender': fields.Bool(load_default=False),
    })
    def _process(self, from_address, body, subject, bcc_addresses, copy_for_sender):
        if from_address not in self.event.get_allowed_sender_emails():
            abort(422, messages={'from_address': ['Invalid sender address']})
        for recipient in self.recipients:
            if self.no_account and isinstance(recipient, EventPerson):
                recipient.invited_dt = now_utc()
            email_body = replace_placeholders('event-persons-email', body, person=recipient,
                                              event=self.event, register_link=self.no_account)
            email_subject = replace_placeholders('event-persons-email', subject, person=recipient,
                                                 event=self.event, register_link=self.no_account)
            bcc = {session.user.email} if copy_for_sender else set()
            bcc.update(bcc_addresses)
            with self.event.force_event_locale():
                tpl = get_template_module('emails/custom.html', subject=email_subject, body=email_body)
                email = make_email(to_list=recipient.email, bcc_list=bcc, from_address=from_address,
                                   template=tpl, html=True)
            send_email(email, self.event, 'Event Persons')
        return jsonify(count=len(self.recipients))


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
        self.event.log(EventLogRealm.management, LogKind.positive, 'Protection',
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
        self.event.log(EventLogRealm.management, LogKind.positive, 'Protection',
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
        self.event.log(EventLogRealm.management, LogKind.negative, 'Protection',
                       'Submission privileges have been revoked from event submitters', session.user)
        flash(ngettext('Submission rights have been revoked from one user',
                       'Submission rights have been revoked from {} users', count).format(count))
        return redirect(url_for('.person_list', self.event))


class RHEventPersonActionBase(RHPersonsBase):
    def _process_args(self):
        RHPersonsBase._process_args(self)
        self.person = EventPerson.query.with_parent(self.event).filter_by(id=request.view_args['person_id']).one()


class RHUpdateEventPerson(RHEventPersonActionBase):
    @use_args(EventPersonUpdateSchema, partial=True)
    def _process(self, args):
        update_person(self.person, args)
        person_data = self.get_persons()[self.person.email or self.person.id]
        tpl = get_template_module('events/persons/management/_person_list_row.html')
        return jsonify(html=tpl.render_person_row(person_data, bool(self.event.registration_forms),
                                                  EventPersonSchema(), Affiliation.query.has_rows()))


class RHDeleteUnusedEventPerson(RHEventPersonActionBase):
    def _process(self):
        if self.person.has_links:
            raise Forbidden(_('Only users with no ties to the event can be deleted.'))
        db.session.delete(self.person)
        logger.info('EventPerson deleted from event %r: %r', self.event, self.person)
        return jsonify_data()


class RHSyncEventPerson(RHEventPersonActionBase):
    def _process(self):
        if not self.person.user:
            raise Forbidden(_('Persons with no associated users cannot be synced.'))
        self.person.sync_user(notify=False)
        logger.info('EventPerson synced with user in event %r: %r', self.event, self.person)
        person_data = self.get_persons()[self.person.email or self.person.id]
        tpl = get_template_module('events/persons/management/_person_list_row.html')
        return jsonify_data(html=tpl.render_person_row(person_data, bool(self.event.registration_forms),
                                                       EventPersonSchema(), Affiliation.query.has_rows()))


class RHEventPersonSearch(RHAuthenticatedEventBase):
    def _search_event_persons(self, exact=False, **criteria):
        criteria = {key: v for key, value in criteria.items() if (v := value.strip())}

        if not criteria:
            return []

        query = EventPerson.query.distinct(EventPerson.id).filter(EventPerson.event_id == self.event.id)

        query = query.filter(
            or_(
                EventPerson.abstract_links.any(AbstractPersonLink.abstract.has(~Abstract.is_deleted)),
                EventPerson.contribution_links.any(ContributionPersonLink.contribution.has(~Contribution.is_deleted)),
                EventPerson.event_links.any(),
                EventPerson.subcontribution_links.any(
                    SubContributionPersonLink.subcontribution.has(
                        and_(~SubContribution.is_deleted, SubContribution.contribution.has(~Contribution.is_deleted))
                    )
                ),
                EventPerson.session_block_links.any(),
            )
        )

        for k, v in criteria.items():
            query = query.filter(unaccent_match(getattr(EventPerson, k), v, exact))

        # wrap as subquery so we can apply order regardless of distinct-by-id
        query = query.from_self()
        query = query.order_by(
            db.func.lower(db.func.indico.indico_unaccent(EventPerson.first_name)),
            db.func.lower(db.func.indico.indico_unaccent(EventPerson.last_name)),
            EventPerson.id,
        )
        return query.limit(10).all(), query.count()

    @use_kwargs({
        'first_name': fields.Str(validate=validate.Length(min=1)),
        'last_name': fields.Str(validate=validate.Length(min=1)),
        'email': fields.Str(validate=lambda s: len(s) > 3),
        'affiliation': fields.Str(validate=validate.Length(min=1)),
        'exact': fields.Bool(load_default=False),
    }, validate=validate_with_message(
        lambda args: args.keys() & {'first_name', 'last_name', 'email', 'affiliation'},
        'No criteria provided'
    ), location='query')
    def _process(self, exact, **criteria):
        matches, total = self._search_event_persons(exact=exact, **criteria)
        return jsonify(
            users=EventPersonSchema(only=EventPersonSchema.Meta.public_fields).dump(matches, many=True),
            total=total
        )


class RHManagePersonLists(EditEventSettingsMixin, RHManageEventBase):
    """Dialog to configure person list settings."""

    settings_proxy = persons_settings
    form_cls = ManagePersonListsForm
    success_message = _('Person lists settings changed successfully')
    log_module = 'Persons'
    log_message = 'Settings updated'
    log_fields = {'disallow_custom_persons': 'Disallow custom persons',
                  'default_search_external': 'Include users with no Indico account by default',
                  'show_titles': 'Show person titles'}
