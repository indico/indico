# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

import os
import re
from uuid import UUID

from dateutil import parser, relativedelta
from marshmallow import ValidationError
from marshmallow.fields import DateTime, Field
from marshmallow.utils import from_iso_datetime
from sqlalchemy import inspect

from indico.core.permissions import get_unified_permissions
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.user import principal_from_identifier


HUMANIZED_DATE_RE = re.compile(r'^(?:(?P<number>-?\d+)(?P<unit>[dwM]))|(?P<iso_date>\d{4}-\d{2}-\d{2})$')
HUMANIZED_UNIT_MAP = {
    'M': 'months',
    'w': 'weeks',
    'd': 'days'
}


def validate_with_message(fn, reason):
    """Create a validation function with a custom error message."""

    def validate(args):
        if not fn(args):
            raise ValidationError(reason)

    return validate


def not_empty(value):
    """Validator which ensures the value is not empty.

    Any falsy value is considered empty.
    """

    if not value:
        raise ValidationError(_('This field cannot be empty.'))


def file_extension(*exts):
    """Validator which checks the file extension."""

    exts = frozenset('.' + ext.lstrip('.') for ext in exts)

    def validate(file):
        if not file:
            return
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in exts:
            raise ValidationError(_('Invalid file extension'))

    return validate


def max_words(max):
    def validate(text):
        count = len(re.split(r'\s+', text, flags=re.UNICODE)) if text else 0
        if count > max:
            raise ValidationError(_('This field has more than {} words').format(max))
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


class ModelField(Field):
    """Marshmallow field for a single database object.

    This serializes an SQLAlchemy object to its identifier (usually the PK),
    and deserializes from the same kind of identifier back to an SQLAlchemy object.
    """

    default_error_messages = {
        'not_found': '"{value}" does not exist',
        'type': 'Invalid input type.'
    }

    def __init__(self, model, column=None, column_type=None, get_query=lambda m: m.query, **kwargs):
        self.model = model
        self.get_query = get_query
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
        super(ModelField, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        return getattr(value, self.column.key) if value is not None else None

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        try:
            value = self.column_type(value)
        except (TypeError, ValueError):
            self.fail('type')
        obj = self.get_query(self.model).filter(self.column == value).one_or_none()
        if obj is None:
            self.fail('not_found', value=value)
        return obj


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

    def __init__(self, model, column=None, column_type=None, get_query=lambda m: m.query, collection_class=list,
                 **kwargs):
        self.model = model
        self.get_query = get_query
        self.collection_class = collection_class
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
            return self.collection_class()
        try:
            value = map(self.column_type, value)
        except (TypeError, ValueError):
            self.fail('type')
        requested = set(value)
        objs = self.get_query(self.model).filter(self.column.in_(value)).all()
        found = {getattr(x, self.column.key) for x in objs}
        invalid = requested - found
        if invalid:
            self.fail('not_found', value=next(iter(invalid)))
        assert found == requested, 'Unexpected objects found'
        return self.collection_class(objs)


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

    def __init__(self, allow_groups=False, allow_external_users=False, allow_event_roles=False,
                 allow_category_roles=False, allow_registration_forms=False, allow_emails=False, **kwargs):
        self.allow_groups = allow_groups
        self.allow_external_users = allow_external_users
        self.allow_event_roles = allow_event_roles
        self.allow_category_roles = allow_category_roles
        self.allow_registration_forms = allow_registration_forms
        self.allow_emails = allow_emails
        super(PrincipalList, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        return [x.identifier for x in value]

    def _deserialize(self, value, attr, data):
        event_id = None
        if self.allow_event_roles or self.allow_category_roles:
            event_id = self.context['event'].id
        try:
            return set(principal_from_identifier(identifier,
                                                 allow_groups=self.allow_groups,
                                                 allow_external_users=self.allow_external_users,
                                                 allow_event_roles=self.allow_event_roles,
                                                 allow_category_roles=self.allow_category_roles,
                                                 allow_registration_forms=self.allow_registration_forms,
                                                 allow_emails=self.allow_emails,
                                                 event_id=event_id)
                       for identifier in value)
        except ValueError as exc:
            raise ValidationError(unicode(exc))


class PrincipalDict(PrincipalList):
    # We need to keep identifiers separately since for pending users we
    # can't get the correct one back from the user
    def _deserialize(self, value, attr, data):
        event_id = None
        if self.allow_event_roles or self.allow_category_roles:
            event_id = self.context['event'].id
        try:
            return {identifier: principal_from_identifier(identifier,
                                                          allow_groups=self.allow_groups,
                                                          allow_external_users=self.allow_external_users,
                                                          allow_event_roles=self.allow_event_roles,
                                                          allow_category_roles=self.allow_category_roles,
                                                          allow_registration_forms=self.allow_registration_forms,
                                                          allow_emails=self.allow_emails,
                                                          event_id=event_id,
                                                          soft_fail=True)
                    for identifier in value}
        except ValueError as exc:
            raise ValidationError(unicode(exc))


class PrincipalPermissionList(Field):
    """Marshmallow field for a list of principals and their permissions.

    :param principal_class: Object class to get principal permissions for
    :param all_permissions: Whether to include all permissions, even if principal has full access
    """

    def __init__(self, principal_class, all_permissions=False, **kwargs):
        self.principal_class = principal_class
        self.all_permissions = all_permissions
        super(PrincipalPermissionList, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        return [(entry.principal.identifier, sorted(get_unified_permissions(entry, self.all_permissions)))
                for entry in value]

    def _deserialize(self, value, attr, data):
        try:
            return {
                principal_from_identifier(identifier, allow_groups=True): set(permissions)
                for identifier, permissions in value
            }
        except ValueError as exc:
            raise ValidationError(unicode(exc))


class HumanizedDate(Field):
    """Marshmallow field for human-written dates used in REST APIs.

    This field allows for simple time deltas, e.g.: ``1d`` = "1 day`, ``1w`` = "1 week",
    ``-2M`` = "2 months ago";
    Simple ISO dates are also accepted (``YYYY-MM-DD``).
    """

    def _serialize(self, value, attr, obj):
        raise NotImplementedError

    def _deserialize(self, value, attr, obj):
        m = HUMANIZED_DATE_RE.match(value)
        if not m:
            raise ValidationError("Can't parse humanized date!")

        if m.group('iso_date'):
            return parser.isoparse(value)
        else:
            unit = m.group('unit')
            today = now_utc(False)
            number = int(m.group('number'))
            return today + relativedelta.relativedelta(**{HUMANIZED_UNIT_MAP[unit]: number})


class FilesField(ModelList):
    """Marshmallow field for a list of previously-uploaded files."""

    default_error_messages = dict(ModelList.default_error_messages, **{
        'claimed': 'File has already been claimed',
    })

    def __init__(self, allow_claimed=False, **kwargs):
        from indico.modules.files.models.files import File
        self.allow_claimed = allow_claimed
        super(FilesField, self).__init__(model=File, column='uuid', column_type=UUID, **kwargs)

    def _deserialize(self, value, attr, data):
        rv = super(FilesField, self)._deserialize(value, attr, data)
        if not self.allow_claimed and any(f.claimed for f in rv):
            self.fail('claimed')
        return rv


class FileField(ModelField):
    """Marshmallow field for one previously-uploaded file."""

    default_error_messages = dict(ModelList.default_error_messages, **{
        'claimed': 'File has already been claimed',
    })

    def __init__(self, allow_claimed=False, **kwargs):
        from indico.modules.files.models.files import File
        self.allow_claimed = allow_claimed
        super(FileField, self).__init__(model=File, column='uuid', column_type=UUID, **kwargs)

    def _deserialize(self, value, attr, data):
        rv = super(FileField, self)._deserialize(value, attr, data)
        if not self.allow_claimed and rv is not None and rv.claimed:
            self.fail('claimed')
        return rv
