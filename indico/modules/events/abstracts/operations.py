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

import mimetypes

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.events.abstracts import logger
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.reviews import AbstractAction
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.notifications import send_abstract_notifications
from indico.modules.events.contributions.operations import delete_contribution
from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind
from indico.modules.events.util import set_custom_fields
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename


def create_abstract(event, abstract_data, custom_fields_data=None):
    abstract = Abstract(event_new=event, submitter=session.user)
    files = abstract_data.pop('attachments', [])
    abstract.populate_from_dict(abstract_data)
    abstract.reviewed_for_tracks = abstract.submitted_for_tracks
    if custom_fields_data:
        set_custom_fields(abstract, custom_fields_data)
    db.session.flush()
    for f in files:
        filename = secure_filename(f.filename, 'attachment')
        content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
        abstract_file = AbstractFile(filename=filename, content_type=content_type, abstract=abstract)
        abstract_file.save(f.file)
        db.session.flush()
    signals.event.abstract_created.send(abstract)
    logger.info('Abstract %s created by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Abstracts',
                           'Abstract "{}" has been created'.format(abstract.title), session.user)
    return abstract


def withdraw_abstract(abstract, delete_contrib=False):
    abstract.state = AbstractState.withdrawn
    contrib = abstract.contribution
    abstract.contribution = None
    if delete_contrib and contrib:
        delete_contribution(contrib)
    db.session.flush()
    signals.event.abstract_state_changed.send(abstract)
    logger.info('Abstract %s withdrawn by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Abstracts',
                           'Abstract "{}" has been withdrawn'.format(abstract.title), session.user)


def delete_abstract(abstract, delete_contrib=False):
    abstract.is_deleted = True
    contrib = abstract.contribution
    abstract.contribution = None
    if delete_contrib and contrib:
        delete_contribution(contrib)
    db.session.flush()
    signals.event.abstract_deleted.send(abstract)
    logger.info('Abstract %s deleted by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Abstracts',
                           'Abstract "{}" has been deleted'.format(abstract.title), session.user)


def judge_abstract(abstract, abstract_data, judgment, judge, contrib_session=None, merge_persons=False,
                   send_notification=False):
    abstract.judge = judge
    abstract.judgment_dt = now_utc()
    abstract.judgment_comment = abstract_data['judgment_comment']
    if judgment == AbstractAction.accept:
        abstract.state = AbstractState.accepted
        abstract.accepted_track = abstract_data['accepted_track']
        abstract.accepted_contrib_type = abstract_data['accepted_contrib_type']
        if not abstract.contribution:
            # TODO: generate contribution
            pass
    elif judgment == AbstractAction.reject:
        abstract.state = AbstractState.rejected
    elif judgment == AbstractAction.mark_as_duplicate:
        abstract.state = AbstractState.duplicate
        abstract.duplicate_of = abstract_data['duplicate_of']
    elif judgment == AbstractAction.merge:
        abstract.state = AbstractState.merged
        abstract.merged_into = abstract_data['merged_into']
        if merge_persons:
            abstract.merged_into.person_links |= abstract.person_links
    db.session.flush()
    if send_notification:
        send_abstract_notifications(abstract)
    logger.info('Abstract %s judged by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.change, 'Abstracts',
                           'Abstract "{}" has been judged'.format(abstract.title), session.user)


def reset_abstract_state(abstract):
    abstract.reset_state()
    db.session.flush()
    logger.info('Abstract %s state reset by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.change, 'Abstracts',
                           'State of abstract "{}" has been reset'.format(abstract.title), session.user)


def schedule_cfa(event, start_dt, end_dt, modification_end_dt):
    event.cfa.schedule(start_dt, end_dt, modification_end_dt)
    logger.info("Call for abstracts for %s scheduled by %s", event, session.user)
    log_data = {}
    if start_dt:
        log_data['Start'] = start_dt.isoformat()
    if end_dt:
        log_data['End'] = end_dt.isoformat()
    if modification_end_dt:
        log_data['Modification deadline'] = modification_end_dt.isoformat()
    event.log(EventLogRealm.management, EventLogKind.change, 'Abstracts', 'Call for abstracts scheduled', session.user,
              data=log_data)


def open_cfa(event):
    event.cfa.open()
    logger.info("Call for abstracts for %s opened by %s", event, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Abstracts', 'Call for abstracts opened', session.user)


def close_cfa(event):
    event.cfa.close()
    logger.info("Call for abstracts for %s closed by %s", event, session.user)
    event.log(EventLogRealm.management, EventLogKind.negative, 'Abstracts', 'Call for abstracts closed', session.user)
