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

from collections import OrderedDict
from operator import itemgetter

from sqlalchemy.orm import contains_eager, joinedload, load_only, undefer

from indico.core import signals
from indico.core.auth import multipass
from indico.core.db import db
from indico.core.db.sqlalchemy.custom.unaccent import unaccent_match
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.categories import Category
from indico.modules.categories.models.principals import CategoryPrincipal
from indico.modules.events import Event
from indico.modules.users import User, logger
from indico.modules.users.models.affiliations import UserAffiliation
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.models.suggestions import SuggestedCategory
from indico.util.event import truncate_path
from indico.util.string import crc32


# colors for user-specific avatar bubbles
user_colors = ['#e06055', '#ff8a65', '#e91e63', '#f06292', '#673ab7', '#ba68c8', '#7986cb', '#3f51b5', '#5e97f6',
               '#00a4e4', '#4dd0e1', '#0097a7', '#d4e157', '#aed581', '#57bb8a', '#4db6ac', '#607d8b', '#795548',
               '#a1887f', '#fdd835', '#a3a3a3']


def get_admin_emails():
    """Get the email addresses of all Indico admins"""
    return {u.email for u in User.find(is_admin=True, is_deleted=False)}


def get_related_categories(user, detailed=True):
    """Gets the related categories of a user for the dashboard"""
    favorites = set()
    if user.favorite_categories:
        favorites = set(Category.query
                        .filter(Category.id.in_(c.id for c in user.favorite_categories))
                        .options(undefer('chain_titles'))
                        .all())
    managed = set(Category.query
                  .filter(Category.acl_entries.any(db.and_(CategoryPrincipal.type == PrincipalType.user,
                                                           CategoryPrincipal.user == user,
                                                           CategoryPrincipal.has_management_permission())),
                          ~Category.is_deleted)
                  .options(undefer('chain_titles')))
    if not detailed:
        return favorites | managed
    res = {}
    for categ in favorites | managed:
        res[(categ.title, categ.id)] = {
            'categ': categ,
            'favorite': categ in favorites,
            'managed': categ in managed,
            'path': truncate_path(categ.chain_titles[:-1], chars=50)
        }
    return OrderedDict(sorted(res.items(), key=itemgetter(0)))


def get_suggested_categories(user):
    """Gets the suggested categories of a user for the dashboard"""
    related = set(get_related_categories(user, detailed=False))
    res = []
    category_strategy = contains_eager('category')
    category_strategy.subqueryload('acl_entries')
    category_strategy.undefer('chain_titles')
    query = (user.suggested_categories
             .filter_by(is_ignored=False)
             .join(SuggestedCategory.category)
             .options(category_strategy))
    for suggestion in query:
        category = suggestion.category
        if (category.is_deleted or category in related or category.suggestions_disabled or
                any(p.suggestions_disabled for p in category.parent_chain_query)):
            user.suggested_categories.remove(suggestion)
            continue
        if not category.can_access(user):
            continue
        res.append({
            'score': suggestion.score,
            'categ': category,
            'path': truncate_path(category.chain_titles[:-1], chars=50)
        })
    return res


def get_linked_events(user, dt, limit=None):
    """Get the linked events and the user's roles in them

    :param user: A `User`
    :param dt: Only include events taking place on/after that date
    :param limit: Max number of events
    """
    from indico.modules.events.abstracts.util import (get_events_with_abstract_reviewer_convener,
                                                      get_events_with_abstract_persons)
    from indico.modules.events.contributions.util import get_events_with_linked_contributions
    from indico.modules.events.papers.util import get_events_with_paper_roles
    from indico.modules.events.registration.util import get_events_registered
    from indico.modules.events.sessions.util import get_events_with_linked_sessions
    from indico.modules.events.surveys.util import get_events_with_submitted_surveys
    from indico.modules.events.util import (get_events_managed_by, get_events_created_by,
                                            get_events_with_linked_event_persons)

    links = OrderedDict()
    for event_id in get_events_registered(user, dt):
        links.setdefault(event_id, set()).add('registration_registrant')
    for event_id in get_events_with_submitted_surveys(user, dt):
        links.setdefault(event_id, set()).add('survey_submitter')
    for event_id in get_events_managed_by(user, dt):
        links.setdefault(event_id, set()).add('conference_manager')
    for event_id in get_events_created_by(user, dt):
        links.setdefault(event_id, set()).add('conference_creator')
    for event_id, principal_roles in get_events_with_linked_sessions(user, dt).iteritems():
        links.setdefault(event_id, set()).update(principal_roles)
    for event_id, principal_roles in get_events_with_linked_contributions(user, dt).iteritems():
        links.setdefault(event_id, set()).update(principal_roles)
    for event_id, role in get_events_with_linked_event_persons(user, dt).iteritems():
        links.setdefault(event_id, set()).add(role)
    for event_id, roles in get_events_with_abstract_reviewer_convener(user, dt).iteritems():
        links.setdefault(event_id, set()).update(roles)
    for event_id, roles in get_events_with_abstract_persons(user, dt).iteritems():
        links.setdefault(event_id, set()).update(roles)
    for event_id, roles in get_events_with_paper_roles(user, dt).iteritems():
        links.setdefault(event_id, set()).update(roles)

    if not links:
        return OrderedDict()

    query = (Event.query
             .filter(~Event.is_deleted,
                     Event.id.in_(links))
             .options(joinedload('series'),
                      load_only('id', 'category_id', 'title', 'start_dt', 'end_dt',
                                'series_id', 'series_pos', 'series_count'))
             .order_by(Event.start_dt, Event.id))
    if limit is not None:
        query = query.limit(limit)
    return OrderedDict((event, links[event.id]) for event in query)


def serialize_user(user):
    """Serialize user to JSON-like object"""
    return {
        'id': user.id,
        'title': user.title,
        'identifier': 'User:{}'.format(user.id),
        'name': user.display_full_name,
        'familyName': user.last_name,
        'firstName': user.first_name,
        'affiliation': user.affiliation,
        'phone': user.phone,
        'email': user.email,
        '_type': 'Avatar'
    }


def search_users(exact=False, include_deleted=False, include_pending=False, external=False, allow_system_user=False,
                 **criteria):
    """Searches for users.

    :param exact: Indicates if only exact matches should be returned.
                  This is MUCH faster than a non-exact saerch,
                  especially when searching external users.
    :param include_deleted: Indicates if also users marked as deleted
                            should be returned.
    :param include_pending: Indicates if also users who are still
                            pending should be returned.
    :param external: Indicates if identity providers should be searched
                     for matching users.
    :param allow_system_user: Whether the system user may be returned
                              in the search results.
    :param criteria: A dict containing any of the following keys:
                     first_name, last_name, email, affiliation, phone,
                     address
    :return: A set of matching users. If `external` was set, it may
             contain both :class:`~flask_multipass.IdentityInfo` objects
             for external users not yet in Indico and :class:`.User`
             objects for existing users.
    """
    unspecified = object()
    query = User.query.options(db.joinedload(User.identities),
                               db.joinedload(User._all_emails),
                               db.joinedload(User.merged_into_user))
    criteria = {key: value.strip() for key, value in criteria.iteritems() if value.strip()}
    original_criteria = dict(criteria)

    if not criteria:
        return set()

    if not include_pending:
        query = query.filter(~User.is_pending)
    if not include_deleted:
        query = query.filter(~User.is_deleted)

    affiliation = criteria.pop('affiliation', unspecified)
    if affiliation is not unspecified:
        query = query.join(UserAffiliation).filter(unaccent_match(UserAffiliation.name, affiliation, exact))

    email = criteria.pop('email', unspecified)
    if email is not unspecified:
        query = query.join(UserEmail).filter(unaccent_match(UserEmail.email, email, exact))

    for k, v in criteria.iteritems():
        query = query.filter(unaccent_match(getattr(User, k), v, exact))

    found_emails = {}
    found_identities = {}
    system_user = set()
    for user in query:
        for identity in user.identities:
            found_identities[(identity.provider, identity.identifier)] = user
        for email in user.all_emails:
            found_emails[email] = user
        if user.is_system and not user.all_emails and allow_system_user:
            system_user = {user}

    # external user providers
    if external:
        identities = multipass.search_identities(exact=exact, **original_criteria)

        for ident in identities:
            if not ident.data.get('email'):
                # Skip users with no email
                continue
            if ((ident.provider.name, ident.identifier) not in found_identities and
                    ident.data['email'].lower() not in found_emails):
                found_emails[ident.data['email'].lower()] = ident
                found_identities[(ident.provider, ident.identifier)] = ident

    return set(found_emails.viewvalues()) | system_user


def get_user_by_email(email, create_pending=False):
    """finds a user based on his email address.

    :param email: The email address of the user.
    :param create_pending: If True, this function searches for external
                           users and creates a new pending User in case
                           no existing user was found.
    :return: A :class:`.User` instance or ``None`` if not exactly one
             user was found.
    """
    email = email.lower().strip()
    if not email:
        return None
    if not create_pending:
        res = User.find_all(~User.is_deleted, User.all_emails.contains(email))
    else:
        res = search_users(exact=True, include_pending=True, external=True, email=email)
    if len(res) != 1:
        return None
    user_or_identity = next(iter(res))
    if isinstance(user_or_identity, User):
        return user_or_identity
    elif not create_pending:
        return None
    # Create a new pending user
    data = user_or_identity.data
    user = User(first_name=data.get('first_name') or '', last_name=data.get('last_name') or '', email=data['email'],
                address=data.get('address', ''), phone=data.get('phone', ''),
                affiliation=data.get('affiliation', ''), is_pending=True)
    db.session.add(user)
    db.session.flush()
    return user


def merge_users(source, target, force=False):
    """Merge two users together, unifying all related data

    :param source: source user (will be set as deleted)
    :param target: target user (final)
    """

    if source.is_deleted and not force:
        raise ValueError('Source user {} has been deleted. Merge aborted.'.format(source))

    if target.is_deleted:
        raise ValueError('Target user {} has been deleted. Merge aborted.'.format(target))

    # Move emails to the target user
    primary_source_email = source.email
    logger.info("Target %s initial emails: %s", target, ', '.join(target.all_emails))
    logger.info("Source %s emails to be linked to target %s: %s", source, target, ', '.join(source.all_emails))
    UserEmail.find(user_id=source.id).update({
        UserEmail.user_id: target.id,
        UserEmail.is_primary: False
    })

    # Make sure we don't have stale data after the bulk update we just performed
    db.session.expire_all()

    # Update favorites
    target.favorite_users |= source.favorite_users
    target.favorite_of |= source.favorite_of
    target.favorite_categories |= source.favorite_categories

    # Update category suggestions
    SuggestedCategory.merge_users(target, source)

    # Merge identities
    for identity in set(source.identities):
        identity.user = target

    # Notify signal listeners about the merge
    signals.users.merged.send(target, source=source)
    db.session.flush()

    # Mark source as merged
    source.merged_into_user = target
    source.is_deleted = True
    db.session.flush()

    # Restore the source user's primary email
    source.email = primary_source_email
    db.session.flush()

    logger.info("Successfully merged %s into %s", source, target)


def get_color_for_username(username):
    return user_colors[crc32(username) % len(user_colors)]
