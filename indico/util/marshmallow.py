# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import re
from datetime import datetime, time, timedelta
from uuid import UUID

from dateutil import parser, relativedelta
from marshmallow import ValidationError
from marshmallow.fields import Date, DateTime, Field, List
from marshmallow.utils import from_iso_datetime
from pytz import timezone
from sqlalchemy import inspect

from indico.core.config import config
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


class NaiveDateTime(DateTime):
    SERIALIZATION_FUNCS = {
        'iso': _naive_isoformat,
    }

    DESERIALIZATION_FUNCS = {
        'iso': _naive_from_iso,
    }


class RelativeDayDateTime(Date):
    """
    A field that accepts a date or relative date offset and deserializes to
    a datetime object at the start/end of that date.

    The datetime objects returned by this field are always using Indico's
    default timezone.
    """

    # Currently this field always uses the default timezone; for typical API
    # endpoints that use a day granularity this should usually be fine, but if
    # any use cases come up where this is not sufficient we may need to add a
    # kwarg to switch the field to UTC or get the timezone from a different field
    # (via ``data`` in ``_deserialize``)

    DELTAS = {
        'today': timedelta(),
        'yesterday': timedelta(days=-1),
        'tomorrow': timedelta(days=1),
    }

    def __init__(self, day_end=False, **kwargs):
        self.day_end = day_end
        super().__init__(**kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        date_value = None
        if value:
            today = now_utc(False).astimezone(timezone(config.DEFAULT_TIMEZONE)).date()
            # yesterday/today/tomorrow
            if (delta := self.DELTAS.get(value)) is not None:
                date_value = today + delta
            # something like -14d or +7d
            elif (match := re.match(r'^([+-])?(\d{1,3})d$', value)) is not None:
                mod = -1 if match.group(1) == '-' else 1
                offset = int(match.group(2))
                date_value = today + timedelta(days=mod*offset)
        # fall back to the normal date parsing
        if date_value is None:
            date_value = super()._deserialize(value, attr, data, **kwargs)
        # attach time information for the day start/end
        if self.day_end:
            return timezone(config.DEFAULT_TIMEZONE).localize(datetime.combine(date_value, time(23, 59, 59)))
        else:
            return timezone(config.DEFAULT_TIMEZONE).localize(datetime.combine(date_value, time(0, 0, 0)))


class ModelField(Field):
    """Marshmallow field for a single database object.

    This serializes an SQLAlchemy object to its identifier (usually the PK),
    and deserializes from the same kind of identifier back to an SQLAlchemy object.
    """

    default_error_messages = {
        'not_found': '"{value}" does not exist',
        'type': 'Invalid input type.'
    }

    def __init__(self, model, column=None, column_type=None, get_query=lambda m: m.query, filter_deleted=False,
                 **kwargs):
        self.model = model
        self.get_query = get_query
        self.filter_deleted = filter_deleted
        if column:
            self.column = getattr(model, column)
            # Custom column -> most likely a string value
            self.column_type = column_type or str
        else:
            pks = inspect(model).primary_key
            assert len(pks) == 1
            self.column = pks[0]
            # Default PK -> most likely an ID
            self.column_type = column_type or int
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        return getattr(value, self.column.key) if value is not None else None

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        try:
            value = self.column_type(value)
        except (TypeError, ValueError):
            self.fail('type')
        query = self.get_query(self.model).filter(self.column == value)
        if self.filter_deleted:
            query = query.filter(~self.model.is_deleted)
        obj = query.one_or_none()
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
                 filter_deleted=False, **kwargs):
        self.model = model
        self.get_query = get_query
        self.filter_deleted = filter_deleted
        self.collection_class = collection_class
        if column:
            self.column = getattr(model, column)
            # Custom column -> most likely a string value
            self.column_type = column_type or str
        else:
            pks = inspect(model).primary_key
            assert len(pks) == 1
            self.column = pks[0]
            # Default PK -> most likely an ID
            self.column_type = column_type or int
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        return [getattr(x, self.column.key) for x in value]

    def _deserialize(self, value, attr, data, **kwargs):
        if not value:
            return self.collection_class()
        try:
            value = list(map(self.column_type, value))
        except (TypeError, ValueError):
            self.fail('type')
        requested = set(value)
        query = self.get_query(self.model).filter(self.column.in_(value))
        if self.filter_deleted:
            query = query.filter(~self.model.is_deleted)
        objs = query.all()
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
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        return value.identifier if value is not None else None

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        try:
            return principal_from_identifier(value,
                                             allow_groups=self.allow_groups,
                                             allow_external_users=self.allow_external_users)
        except ValueError as exc:
            raise ValidationError(str(exc))


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
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        return [x.identifier for x in value]

    def _deserialize(self, value, attr, data, **kwargs):
        event_id = None
        if self.allow_event_roles or self.allow_category_roles:
            event_id = self.context['event'].id
        try:
            return {principal_from_identifier(identifier,
                                              allow_groups=self.allow_groups,
                                              allow_external_users=self.allow_external_users,
                                              allow_event_roles=self.allow_event_roles,
                                              allow_category_roles=self.allow_category_roles,
                                              allow_registration_forms=self.allow_registration_forms,
                                              allow_emails=self.allow_emails,
                                              event_id=event_id)
                    for identifier in value}
        except ValueError as exc:
            raise ValidationError(str(exc))


class PrincipalDict(PrincipalList):
    # We need to keep identifiers separately since for pending users we
    # can't get the correct one back from the user
    def _deserialize(self, value, attr, data, **kwargs):
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
            raise ValidationError(str(exc))


class PrincipalPermissionList(Field):
    """Marshmallow field for a list of principals and their permissions.

    :param principal_class: Object class to get principal permissions for
    :param all_permissions: Whether to include all permissions, even if principal has full access
    """

    def __init__(self, principal_class, all_permissions=False, **kwargs):
        self.principal_class = principal_class
        self.all_permissions = all_permissions
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        return [(entry.principal.identifier, sorted(get_unified_permissions(entry, self.all_permissions)))
                for entry in value]

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return {
                principal_from_identifier(identifier, allow_groups=True): set(permissions)
                for identifier, permissions in value
            }
        except ValueError as exc:
            raise ValidationError(str(exc))


class HumanizedDate(Field):
    """Marshmallow field for human-written dates used in REST APIs.

    This field allows for simple time deltas, e.g.: ``1d`` = "1 day`, ``1w`` = "1 week",
    ``-2M`` = "2 months ago";
    Simple ISO dates are also accepted (``YYYY-MM-DD``).
    """

    def _serialize(self, value, attr, obj, **kwargs):
        raise NotImplementedError

    def _deserialize(self, value, attr, data, **kwargs):
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

    default_error_messages = {
        **ModelList.default_error_messages,
        'claimed': 'File has already been claimed',
    }

    def __init__(self, allow_claimed=False, **kwargs):
        from indico.modules.files.models.files import File
        self.allow_claimed = allow_claimed
        super().__init__(model=File, column='uuid', column_type=UUID, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        rv = super()._deserialize(value, attr, data)
        if not self.allow_claimed and any(f.claimed for f in rv):
            self.fail('claimed')
        return rv


class FileField(ModelField):
    """Marshmallow field for one previously-uploaded file."""

    default_error_messages = {
        **ModelList.default_error_messages,
        'claimed': 'File has already been claimed',
    }

    def __init__(self, allow_claimed=False, **kwargs):
        from indico.modules.files.models.files import File
        self.allow_claimed = allow_claimed
        super().__init__(model=File, column='uuid', column_type=UUID, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        rv = super()._deserialize(value, attr, data)
        if not self.allow_claimed and rv is not None and rv.claimed:
            self.fail('claimed')
        return rv


class NoneRemovingList(List):
    """Marshmallow field for a `List` that skips None during serialization."""

    def _serialize(self, value, attr, obj, **kwargs):
        rv = super()._serialize(value, attr, obj, **kwargs)
        if rv is None:
            return None
        return [x for x in rv if x is not None]
