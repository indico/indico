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

from collections import OrderedDict
from operator import itemgetter

from indico.core import signals
from indico.core.auth import multipass
from indico.core.db import db
from indico.core.db.sqlalchemy.custom.unaccent import unaccent_match
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.categories import Category
from indico.modules.categories.models.principals import CategoryPrincipal
from indico.modules.users import User, logger
from indico.modules.users.models.affiliations import UserAffiliation
from indico.modules.users.models.emails import UserEmail
from indico.util.event import truncate_path
from indico.util.redis import write_client as redis_write_client
from indico.util.redis import suggestions, avatar_links
from MaKaC.accessControl import AccessWrapper


def get_related_categories(user, detailed=True):
    """Gets the related categories of a user for the dashboard"""
    favorites = user.favorite_categories
    managed = set(Category.query
                  .filter(Category.acl_entries.any(db.and_(CategoryPrincipal.type == PrincipalType.user,
                                                           CategoryPrincipal.user == user))))
    if not detailed:
        return favorites | managed
    res = {}
    for categ in favorites | managed:
        res[(categ.title, categ.id)] = {
            'categ': categ,
            'favorite': categ in favorites,
            'managed': categ in managed,
            'path': truncate_path(categ.get_chain_titles()[:-1], chars=50)
        }
    return OrderedDict(sorted(res.items(), key=itemgetter(0)))


def get_suggested_categories(user):
    """Gets the suggested categories of a user for the dashboard"""
    if not redis_write_client:
        return []
    related = {cat.id for cat in get_related_categories(user, detailed=False)}
    res = []
    categ_suggestions = suggestions.get_suggestions(user, 'category')
    query = Category.find_all(Category.id.in_(categ_suggestions),
                              ~Category.id.in_(related),
                              ~Category.is_deleted,
                              ~Category.suggestions_disabled)
    categories = {c.id: c for c in query}
    for id_, score in categ_suggestions.iteritems():
        try:
            categ = categories[int(id_)]
        except KeyError:
            suggestions.unsuggest(user, 'category', id_)
            continue
        if any(p.suggestions_disabled for p in categ.parent_chain_query):
            suggestions.unsuggest(user, 'category', id_)
            continue
        if not categ.can_access(user):
            continue
        res.append({
            'score': score,
            'categ': categ,
            'path': truncate_path(categ.get_chain_titles()[:-1], chars=50)
        })
    return res


def serialize_user(user):
    """Serialize user to JSON-like object"""
    return {
        'id': user.id,
        'title': user.title,
        'identifier': 'User:{}'.format(user.id),
        'name': user.full_name,
        'familyName': user.last_name,
        'firstName': user.first_name,
        'affiliation': user.affiliation,
        'phone': user.phone,
        'email': user.email,
        '_type': 'Avatar'
    }


def search_users(exact=False, include_deleted=False, include_pending=False, external=False, **criteria):
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

    organisation = criteria.pop('affiliation', unspecified)
    if organisation is not unspecified:
        query = query.join(UserAffiliation).filter(unaccent_match(UserAffiliation.name, organisation, exact))

    email = criteria.pop('email', unspecified)
    if email is not unspecified:
        query = query.join(UserEmail).filter(unaccent_match(UserEmail.email, email, exact))

    for k, v in criteria.iteritems():
        query = query.filter(unaccent_match(getattr(User, k), v, exact))

    found_emails = {}
    found_identities = {}
    for user in query:
        for identity in user.identities:
            found_identities[(identity.provider, identity.identifier)] = user
        for email in user.all_emails:
            found_emails[email] = user

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

    return set(found_emails.viewvalues())


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

    # Merge links
    for link in source.linked_objects:
        if link.object is None:
            # remove link if object does no longer exist
            db.session.delete(link)
        else:
            link.user = target

    # De-duplicate links
    unique_links = {(link.object, link.role): link for link in target.linked_objects}
    to_delete = set(target.linked_objects) - set(unique_links.viewvalues())

    for link in to_delete:
        db.session.delete(link)

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

    # Merge identities
    for identity in set(source.identities):
        identity.user = target

    # Merge avatars in redis
    if redis_write_client:
        avatar_links.merge_avatars(target, source)
        suggestions.merge_avatars(target, source)

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
