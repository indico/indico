# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import mimetypes
from collections import defaultdict
from operator import attrgetter
from uuid import uuid4

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.events.abstracts import logger
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState, EditTrackMode
from indico.modules.events.abstracts.models.comments import AbstractComment
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.models.review_ratings import AbstractReviewRating
from indico.modules.events.abstracts.models.reviews import AbstractAction, AbstractReview
from indico.modules.events.abstracts.notifications import send_abstract_notifications
from indico.modules.events.contributions.operations import create_contribution_from_abstract, delete_contribution
from indico.modules.events.logs.models.entries import EventLogKind, EventLogRealm
from indico.modules.events.logs.util import make_diff_log
from indico.modules.events.util import set_custom_fields
from indico.util.date_time import now_utc
from indico.util.fs import secure_client_filename
from indico.util.i18n import orig_string


def _update_tracks(abstract, tracks, only_reviewed_for=False):
    edit_track_mode = abstract.edit_track_mode
    if edit_track_mode == EditTrackMode.none:
        return {}

    changes = {}
    old_submitted_for_tracks = new_submitted_for_tracks = set(abstract.submitted_for_tracks)
    old_reviewed_for_tracks = new_reviewed_for_tracks = set(abstract.reviewed_for_tracks)
    if edit_track_mode == EditTrackMode.both:
        if not only_reviewed_for:
            abstract.submitted_for_tracks = tracks
            new_submitted_for_tracks = tracks
        abstract.reviewed_for_tracks = tracks
        new_reviewed_for_tracks = tracks
    elif edit_track_mode == EditTrackMode.reviewed_for:
        abstract.reviewed_for_tracks = tracks
        new_reviewed_for_tracks = tracks
    if old_submitted_for_tracks != new_submitted_for_tracks:
        changes['submitted_for_tracks'] = (old_submitted_for_tracks, new_submitted_for_tracks)
    if old_reviewed_for_tracks != new_reviewed_for_tracks:
        changes['reviewed_for_tracks'] = (old_reviewed_for_tracks, new_reviewed_for_tracks)
    return changes


def add_abstract_files(abstract, files, log_action=True):
    if not files:
        return
    for f in files:
        filename = secure_client_filename(f.filename)
        content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
        abstract_file = AbstractFile(filename=filename, content_type=content_type, abstract=abstract)
        abstract_file.save(f.stream)
        db.session.flush()
    if log_action:
        logger.info('%d abstract file(s) added to %s by %s', len(files), abstract, session.user)
        num = len(files)
        if num == 1:
            msg = 'Added file to abstract {}'.format(abstract.verbose_title)
        else:
            msg = 'Added {} files to abstract {}'.format(num, abstract.verbose_title)
        abstract.log(EventLogRealm.reviewing, EventLogKind.positive, 'Abstracts', msg, session.user,
                     data={'Files': ', '.join(f.filename for f in abstract.files)})


def delete_abstract_files(abstract, files):
    if not files:
        return
    num = len(files)
    for file_ in files:
        db.session.delete(file_)
    logger.info('%d abstract files deleted from %s by %s', num, abstract, session.user)
    if num == 1:
        msg = 'Deleted file from abstract {}'.format(abstract.verbose_title)
    else:
        msg = 'Deleted {} files from abstract {}'.format(num, abstract.verbose_title)
    abstract.log(EventLogRealm.reviewing, EventLogKind.negative, 'Abstracts', msg, session.user,
                 data={'Files': ', '.join(f.filename for f in files)})


def create_abstract(event, abstract_data, custom_fields_data=None, send_notifications=False, submitter=None,
                    is_invited=False):
    abstract = Abstract(event=event, submitter=submitter or session.user)
    if is_invited:
        abstract.uuid = unicode(uuid4())
        abstract.state = AbstractState.invited
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
    abstract.log(EventLogRealm.reviewing, EventLogKind.positive, 'Abstracts',
                 'Abstract {} created'.format(abstract.verbose_title), session.user)
    return abstract


def update_abstract(abstract, abstract_data, custom_fields_data=None):
    tracks = abstract_data.pop('submitted_for_tracks', None)
    attachments = abstract_data.pop('attachments', None)
    changes = {}

    if tracks is not None and abstract.edit_track_mode == EditTrackMode.both:
        changes.update(_update_tracks(abstract, tracks))

    if attachments:
        deleted_files = {f for f in abstract.files if f.id in attachments['deleted']}
        abstract.files = list(set(abstract.files) - deleted_files)
        delete_abstract_files(abstract, deleted_files)
        add_abstract_files(abstract, attachments['added'])

    changes.update(abstract.populate_from_dict(abstract_data))
    if custom_fields_data:
        changes.update(set_custom_fields(abstract, custom_fields_data))
    db.session.flush()
    logger.info('Abstract %s modified by %s', abstract, session.user)
    log_fields = {
        'title': 'Title',
        'description': 'Content',
        'submission_comment': 'Comment',
        'submitted_for_tracks': {
            'title': 'Tracks',
            'convert': lambda change: [sorted(t.title for t in x) for x in change]
        },
        'submitted_contrib_type': {
            'title': 'Contribution type',
            'type': 'string',
            'convert': lambda change: [t.name if t else None for t in change]
        }
    }
    for field_name, change in changes.iteritems():
        # we skip skip None -> '' changes (editing an abstract that
        # did not have a value for a new field yet without filling
        # it out)
        if not field_name.startswith('custom_') or not any(changes):
            continue
        field_id = int(field_name[7:])
        field = abstract.event.get_contribution_field(field_id)
        field_impl = field.field
        log_fields[field_name] = {
            'title': field.title,
            'type': field_impl.log_type,
            'convert': lambda change, field_impl=field_impl: map(field_impl.get_friendly_value, change)
        }
    abstract.log(EventLogRealm.reviewing, EventLogKind.change, 'Abstracts',
                 'Abstract {} modified'.format(abstract.verbose_title), session.user,
                 data={'Changes': make_diff_log(changes, log_fields)})


def withdraw_abstract(abstract):
    abstract.reset_state()
    abstract.state = AbstractState.withdrawn
    contrib = abstract.contribution
    abstract.contribution = None
    if contrib:
        delete_contribution(contrib)
    db.session.flush()
    signals.event.abstract_state_changed.send(abstract)
    logger.info('Abstract %s withdrawn by %s', abstract, session.user)
    abstract.log(EventLogRealm.reviewing, EventLogKind.negative, 'Abstracts',
                 'Abstract {} withdrawn'.format(abstract.verbose_title), session.user)


def delete_abstract(abstract, delete_contrib=False):
    abstract.is_deleted = True
    contrib = abstract.contribution
    abstract.contribution = None
    if delete_contrib and contrib:
        delete_contribution(contrib)
    db.session.flush()
    signals.event.abstract_deleted.send(abstract)
    logger.info('Abstract %s deleted by %s', abstract, session.user)
    abstract.log(EventLogRealm.reviewing, EventLogKind.negative, 'Abstracts',
                 'Abstract {} deleted'.format(abstract.verbose_title), session.user)


def judge_abstract(abstract, abstract_data, judgment, judge, contrib_session=None, merge_persons=False,
                   send_notifications=False):
    abstract.judge = judge
    abstract.judgment_dt = now_utc()
    abstract.judgment_comment = abstract_data['judgment_comment']
    log_data = {'Judgment': orig_string(judgment.title)}
    if judgment == AbstractAction.accept:
        abstract.state = AbstractState.accepted
        abstract.accepted_track = abstract_data.get('accepted_track')
        if abstract_data.get('override_contrib_type') or abstract_data.get('accepted_contrib_type'):
            abstract.accepted_contrib_type = abstract_data.get('accepted_contrib_type')
        else:
            abstract.accepted_contrib_type = abstract.submitted_contrib_type
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
        log_data['Duplicate of'] = abstract.duplicate_of.verbose_title
    elif judgment == AbstractAction.merge:
        abstract.state = AbstractState.merged
        abstract.merged_into = abstract_data['merged_into']
        log_data['Merged into'] = abstract.merged_into.verbose_title
        log_data['Merge authors'] = merge_persons
        if merge_persons:
            _merge_person_links(abstract.merged_into, abstract)
    db.session.flush()
    if send_notifications:
        log_data['Notifications sent'] = send_abstract_notifications(abstract)
    logger.info('Abstract %s judged by %s', abstract, judge)
    abstract.log(EventLogRealm.reviewing, EventLogKind.change, 'Abstracts',
                 'Abstract {} judged'.format(abstract.verbose_title), judge, data=log_data)


def _merge_person_links(target_abstract, source_abstract):
    """Merge `person_links` of different abstracts.

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
    abstract.log(EventLogRealm.reviewing, EventLogKind.change, 'Abstracts',
                 'Reviewed tracks of abstract {} updated'.format(abstract.verbose_title), session.user)


def reset_abstract_state(abstract):
    abstract.reset_state()
    db.session.flush()
    logger.info('Abstract %s state reset by %s', abstract, session.user)
    abstract.log(EventLogRealm.reviewing, EventLogKind.change, 'Abstracts',
                 'State of abstract {} reset'.format(abstract.verbose_title), session.user)


def create_abstract_comment(abstract, comment_data):
    comment = AbstractComment(user=session.user)
    comment.populate_from_dict(comment_data)
    comment.abstract = abstract
    db.session.flush()
    logger.info("Abstract %s received a comment from %s", abstract, session.user)
    abstract.log(EventLogRealm.reviewing, EventLogKind.positive, 'Abstracts',
                 'Abstract {} received a comment'.format(abstract.verbose_title), session.user)


def update_abstract_comment(comment, comment_data):
    changes = comment.populate_from_dict(comment_data)
    comment.modified_by = session.user
    comment.modified_dt = now_utc()
    db.session.flush()
    logger.info("Abstract comment %s modified by %s", comment, session.user)
    comment.abstract.log(EventLogRealm.reviewing, EventLogKind.change, 'Abstracts',
                         'Comment on abstract {} modified'.format(comment.abstract.verbose_title),
                         session.user,
                         data={'Changes': make_diff_log(changes, {'text': 'Text', 'visibility': 'Visibility'})})


def delete_abstract_comment(comment):
    comment.is_deleted = True
    db.session.flush()
    logger.info("Abstract comment %s deleted by %s", comment, session.user)
    comment.abstract.log(EventLogRealm.reviewing, EventLogKind.negative, 'Abstracts',
                         'Comment on abstract {} removed'.format(comment.abstract.verbose_title), session.user)


def create_abstract_review(abstract, track, user, review_data, questions_data):
    review = AbstractReview(abstract=abstract, track=track, user=user)
    review.populate_from_dict(review_data)
    log_data = {}
    for question in abstract.event.abstract_review_questions:
        value = questions_data['question_{}'.format(question.id)]
        review.ratings.append(AbstractReviewRating(question=question, value=value))
        log_data[question.title] = question.field.get_friendly_value(value)
    db.session.flush()
    logger.info("Abstract %s received a review by %s for track %s", abstract, user, track)
    log_data.update({
        'Track': track.title,
        'Action': orig_string(review.proposed_action.title),
        'Comment': review.comment
    })
    if review.proposed_action == AbstractAction.accept:
        log_data['Contribution type'] = (review.proposed_contribution_type.name if review.proposed_contribution_type
                                         else None)
    elif review.proposed_action == AbstractAction.change_tracks:
        log_data['Other tracks'] = sorted(t.title for t in review.proposed_tracks)
    elif review.proposed_action in {AbstractAction.mark_as_duplicate, AbstractAction.merge}:
        log_data['Other abstract'] = review.proposed_related_abstract.verbose_title
    abstract.log(EventLogRealm.reviewing, EventLogKind.positive, 'Abstracts',
                 'Abstract {} reviewed'.format(abstract.verbose_title), user, data=log_data)
    return review


def update_abstract_review(review, review_data, questions_data):
    event = review.abstract.event
    changes = review.populate_from_dict(review_data)
    review.modified_dt = now_utc()
    log_fields = {}
    for question in event.abstract_review_questions:
        field_name = 'question_{}'.format(question.id)
        rating = question.get_review_rating(review, allow_create=True)
        old_value = rating.value
        rating.value = questions_data[field_name]
        if old_value != rating.value:
            field_type = question.field_type
            changes[field_name] = (question.field.get_friendly_value(old_value),
                                   question.field.get_friendly_value(rating.value))
            log_fields[field_name] = {
                'title': question.title,
                'type': field_type if field_type != 'rating' else 'number'
            }

    db.session.flush()
    logger.info("Abstract review %s modified", review)
    log_fields.update({
        'proposed_action': 'Action',
        'comment': 'Comment'
    })
    if review.proposed_action in {AbstractAction.mark_as_duplicate, AbstractAction.merge}:
        log_fields['proposed_related_abstract'] = {
            'title': 'Other abstract',
            'type': 'string',
            'convert': lambda change: [x.verbose_title if x else None for x in change]
        }
    elif review.proposed_action == AbstractAction.accept:
        log_fields['proposed_contribution_type'] = {
            'title': 'Contribution type',
            'type': 'string',
            'convert': lambda change: [x.name if x else None for x in change]
        }
    elif review.proposed_action == AbstractAction.change_tracks:
        log_fields['proposed_tracks'] = {
            'title': 'Other tracks',
            'convert': lambda change: [sorted(t.title for t in x) for x in change]
        }
    event.log(EventLogRealm.reviewing, EventLogKind.change, 'Abstracts',
              'Review for abstract {} modified'.format(review.abstract.verbose_title),
              session.user, data={'Track': review.track.title, 'Changes': make_diff_log(changes, log_fields)})


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
    event.log(EventLogRealm.reviewing, EventLogKind.change, 'Abstracts', 'Call for abstracts scheduled', session.user,
              data=log_data)


def open_cfa(event):
    event.cfa.open()
    logger.info("Call for abstracts for %s opened by %s", event, session.user)
    event.log(EventLogRealm.reviewing, EventLogKind.positive, 'Abstracts', 'Call for abstracts opened', session.user)


def close_cfa(event):
    event.cfa.close()
    logger.info("Call for abstracts for %s closed by %s", event, session.user)
    event.log(EventLogRealm.reviewing, EventLogKind.negative, 'Abstracts', 'Call for abstracts closed', session.user)
