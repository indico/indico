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

import operator
from collections import OrderedDict

from flask import request
from MaKaC.accessControl import AccessWrapper

from indico.core.db import db
from indico.modules.users import User, UserAffiliation, UserEmail
from indico.util.event import truncate_path
from indico.util.redis import write_client as redis_write_client
from indico.util.redis import suggestions
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
    return OrderedDict(sorted(res.items(), key=operator.itemgetter(0)))


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
        'identifier': 'User:{}'.format(user.id),
        'name': user.full_name,
        'familyName': user.last_name,
        'firstName': user.first_name,
        'affiliation': user.affiliation,
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
    query = User.query.options(db.joinedload(User.identities), db.joinedload(User._all_emails))
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
            found_emails[email.lower()] = user

    # external user providers
    if external:
        from indico.modules.auth import multipass
        identities = multipass.search_identities(
            exact=exact,
            **{c: v for c, v in original_criteria.iteritems()})

        for ident in identities:
            if ((ident.provider.name, ident.identifier) not in found_identities and
                    ident.data['email'].lower() not in found_emails):
                found_emails[ident.data['email'].lower()] = ident
                found_identities[(ident.provider, ident.identifier)] = ident

    return set(found_emails.values())
