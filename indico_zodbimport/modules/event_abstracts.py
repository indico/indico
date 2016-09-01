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

import traceback
from datetime import timedelta
from operator import attrgetter

import click
from pytz import utc
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.email_templates import AbstractEmailTemplate
from indico.modules.events.abstracts.settings import (abstracts_settings, boa_settings,
                                                      BOACorrespondingAuthorType, BOASortField)
from indico.modules.events.models.events import EventType
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.users import User
from indico.modules.users.legacy import AvatarUserWrapper
from indico.util.console import verbose_iterator, cformat
from indico.util.string import sanitize_email
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode


def strict_sanitize_email(email, fallback=None):
    return sanitize_email(convert_to_unicode(email).lower(), require_valid=True) or fallback


class AbstractMigration(object):
    CONDITION_MAP = {'NotifTplCondAccepted': AbstractState.accepted,
                     'NotifTplCondRejected': AbstractState.rejected,
                     'NotifTplCondMerged': AbstractState.merged}

    def __init__(self, importer, conf, event):
        self.importer = importer
        self.conf = conf
        self.event = event
        self.amgr = conf.abstractMgr
        self.track_map = {}
        self.legacy_warnings_shown = set()

    def __repr__(self):
        return '<AbstractMigration({})>'.format(self.event)

    def run(self):
        self.importer.print_success(cformat('%{blue!}{}').format(self.event), event_id=self.event.id)
        self._migrate_tracks()
        self._migrate_boa_settings()
        self._migrate_settings()
        self._migrate_email_templates()
        # TODO...

    def _user_from_legacy(self, legacy_user):
        if isinstance(legacy_user, AvatarUserWrapper):
            user = legacy_user.user
            email = convert_to_unicode(legacy_user.__dict__.get('email', '')).lower() or None
        elif legacy_user.__class__.__name__ == 'Avatar':
            user = AvatarUserWrapper(legacy_user.id).user
            email = convert_to_unicode(legacy_user.email).lower()
        else:
            self.importer.print_error(cformat('%{red!}Invalid legacy user: {}').format(legacy_user),
                                      event_id=self.event.id)
            return None
        if user is None:
            user = self.importer.all_users_by_email.get(email) if email else None
            if user is not None:
                msg = 'Using {} for {} (matched via {})'.format(user, legacy_user, email)
            else:
                msg = cformat('%{yellow}Invalid legacy user: {}').format(legacy_user)
            self.importer.print_warning(msg, event_id=self.event.id, always=(msg not in self.legacy_warnings_shown))
            self.legacy_warnings_shown.add(msg)
        return user

    def _event_to_utc(self, dt):
        return self.event.tzinfo.localize(dt).astimezone(utc)

    def _migrate_tracks(self):
        for pos, old_track in enumerate(self.conf.program, 1):
            track = Track(title=convert_to_unicode(old_track.title),
                          description=convert_to_unicode(old_track.description),
                          code=convert_to_unicode(old_track._code),
                          position=pos,
                          abstract_reviewers=set())
            self.importer.print_info(cformat('%{white!}Track:%{reset} {}').format(track.title))
            for coordinator in old_track._coordinators:
                user = self._user_from_legacy(coordinator)
                if user is None:
                    continue
                self.importer.print_info(cformat('%{blue!}  Coordinator:%{reset} {}').format(user))
                track.abstract_reviewers.add(user)
                self.event.update_principal(user, add_roles={'abstract_reviewer'}, quiet=True)
            self.track_map[old_track] = track
            self.event.tracks.append(track)

    def _migrate_boa_settings(self):
        boa_config = self.conf._boa
        sort_field_map = {'number': 'id', 'none': 'id', 'name': 'abstract_title', 'sessionTitle': 'session_title',
                          'speakers': 'speaker', 'submitter': 'id'}
        try:
            sort_by = sort_field_map.get(boa_config._sortBy, boa_config._sortBy)
        except AttributeError:
            sort_by = 'id'
        corresponding_author = getattr(boa_config, '_correspondingAuthor', 'submitter')
        boa_settings.set_multi(self.event, {
            'extra_text': convert_to_unicode(boa_config._text),
            'sort_by': BOASortField[sort_by],
            'corresponding_author': BOACorrespondingAuthorType[corresponding_author],
            'show_abstract_ids': bool(getattr(boa_config, '_showIds', False))
        })

    def _migrate_settings(self):
        start_dt = self._event_to_utc(self.amgr._submissionStartDate)
        end_dt = self._event_to_utc(self.amgr._submissionEndDate)
        modification_end_dt = (self._event_to_utc(self.amgr._modifDeadline)
                               if getattr(self.amgr, '_modifDeadline', None)
                               else None)
        assert start_dt < end_dt
        if modification_end_dt and modification_end_dt - end_dt < timedelta(minutes=1):
            if modification_end_dt != end_dt:
                self.importer.print_warning('Ignoring mod deadline ({} > {})'.format(end_dt, modification_end_dt),
                                            event_id=self.event.id)
            modification_end_dt = None
        abstracts_settings.set_multi(self.event, {
            'start_dt': start_dt,
            'end_dt': end_dt,
            'modification_end_dt': modification_end_dt,
            'announcement': convert_to_unicode(self.amgr._announcement),
            'allow_multiple_tracks': bool(getattr(self.amgr, '_multipleTracks', True)),
            'tracks_required': bool(getattr(self.amgr, '_tracksMandatory', False)),
            'allow_attachments': bool(getattr(self.amgr, '_attachFiles', False)),
            'allow_speakers': bool(getattr(self.amgr, '_showSelectAsSpeaker', True)),
            'speakers_required': bool(getattr(self.amgr, '_selectSpeakerMandatory', True)),
            'authorized_submitters': set(filter(None, map(self._user_from_legacy, self.amgr._authorizedSubmitter)))
        })

    def _convert_email_template(self, tpl):
        placeholders = {'abstract_URL': 'abstract_url',
                        'abstract_id': 'abstract_id',
                        'abstract_review_comments': 'judgment_comment',
                        'abstract_session': 'abstract_session',
                        'abstract_title': 'abstract_title',
                        'abstract_track': 'abstract_track',
                        'conference_URL': 'event_url',
                        'conference_title': 'event_title',
                        'contribution_URL': 'contribution_url',
                        'contribution_type': 'contribution_type',
                        'merge_target_abstract_id': 'target_abstract_id',
                        'merge_target_abstract_title': 'target_abstract_title',
                        'merge_target_submitter_family_name': 'target_submitter_last_name',
                        'merge_target_submitter_first_name': 'target_submitter_first_name',
                        'primary_authors': 'primary_authors',
                        'submitter_family_name': 'submitter_last_name',
                        'submitter_first_name': 'submitter_first_name',
                        'submitter_title': 'submitter_title'}
        tpl = convert_to_unicode(tpl)
        for old, new in placeholders.iteritems():
            tpl = tpl.replace('%({})s'.format(old), '{%s}' % new)
        return tpl.replace('%%', '%')

    def _migrate_email_templates(self):
        assert bool(dict(self.amgr._notifTpls.iteritems())) == bool(self.amgr._notifTplsOrder)
        pos = 1
        for old_tpl in self.amgr._notifTplsOrder:
            title = convert_to_unicode(old_tpl._name)
            body = self._convert_email_template(old_tpl._tplBody)
            subject = self._convert_email_template(old_tpl._tplSubject) or 'Your Abstract Submission'
            reply_to_address = strict_sanitize_email(old_tpl._fromAddr, self.importer.default_email)
            extra_cc_emails = sorted(set(filter(None, map(strict_sanitize_email, old_tpl._ccAddrList))))
            include_submitter = any(x.__class__.__name__ == 'NotifTplToAddrSubmitter' for x in old_tpl._toAddrs)
            include_authors = any(x.__class__.__name__ == 'NotifTplToAddrPrimaryAuthors' for x in old_tpl._toAddrs)
            if not body:
                self.importer.print_warning(cformat('%{yellow!}Template "{}" has no body').format(title),
                                            event_id=self.event.id)
                continue
            tpl = AbstractEmailTemplate(title=title,
                                        position=pos,
                                        reply_to_address=reply_to_address,
                                        subject=subject,
                                        body=body,
                                        extra_cc_emails=extra_cc_emails,
                                        include_submitter=include_submitter,
                                        include_authors=include_authors,
                                        include_coauthors=bool(getattr(old_tpl, '_CAasCCAddr', False)))
            pos += 1
            self.importer.print_info(cformat('%{white!}Email Template:%{reset} {}').format(tpl.title))
            self.event.abstract_email_templates.append(tpl)
            rules = []
            for old_cond in old_tpl._conditions:
                # state
                try:
                    state = self.CONDITION_MAP[old_cond.__class__.__name__]
                except KeyError:
                    self.importer.print_error(cformat('%{red!}Invalid condition type: {}')
                                              .format(old_cond.__class__.__name__), event_id=self.event.id)
                    continue
                if state == AbstractState.rejected:
                    track = contrib_type = any
                else:
                    # track
                    if getattr(old_cond, '_track', '--any--') == '--any--':
                        track = any
                    elif getattr(old_cond, '_track', '--any--') == '--none--':
                        track = None
                    else:
                        try:
                            track = self.track_map[old_cond._track]
                        except KeyError:
                            self.importer.print_warning(cformat('%{yellow!}Invalid track: {}').format(old_cond._track),
                                                        event_id=self.event.id)
                            continue
                    # contrib type
                    if hasattr(old_cond, '_contrib_type_id'):
                        contrib_type_id = old_cond._contrib_type_id
                        if contrib_type_id == '--any--':
                            contrib_type = any
                        elif contrib_type_id == '--none--':
                            contrib_type = None
                        else:
                            contrib_type = self.event.contribution_types.filter_by(id=contrib_type_id).one()
                    elif not hasattr(old_cond, '_contribType'):
                        contrib_type = any
                        self.importer.print_warning(cformat('%{yellow}No contrib type data, using any [{}]')
                                                    .format(old_cond.__dict__), event_id=self.event.id)
                    else:
                        contrib_type = None
                        self.importer.print_error(cformat('%{red!}Legacy contribution type found: {}')
                                                  .format(old_cond._contribType), event_id=self.event.id)
                _any_str = cformat('%{green}any%{reset}')
                self.importer.print_success(cformat('%{white!}Condition:%{reset} {} | {} | {}')
                                            .format(state.name,
                                                    track if track is not any else _any_str,
                                                    contrib_type if contrib_type is not any else _any_str),
                                            event_id=self.event.id)
                rule = {'state': [state.value]}
                if track is not any:
                    rule['track'] = [track.id if track else None]
                if contrib_type is not any:
                    rule['contribution_type'] = [contrib_type.id if contrib_type else None]
                rules.append(rule)
            if not rules:
                self.importer.print_warning(cformat('%{yellow}Template "{}" has no rules').format(tpl.title),
                                            event_id=self.event.id, always=False)
            tpl.rules = rules


class EventAbstractsImporter(Importer):
    def __init__(self, **kwargs):
        self.default_email = kwargs.pop('default_email').lower()
        self.all_users_by_email = {}
        super(EventAbstractsImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--default-email', required=True, help="Fallback email in case of garbage")(command)
        return command

    def has_data(self):
        return Abstract.has_rows() or Track.has_rows()

    def migrate(self):
        self.load_data()
        self.migrate_event_abstracts()

    def load_data(self):
        self.print_step("Loading some data")
        all_users_query = User.query.options(joinedload('_all_emails')).filter_by(is_deleted=False)
        for user in all_users_query:
            for email in user.all_emails:
                self.all_users_by_email[email] = user

    def migrate_event_abstracts(self):
        self.print_step("Migrating event abstracts")
        for conf, event in committing_iterator(self._iter_events()):
            amgr = conf.abstractMgr
            duration = amgr._submissionEndDate - amgr._submissionStartDate
            if (not amgr._activated and not amgr._abstracts and not amgr._notifTpls and
                    duration < timedelta(minutes=1) and not conf.program):
                continue
            mig = AbstractMigration(self, conf, event)
            try:
                with db.session.begin_nested():
                    with db.session.no_autoflush:
                        mig.run()
                        db.session.flush()
            except Exception:
                self.print_error(cformat('%{red!}MIGRATION FAILED!'), event_id=event.id)
                traceback.print_exc()
                raw_input('Press ENTER to continue')
            db.session.flush()

    def _iter_events(self):
        from sqlalchemy.orm import subqueryload
        query = (Event.query
                 .filter(~Event.is_deleted)
                 .filter(Event.legacy_abstracts.any() | (Event.type_ == EventType.conference))
                 .options(subqueryload('legacy_abstracts')))
        it = iter(query)
        if self.quiet:
            it = verbose_iterator(query, query.count(), attrgetter('id'), lambda x: '')
        confs = self.zodb_root['conferences']
        for event in it:
            yield confs[str(event.id)], event
