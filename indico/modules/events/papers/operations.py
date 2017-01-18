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

import mimetypes

from flask import session

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.notifications import make_email, send_email
from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.reviews import PaperAction
from indico.modules.events.papers.models.revisions import PaperRevision, PaperRevisionState
from indico.modules.events.papers import logger
from indico.modules.events.papers.models.competences import PaperCompetence
from indico.modules.events.papers.models.papers import Paper
from indico.modules.events.papers.models.templates import PaperTemplate
from indico.modules.events.util import update_object_principals
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.util.i18n import orig_string
from indico.web.flask.templating import get_template_module


def set_reviewing_state(event, reviewing_type, enable):
    event.cfp.set_reviewing_state(reviewing_type, enable)
    action = 'enabled' if enable else 'disabled'
    logger.info("Reviewing type '%s' for event %r %s by %r", reviewing_type, event, action, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
              "{} reviewing type '{}'".format("Enabled" if enable else "Disabled", reviewing_type), session.user)


def update_team_members(event, managers, judges, content_reviewers=None, layout_reviewers=None):
    update_object_principals(event, managers, role='paper_manager')
    update_object_principals(event, judges, role='paper_judge')
    if content_reviewers is not None:
        update_object_principals(event, content_reviewers, role='paper_content_reviewer')
    if layout_reviewers is not None:
        update_object_principals(event, layout_reviewers, role='paper_layout_reviewer')
    logger.info("Paper teams of %r updated by %r", event, session.user)


def create_competences(event, user, competences):
    PaperCompetence(event_new=event, user=user, competences=competences)
    logger.info("Competences for user %r for event %r created by %r", user, event, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
              "Added competences of {}".format(user.full_name), session.user,
              data={'Competences': ', '.join(competences)})


def update_competences(user_competences, competences):
    event = user_competences.event_new
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


@no_autoflush
def create_paper_revision(contribution, submitter, files):
    paper = Paper(contribution=contribution)
    revision = PaperRevision(paper=paper, submitter=submitter)
    for f in files:
        filename = secure_filename(f.filename, 'paper')
        content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
        pf = PaperFile(filename=filename, content_type=content_type, paper_revision=revision, contribution=contribution)
        pf.save(f.file)
    db.session.flush()
    logger.info('Paper revision %r submitted by %r', revision, session.user)
    contribution.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
                               "Paper revision {} submitted for contribution {} ({})"
                               .format(revision.id, contribution.title, contribution.friendly_id), session.user)
    return revision


@no_autoflush
def judge_paper(paper, contrib_data, judgment, judge, send_notifications=False):
    if judgment == PaperAction.accept:
        paper.state = PaperRevisionState.accepted
    elif judgment == PaperAction.reject:
        paper.state = PaperRevisionState.rejected
    elif judgment == PaperAction.to_be_corrected:
        paper.state = PaperRevisionState.to_be_corrected
    paper.last_revision.judgment_comment = contrib_data['judgment_comment']
    paper.last_revision.judge = judge
    paper.last_revision.judgment_dt = now_utc()
    db.session.flush()
    log_data = {'New state': orig_string(judgment.title), 'Sent notifications': send_notifications}
    if send_notifications:
        send_paper_notifications(paper.contribution)
    logger.info('Paper %r was judged by %r to %s', paper, judge, orig_string(judgment.title))
    paper.event_new.log(EventLogRealm.management, EventLogKind.change, 'Papers',
                        'Paper "{}" was judged'.format(orig_string(paper.verbose_title)), judge,
                        data=log_data)


def send_paper_notifications(contribution):
    """Send paper notification e-mails.

    :param contribution: the contribution whose last paper revision was judged
    """
    template = get_template_module('events/static/emails/paper_judgment_notification_email.txt',
                                   contribution=contribution, paper=contribution.paper_last_revision)
    email = make_email(to_list=[contribution.paper_last_revision.submitter.email], template=template)
    send_email(email, contribution.event_new, 'Papers', session.user)


def _store_paper_template_file(template, file):
    content_type = mimetypes.guess_type(file.filename)[0] or file.mimetype or 'application/octet-stream'
    filename = secure_filename(file.filename, 'template')
    # reset fields in case an existing file is replaced so we can save() again
    template.storage_backend = None
    template.storage_file_id = None
    template.size = None
    template.content_type = content_type
    template.filename = filename
    template.save(file.file)


def create_paper_template(event, data):
    file = data.pop('template')
    template = PaperTemplate(event_new=event)
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
