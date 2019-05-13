# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

from marshmallow import ValidationError
from marshmallow.fields import DateTime, Field
from marshmallow.utils import from_iso_datetime
from sqlalchemy import inspect

from indico.core.permissions import get_split_permissions, get_unified_permissions
from indico.util.user import principal_from_identifier


def validate_with_message(fn, reason):
    """Create a validation function with a custom error message"""

    def validate(args):
        if not fn(args):
            raise ValidationError(reason)

    return validate


def _naive_isoformat(dt, **unused):
    assert dt.tzinfo is None, 'expected naive datetime'
    return dt.isoformat()


def _naive_from_iso(value):
    dt = from_iso_datetime(value)
    if dt.tzinfo is not None:
        raise ValidationError('expected naive datetime')
    return dt


class UnicodeDateTime(DateTime):
    """Unicode-producing/parsing DateTime."""

    def _serialize(self, value, attr, obj, **kwargs):
        return super(UnicodeDateTime, self)._serialize(value, attr, obj, **kwargs).decode('utf-8')


class NaiveDateTime(UnicodeDateTime):
    SERIALIZATION_FUNCS = {
        'iso': _naive_isoformat,
    }

    DESERIALIZATION_FUNCS = {
        'iso': _naive_from_iso,
    }


class ModelList(Field):
    """Marshmallow field for a list of database objects.

    This serializes a list of SQLAlchemy objects to a list of
    identifiers (usually the PK), and deserializes from the same
    kind of list back to actual SQLAlchemy objects.
    """

    default_error_messages = {
        'not_found': '"{value}" does not exist',
        'type': 'Invalid input type.'
    }

    def __init__(self, model, column=None, column_type=None, **kwargs):
        self.model = model
        if column:
            self.column = getattr(model, column)
            # Custom column -> most likely a string value
            self.column_type = column_type or unicode
        else:
            pks = inspect(model).primary_key
            assert len(pks) == 1
            self.column = pks[0]
            # Default PK -> most likely an ID
            self.column_type = column_type or int
        super(ModelList, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        return [getattr(x, self.column.key) for x in value]

    def _deserialize(self, value, attr, data):
        if not value:
            return []
        try:
            value = map(self.column_type, value)
        except (TypeError, ValueError):
            self.fail('type')
        requested = set(value)
        objs = self.model.query.filter(self.column.in_(value)).all()
        found = {getattr(x, self.column.key) for x in objs}
        invalid = requested - found
        if invalid:
            self.fail('not_found', value=next(iter(invalid)))
        assert found == requested, 'Unexpected objects found'
        return objs


class Principal(Field):
    """Marshmallow field for a single principal."""

    def __init__(self, allow_groups=False, allow_external_users=False, **kwargs):
        self.allow_groups = allow_groups
        self.allow_external_users = allow_external_users
        super(Principal, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        return value.identifier if value is not None else None

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        try:
            return principal_from_identifier(value,
                                             allow_groups=self.allow_groups,
                                             allow_external_users=self.allow_external_users)
        except ValueError as exc:
            raise ValidationError(unicode(exc))


class PrincipalList(Field):
    """Marshmallow field for a list of principals."""

    def __init__(self, allow_groups=False, allow_external_users=False, **kwargs):
        self.allow_groups = allow_groups
        self.allow_external_users = allow_external_users
        super(PrincipalList, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        return [x.identifier for x in value]

    def _deserialize(self, value, attr, data):
        try:
            return set(principal_from_identifier(identifier,
                                                 allow_groups=self.allow_groups,
                                                 allow_external_users=self.allow_external_users)
                       for identifier in value)
        except ValueError as exc:
            raise ValidationError(unicode(exc))


class PrincipalPermissionList(Field):
    """Marshmallow field for a list of principals and their permissions."""

    def __init__(self, principal_class, **kwargs):
        self.principal_class = principal_class
        super(PrincipalPermissionList, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        return [(entry.principal.identifier, sorted(get_unified_permissions(entry))) for entry in value]

    def _deserialize(self, value, attr, data):
        try:
            return {
                principal_from_identifier(identifier, allow_groups=True): set(permissions)
                for identifier, permissions in value
            }
        except ValueError as exc:
            raise ValidationError(unicode(exc))
