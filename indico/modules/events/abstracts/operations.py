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
from collections import defaultdict
from operator import attrgetter

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.events.abstracts import logger
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState, EditTrackMode
from indico.modules.events.abstracts.models.comments import AbstractComment
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.models.reviews import AbstractAction, AbstractReview
from indico.modules.events.abstracts.models.review_ratings import AbstractReviewRating
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.notifications import send_abstract_notifications
from indico.modules.events.contributions.operations import delete_contribution, create_contribution_from_abstract
from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind
from indico.modules.events.util import set_custom_fields
from indico.util.date_time import now_utc
from indico.util.i18n import orig_string
from indico.util.fs import secure_filename


def _update_tracks(abstract, tracks, only_reviewed_for=False):
    edit_track_mode = abstract.edit_track_mode
    if edit_track_mode == EditTrackMode.none:
        return

    if edit_track_mode == EditTrackMode.both:
        if not only_reviewed_for:
            abstract.submitted_for_tracks = tracks
        abstract.reviewed_for_tracks = tracks
    elif edit_track_mode == EditTrackMode.reviewed_for:
        abstract.reviewed_for_tracks = tracks


def add_abstract_files(abstract, files, log_action=True):
    for f in files:
        filename = secure_filename(f.filename, 'attachment')
        content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
        abstract_file = AbstractFile(filename=filename, content_type=content_type, abstract=abstract)
        abstract_file.save(f.file)
        db.session.flush()
    if log_action and files:
        logger.info('%d abstract file(s) added to %s by %s', len(files), abstract, session.user)
        num = len(files)
        if num == 1:
            msg = 'Added file to abstract #{} ({})'.format(abstract.friendly_id, abstract.title)
        else:
            msg = 'Added {} files to abstract #{} ({})'.format(num, abstract.friendly_id, abstract.title)
        abstract.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Abstracts', msg, session.user,
                               data={'Files': ', '.join(f.filename for f in files)})


def delete_abstract_files(abstract, files):
    num = len(files)
    for file_ in files:
        db.session.delete(file_)
    logger.info('%d abstract files deleted from %s by %s', num, abstract, session.user)
    if num == 1:
        msg = 'Deleted file from abstract #{} ({})'.format(abstract.friendly_id, abstract.title)
    else:
        msg = 'Deleted {} files from abstract #{} ({})'.format(num, abstract.friendly_id, abstract.title)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Abstracts', msg, session.user,
                           data={'Files': ', '.join(f.filename for f in files)})


def create_abstract(event, abstract_data, custom_fields_data=None, send_notifications=False):
    abstract = Abstract(event_new=event, submitter=session.user)
    tracks = abstract_data.pop('submitted_for_tracks', None)
    attachments = abstract_data.pop('attachments', None)
    abstract.populate_from_dict(abstract_data)
    if tracks is not None:
        _update_tracks(abstract, tracks)
    if custom_fields_data:
        set_custom_fields(abstract, custom_fields_data)
    db.session.flush()

    if attachments:
        add_abstract_files(abstract, attachments['added'], log_action=False)
    signals.event.abstract_created.send(abstract)

    if send_notifications:
        send_abstract_notifications(abstract)
    logger.info('Abstract %s created by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Abstracts',
                           'Abstract #{} ({}) created'.format(abstract.friendly_id, abstract.title), session.user)
    return abstract


def update_abstract(abstract, abstract_data, custom_fields_data=None):
    tracks = abstract_data.pop('submitted_for_tracks', None)
    attachments = abstract_data.pop('attachments', None)

    if tracks is not None and abstract.edit_track_mode == EditTrackMode.both:
        _update_tracks(abstract, tracks)

    if attachments:
        deleted_files = {f for f in abstract.files if f.id in attachments['deleted']}
        abstract.files = list(set(abstract.files) - deleted_files)
        delete_abstract_files(abstract, deleted_files)
        add_abstract_files(abstract, attachments['added'])

    abstract.populate_from_dict(abstract_data)
    if custom_fields_data:
        set_custom_fields(abstract, custom_fields_data)
    db.session.flush()
    logger.info('Abstract %s modified by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.change, 'Abstracts',
                           'Abstract #{} ({}) modified'.format(abstract.friendly_id, abstract.title), session.user)


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
                           'Abstract #{} ({}) withdrawn'.format(abstract.friendly_id, abstract.title), session.user)


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
                           'Abstract #{} ({}) deleted'.format(abstract.friendly_id, abstract.title), session.user)


def judge_abstract(abstract, abstract_data, judgment, judge, contrib_session=None, merge_persons=False,
                   send_notifications=False):
    abstract.judge = judge
    abstract.judgment_dt = now_utc()
    abstract.judgment_comment = abstract_data['judgment_comment']
    log_data = {'Judgment': orig_string(judgment.title)}
    if judgment == AbstractAction.accept:
        abstract.state = AbstractState.accepted
        abstract.accepted_track = abstract_data.get('accepted_track')
        abstract.accepted_contrib_type = abstract_data.get('accepted_contrib_type')
        if not abstract.contribution:
            abstract.contribution = create_contribution_from_abstract(abstract, contrib_session)
        if abstract.accepted_track:
            log_data['Track'] = abstract.accepted_track.title
        if abstract.accepted_contrib_type:
            log_data['Type'] = abstract.accepted_contrib_type.name
    elif judgment == AbstractAction.reject:
        abstract.state = AbstractState.rejected
    elif judgment == AbstractAction.mark_as_duplicate:
        abstract.state = AbstractState.duplicate
        abstract.duplicate_of = abstract_data['duplicate_of']
        log_data['Duplicate of'] = '#{}: {}'.format(abstract.duplicate_of.friendly_id, abstract.duplicate_of.title)
    elif judgment == AbstractAction.merge:
        abstract.state = AbstractState.merged
        abstract.merged_into = abstract_data['merged_into']
        log_data['Merged into'] = '#{}: {}'.format(abstract.merged_into.friendly_id, abstract.merged_into.title)
        log_data['Merge authors'] = merge_persons
        if merge_persons:
            _merge_person_links(abstract.merged_into, abstract)
    db.session.flush()
    log_data['Sent notifications'] = send_notifications
    if send_notifications:
        send_abstract_notifications(abstract)
    logger.info('Abstract %s judged by %s', abstract, judge)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.change, 'Abstracts',
                           'Abstract #{} ({}) judged'.format(abstract.friendly_id, abstract.title), judge,
                           data=log_data)


def _merge_person_links(target_abstract, source_abstract):
    """
    Merge `person_links` of different abstracts.

    Add to `target_abstract` new `AbstractPersonLink`s whose `EventPerson`
    exists in the `source_abstract` but is not yet in the `target_abstract`.

    :param target_abstract: The target abstract (to which the links should then be added)
    :param source_abstract: The source abstract
    """
    new_links = set()
    source_links = source_abstract.person_links
    source_link_map = defaultdict(set)
    for link in source_links:
        source_link_map[link.person.id].add(link)
    unique_persons = {link.person for link in source_links} - {link.person for link in target_abstract.person_links}
    sort_position = max(link.display_order for link in target_abstract.person_links) + 1
    persons_sorted = sort_position > 1

    for person in unique_persons:
        for source_link in source_link_map[person.id]:
            link = AbstractPersonLink(person=person, author_type=source_link.author_type,
                                      is_speaker=source_link.is_speaker)
            # if the persons in the abstract are sorted, add at the end
            # otherwise, keep alphabetical order
            if persons_sorted:
                link.display_order = sort_position
                sort_position += 1
            else:
                link.display_order = 0
            new_links.add(link)
            for column_name in {'_title', '_affiliation', '_address', '_phone', '_first_name', '_last_name'}:
                setattr(link, column_name, getattr(source_link, column_name))

    # Add new links in order
    for link in sorted(new_links, key=attrgetter('display_order_key')):
        target_abstract.person_links.append(link)


def update_reviewed_for_tracks(abstract, tracks):
    _update_tracks(abstract, tracks, only_reviewed_for=True)
    db.session.flush()
    logger.info('Reviewed tracks of abstract %s updated by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.change, 'Abstracts',
                           'Reviewed tracks of abstract #{} ({}) updated'.format(abstract.friendly_id, abstract.title),
                           session.user)


def reset_abstract_state(abstract):
    abstract.reset_state()
    db.session.flush()
    logger.info('Abstract %s state reset by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.change, 'Abstracts',
                           'State of abstract #{} ({}) reset'.format(abstract.friendly_id, abstract.title),
                           session.user)


def create_abstract_comment(abstract, comment_data):
    comment = AbstractComment(user=session.user)
    comment.populate_from_dict(comment_data)
    comment.abstract = abstract
    db.session.flush()
    logger.info("Abstract %s received a comment from %s", abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Abstracts',
                           'Abstract #{} ({}) received a comment'.format(abstract.friendly_id, abstract.title),
                           session.user)


def update_abstract_comment(comment, comment_data):
    comment.populate_from_dict(comment_data)
    comment.modified_by = session.user
    comment.modified_dt = now_utc()
    db.session.flush()
    logger.info("Abstract comment %s modified by %s", comment, session.user)
    comment.abstract.event_new.log(EventLogRealm.management, EventLogKind.change, 'Abstracts',
                                   'Comment on abstract #{} ({}) modified'.format(comment.abstract.friendly_id,
                                                                                  comment.abstract.title),
                                   session.user)


def delete_abstract_comment(comment):
    db.session.delete(comment)
    db.session.flush()
    logger.info("Abstract comment %s deleted by %s", comment, session.user)
    comment.abstract.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Abstracts',
                                   'Comment on abstract #{} ({}) removed'.format(comment.abstract.friendly_id,
                                                                                 comment.abstract.title),
                                   session.user)


def create_abstract_review(abstract, track, user, review_data, questions_data):
    review = AbstractReview(abstract=abstract, track=track, user=user)
    review.populate_from_dict(review_data)
    for question in abstract.event_new.abstract_review_questions:
        value = int(questions_data['question_{}'.format(question.id)])
        review.ratings.append(AbstractReviewRating(question=question, value=value))
    db.session.flush()
    logger.info("Abstract %s received a review by %s for track %s", abstract, user, track)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Abstracts',
                           'Abstract #{} ({}) reviewed'.format(abstract.friendly_id, abstract.title), user)
    return review


def update_abstract_review(review, review_data, questions_data):
    event = review.abstract.event_new
    review.populate_from_dict(review_data)
    review.modified_dt = now_utc()
    for question in event.abstract_review_questions:
        rating = question.get_review_rating(review, allow_create=True)
        rating.value = int(questions_data['question_{}'.format(question.id)])
    db.session.flush()
    logger.info("Abstract review %s modified", review)
    event.log(EventLogRealm.management, EventLogKind.change, 'Abstracts',
              'Review "{}" for abstract #{} ({}) modified'.format(review.id, review.abstract.friendly_id,
                                                                  review.abstract.title),
              session.user)


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
