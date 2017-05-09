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

from __future__ import unicode_literals

from flask import session

from indico.core.notifications import make_email, send_email
from indico.modules.events.papers.settings import paper_reviewing_settings, PaperReviewingRole
from indico.web.flask.templating import get_template_module


def notify_paper_revision_submission(revision):
    event = revision.paper.event_new
    roles_to_notify = paper_reviewing_settings.get(event, 'notify_on_paper_submission')
    if PaperReviewingRole.judge in roles_to_notify:
        for judge in revision.paper.contribution.paper_judges:
            template = get_template_module('events/papers/emails/revision_submission_to_judge.html', event=event,
                                           revision=revision, receiver=judge)
            email = make_email(to_list=judge.email, template=template, html=True)
            send_email(email, event=event, module='Papers', user=session.user)
    reviewers = set()
    if PaperReviewingRole.layout_reviewer in roles_to_notify:
        reviewers |= revision.paper.contribution.paper_layout_reviewers
    if PaperReviewingRole.content_reviewer in roles_to_notify:
        reviewers |= revision.paper.contribution.paper_content_reviewers
    for reviewer in reviewers:
        template = get_template_module('events/papers/emails/revision_submission_to_reviewer.html', event=event,
                                       revision=revision, receiver=reviewer)
        email = make_email(to_list=reviewer.email, template=template, html=True)
        send_email(email, event=event, module='Papers', user=session.user)


def notify_paper_review_submission(review):
    event = review.revision.paper.event_new
    if not paper_reviewing_settings.get(event, 'notify_judge_on_review'):
        return
    for judge in review.revision.paper.contribution.paper_judges:
        template = get_template_module('events/papers/emails/review_submission_to_judge.html', event=event,
                                       review=review, contribution=review.revision.paper.contribution, receiver=judge)
        email = make_email(to_list=judge.email, template=template, html=True)
        send_email(email, event=event, module='Papers', user=session.user)


def notify_paper_judgment(paper, reset=False):
    event = paper.event_new
    authors = [x for x in paper.contribution.person_links if x.is_author]
    recipients = ([x for x in authors if x.email] if paper.last_revision.submitter.is_system
                  else [paper.last_revision.submitter])
    template_file = None
    if reset:
        template_file = 'events/papers/emails/judgment_reset_to_author.html'
    elif paper_reviewing_settings.get(event, 'notify_author_on_judgment'):
        template_file = 'events/papers/emails/judgment_to_author.html'

    if not template_file:
        return
    for receiver in recipients:
        template = get_template_module(template_file, event=event, paper=paper, contribution=paper.contribution,
                                       receiver=receiver)
        email = make_email(to_list=receiver.email, template=template, html=True)
        send_email(email, event=event, module='Papers', user=session.user)


def _notify_changes_in_reviewing_team(user, template, event, role):
    template = get_template_module(template, event=event, receiver=user, role=role)
    email = make_email(to_list=user.email, template=template, html=True)
    send_email(email, event=event, module='Papers', user=session.user)


def notify_added_to_reviewing_team(user, role, event):
    template = 'events/papers/emails/added_to_reviewing_team.html'
    _notify_changes_in_reviewing_team(user, template, event, role)


def notify_removed_from_reviewing_team(user, role, event):
    template = 'events/papers/emails/removed_from_reviewing_team.html'
    _notify_changes_in_reviewing_team(user, template, event, role)


def notify_paper_assignment(user, role, contributions, event, assign):
    template = get_template_module('events/papers/emails/paper_assignment.html', event=event, contribs=contributions,
                                   receiver=user, assign=assign, role=role)
    email = make_email(to_list=user.email, template=template, html=True)
    send_email(email, event=event, module='Papers', user=session.user)


def notify_comment(person, paper, comment, submitter):
    event = paper.event_new
    receiver_name = person.first_name or 'user'
    template = get_template_module('events/papers/emails/comment.html', event=event, receiver=receiver_name,
                                   contribution=paper.contribution, comment=comment, submitter=submitter)
    email = make_email(to_list=person.email, template=template, html=True)
    send_email(email, event=event, module='Papers', user=session.user)
