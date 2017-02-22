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

import itertools
import mimetypes
from collections import defaultdict
from operator import attrgetter

import click
from pytz import utc
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.storage import StorageError, StoredFileMixin
from indico.modules.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.models.events import EventType
from indico.modules.events.papers.models.competences import PaperCompetence
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.review_questions import PaperReviewQuestion
from indico.modules.events.papers.models.review_ratings import PaperReviewRating
from indico.modules.events.papers.models.reviews import PaperReview, PaperReviewType, PaperAction
from indico.modules.events.papers.models.revisions import PaperRevision, PaperRevisionState
from indico.modules.events.papers.models.templates import PaperTemplate
from indico.modules.events.papers.settings import paper_reviewing_settings, PaperReviewingRole
from indico.modules.users import User
from indico.util.console import verbose_iterator, cformat
from indico.util.fs import secure_filename
from indico.util.string import crc32, format_repr
from indico.util.struct.enum import IndicoEnum
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import LocalFileImporterMixin

CPR_NO_REVIEWING = 1
CPR_CONTENT_REVIEWING = 2
CPR_LAYOUT_REVIEWING = 3
CPR_CONTENT_AND_LAYOUT_REVIEWING = 4

JUDGMENT_STATE_PAPER_ACTION_MAP = {
    1: PaperAction.accept,
    2: PaperAction.to_be_corrected,
    3: PaperAction.reject
}

JUDGMENT_STATE_REVISION_MAP = {
    1: PaperRevisionState.accepted,
    2: PaperRevisionState.to_be_corrected,
    3: PaperRevisionState.rejected
}

STATE_COLOR_MAP = {
    PaperRevisionState.submitted: 'white',
    PaperRevisionState.accepted: 'green',
    PaperRevisionState.to_be_corrected: 'yellow',
    PaperRevisionState.rejected: 'red'
}


class LegacyPaperReviewingRoleType(int, IndicoEnum):
    reviewer = 0
    referee = 1
    editor = 2


class LegacyPaperReviewingRole(db.Model):
    __tablename__ = 'legacy_contribution_roles'
    __table_args__ = {'schema': 'event_paper_reviewing'}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.users.id'), nullable=False)
    contribution_id = db.Column(db.Integer, db.ForeignKey('events.contributions.id'))
    role = db.Column(PyIntEnum(LegacyPaperReviewingRoleType))

    contribution = db.relationship('Contribution', lazy=False, backref='legacy_paper_reviewing_roles')
    user = db.relationship('User', lazy=False)

    def __repr__(self):
        return format_repr(self, 'id')


class LegacyPaperFile(StoredFileMixin, db.Model):
    __tablename__ = 'legacy_paper_files'
    __table_args__ = {'schema': 'event_paper_reviewing'}

    id = db.Column(db.Integer, primary_key=True)
    contribution_id = db.Column(db.Integer, db.ForeignKey('events.contributions.id'))
    revision_id = db.Column(db.Integer)
    contribution = db.relationship('Contribution', lazy=False, backref='legacy_paper_files')

    def __repr__(self):
        return format_repr(self, 'id')


def _to_utc(dt):
    return dt.astimezone(utc) if dt else None


def _translate_notif_options(pr, options):
    return {PaperReviewingRole[role] for role, (attr, default) in options.viewitems() if getattr(pr, attr, default)}


def _review_color(review, text):
    return '%{{{}}}{}%{{reset}}'.format({
        PaperAction.accept: 'green',
        PaperAction.to_be_corrected: 'yellow',
        PaperAction.reject: 'red'
    }[review.proposed_action], text)


def _paper_file_from_legacy(lpf):
    return PaperFile(filename=lpf.filename, content_type=lpf.content_type, size=lpf.size,
                     storage_backend=lpf.storage_backend, storage_file_id=lpf.storage_file_id,
                     created_dt=_to_utc(lpf.created_dt), _contribution=lpf.contribution)


class PaperMigration(object):
    def __init__(self, importer, conf, event, janitor_user):
        self.importer = importer
        self.conf = conf
        self.event = event
        self.janitor_user = janitor_user
        self.pr = conf._confPaperReview
        self.legacy_question_map = {}
        self.legacy_contrib_revision_map = {}
        self.legacy_contrib_last_revision_map = dict()

    def run(self):
        self.importer.print_success(cformat('%{blue!}{}').format(self.event), event_id=self.event.id)
        self._migrate_feature()
        self._migrate_settings()
        self._migrate_event_roles()
        self._migrate_questions()
        self._migrate_templates()
        self._migrate_competences()
        self._migrate_papers()
        self._migrate_paper_files()

    def _migrate_feature(self):
        if self.pr._choice != CPR_NO_REVIEWING:
            set_feature_enabled(self.event, 'papers', True)

    def _migrate_settings(self):
        pr = self.pr

        role_add = _translate_notif_options(pr, {
            'layout_reviewer': ('_enableEditorEmailNotif', False),
            'content_reviewer': ('_enableReviewerEmailNotif', False),
            'judge': ('_enableRefereeEmailNotif', False)
        })

        contrib_assignment = _translate_notif_options(pr, {
            'layout_reviewer': ('_enableEditorEmailNotifForContribution', False),
            'content_reviewer': ('_enableReviewerEmailNotifForContribution', False),
            'judge': ('_enableRefereeEmailNotifForContribution', False)
        })

        paper_submission = _translate_notif_options(pr, {
            'layout_reviewer': ('_enableAuthorSubmittedMatEditorEmailNotif', True),
            'content_reviewer': ('_enableAuthorSubmittedMatReviewerEmailNotif', True),
            'judge': ('_enableAuthorSubmittedMatRefereeEmailNotif', False)
        })

        paper_reviewing_settings.set_multi(self.event, {
            'start_dt': _to_utc(pr._startSubmissionDate),
            'end_dt': _to_utc(pr._endSubmissionDate),
            'judge_deadline': _to_utc(pr._defaultRefereeDueDate),
            'content_reviewer_deadline': _to_utc(pr._defaultReviwerDueDate),
            'layout_reviewer_deadline': _to_utc(pr._defaultEditorDueDate),
            'enforce_judge_deadline': False,
            'enforce_layout_reviewer_deadline': False,
            'enforce_content_reviewer_deadline': False,
            'content_reviewing_enabled': pr._choice in {CPR_CONTENT_REVIEWING, CPR_CONTENT_AND_LAYOUT_REVIEWING},
            'layout_reviewing_enabled': pr._choice in {CPR_LAYOUT_REVIEWING, CPR_CONTENT_AND_LAYOUT_REVIEWING},
            'scale_lower': -3,
            'scale_upper': 3,

            # notifications
            'notify_on_added_to_event': role_add,
            'notify_on_assigned_contrib': contrib_assignment,
            'notify_on_paper_submission': paper_submission,
            'notify_judge_on_review': (getattr(pr, '_enableEditorSubmittedRefereeEmailNotif', True) or
                                       getattr(pr, '_enableReviewerSubmittedRefereeEmailNotif', True)),
            'notify_author_on_judgment': (pr._enableRefereeJudgementEmailNotif or pr._enableEditorJudgementEmailNotif or
                                          pr._enableReviewerJudgementEmailNotif)
        })

    def _migrate_event_roles(self):
        for avatar in self.pr._paperReviewManagersList:
            self.event.update_principal(avatar.user, add_roles={'paper_manager'}, quiet=True)
        for avatar in self.pr._refereesList:
            self.event.update_principal(avatar.user, add_roles={'paper_judge'}, quiet=True)
        for avatar in self.pr._reviewersList:
            self.event.update_principal(avatar.user, add_roles={'paper_content_reviewer'}, quiet=True)
        for avatar in self.pr._editorsList:
            self.event.update_principal(avatar.user, add_roles={'paper_layout_reviewer'}, quiet=True)

    def _migrate_questions(self):
        for n, q in enumerate(self.pr._reviewingQuestions, 1):
            question = PaperReviewQuestion(text=q._text, type=PaperReviewType.content, position=n, event_new=self.event)
            self.event.paper_review_questions.append(question)
            self.legacy_question_map[q] = question

        for n, q in enumerate(self.pr._layoutQuestions, 1):
            question = PaperReviewQuestion(text=q._text, type=PaperReviewType.layout, position=n, event_new=self.event)
            self.event.paper_review_questions.append(question)
            self.legacy_question_map[q] = question

    def _migrate_templates(self):
        for __, old_tpl in self.pr._templates.viewitems():
            old_filename = convert_to_unicode(old_tpl._Template__file.name)
            storage_backend, storage_path, size = self.importer._get_local_file_info(old_tpl._Template__file)
            if storage_path is None:
                self.importer.print_error(cformat('%{red!}File not found on disk; skipping it [{}]')
                                          .format(old_filename),
                                          event_id=self.event.id)
                continue

            filename = secure_filename(old_filename, 'attachment')
            content_type = mimetypes.guess_type(old_filename)[0] or 'application/octet-stream'
            tpl = PaperTemplate(filename=filename, content_type=content_type, size=size,
                                storage_backend=storage_backend, storage_file_id=storage_path,
                                name=convert_to_unicode(old_tpl._Template__name) or old_filename,
                                description=convert_to_unicode(old_tpl._Template__description))
            self.event.paper_templates.append(tpl)

    def _migrate_competences(self):
        competence_map = {}
        for avatar, competences in self.pr._userCompetences.viewitems():
            if avatar.user.id in competence_map:
                # add to existing list, which SQLAlchemy will commit
                competence_map[avatar.user.id] += competences
            elif competences:
                competence_map[avatar.user.id] = competences
                competence = PaperCompetence(user=avatar.user, competences=competences)
                self.event.paper_competences.append(competence)

    def _migrate_paper_roles(self, contribution):
        for role in contribution.legacy_paper_reviewing_roles:
            if role.role == LegacyPaperReviewingRoleType.referee:
                contribution.paper_judges.add(role.user)
            elif role.role == LegacyPaperReviewingRoleType.reviewer:
                contribution.paper_content_reviewers.add(role.user)
            elif role.role == LegacyPaperReviewingRoleType.editor:
                contribution.paper_layout_reviewers.add(role.user)

    def _migrate_review(self, contribution, old_judgment, review_type):
        # Consider legacy custom states the same as "to be corrected"
        proposed_action = JUDGMENT_STATE_PAPER_ACTION_MAP.get(int(old_judgment._judgement._id),
                                                              PaperAction.to_be_corrected)
        review = PaperReview(user=old_judgment._author.user, comment=convert_to_unicode(old_judgment._comments),
                             type=review_type, proposed_action=proposed_action,
                             created_dt=_to_utc(old_judgment._submissionDate))
        for old_answer in old_judgment._answers:
            old_question = old_answer._question
            try:
                question = self.legacy_question_map[old_question]
            except KeyError:
                self.importer.print_warning(cformat('%{yellow!}Answer to deleted question {} has been ignored [{}, {}]')
                                            .format(old_question._id, contribution, review_type),
                                            event_id=self.event.id)
                continue

            assert old_answer._rbValue >= 0 and old_answer._rbValue <= 6
            rating = PaperReviewRating(question=question, value=(old_answer._rbValue - 3))
            review.ratings.append(rating)
        return review

    def _migrate_revisions(self, contribution, rm):
        self.importer.print_info(cformat('%{white!}{}%{reset}').format(contribution.title))

        self.file_checksums = defaultdict()

        # Here we iterate over what the legacy PR mode calls "Reviews" (our `PaperRevisions`)
        for n, old_revision in enumerate(rm._versioning, 1):
            old_judgment = old_revision._refereeJudgement
            old_content_reviews = old_revision._reviewerJudgements.values()
            old_layout_review = old_revision._editorJudgement

            # keep track of the last legacy revision, so that we can come back to it
            # during paper file migration
            self.legacy_contrib_last_revision_map[contribution.id] = old_revision

            # skip revisions that haven't been submitted by the author
            if not old_revision._isAuthorSubmitted:
                # ... except if said revision has been judged before being marked as submitted (!)
                if old_judgment._submitted:
                    self.importer.print_warning(cformat('%{yellow!}Revision judged without being submitted! [{}: {}]')
                                                .format(contribution, old_revision._version), event_id=self.event.id)
                else:
                    continue

            # It seems contradictory, but 'submitted' in legacy means that there is a final decision
            # We'll ignore legacy custom states and use TBC
            state = (JUDGMENT_STATE_REVISION_MAP.get(int(old_judgment._judgement._id),
                                                     PaperRevisionState.to_be_corrected)
                     if old_judgment._submitted
                     else PaperRevisionState.submitted)
            judge = old_judgment._author.user if old_judgment._submitted else None
            judgment_dt = _to_utc(old_judgment._submissionDate) if old_judgment._submitted else None
            last_file = (LegacyPaperFile.query.with_parent(contribution)
                         .filter(LegacyPaperFile.revision_id == old_revision._version)
                         .order_by(LegacyPaperFile.created_dt.desc())
                         .limit(1)
                         .first())
            # Legacy didn't keep track of the submission date (nor submitter for that matter)
            # we're taking the most recent uploaded file and using that one
            # if there are no files, the event's end date will be used
            submitted_dt = _to_utc(last_file.created_dt) if last_file else self.event.end_dt
            revision = PaperRevision(state=state, submitter=self.janitor_user, judge=judge,
                                     judgment_dt=judgment_dt, submitted_dt=submitted_dt,
                                     judgment_comment=convert_to_unicode(old_judgment._comments))
            self.legacy_contrib_revision_map[(contribution.id, old_revision._version)] = revision

            # Then we'll add the layout and content reviews
            review_colors = ''

            for old_content_review in old_content_reviews:
                if old_content_review._submitted:
                    review = self._migrate_review(contribution, old_content_review, PaperReviewType.content)
                    revision.reviews.append(review)
                    review_colors += _review_color(review, 'C')
            if old_layout_review._submitted:
                review = self._migrate_review(contribution, old_layout_review, PaperReviewType.layout)
                revision.reviews.append(review)
                review_colors += _review_color(review, 'L')
            contribution._paper_revisions.append(revision)

            self.importer.print_info(cformat('\tRevision %{{blue!}}{}%{{reset}} %{{white,{}}}  %{{reset}} {}'.format(
                n, STATE_COLOR_MAP[state], review_colors)))

    def _migrate_papers(self):
        contributions = {c.id: c for c in (Contribution.find(event_new=self.event)
                                           .options(joinedload('legacy_paper_reviewing_roles')))}
        if not hasattr(self.pr, '_contribution_index'):
            self.importer.print_warning(cformat('%{yellow!}Event has no contribution index!'), event_id=self.event.id)
            return
        for contrib_id, rm in self.pr._contribution_index.iteritems():
            if contrib_id not in contributions:
                self.importer.print_warning(cformat('%{yellow!}Contribution {} not found in event').format(contrib_id),
                                            event_id=self.event.id)
                continue
            contribution = contributions[contrib_id]
            self._migrate_paper_roles(contribution)
            self._migrate_revisions(contribution, rm)

    def _migrate_paper_files(self):
        n = 0
        # we look for paper files in increasing order, so that we can detect file reuse
        q = (LegacyPaperFile.query
             .filter(Contribution.event_new == self.event)
             .join(Contribution)
             .order_by(Contribution.id, LegacyPaperFile.revision_id))

        for contribution_id, revision in itertools.groupby(q, attrgetter('contribution_id')):
            for revision_id, files in itertools.groupby(revision, attrgetter('revision_id')):
                ignored_checksums = set()
                checksum_map = {}
                if revision_id is None:
                    # Two types of `LegacyPaperFile`s with `revision=None`:
                    #   - files uploaded whose revision was not yet submitted
                    #   - files within the latest revision
                    last_revision = self.legacy_contrib_last_revision_map[contribution_id]
                    if last_revision._isAuthorSubmitted:
                        revision = self.legacy_contrib_revision_map[(contribution_id, last_revision._version)]
                    else:
                        revision = None
                else:
                    revision = self.legacy_contrib_revision_map[(contribution_id, revision_id)]

                for lpf in files:
                    # check whether the same file has been uploaded to a subsequent revision
                    try:
                        with lpf.open() as f:
                            checksum = crc32(f.read())
                        checksum_map[checksum] = lpf
                        collision = self.file_checksums.get(checksum)
                        if collision:
                            ignored_checksums.add(checksum)
                            self.importer.print_warning(
                                cformat('%{yellow!}File {} (rev. {}) already in revision {}').format(
                                    lpf.filename, revision.id if revision else None, collision.id),
                                event_id=self.event.id)
                            continue
                        else:
                            self.file_checksums[checksum] = revision
                    except (RuntimeError, StorageError):
                        self.importer.print_error(cformat("%{red!}File not accessible; can't CRC it [{}]")
                                                  .format(lpf.filename), event_id=self.event.id)

                    if revision:
                        revision.files.append(_paper_file_from_legacy(lpf))
                    n += 1

                # if a revision has no files (because they've all been ignored), then keep around a copy of each
                if revision and not revision.files and ignored_checksums:
                    for checksum in ignored_checksums:
                        lpf = checksum_map[checksum]
                        revision.files.append(_paper_file_from_legacy(lpf))
                        self.importer.print_warning(
                            cformat('%{yellow!}File {} (rev. {}) reinstated').format(lpf.filename, revision.id),
                            event_id=self.event.id)
                        n += 1

        self.importer.print_info('{} paper files migrated'.format(n))


class EventPapersImporter(LocalFileImporterMixin, Importer):
    def __init__(self, **kwargs):
        kwargs = self._set_config_options(**kwargs)
        self.janitor_user_id = kwargs.pop('janitor_user_id')
        self.janitor_user = None
        super(EventPapersImporter, self).__init__(**kwargs)

    @staticmethod
    def decorate_command(command):
        command = click.option('--janitor-user-id', type=int, required=True, help="The ID of the Janitor user")(command)
        return super(EventPapersImporter, EventPapersImporter).decorate_command(command)

    def has_data(self):
        return (PaperFile.query.has_rows() or PaperReview.query.has_rows() or PaperRevision.query.has_rows() or
                PaperTemplate.query.has_rows() or PaperCompetence.query.has_rows())

    def migrate(self):
        self.janitor_user = User.get_one(self.janitor_user_id)
        self.migrate_event_pr()

    def migrate_event_pr(self):
        self.print_step("Migrating paper reviewing data")
        for conf, event in committing_iterator(self._iter_events()):
            pr = getattr(conf, '_confPaperReview', None)
            if not pr:
                self.print_warning(cformat('%{yellow!}Event {} has no PR settings').format(event), event_id=event.id)
                continue

            mig = PaperMigration(self, conf, event, self.janitor_user)
            with db.session.begin_nested():
                with db.session.no_autoflush:
                    mig.run()
                    db.session.flush()

    def _iter_events(self):
        query = (Event.query
                 .filter(~Event.is_deleted)
                 .filter(db.or_(Event.contributions.any(Contribution.legacy_paper_files.any() |
                                                        Contribution.legacy_paper_reviewing_roles.any()),
                                (Event.type_ == EventType.conference))))
        it = iter(query)
        if self.quiet:
            it = verbose_iterator(query, query.count(), attrgetter('id'), lambda x: '')
        confs = self.zodb_root['conferences']
        for event in it:
            yield confs[str(event.id)], event
