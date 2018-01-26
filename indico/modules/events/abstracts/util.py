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

import errno
import os
import shutil
from collections import OrderedDict, defaultdict, namedtuple

from sqlalchemy.orm import joinedload, load_only

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.legacy.pdfinterface.conference import AbstractBook
from indico.modules.events import Event
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.email_templates import AbstractEmailTemplate
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.models.reviews import AbstractReview
from indico.modules.events.abstracts.settings import abstracts_settings, boa_settings
from indico.modules.events.contributions.models.fields import ContributionFieldVisibility
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.users import User
from indico.util.i18n import _
from indico.util.spreadsheets import unique_col
from indico.web.flask.templating import get_template_module


def build_default_email_template(event, tpl_type):
    """Build a default e-mail template based on a notification type provided by the user."""
    email = get_template_module('events/abstracts/emails/default_{}_notification.txt'.format(tpl_type))
    tpl = AbstractEmailTemplate(body=email.get_body(),
                                extra_cc_emails=[],
                                reply_to_address=event.contact_emails[0] if event.contact_emails else '',
                                subject=email.get_subject(),
                                include_authors=True,
                                include_submitter=True,
                                include_coauthors=True)
    return tpl


def generate_spreadsheet_from_abstracts(abstracts, static_item_ids, dynamic_items):
    """Generates a spreadsheet data from a given abstract list.

    :param abstracts: The list of abstracts to include in the file
    :param static_item_ids: The abstract properties to be used as columns
    :param dynamic_items: Contribution fields as extra columns
    """
    field_names = ['Id', 'Title']
    static_item_mapping = OrderedDict([
        ('state', ('State', lambda x: x.state.title)),
        ('submitter', ('Submitter', lambda x: x.submitter.full_name)),
        ('authors', ('Primary authors', lambda x: [a.full_name for a in x.primary_authors])),
        ('accepted_track', ('Accepted track', lambda x: x.accepted_track.short_title if x.accepted_track else None)),
        ('submitted_for_tracks', ('Submitted for tracks',
                                  lambda x: [t.short_title for t in x.submitted_for_tracks])),
        ('reviewed_for_tracks', ('Reviewed for tracks', lambda x: [t.short_title for t in x.reviewed_for_tracks])),
        ('accepted_contrib_type', ('Accepted type',
                                   lambda x: x.accepted_contrib_type.name if x.accepted_contrib_type else None)),
        ('submitted_contrib_type', ('Submitted type',
                                    lambda x: x.submitted_contrib_type.name if x.submitted_contrib_type else None)),
        ('score', ('Score', lambda x: round(x.score, 1) if x.score is not None else None)),
        ('submitted_dt', ('Submission date', lambda x: x.submitted_dt)),
        ('modified_dt', ('Modification date', lambda x: x.modified_dt if x.modified_dt else ''))
    ])
    field_names.extend(unique_col(item.title, item.id) for item in dynamic_items)
    field_names.extend(title for name, (title, fn) in static_item_mapping.iteritems() if name in static_item_ids)
    rows = []
    for abstract in abstracts:
        data = abstract.data_by_field
        abstract_dict = {
            'Id': abstract.friendly_id,
            'Title': abstract.title
        }
        for item in dynamic_items:
            key = unique_col(item.title, item.id)
            abstract_dict[key] = data[item.id].friendly_data if item.id in data else ''
        for name, (title, fn) in static_item_mapping.iteritems():
            if name not in static_item_ids:
                continue
            value = fn(abstract)
            abstract_dict[title] = value
        rows.append(abstract_dict)
    return field_names, rows


@no_autoflush
def create_mock_abstract(event):
    """Create a mock abstract that can be used in previews.

    Brace for geek references.
    """
    User = namedtuple('Author', ['first_name', 'last_name', 'title', 'full_name'])
    Track = namedtuple('Track', ['title'])
    Session = namedtuple('Session', ['title'])
    ContributionType = namedtuple('ContributionType', ['name'])
    Contribution = namedtuple('Contribution', ['title', 'track', 'session', 'type', 'locator'])
    Abstract = namedtuple('Abstract', ['friendly_id', 'title', 'event', 'submitter', 'contribution',
                                       'primary_authors', 'secondary_authors', 'locator', 'judgment_comment',
                                       'accepted_track', 'accepted_contrib_type', 'state', 'merged_into'])

    englert = User(full_name="Fran\xe7ois Englert", first_name="Fran\xe7ois", last_name="Englert", title="Prof.")
    brout = User(full_name="Robert Brout", first_name="Robert", last_name="Brout", title="Prof.")
    guralnik = User(full_name="Gerald Guralnik", first_name="Gerald", last_name="Guralnik", title="Prof.")
    hagen = User(full_name="Carl Hagen", first_name="Carl", last_name="Hagen", title="Prof.")
    kibble = User(full_name="Tom Kibble", first_name="Tom", last_name="Kibble", title="Prof.")
    higgs = User(full_name="Peter Higgs", first_name="Peter", last_name="Higgs", title="Prof.")

    track = Track(title=_("Higgs Fields"))
    session = Session(title=_("Higgs Fields Posters"))
    contribution_type = ContributionType(name=_("Poster"))
    contribution = Contribution(title="Broken Symmetry and the Mass of Gauge Vector Mesons",
                                track=track,
                                session=session,
                                type=contribution_type,
                                locator={'confId': -314, 'contrib_id': 1234})

    target_abstract = Abstract(friendly_id=315,
                               title="Broken Symmetry",
                               accepted_track=track,
                               accepted_contrib_type=contribution_type,
                               event=event,
                               submitter=brout,
                               state=AbstractState.accepted,
                               contribution=contribution,
                               primary_authors=[englert, brout],
                               secondary_authors=[guralnik, hagen, kibble, higgs],
                               locator={'confId': -314, 'abstract_id': 1235},
                               judgment_comment='Vague but interesting!',
                               merged_into=None)

    abstract = Abstract(friendly_id=314,
                        title="Broken Symmetry and the Mass of Gauge Vector Mesons",
                        accepted_track=track,
                        accepted_contrib_type=contribution_type,
                        event=event,
                        submitter=brout,
                        state=AbstractState.accepted,
                        contribution=contribution,
                        primary_authors=[englert, brout],
                        secondary_authors=[guralnik, hagen, kibble, higgs],
                        locator={'confId': -314, 'abstract_id': 1234},
                        judgment_comment='Vague but interesting!',
                        merged_into=target_abstract)

    return abstract


def make_abstract_form(event, user, notification_option=False, management=False):
    """Extends the abstract WTForm to add the extra fields.

    Each extra field will use a field named ``custom_ID``.

    :param event: The `Event` for which to create the abstract form.
    :param user: The user who is going to use the form.
    :param notification_option: Whether to add a field to the form to
                                disable triggering notifications for
                                the abstract submission.
    :param management: Whether the form is used in the management area
    :return: An `AbstractForm` subclass.
    """
    from indico.modules.events.abstracts.forms import (AbstractForm, MultiTrackMixin, SingleTrackMixin, NoTrackMixin,
                                                       SendNotificationsMixin)

    mixins = []
    if not event.tracks:
        mixins.append(NoTrackMixin)
    elif abstracts_settings.get(event, 'allow_multiple_tracks'):
        mixins.append(MultiTrackMixin)
    else:
        mixins.append(SingleTrackMixin)
    if notification_option:
        mixins.append(SendNotificationsMixin)
    form_class = type(b'_AbstractForm', tuple(mixins) + (AbstractForm,), {})
    for custom_field in event.contribution_fields:
        field_impl = custom_field.mgmt_field if management else custom_field.field
        if field_impl is None:
            # field definition is not available anymore
            continue
        if custom_field.is_user_editable or event.can_manage(user):
            name = 'custom_{}'.format(custom_field.id)
            setattr(form_class, name, field_impl.create_wtf_field())
    return form_class


def get_roles_for_event(event):
    """Return a dictionary of all abstract reviewing roles for this event.

    :param event: the actual event object.
    :return: A dictionary in the form ``{track: {role: [users]}}``
    """
    roles = defaultdict(dict)
    for track in Track.query.with_parent(event).options(joinedload('conveners'), joinedload('abstract_reviewers')):
        roles[str(track.id)].setdefault('reviewer', [])
        roles[str(track.id)].setdefault('convener', [])
        for reviewer in track.abstract_reviewers:
            roles[str(track.id)]['reviewer'].append(reviewer.id)
        for convener in track.conveners:
            roles[str(track.id)]['convener'].append(convener.id)
    roles['*']['reviewer'] = [reviewer.id for reviewer in event.global_abstract_reviewers]
    roles['*']['convener'] = [reviewer.id for reviewer in event.global_conveners]
    return roles


def get_user_abstracts(event, user):
    """Get the list of abstracts where the user is a reviewer/convener"""
    return (Abstract.query.with_parent(event)
            .options(joinedload('reviews'),
                     joinedload('person_links'))
            .filter(db.or_(Abstract.submitter == user,
                           Abstract.person_links.any(AbstractPersonLink.person.has(user=user))))
            .order_by(Abstract.friendly_id)
            .all())


def get_visible_reviewed_for_tracks(abstract, user):
    event = abstract.event
    if abstract.can_judge(user, check_state=True) or user in event.global_conveners:
        return abstract.reviewed_for_tracks
    convener_tracks = {track for track in event.tracks if track.can_convene(user)}
    return abstract.reviewed_for_tracks & convener_tracks


def _query_user_tracks(event, user):
    query = Track.query.with_parent(event)
    if user not in event.global_abstract_reviewers and user not in event.global_conveners:
        query = query.filter(db.or_(Track.conveners.any(User.id == user.id),
                                    Track.abstract_reviewers.any(User.id == user.id)))
    return query


def get_user_tracks(event, user):
    """Get the list of tracks where the user is a reviewer/convener"""
    return _query_user_tracks(event, user).order_by(Track.title).all()


def has_user_tracks(event, user):
    return _query_user_tracks(event, user).has_rows()


def get_track_reviewer_abstract_counts(event, user):
    """Get the numbers of abstracts per track for a specific user.

    Note that this does not take into account if the user is a
    reviewer for a track; it just checks whether the user has
    reviewed an abstract in a track or not.

    :return: A dict mapping tracks to dicts containing the counts.
    """
    # COUNT() does not count NULL values so we pass NULL in case an
    # abstract is not in the submitted state. That way we still get
    # the track - filtering using WHERE would only include tracks
    # that have some abstract in the submitted state.
    count_total = db.func.count(Abstract.id)
    count_reviewable = db.func.count(db.case({AbstractState.submitted.value: Abstract.id}, value=Abstract.state))
    count_reviewable_reviewed = db.func.count(db.case({AbstractState.submitted.value: AbstractReview.id},
                                                      value=Abstract.state))
    count_total_reviewed = db.func.count(AbstractReview.id)
    query = (Track.query.with_parent(event)
             .with_entities(Track,
                            count_total,
                            count_total_reviewed,
                            count_reviewable - count_reviewable_reviewed)
             .outerjoin(Track.abstracts_reviewed)
             .outerjoin(AbstractReview, db.and_(AbstractReview.abstract_id == Abstract.id,
                                                AbstractReview.user_id == user.id,
                                                AbstractReview.track_id == Track.id))
             .group_by(Track.id))
    return {track: {'total': total, 'reviewed': reviewed, 'unreviewed': unreviewed}
            for track, total, reviewed, unreviewed in query}


def create_boa(event):
    """Create the book of abstracts if necessary

    :return: The path to the PDF file
    """
    path = boa_settings.get(event, 'cache_path')
    if path:
        path = os.path.join(config.CACHE_DIR, path)
        if os.path.exists(path):
            # update file mtime so it's not deleted during cache cleanup
            os.utime(path, None)
            return path
    pdf = AbstractBook(event)
    tmp_path = pdf.generate()
    filename = 'boa-{}.pdf'.format(event.id)
    full_path = os.path.join(config.CACHE_DIR, filename)
    shutil.move(tmp_path, full_path)
    boa_settings.set(event, 'cache_path', filename)
    return full_path


def clear_boa_cache(event):
    """Delete the cached book of abstract"""
    path = boa_settings.get(event, 'cache_path')
    if path:
        try:
            os.remove(os.path.join(config.CACHE_DIR, path))
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
        boa_settings.delete(event, 'cache_path')


def get_events_with_abstract_reviewer_convener(user, dt=None):
    """
    Return a dict of event ids and the abstract reviewing related
    roles the user has in that event.

    :param user: A `User`
    :param dt: Only include events taking place on/after that date
    """
    data = defaultdict(set)
    # global reviewer/convener
    mapping = {'global_abstract_reviewer_for_events': 'abstract_reviewer',
               'global_convener_for_events': 'track_convener'}
    for rel, role in mapping.iteritems():
        query = (Event.query.with_parent(user, rel)
                 .filter(Event.ends_after(dt), ~Event.is_deleted)
                 .options(load_only('id')))
        for event in query:
            data[event.id].add(role)
    # track reviewer/convener
    mapping = {'abstract_reviewer_for_tracks': 'abstract_reviewer',
               'convener_for_tracks': 'track_convener'}
    for rel, role in mapping.iteritems():
        query = (Track.query.with_parent(user, rel)
                 .join(Track.event)
                 .filter(Event.ends_after(dt), ~Event.is_deleted)
                 .options(load_only('event_id')))
        for track in query:
            data[track.event_id].add(role)
    return data


def get_events_with_abstract_persons(user, dt=None):
    """
    Return a dict of event ids and the abstract submission related
    roles the user has in that event.

    :param user: A `User`
    :param dt: Only include events taking place on/after that date
    """
    data = defaultdict(set)
    bad_states = {AbstractState.withdrawn, AbstractState.rejected}
    # submitter
    query = (Abstract.query
             .filter(~Event.is_deleted,
                     ~Abstract.is_deleted,
                     ~Abstract.state.in_(bad_states),
                     Event.ends_after(dt),
                     Abstract.submitter == user)
             .join(Abstract.event)
             .options(load_only('event_id')))
    for abstract in query:
        data[abstract.event_id].add('abstract_submitter')
    # person
    abstract_criterion = db.and_(~Abstract.state.in_(bad_states), ~Abstract.is_deleted)
    query = (user.event_persons
             .filter(~Event.is_deleted,
                     Event.ends_after(dt),
                     EventPerson.abstract_links.any(AbstractPersonLink.abstract.has(abstract_criterion)))
             .join(EventPerson.event)
             .options(load_only('event_id')))
    for person in query:
        data[person.event_id].add('abstract_person')
    return data


def filter_field_values(fields, can_manage, owns_abstract):
    active_fields = {field for field in fields if field.contribution_field.is_active}
    if can_manage:
        return active_fields
    if owns_abstract:
        return {field for field in active_fields
                if field.contribution_field.visibility != ContributionFieldVisibility.managers_only}
    return {field for field in active_fields
            if field.contribution_field.visibility == ContributionFieldVisibility.public}
