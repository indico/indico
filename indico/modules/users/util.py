# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import request

from indico.core import signals
from indico.core.auth import multipass
from indico.core.db import db
from indico.modules.users import User
from indico.modules.users.models.affiliations import UserAffiliation
from indico.modules.users.models.emails import UserEmail
from indico.util.event import truncate_path
from indico.util.redis import write_client as redis_write_client
from indico.util.redis import suggestions, avatar_links
from MaKaC.accessControl import AccessWrapper
from MaKaC.conference import CategoryManager


def get_related_categories(user):
    """Gets the related categories of a user for the dashboard"""
    favorites = user.favorite_categories
    managed = user.get_linked_objects('category', 'manager')
    res = {}
    for categ in favorites | managed:
        res[(categ.getTitle(), categ.getId())] = {
            'categ': categ,
            'favorite': categ in favorites,
            'managed': categ in managed,
            'path': truncate_path(categ.getCategoryPathTitles(), 30, False)
        }
    return OrderedDict(sorted(res.items(), key=itemgetter(0)))


def get_suggested_categories(user):
    """Gets the suggested categories of a user for the dashboard"""
    if not redis_write_client:
        return []
    related = user.favorite_categories | user.get_linked_objects('category', 'manager')
    res = []
    for id_, score in suggestions.get_suggestions(user, 'category').iteritems():
        try:
            categ = CategoryManager().getById(id_)
        except KeyError:
            suggestions.unsuggest(user, 'category', id_)
            continue
        if not categ or categ.isSuggestionsDisabled() or categ in related:
            continue
        if any(p.isSuggestionsDisabled() for p in categ.iterParents()):
            continue
        if not categ.canAccess(AccessWrapper(user.as_avatar, request.remote_addr)):
            continue
        res.append({
            'score': score,
            'categ': categ,
            'path': truncate_path(categ.getCategoryPathTitles(), 30, False)
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


def _build_match(column, value, exact):
    value = value.replace('%', '')
    if exact:
        return db.func.lower(column) == value.lower()
    else:
        return column.ilike("%{}%".format(value))


def search_users(exact=False, include_deleted=False, include_pending=False, external=False, **criteria):
    unspecified = object()
    query = User.query.options(db.joinedload(User.identities),
                               db.joinedload(User._all_emails),
                               db.joinedload(User.merged_into_user))
    original_criteria = dict(criteria)

    if not criteria:
        return set()

    if not include_pending:
        query = query.filter(~User.is_pending)
    if not include_deleted:
        query = query.filter(~User.is_deleted)

    organisation = criteria.pop('affiliation', unspecified)
    if organisation is not unspecified:
        query = query.join(UserAffiliation).filter(_build_match(UserAffiliation.name, organisation, exact))

    email = criteria.pop('email', unspecified)
    if email is not unspecified:
        query = query.join(UserEmail).filter(_build_match(UserEmail.email, email, exact))

    for k, v in criteria.iteritems():
        query = query.filter(_build_match(getattr(User, k), v, exact))

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
            if ((ident.provider.name, ident.identifier) not in found_identities and
                    ident.data['email'].lower() not in found_emails):
                found_emails[ident.data['email'].lower()] = ident
                found_identities[(ident.provider, ident.identifier)] = ident

    return set(found_emails.viewvalues())


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

    # Merge avatars in RB
    from indico.modules.rb.utils import rb_merge_users
    rb_merge_users(str(target.id), str(source.id))

    # Notify signal listeners about the merge
    signals.merge_users.send(target.as_avatar, merged=source.as_avatar)
    db.session.flush()

    # Mark source as merged
    source.merged_into_user = target
    source.is_deleted = True
    db.session.flush()

    # Restore the source user's primary email
    source.email = primary_source_email
    db.session.flush()
