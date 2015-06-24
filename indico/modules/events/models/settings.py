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

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.settings.models.base import JSONSettingsBase, PrincipalSettingsBase
from indico.util.decorators import strict_classproperty
from indico.util.string import return_ascii


class EventSettingsMixin(object):
    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        return (db.Index(None, 'event_id', 'module', 'name'),
                db.Index(None, 'event_id', 'module'),
                {'schema': 'events'})

    event_id = db.Column(
        db.Integer,
        index=True,
        nullable=False
    )

    @property
    def event(self):
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(self.event_id, True)

    @classmethod
    def delete_event(cls, event_id):
        cls.find(event_id=event_id).delete(synchronize_session='fetch')


class EventSetting(JSONSettingsBase, EventSettingsMixin, db.Model):
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
    extra_key_cols = ('event_id',)

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    @return_ascii
    def __repr__(self):
        return '<EventSettingPrincipal({}, {}, {}, {!r})>'.format(self.event_id, self.module, self.name, self.principal)
