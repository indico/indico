# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals, division

import mimetypes
import textwrap
import traceback
from collections import defaultdict
from datetime import timedelta
from operator import attrgetter

import click
from pytz import utc
from sqlalchemy.orm import joinedload
from werkzeug.utils import cached_property

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.modules.events import Event
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.comments import AbstractComment
from indico.modules.events.abstracts.models.email_logs import AbstractEmailLogEntry
from indico.modules.events.abstracts.models.email_templates import AbstractEmailTemplate
from indico.modules.events.abstracts.models.fields import AbstractFieldValue
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.models.review_questions import AbstractReviewQuestion
from indico.modules.events.abstracts.models.review_ratings import AbstractReviewRating
from indico.modules.events.abstracts.models.reviews import AbstractReview, AbstractAction
from indico.modules.events.abstracts.settings import (abstracts_settings, boa_settings, abstracts_reviewing_settings,
                                                      BOACorrespondingAuthorType, BOASortField)
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.models.events import EventType
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.tracks.settings import track_settings
from indico.modules.users import User
from indico.modules.users.legacy import AvatarUserWrapper
from indico.modules.users.models.users import UserTitle
from indico.util.console import verbose_iterator, cformat
from indico.util.date_time import as_utc
from indico.util.fs import secure_filename
from indico.util.string import sanitize_email, format_repr
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import LocalFileImporterMixin


def strict_sanitize_email(email, fallback=None):
    return sanitize_email(convert_to_unicode(email).lower(), require_valid=True) or fallback


# Add "temporary" column to model
# Contribution.legacy_track_id = db.Column(db.Integer, nullable=True)


class OldAbstract(db.Model):
    __tablename__ = 'legacy_abstracts'
    # XXX: remove keep_existing when removing the LegacyAbstract model from core
    __table_args__ = {'schema': 'event_abstracts', 'keep_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    friendly_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    event_id = db.Column(db.Integer, db.ForeignKey('events.events.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('events.contribution_types.id'))
    accepted_track_id = db.Column(db.Integer)
    accepted_type_id = db.Column(db.Integer, db.ForeignKey('events.contribution_types.id'))

    judgments = db.relationship('OldJudgment', lazy=False)
    event_new = db.relationship('Event', backref='old_abstracts')

    def __repr__(self):
        return format_repr(self, 'id')


class OldJudgment(db.Model):
    __tablename__ = 'judgments'
    # XXX: remove keep_existing when removing the Judgment model from core
    __table_args__ = {'schema': 'event_abstracts', 'keep_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    creation_dt = db.Column(UTCDateTime)
    abstract_id = db.Column(db.Integer, db.ForeignKey('event_abstracts.legacy_abstracts.id'))
    track_id = db.Column(db.Integer)
    judge_user_id = db.Column(db.Integer, db.ForeignKey('users.users.id'))
    accepted_type_id = db.Column(db.Integer, db.ForeignKey('events.contribution_types.id'))

    judge = db.relationship('User')
    accepted_type = db.relationship('ContributionType')

    def __repr__(self):
        return format_repr(self, 'id')


class AbstractMigration(object):
    CONDITION_MAP = {'NotifTplCondAccepted': AbstractState.accepted,
                     'NotifTplCondRejected': AbstractState.rejected,
                     'NotifTplCondMerged': AbstractState.merged}

    STATE_MAP = {'AbstractStatusSubmitted': AbstractState.submitted,
                 'AbstractStatusWithdrawn': AbstractState.withdrawn,
                 'AbstractStatusAccepted': AbstractState.accepted,
                 'AbstractStatusRejected': AbstractState.rejected,
                 'AbstractStatusMerged': AbstractState.merged,
                 'AbstractStatusDuplicated': AbstractState.duplicate,
                 # obsolete states
                 'AbstractStatusUnderReview': AbstractState.submitted,
                 'AbstractStatusProposedToReject': AbstractState.submitted,
                 'AbstractStatusProposedToAccept': AbstractState.submitted,
                 'AbstractStatusInConflict': AbstractState.submitted}

    JUDGED_STATES = {AbstractState.accepted, AbstractState.rejected, AbstractState.duplicate, AbstractState.merged}

    ACTION_MAP = {'AbstractAcceptance': AbstractAction.accept,
                  'AbstractRejection': AbstractAction.reject,
                  'AbstractReallocation': AbstractAction.change_tracks,
                  'AbstractMarkedAsDuplicated': AbstractAction.mark_as_duplicate}

    USER_TITLE_MAP = {unicode(x.title): x for x in UserTitle}

    SUBMISSION_NOTIFICATION_BODY = textwrap.dedent('''
        We've received your abstract "{abstract_title}" to which we have assigned id #{abstract_id}.

        Kind regards,
        The organizers of {event_title}
    ''').strip()

    def __init__(self, importer, conf, event):
        self.importer = importer
        self.conf = conf
        self.event = event
        self.amgr = conf.abstractMgr
        self.track_map = {}
        self.track_map_by_id = {}
        self.question_map = {}
        self.email_template_map = {}
        self.legacy_warnings_shown = set()
        self.old_scale = None
        self.new_scale = None

    def __repr__(self):
        return '<AbstractMigration({})>'.format(self.event)

    @cached_property
    def event_persons_by_email(self):
        return {ep.email: ep for ep in self.event.persons if ep.email}

    @cached_property
    def event_persons_by_user(self):
        return {ep.user: ep for ep in self.event.persons if ep.user}

    @cached_property
    def event_persons_noemail_by_data(self):
        return {(ep.first_name, ep.last_name, ep.affiliation): ep
                for ep in self.event.persons
                if not ep.email and not ep.user}

    def run(self):
        self.importer.print_success(cformat('%{blue!}{}').format(self.event), event_id=self.event.id)
        self._migrate_feature()
        self._migrate_tracks()
        self._migrate_boa_settings()
        self._migrate_settings()
        self._migrate_review_settings()
        self._migrate_email_templates()
        self._migrate_abstracts()
        self._migrate_contribution_tracks()

    def _user_from_legacy(self, legacy_user, janitor=False):
        if isinstance(legacy_user, AvatarUserWrapper):
            user = legacy_user.user
            email = convert_to_unicode(legacy_user.__dict__.get('email', '')).lower() or None
        elif legacy_user.__class__.__name__ == 'Avatar':
            user = AvatarUserWrapper(legacy_user.id).user
            email = convert_to_unicode(legacy_user.email).lower()
        else:
            self.importer.print_error(cformat('%{red!}Invalid legacy user: {}').format(legacy_user),
                                      event_id=self.event.id)
            return self.importer.janitor_user if janitor else None
        if user is None:
            user = self.importer.all_users_by_email.get(email) if email else None
            if user is not None:
                msg = 'Using {} for {} (matched via {})'.format(user, legacy_user, email)
            else:
                msg = cformat('%{yellow}Invalid legacy user: {}').format(legacy_user)
            self.importer.print_warning(msg, event_id=self.event.id, always=(msg not in self.legacy_warnings_shown))
            self.legacy_warnings_shown.add(msg)
        return user or (self.importer.janitor_user if janitor else None)

    def _event_to_utc(self, dt):
        return self.event.tzinfo.localize(dt).astimezone(utc)

    def _migrate_feature(self):
        if self.amgr._activated:
            set_feature_enabled(self.event, 'abstracts', True)

    def _migrate_tracks(self):
        program = convert_to_unicode(getattr(self.conf, 'programDescription', ''))
        if program:
            track_settings.set_multi(self.event, {'program_render_mode': RenderMode.html, 'program': program})
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
                track.conveners.add(user)
                track.abstract_reviewers.add(user)
                self.event.update_principal(user, add_roles={'abstract_reviewer', 'track_convener'}, quiet=True)
            self.track_map[old_track] = track
            self.track_map_by_id[int(old_track.id)] = track
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
            'announcement_render_mode': RenderMode.html,
            'allow_multiple_tracks': bool(getattr(self.amgr, '_multipleTracks', True)),
            'tracks_required': bool(getattr(self.amgr, '_tracksMandatory', False)),
            'allow_attachments': bool(getattr(self.amgr, '_attachFiles', False)),
            'allow_speakers': bool(getattr(self.amgr, '_showSelectAsSpeaker', True)),
            'speakers_required': bool(getattr(self.amgr, '_selectSpeakerMandatory', True)),
            'authorized_submitters': set(filter(None, map(self._user_from_legacy, self.amgr._authorizedSubmitter)))
        })

    def _migrate_review_settings(self):
        try:
            old_settings = self.conf._confAbstractReview
        except AttributeError:
            return
        self.old_scale = (int(old_settings._scaleLower), int(old_settings._scaleHigher))
        if self.old_scale[1] - self.old_scale[0] <= 20:
            self.new_scale = self.old_scale
        else:
            self.new_scale = (0, 10)
        abstracts_reviewing_settings.set_multi(self.event, {
            'scale_lower': self.new_scale[0],
            'scale_upper': self.new_scale[1],
            'allow_convener_judgment': bool(getattr(old_settings, '_canReviewerAccept', False))
        })
        for pos, old_question in enumerate(old_settings._reviewingQuestions, 1):
            self._migrate_question(old_question, pos=pos)

    def _migrate_question(self, old_question, pos=None, is_deleted=False):
        assert old_question not in self.question_map
        question = AbstractReviewQuestion(position=pos, text=convert_to_unicode(old_question._text),
                                          is_deleted=is_deleted)
        self.question_map[old_question] = question
        self.event.abstract_review_questions.append(question)
        return question

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
            self.email_template_map[old_tpl] = tpl
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

        # submission notification
        reply_to_address = strict_sanitize_email(self.conf._supportInfo._email, self.importer.default_email)
        try:
            old_sn = self.amgr._submissionNotification
        except AttributeError:
            emails = []
        else:
            emails = old_sn._toList + old_sn._ccList
        tpl = AbstractEmailTemplate(title='Abstract submitted', position=pos,
                                    reply_to_address=reply_to_address,
                                    subject='Abstract Submission confirmation (#{abstract_id})',
                                    body=self.SUBMISSION_NOTIFICATION_BODY,
                                    extra_cc_emails=sorted(set(filter(None, map(strict_sanitize_email, emails)))),
                                    include_submitter=True,
                                    rules=[{'state': [AbstractState.submitted.value]}])
        self.event.abstract_email_templates.append(tpl)

    def _migrate_abstracts(self):
        old_by_id = {oa.friendly_id: oa for oa in self.event.old_abstracts}
        abstract_map = {}
        old_abstract_state_map = {}
        as_duplicate_reviews = set()
        for zodb_abstract in self.amgr._abstracts.itervalues():
            old_abstract = old_by_id[int(zodb_abstract._id)]
            submitter = self._user_from_legacy(zodb_abstract._submitter._user, janitor=True)
            submitted_dt = zodb_abstract._submissionDate
            modified_dt = (zodb_abstract._modificationDate
                           if (submitted_dt - zodb_abstract._modificationDate) > timedelta(seconds=10)
                           else None)
            try:
                accepted_track = (self.track_map_by_id[old_abstract.accepted_track_id]
                                  if old_abstract.accepted_track_id is not None
                                  else None)
            except KeyError:
                self.importer.print_error(cformat('%{yellow!}Abstract #{} accepted in invalid track #{}')
                                          .format(old_abstract.friendly_id, old_abstract.accepted_track_id),
                                          event_id=self.event.id)
                accepted_track = None
            abstract = Abstract(id=old_abstract.id,
                                friendly_id=old_abstract.friendly_id,
                                title=convert_to_unicode(zodb_abstract._title),
                                description=old_abstract.description,
                                submitter=submitter,
                                submitted_dt=submitted_dt,
                                submitted_contrib_type_id=old_abstract.type_id,
                                submission_comment=convert_to_unicode(zodb_abstract._comments),
                                modified_dt=modified_dt)
            self.importer.print_info(cformat('%{white!}Abstract:%{reset} {}').format(abstract.title))
            self.event.abstracts.append(abstract)
            abstract_map[zodb_abstract] = abstract

            # files
            for old_attachment in getattr(zodb_abstract, '_attachments', {}).itervalues():
                storage_backend, storage_path, size = self.importer._get_local_file_info(old_attachment)
                if storage_path is None:
                    self.importer.print_error(cformat('%{red!}File not found on disk; skipping it [{}]')
                                              .format(convert_to_unicode(old_attachment.fileName)),
                                              event_id=self.event.id)
                    continue
                content_type = mimetypes.guess_type(old_attachment.fileName)[0] or 'application/octet-stream'
                filename = secure_filename(convert_to_unicode(old_attachment.fileName), 'attachment')
                attachment = AbstractFile(filename=filename, content_type=content_type, size=size,
                                          storage_backend=storage_backend, storage_file_id=storage_path)
                abstract.files.append(attachment)

            # internal comments
            for old_comment in zodb_abstract._intComments:
                comment = AbstractComment(user=self._user_from_legacy(old_comment._responsible),
                                          text=convert_to_unicode(old_comment._content),
                                          created_dt=old_comment._creationDate,
                                          modified_dt=old_comment._modificationDate)
                abstract.comments.append(comment)

            # state
            old_state = zodb_abstract._currentStatus
            old_state_name = old_state.__class__.__name__
            old_abstract_state_map[abstract] = old_state
            abstract.state = self.STATE_MAP[old_state_name]
            if abstract.state == AbstractState.accepted:
                abstract.accepted_contrib_type_id = old_abstract.accepted_type_id
                abstract.accepted_track = accepted_track

            if abstract.state in self.JUDGED_STATES:
                abstract.judge = self._user_from_legacy(old_state._responsible, janitor=True)
                abstract.judgment_dt = as_utc(old_state._date)

            # tracks
            reallocated = set(r._track for r in getattr(zodb_abstract, '_trackReallocations', {}).itervalues())
            for old_track in zodb_abstract._tracks.values():
                abstract.reviewed_for_tracks.add(self.track_map[old_track])
                if old_track not in reallocated:
                    abstract.submitted_for_tracks.add(self.track_map[old_track])

            # judgments (reviews)
            self._migrate_abstract_reviews(abstract, zodb_abstract, old_abstract, as_duplicate_reviews)
            # persons
            self._migrate_abstract_persons(abstract, zodb_abstract)
            # email log
            self._migrate_abstract_email_log(abstract, zodb_abstract)

        # merges/duplicates
        for abstract in self.event.abstracts:
            old_state = old_abstract_state_map[abstract]
            if abstract.state == AbstractState.merged:
                abstract.merged_into = abstract_map[old_state._target]
            elif abstract.state == AbstractState.duplicate:
                abstract.duplicate_of = abstract_map[old_state._original]

        # mark-as-duplicate judgments
        for review, old_abstract in as_duplicate_reviews:
            try:
                review.proposed_related_abstract = abstract_map[old_abstract]
            except KeyError:
                self.importer.print_error(cformat('%{yellow!}Abstract #{} marked as duplicate of invalid abstract #{}')
                                          .format(review.abstract.friendly_id, old_abstract._id),
                                          event_id=self.event.id)
                # delete the review; it would violate our CHECKs
                review.abstract = None
                # not needed but avoids some warnings about the object not in the session
                review.track = None
                review.user = None

    def _migrate_contribution_tracks(self):
        for contrib in Contribution.find(Contribution.event_new == self.event, ~Contribution.legacy_track_id.is_(None)):
            if contrib.legacy_track_id not in self.track_map_by_id:
                self.importer.print_warning(cformat(
                    "%{yellow!}{} %{reset}assigned to track %{yellow!}{}%{reset} which doesn't exist. Unassigning it.")
                    .format(contrib, contrib.track_id),
                    event_id=self.event.id)
                contrib.track = None
                continue

            track = self.track_map_by_id[contrib.legacy_track_id]
            contrib.track = track
            self.importer.print_success(cformat('%{blue!}{} %{reset}-> %{yellow!}{}').format(contrib, track),
                                        event_id=self.event.id)

    def _migrate_abstract_reviews(self, abstract, zodb_abstract, old_abstract, as_duplicate_reviews):
        old_judgments = {(j.track_id, j.judge): j for j in old_abstract.judgments}
        for old_track_id, zodb_judgments in getattr(zodb_abstract, '_trackJudgementsHistorical', {}).iteritems():
            seen_judges = set()
            for zodb_judgment in zodb_judgments:
                if zodb_judgment is None:
                    continue
                if zodb_judgment.__class__.__name__ == 'AbstractUnMarkedAsDuplicated':
                    # we don't have "unmarked as duplicate" anymore
                    continue
                try:
                    track = self.track_map_by_id[int(zodb_judgment._track.id)]
                except KeyError:
                    self.importer.print_warning(
                        cformat('%{blue!}Abstract {} {yellow}judged in invalid track {}%{reset}').format(
                            zodb_abstract._id, int(zodb_judgment._track.id)), event_id=self.event.id)
                    continue
                judge = self._user_from_legacy(zodb_judgment._responsible)
                if not judge:
                    # self.importer.print_warning(
                    #     cformat('%{blue!}Abstract {} {yellow}had an empty judge ({})!%{reset}').format(
                    #         zodb_abstract._id, zodb_judgment), event_id=self.event.id)
                    continue
                elif judge in seen_judges:
                    # self.importer.print_warning(
                    #     cformat("%{blue!}Abstract {}: {yellow}judge '{}' seen more than once ({})!%{reset}")
                    #         .format(zodb_abstract._id, judge, zodb_judgment), event_id=self.event.id)
                    continue

                seen_judges.add(judge)
                try:
                    created_dt = as_utc(zodb_judgment._date)
                except AttributeError:
                    created_dt = self.event.start_dt
                review = AbstractReview(created_dt=created_dt,
                                        proposed_action=self.ACTION_MAP[zodb_judgment.__class__.__name__],
                                        comment=convert_to_unicode(zodb_judgment._comment))
                if review.proposed_action == AbstractAction.accept:
                    try:
                        old_judgment = old_judgments[int(old_track_id), judge]
                    except KeyError:
                        self.importer.print_error(cformat('%{yellow!}Abstract #{} has no new judgment for {} / {}')
                                                  .format(abstract.friendly_id, int(old_track_id), judge),
                                                  event_id=self.event.id)
                        continue
                    review.proposed_contribution_type = old_judgment.accepted_type
                    review.proposed_track = self.track_map_by_id[old_judgment.track_id]
                elif review.proposed_action == AbstractAction.change_tracks:
                    review.proposed_tracks = {self.track_map[t] for t in zodb_judgment._proposedTracks}
                elif review.proposed_action == AbstractAction.mark_as_duplicate:
                    as_duplicate_reviews.add((review, zodb_judgment._originalAbst))

                review.user = judge
                review.track = track

                answered_questions = set()
                for old_answer in getattr(zodb_judgment, '_answers', []):
                    if old_answer._question in answered_questions:
                        self.importer.print_warning(
                            cformat("%{blue!}Abstract {}: {yellow}question answered more than once!").format(
                                abstract.friendly_id), event_id=self.event.id)
                        continue
                    try:
                        question = self.question_map[old_answer._question]
                    except KeyError:
                        question = self._migrate_question(old_answer._question, is_deleted=True)
                        self.importer.print_warning(
                            cformat("%{blue!}Abstract {}: {yellow}answer for deleted question").format(
                                abstract.friendly_id), event_id=self.event.id)
                    rating = AbstractReviewRating(question=question, value=self._convert_scale(old_answer))
                    review.ratings.append(rating)
                    answered_questions.add(old_answer._question)

                abstract.reviews.append(review)

    def _convert_scale(self, old_answer):
        old_value = float(old_answer._value)
        old_min, old_max = self.old_scale
        new_min, new_max = self.new_scale
        new_value = int(round((((old_value - old_min) * (new_max - new_min)) / (old_max - old_min)) + new_min))
        if int(old_value) != new_value:
            self.importer.print_warning(cformat('Adjusted value: %{cyan}{} [{}..{}] %{white}==> %{cyan!}{} [{}..{}]')
                                        .format(old_value, self.old_scale[0], self.old_scale[1],
                                                new_value, self.new_scale[0], self.new_scale[1]),
                                        always=False, event_id=self.event.id)
        return new_value

    def _migrate_abstract_email_log(self, abstract, zodb_abstract):
        for old_entry in zodb_abstract._notifLog._entries:
            email_template = self.email_template_map.get(old_entry._tpl)
            email_template_name = email_template.title if email_template else convert_to_unicode(old_entry._tpl._name)
            entry = AbstractEmailLogEntry(email_template=email_template, sent_dt=old_entry._date,
                                          user=self._user_from_legacy(old_entry._responsible),
                                          recipients=[], subject='<not available>', body='<not available>',
                                          data={'_legacy': True, 'template_name': email_template_name or '<unnamed>'})
            abstract.email_logs.append(entry)

    def _migrate_abstract_persons(self, abstract, zodb_abstract):
        old_persons = defaultdict(lambda: {'is_speaker': False, 'author_type': AuthorType.none})
        for old_person in zodb_abstract._coAuthors:
            old_persons[old_person]['author_type'] = AuthorType.secondary
        for old_person in zodb_abstract._primaryAuthors:
            old_persons[old_person]['author_type'] = AuthorType.primary
        for old_person in zodb_abstract._speakers:
            old_persons[old_person]['is_speaker'] = True

        person_links_by_person = {}
        for person, roles in old_persons.iteritems():
            person_link = self._event_person_from_legacy(person)
            person_link.author_type = roles['author_type']
            person_link.is_speaker = roles['is_speaker']
            try:
                existing = person_links_by_person[person_link.person]
            except KeyError:
                person_links_by_person[person_link.person] = person_link
            else:
                author_type = AuthorType.get_highest(existing.author_type, person_link.author_type)
                new_flags = '{}{}{}'.format('P' if person_link.author_type == AuthorType.primary else '_',
                                            'S' if person_link.author_type == AuthorType.secondary else '_',
                                            's' if person_link.is_speaker else '_')
                existing_flags = '{}{}{}'.format('P' if existing.author_type == AuthorType.primary else '_',
                                                 'S' if existing.author_type == AuthorType.secondary else '_',
                                                 's' if existing.is_speaker else '_')
                if person_link.author_type == author_type and existing.author_type != author_type:
                    # the new one has the higher author type -> use that one
                    person_link.author_type = author_type
                    person_link.is_speaker |= existing.is_speaker
                    person_links_by_person[person_link.person] = person_link
                    self.importer.print_warning(cformat('%{blue!}Abstract {}: {yellow}Author {} already exists '
                                                        '(%{magenta}{} [{}] %{yellow}/ %{green}{} [{}]%{yellow})')
                                                .format(abstract.friendly_id, existing.person.full_name,
                                                        existing.full_name, existing_flags,
                                                        person_link.full_name, new_flags),
                                                event_id=self.event.id)
                    existing.person = None  # cut the link to an already-persistent object
                else:
                    # the existing one has the higher author type -> use that one
                    existing.author_type = author_type
                    existing.is_speaker |= person_link.is_speaker
                    self.importer.print_warning(cformat('%{blue!}Abstract {}: {yellow}Author {} already exists '
                                                        '(%{green}{} [{}]%{yellow} / %{magenta}{} [{}]%{yellow})')
                                                .format(abstract.friendly_id, existing.person.full_name,
                                                        existing.full_name, existing_flags,
                                                        person_link.full_name, new_flags),
                                                event_id=self.event.id)
                    person_link.person = None  # cut the link to an already-persistent object

        abstract.person_links.extend(person_links_by_person.viewvalues())

    def _event_person_from_legacy(self, old_person):
        data = dict(first_name=convert_to_unicode(old_person._firstName),
                    last_name=convert_to_unicode(old_person._surName),
                    _title=self.USER_TITLE_MAP.get(getattr(old_person, '_title', ''), UserTitle.none),
                    affiliation=convert_to_unicode(old_person._affilliation),
                    address=convert_to_unicode(old_person._address),
                    phone=convert_to_unicode(old_person._telephone))
        email = strict_sanitize_email(old_person._email)
        if email:
            person = (self.event_persons_by_email.get(email) or
                      self.event_persons_by_user.get(self.importer.all_users_by_email.get(email)))
        else:
            person = self.event_persons_noemail_by_data.get((data['first_name'], data['last_name'],
                                                             data['affiliation']))
        if not person:
            user = self.importer.all_users_by_email.get(email)
            person = EventPerson(event_new=self.event, user=user, email=email, **data)
            if email:
                self.event_persons_by_email[email] = person
            if user:
                self.event_persons_by_user[user] = person
            if not email and not user:
                self.event_persons_noemail_by_data[(person.first_name, person.last_name, person.affiliation)] = person
        person_link = AbstractPersonLink(person=person)
        person_link.populate_from_dict(data)
        return person_link


class EventAbstractsImporter(LocalFileImporterMixin, Importer):
    def __init__(self, **kwargs):
        kwargs = self._set_config_options(**kwargs)
        self.default_email = kwargs.pop('default_email').lower()
        self.janitor_user_id = kwargs.pop('janitor_user_id')
        self.janitor_user = None
        self.all_users_by_email = {}
        super(EventAbstractsImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--default-email', required=True, help="Fallback email in case of garbage")(command)
        command = click.option('--janitor-user-id', type=int, required=True, help="The ID of the Janitor user")(command)
        return super(EventAbstractsImporter, EventAbstractsImporter).decorate_command(command)

    def has_data(self):
        return Abstract.query.has_rows() or Track.query.has_rows()

    def migrate(self):
        self.load_data()
        self.delete_orphaned_abstract_data()
        self.migrate_event_abstracts()
        self.fix_sequences('event_abstracts', {'abstracts'})

    def load_data(self):
        self.print_step("Loading some data")
        self.janitor_user = User.get_one(self.janitor_user_id)
        all_users_query = User.query.options(joinedload('_all_emails')).filter_by(is_deleted=False)
        for user in all_users_query:
            for email in user.all_emails:
                self.all_users_by_email[email] = user

    def delete_orphaned_abstract_data(self):
        self.print_step("Deleting orphaned abstract data")
        ids = {a.id for a in OldAbstract.query.join('event_new').filter(Event.is_deleted).all()}
        if ids:
            self.print_warning('Deleting abstract field values for abstracts in deleted events: {}'
                               .format(', '.join(map(unicode, ids))))
            Contribution.query.filter(Contribution.abstract_id.in_(ids)).update({Contribution.abstract_id: None},
                                                                                synchronize_session=False)
            OldAbstract.query.filter(OldAbstract.id.in_(ids)).delete(synchronize_session=False)
            OldJudgment.query.filter(OldJudgment.abstract_id.in_(ids)).delete(synchronize_session=False)
            AbstractFieldValue.query.filter(AbstractFieldValue.abstract_id.in_(ids)).delete(synchronize_session=False)
            db.session.commit()

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
                 .filter(Event.old_abstracts.any() | (Event.type_ == EventType.conference))
                 .options(subqueryload('old_abstracts')))
        it = iter(query)
        if self.quiet:
            it = verbose_iterator(query, query.count(), attrgetter('id'), lambda x: '')
        confs = self.zodb_root['conferences']
        for event in it:
            yield confs[str(event.id)], event
