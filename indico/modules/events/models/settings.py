# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
    def event_new(cls):
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

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    @return_ascii
    def __repr__(self):
        return '<EventSettingPrincipal({}, {}, {}, {!r})>'.format(self.event_id, self.module, self.name, self.principal)
