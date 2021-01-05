# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db


def uniqueId(obj):
    if isinstance(obj, db.m.Contribution):
        return '{}.{}'.format(obj.event_id, obj.legacy_mapping.legacy_contribution_id if obj.legacy_mapping else obj.id)
    elif isinstance(obj, db.m.SubContribution):
        return '{}.{}.{}'.format(
            obj.event.id,
            obj.legacy_mapping.legacy_contribution_id if obj.legacy_mapping else obj.contribution.id,
            obj.legacy_mapping.legacy_subcontribution_id if obj.legacy_mapping else obj.id
        )
    elif isinstance(obj, db.m.Session):
        return '{}.s{}'.format(obj.event_id, obj.legacy_mapping.legacy_session_id if obj.legacy_mapping else obj.id)
    elif isinstance(obj, db.m.SessionBlock):
        return '{}.s{}.{}'.format(obj.event.id,
                                  obj.legacy_mapping.legacy_session_id if obj.legacy_mapping else obj.session.id,
                                  obj.legacy_mapping.legacy_session_block_id if obj.legacy_mapping else obj.id)
    elif isinstance(obj, db.m.EventNote):
        return '{}.n{}'.format(uniqueId(obj.object), obj.id)
    else:
        # XXX: anything besides Conference/Event?! probably not..
        return obj.getId() if hasattr(obj, 'getId') else obj.id


def truncate_path(full_path, chars=30, skip_first=True):
    """Truncate the path of a category to the number of character.

    Only the path is truncated by removing nodes, but the nodes
    themselves are never truncated.

    If the last node is longer than the ``chars`` constraint, then it is
    returned as is (with ``None`` for the first and inner nodes.)
    This is the only case where the ``chars`` constraint might not be
    respected.

    If ``skip_first`` is ``True``, the first node will be skipped,
    except if the path has 1 or 2 nodes only and the first node fits
    under the ``chars`` constraint

    :param full_path: list -- all the nodes of the path in order
    :param chars: int -- the desired length in characters of the path
    :param skip_first: bool -- whether to ignore the first node or not
                       If the path only has 1 or 2 nodes, then the first
                       node will not be skipped if it can fit within the
                       ``chars`` constraint.

    :returns: tuple -- the first node, the inner nodes, the last node
              and whether the path was truncated. If any of the values
              have been truncated, they will be ``None``.

    """
    truncated = False
    if skip_first:
        skip, full_path = full_path[:1], full_path[1:]
        skip = skip[0] if skip else None
    else:
        skip = None

    if not full_path:
        return None, None, skip, truncated
    if len(full_path) == 1:
        if skip is not None and len(skip) + len(full_path[0]) <= chars:
            return skip, None, full_path[0], truncated
        else:
            return None, None, full_path[0], skip is not None  # only truncated if we skip the first

    first_node, inner, last_node = full_path[0], full_path[1:-1], full_path[-1]
    char_length = len(last_node)

    if char_length + len(first_node) > chars:
        first_node = None
        truncated = True
    else:
        char_length += len(first_node)

    if not inner:
        return first_node, None, last_node, truncated

    path = []
    prev = inner.pop()
    while char_length + len(prev) <= chars:
        char_length += len(prev)
        path.append(prev)
        if not inner:
            break
        prev = inner.pop()
    else:
        truncated = True

    return first_node, path[::-1], last_node, truncated
