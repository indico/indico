# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import OrderedDict
from datetime import timedelta

import dateutil.parser
import pytz
from sqlalchemy import inspect
from werkzeug.utils import cached_property

from indico.core.db import db


class SettingConverter(object):
    """
    Implement a custom conversion between Python types and
    JSON-serializable types.

    The methods are never called with a ``None`` value.
    """

    @staticmethod
    def from_python(value):
        raise NotImplementedError

    @staticmethod
    def to_python(value):
        raise NotImplementedError


class DatetimeConverter(SettingConverter):
    """Convert a tz-aware datetime object from/to an ISO-8601 string.

    The datetime is always stored as UTC, but any ISO-8601 string can
    be converted back to a datetime object as long as it has timezone
    information attached.
    """

    @staticmethod
    def from_python(value):
        assert value.tzinfo is not None
        return value.astimezone(pytz.utc).isoformat()

    @staticmethod
    def to_python(value):
        return dateutil.parser.parse(value).astimezone(pytz.utc)


class TimedeltaConverter(SettingConverter):
    """Convert a timedelta object from/to seconds."""

    @staticmethod
    def from_python(value):
        return int(value.total_seconds())

    @staticmethod
    def to_python(value):
        return timedelta(seconds=value)


class EnumConverter(SettingConverter):
    """Convert an enum object from/to its name."""

    def __init__(self, enum):
        self.enum = enum

    def from_python(self, value):
        assert isinstance(value, self.enum)
        return value.name

    def to_python(self, value):
        return self.enum[value]


class ModelConverter(SettingConverter):
    """Convert a SQLAlchemy object from/to its PK.

    :param model: A SQLAlchemy model with a single-column PK or the name
                  of a model (if importing the model would cause circular
                  dependencies).
    """

    def __init__(self, model):
        self._model = model

    @cached_property
    def model(self):
        model = getattr(db.m, self._model) if isinstance(self._model, basestring) else self._model
        assert len(inspect(model).primary_key) == 1
        return model

    def from_python(self, value):
        if value is None:
            return None
        assert isinstance(value, self.model)
        return inspect(value).identity_key[1][0]

    def to_python(self, value):
        if value is None:
            return None
        return self.model.query.get(value)


class ModelListConverter(SettingConverter):
    """Convert a list of SQLAlchemy objects from/to a list of PKs.

    :param model: A SQLAlchemy model with a single-column PK or the name
                  of a model (if importing the model would cause circular
                  dependencies).
    :param collection_class: The collection to use for the python-side
                             value. Defaults to `list` but could also be
                             `set` for example.
    """

    def __init__(self, model, collection_class=list):
        self._model = model
        self.collection_class = collection_class

    @cached_property
    def model(self):
        if isinstance(self._model, basestring):
            return getattr(db.m, self._model)
        return self._model

    @cached_property
    def column(self):
        pks = inspect(self.model).primary_key
        assert len(pks) == 1
        return pks[0]

    def from_python(self, value):
        if not value:
            return []
        assert all(isinstance(x, self.model) for x in value)
        return [inspect(x).identity_key[1][0] for x in value]

    def to_python(self, value):
        if not value:
            return []
        return self.collection_class(self.model.query.filter(self.column.in_(value)))


class OrderedDictConverter(SettingConverter):
    @staticmethod
    def from_python(value):
        return value.items()

    @staticmethod
    def to_python(value):
        return OrderedDict(value)
