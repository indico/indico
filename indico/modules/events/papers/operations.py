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

import mimetypes
from operator import attrgetter

from flask import session

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.contributions import Contribution
from indico.modules.events.logs.models.entries import EventLogKind, EventLogRealm
from indico.modules.events.logs.util import make_diff_log
from indico.modules.events.papers import logger
from indico.modules.events.papers.models.comments import PaperReviewComment
from indico.modules.events.papers.models.competences import PaperCompetence
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.review_ratings import PaperReviewRating
from indico.modules.events.papers.models.reviews import (PaperAction, PaperCommentVisibility, PaperReview,
                                                         PaperReviewType)
from indico.modules.events.papers.models.revisions import PaperRevision, PaperRevisionState
from indico.modules.events.papers.models.templates import PaperTemplate
from indico.modules.events.papers.notifications import (notify_added_to_reviewing_team, notify_comment,
                                                        notify_paper_assignment, notify_paper_judgment,
                                                        notify_paper_review_submission,
                                                        notify_paper_revision_submission,
                                                        notify_removed_from_reviewing_team)
from indico.modules.events.papers.settings import PaperReviewingRole, paper_reviewing_settings
from indico.modules.events.util import update_object_principals
from indico.modules.users import User
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.util.i18n import orig_string


def set_reviewing_state(event, reviewing_type, enable):
    event.cfp.set_reviewing_state(reviewing_type, enable)
    action = 'enabled' if enable else 'disabled'
    logger.info("Reviewing type '%s' for event %r %s by %r", reviewing_type.name, event, action, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive if enable else EventLogKind.negative, 'Papers',
              "{} {} reviewing".format("Enabled" if enable else "Disabled", orig_string(reviewing_type.title.lower())),
              session.user)


def _unassign_removed(event, changes):
    role_map = {
        PaperReviewingRole.judge: Contribution.paper_judges,
        PaperReviewingRole.content_reviewer: Contribution.paper_content_reviewers,
        PaperReviewingRole.layout_reviewer: Contribution.paper_layout_reviewers,
    }
    changed_contribs = set()
    for role, role_changes in changes.iteritems():
        removed = role_changes['removed']
        if not removed:
            continue
        attr = role_map[role]
        contribs = (Contribution.query.with_parent(event)
                    .filter(attr.any(User.id.in_(x.id for x in removed)))
                    .all())
        changed_contribs.update(contribs)
        for contrib in contribs:
            getattr(contrib, attr.key).difference_update(removed)
    return changed_contribs


def update_team_members(event, managers, judges, content_reviewers=None, layout_reviewers=None):
    updated = {}
    update_object_principals(event, managers, role='paper_manager')
    updated[PaperReviewingRole.judge] = update_object_principals(event, judges, role='paper_judge')
    if content_reviewers is not None:
        updated[PaperReviewingRole.content_reviewer] = update_object_principals(event, content_reviewers,
                                                                                role='paper_content_reviewer')
    if layout_reviewers is not None:
        updated[PaperReviewingRole.layout_reviewer] = update_object_principals(event, layout_reviewers,
                                                                               role='paper_layout_reviewer')
    unassigned_contribs = _unassign_removed(event, updated)
    roles_to_notify = paper_reviewing_settings.get(event, 'notify_on_added_to_event')
    if PaperReviewingRole.judge in roles_to_notify:
        for judge in updated[PaperReviewingRole.judge]['added']:
            notify_added_to_reviewing_team(judge, PaperReviewingRole.judge, event)
        for judge in updated[PaperReviewingRole.judge]['removed']:
            notify_removed_from_reviewing_team(judge, PaperReviewingRole.judge, event)
    if PaperReviewingRole.content_reviewer in roles_to_notify:
        for reviewer in updated[PaperReviewingRole.content_reviewer]['added']:
            notify_added_to_reviewing_team(reviewer, PaperReviewingRole.content_reviewer, event)
        for reviewer in updated[PaperReviewingRole.content_reviewer]['removed']:
            notify_removed_from_reviewing_team(reviewer, PaperReviewingRole.content_reviewer, event)
    if PaperReviewingRole.layout_reviewer in roles_to_notify:
        for reviewer in updated[PaperReviewingRole.layout_reviewer]['added']:
            notify_added_to_reviewing_team(reviewer, PaperReviewingRole.layout_reviewer, event)
        for reviewer in updated[PaperReviewingRole.layout_reviewer]['removed']:
            notify_removed_from_reviewing_team(reviewer, PaperReviewingRole.layout_reviewer, event)
    logger.info("Paper teams of %r updated by %r", event, session.user)
    return unassigned_contribs


def create_competences(event, user, competences):
    PaperCompetence(event=event, user=user, competences=competences)
    logger.info("Competences for user %r for event %r created by %r", user, event, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
              "Added competences of {}".format(user.full_name), session.user,
              data={'Competences': ', '.join(competences)})


def update_competences(user_competences, competences):
    event = user_competences.event
    user_competences.competences = competences
    logger.info("Competences for user %r in event %r updated by %r", user_competences.user, event, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
              "Updated competences for user {}".format(user_competences.user.full_name), session.user,
              data={'Competences': ', '.join(competences)})


def schedule_cfp(event, start_dt, end_dt):
    event.cfp.schedule(start_dt, end_dt)
    log_data = {}
    if start_dt:
        log_data['Start'] = start_dt.isoformat()
    if end_dt:
        log_data['End'] = end_dt.isoformat()
    logger.info("Call for papers for %r scheduled by %r", event, session.user)
    event.log(EventLogRealm.management, EventLogKind.change, 'Papers', 'Call for papers scheduled', session.user,
              data=log_data)


def open_cfp(event):
    event.cfp.open()
    logger.info("Call for papers for %r opened by %r", event, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Papers', 'Call for papers opened', session.user)


def close_cfp(event):
    event.cfp.close()
    logger.info("Call for papers for %r closed by %r", event, session.user)
    event.log(EventLogRealm.management, EventLogKind.negative, 'Papers', 'Call for papers closed', session.user)


def create_paper_revision(paper, submitter, files):
    revision = PaperRevision(paper=paper, submitter=submitter)
    for f in files:
        filename = secure_filename(f.filename, 'paper')
        content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
        pf = PaperFile(filename=filename, content_type=content_type, paper_revision=revision,
                       _contribution=paper.contribution)
        pf.save(f.stream)
    db.session.flush()
    db.session.expire(revision._contribution, ['_paper_last_revision'])
    notify_paper_revision_submission(revision)
    logger.info('Paper revision %r submitted by %r', revision, session.user)
    paper.event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
                    "Paper revision {} submitted for contribution {} ({})"
                    .format(revision.id, paper.contribution.title, paper.contribution.friendly_id), session.user)
    return revision


@no_autoflush
def judge_paper(paper, judgment, comment, judge):
    if judgment == PaperAction.accept:
        paper.state = PaperRevisionState.accepted
    elif judgment == PaperAction.reject:
        paper.state = PaperRevisionState.rejected
    elif judgment == PaperAction.to_be_corrected:
        paper.state = PaperRevisionState.to_be_corrected
    paper.last_revision.judgment_comment = comment
    paper.last_revision.judge = judge
    paper.last_revision.judgment_dt = now_utc()
    db.session.flush()
    log_data = {'New state': orig_string(judgment.title)}
    notify_paper_judgment(paper)
    logger.info('Paper %r was judged by %r to %s', paper, judge, orig_string(judgment.title))
    paper.event.log(EventLogRealm.management, EventLogKind.change, 'Papers',
                    'Paper "{}" was judged'.format(orig_string(paper.verbose_title)), judge,
                    data=log_data)


def reset_paper_state(paper):
    paper.reset_state()
    db.session.flush()
    notify_paper_judgment(paper, reset=True)
    logger.info('Paper %r state reset by %r', paper, session.user)
    paper.event.log(EventLogRealm.management, EventLogKind.change, 'Papers',
                    'Judgment {} reset'.format(paper.verbose_title), session.user)


def _store_paper_template_file(template, file):
    content_type = mimetypes.guess_type(file.filename)[0] or file.mimetype or 'application/octet-stream'
    filename = secure_filename(file.filename, 'template')
    # reset fields in case an existing file is replaced so we can save() again
    template.storage_backend = None
    template.storage_file_id = None
    template.size = None
    template.content_type = content_type
    template.filename = filename
    template.save(file.stream)


def create_paper_template(event, data):
    file = data.pop('template')
    template = PaperTemplate(event=event)
    template.populate_from_dict(data)
    _store_paper_template_file(template, file)
    db.session.flush()
    logger.info('Paper template %r uploaded by %r', template, session.user)
    return template


def update_paper_template(template, data):
    file = data.pop('template', None)
    template.populate_from_dict(data)
    if file is not None:
        _store_paper_template_file(template, file)
    logger.info('Paper template %r updated by %r', template, session.user)


def delete_paper_template(template):
    db.session.delete(template)
    db.session.flush()
    logger.info('Paper template %r deleted by %r', template, session.user)


def update_reviewing_roles(event, users, contributions, role, assign):
    role_map = {
        PaperReviewingRole.judge: attrgetter('paper_judges'),
        PaperReviewingRole.content_reviewer: attrgetter('paper_content_reviewers'),
        PaperReviewingRole.layout_reviewer: attrgetter('paper_layout_reviewers'),
    }

    for contrib in contributions:
        role_group = role_map[role](contrib)
        for user in users:
            if assign:
                role_group.add(user)
            else:
                role_group.discard(user)

    contrib_ids = ['#{}'.format(c.friendly_id) for c in sorted(contributions, key=attrgetter('friendly_id'))]
    log_data = {'Users': ', '.join(sorted(person.full_name for person in users)),
                'Contributions': ', '.join(contrib_ids)}
    roles_to_notify = paper_reviewing_settings.get(event, 'notify_on_assigned_contrib')
    if role in roles_to_notify:
        for user in users:
            notify_paper_assignment(user, role, contributions, event, assign)
    if assign:
        event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
                  'Papers assigned ({})'.format(orig_string(role.title)), session.user, data=log_data)
    else:
        event.log(EventLogRealm.management, EventLogKind.negative, 'Papers',
                  'Papers unassigned ({})'.format(orig_string(role.title)), session.user, data=log_data)
    db.session.flush()
    logger.info('Paper reviewing roles in event %r updated by %r', event, session.user)


def create_review(paper, review_type, user, review_data, questions_data):
    review = PaperReview(revision=paper.last_revision, type=review_type.instance, user=user)
    review.populate_from_dict(review_data)
    log_data = {}
    for question in paper.event.cfp.get_questions_for_review_type(review_type.instance):
        value = int(questions_data['question_{}'.format(question.id)])
        review.ratings.append(PaperReviewRating(question=question, value=value))
        log_data[question.text] = value
    db.session.flush()
    notify_paper_review_submission(review)
    logger.info("Paper %r received a review of type %s by %r", paper, review_type.instance.name, user)
    log_data.update({
        'Type': orig_string(review_type.title),
        'Action': orig_string(review.proposed_action.title),
        'Comment': review.comment
    })
    paper.event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
                    'Paper for contribution {} reviewed'.format(paper.contribution.verbose_title),
                    user, data=log_data)
    return review


def update_review(review, review_data, questions_data):
    paper = review.revision.paper
    event = paper.event
    changes = review.populate_from_dict(review_data)
    review.modified_dt = now_utc()
    log_fields = {}
    for question in event.cfp.get_questions_for_review_type(review.type):
        field_name = 'question_{}'.format(question.id)
        rating = question.get_review_rating(review, allow_create=True)
        old_value = rating.value
        rating.value = int(questions_data[field_name])
        if old_value != rating.value:
            changes[field_name] = (old_value, rating.value)
            log_fields[field_name] = {
                'title': question.text,
                'type': 'number'
            }
    db.session.flush()
    notify_paper_review_submission(review)
    logger.info("Paper review %r modified", review)
    log_fields.update({
        'proposed_action': 'Action',
        'comment': 'Comment'
    })
    event.log(EventLogRealm.management, EventLogKind.change, 'Papers',
              'Review for paper {} modified'.format(paper.verbose_title),
              session.user, data={'Changes': make_diff_log(changes, log_fields)})


@no_autoflush
def create_comment(paper, text, visibility, user):
    comment = PaperReviewComment(user=user, text=text, visibility=visibility)
    paper.last_revision.comments.append(comment)
    db.session.flush()
    recipients = {x for x in paper.contribution.paper_judges}
    if visibility == PaperCommentVisibility.contributors or visibility == PaperCommentVisibility.reviewers:
        recipients |= paper.contribution.paper_layout_reviewers if paper.cfp.layout_reviewing_enabled else set()
        recipients |= paper.contribution.paper_content_reviewers if paper.cfp.content_reviewing_enabled else set()
    if visibility == PaperCommentVisibility.contributors:
        recipients |= {x.person for x in paper.contribution.person_links
                       if x.person.email and x.person.email != user.email}
    recipients.discard(user)
    for receiver in recipients:
        notify_comment(receiver, paper, text, user)
    logger.info("Paper %r received a comment from %r", paper, session.user)
    paper.event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
                    'Paper {} received a comment'.format(paper.verbose_title),
                    session.user)


def update_comment(comment, text, visibility):
    changes = comment.populate_from_dict({'text': text, 'visibility': visibility})
    comment.modified_by = session.user
    comment.modified_dt = now_utc()
    db.session.flush()
    logger.info("Paper comment %r modified by %r", comment, session.user)
    paper = comment.paper_revision.paper
    paper.event.log(EventLogRealm.management, EventLogKind.change, 'Papers',
                    'Comment on paper {} modified'.format(paper.verbose_title), session.user,
                    data={'Changes': make_diff_log(changes, {'text': 'Text', 'visibility': 'Visibility'})})


def delete_comment(comment):
    comment.is_deleted = True
    db.session.flush()
    logger.info("Paper comment %r deleted by %r", comment, session.user)
    paper = comment.paper_revision.paper
    paper.event.log(EventLogRealm.management, EventLogKind.negative, 'Papers',
                    'Comment on paper {} removed'.format(paper.verbose_title), session.user)


def set_deadline(event, role, deadline, enforce=True):
    paper_reviewing_settings.set_multi(event, {
        '{}_deadline'.format(role.name): deadline,
        'enforce_{}_deadline'.format(role.name): enforce
    })
    log_data = {'Enforced': enforce, 'Deadline': deadline.isoformat() if deadline else 'None'}
    logger.info('Paper reviewing deadline (%s) set in %r by %r', role.name, event, session.user)
    event.log(EventLogRealm.management, EventLogKind.change, 'Papers',
              "Paper reviewing deadline ({}) set".format(role.title), session.user, data=log_data)
