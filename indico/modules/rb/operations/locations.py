# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.orm import joinedload, load_only

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.principals import LocationPrincipal
from indico.util.caching import memoize_redis


def _query_managed_location(user):
    criteria = [db.and_(LocationPrincipal.type == PrincipalType.user,
                        LocationPrincipal.user_id == user.id,
                        LocationPrincipal.has_management_permission())]
    for group in user.local_groups:
        criteria.append(db.and_(LocationPrincipal.type == PrincipalType.local_group,  # noqa: PERF401
                                LocationPrincipal.local_group_id == group.id,
                                LocationPrincipal.has_management_permission()))
    for group in user.iter_all_multipass_groups():
        criteria.append(db.and_(LocationPrincipal.type == PrincipalType.multipass_group,  # noqa: PERF401
                                LocationPrincipal.multipass_group_provider == group.provider.name,
                                db.func.lower(LocationPrincipal.multipass_group_name) == group.name.lower(),
                                LocationPrincipal.has_management_permission()))
    return Location.query.filter(~Location.is_deleted, Location.acl_entries.any(db.or_(*criteria)))


def _query_all_locations_for_acl_check():
    return (Location.query
            .filter(~Location.is_deleted)
            .options(load_only('id'), joinedload('acl_entries')))


@memoize_redis(900)
def has_managed_locations(user):
    if user.can_get_all_multipass_groups:
        return _query_managed_location(user).has_rows()
    else:
        query = _query_all_locations_for_acl_check()
        return any(loc.can_manage(user, allow_admin=False) for loc in query)
