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

from __future__ import unicode_literals, division

import mimetypes
from operator import attrgetter

from pytz import utc
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.models.events import EventType
from indico.modules.events.papers.models.competences import PaperCompetence
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.review_questions import PaperReviewQuestion
from indico.modules.events.papers.models.reviews import PaperReview, PaperReviewType
from indico.modules.events.papers.models.revisions import PaperRevision
from indico.modules.events.papers.models.templates import PaperTemplate
from indico.modules.events.papers.settings import paper_reviewing_settings, PaperReviewingRole
from indico.modules.events.paper_reviewing.models.roles import PaperReviewingRoleType
from indico.util.console import verbose_iterator, cformat
from indico.util.fs import secure_filename
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer, convert_to_unicode
from indico_zodbimport.util import LocalFileImporterMixin

CPR_NO_REVIEWING = 1
CPR_CONTENT_REVIEWING = 2
CPR_LAYOUT_REVIEWING = 3
CPR_CONTENT_AND_LAYOUT_REVIEWING = 4


def _to_utc(dt):
    return dt.astimezone(utc) if dt else None


def _translate_notif_options(pr, options):
    return {PaperReviewingRole[role] for role, (attr, default) in options.viewitems() if getattr(pr, attr, default)}


class PaperMigration(object):
    def __init__(self, importer, conf, event):
        self.importer = importer
        self.conf = conf
        self.event = event
        self.pr = conf._confPaperReview

    def run(self):
        self.importer.print_success(cformat('%{blue!}{}').format(self.event), event_id=self.event.id)
        self._migrate_settings()
        self._migrate_event_roles()
        self._migrate_questions()
        self._migrate_templates()
        self._migrate_competences()
        self._migrate_papers()

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
            'content_reviewing_enabled': pr._choice in {CPR_CONTENT_REVIEWING, CPR_CONTENT_AND_LAYOUT_REVIEWING},
            'layout_reviewing_enabled': pr._choice in {CPR_LAYOUT_REVIEWING, CPR_CONTENT_AND_LAYOUT_REVIEWING},

            # notifications
            'notify_on_added_to_event': role_add,
            'notify_on_assigned_contrib': contrib_assignment,
            'notify_on_paper_submission': paper_submission,
            'notify_judge_on_review': (getattr(pr, '_enableEditorSubmittedRefereeEmailNotif', True) or
                                       getattr(pr, '_enableReviewerSubmittedRefereeEmailNotif', True)),
            'notify_author_on_judgment': (pr._enableRefereeJudgementEmailNotif or pr._enableEditorJudgementEmailNotif or
                                          pr._enableReviewerJudgementEmailNotif)
        })

        # TODO: check question range (add setting?)

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

        for n, q in enumerate(self.pr._layoutQuestions, 1):
            question = PaperReviewQuestion(text=q._text, type=PaperReviewType.layout, position=n, event_new=self.event)
            self.event.paper_review_questions.append(question)

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
                                name=old_tpl._Template__name, description=old_tpl._Template__description)
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
            if role.role == PaperReviewingRoleType.referee:
                contribution.paper_judges.add(role.user)
            elif role.role == PaperReviewingRoleType.reviewer:
                contribution.paper_content_reviewers.add(role.user)
            elif role.role == PaperReviewingRoleType.editor:
                contribution.paper_layout_reviewers.add(role.user)

    def _migrate_papers(self):
        contributions = {c.id: c for c in (Contribution.find(event_new=self.event)
                                           .options(joinedload('legacy_paper_reviewing_roles')))}
        for contrib_id, rm in self.pr._contribution_index.iteritems():
            if contrib_id not in contributions:
                self.importer.print_warning(cformat('%{yellow!}Contribution {} not found in event').format(contrib_id),
                                            event_id=self.event.id)
                continue
            contribution = contributions[contrib_id]
            self._migrate_paper_roles(contribution)


class EventPapersImporter(LocalFileImporterMixin, Importer):
    def __init__(self, **kwargs):
        kwargs = self._set_config_options(**kwargs)
        super(EventPapersImporter, self).__init__(**kwargs)

    def has_data(self):
        return PaperFile.query.has_rows() or PaperReview.query.has_rows() or PaperRevision.query.has_rows()

    def migrate(self):
        self.migrate_event_pr()

    def migrate_event_pr(self):
        self.print_step("Migrating paper reviewing data")
        for conf, event in committing_iterator(self._iter_events()):
            pr = getattr(conf, '_confPaperReview', None)
            if not pr:
                self.print_warning(cformat('%{yellow!}Event {} has no PR settings').format(event), event_id=event.id)
                continue

            mig = PaperMigration(self, conf, event)
            with db.session.begin_nested():
                with db.session.no_autoflush:
                    mig.run()
                    db.session.flush()

        # TODO: paper files (from legacy)
        # TODO: revisions
        # TODO: reviews/judgments


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
