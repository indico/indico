# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.settings.models.base import JSONSettingsBase, PrincipalSettingsBase
from indico.util.decorators import strict_classproperty
from indico.util.string import return_ascii


class EventSettingsMixin(object):
    settings_backref_name = None

    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        return (db.Index(None, 'event_id', 'module', 'name'),
                db.Index(None, 'event_id', 'module'),
                {'schema': 'events'})

    @declared_attr
    def event_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('events.events.id'),
            index=True,
            nullable=False
        )

    @declared_attr
    def event(cls):
        return db.relationship(
            'Event',
            lazy=True,
            backref=db.backref(
                cls.settings_backref_name,
                lazy='dynamic'
            )
        )


class EventSetting(JSONSettingsBase, EventSettingsMixin, db.Model):
    settings_backref_name = 'settings'

    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        return db.UniqueConstraint('event_id', 'module', 'name'),

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    @return_ascii
    def __repr__(self):
        return '<EventSetting({}, {}, {}, {!r})>'.format(self.event_id, self.module, self.name, self.value)


class EventSettingPrincipal(PrincipalSettingsBase, EventSettingsMixin, db.Model):
    principal_backref_name = 'in_event_settings_acls'
    settings_backref_name = 'settings_principals'
    extra_key_cols = ('event_id',)
    allow_event_roles = True
    allow_category_roles = True

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    @return_ascii
    def __repr__(self):
        return '<EventSettingPrincipal({}, {}, {}, {!r})>'.format(self.event_id, self.module, self.name, self.principal)
