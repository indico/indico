# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.settings.models.base import JSONSettingsBase, PrincipalSettingsBase
from indico.util.decorators import strict_classproperty
from indico.util.string import return_ascii


class CoreSettingsMixin(object):
    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        return (db.Index(None, 'module', 'name'),
                {'schema': 'indico'})


class Setting(JSONSettingsBase, CoreSettingsMixin, db.Model):
    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        return db.UniqueConstraint('module', 'name'),

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    @return_ascii
    def __repr__(self):
        return '<Setting({}, {}, {!r})>'.format(self.module, self.name, self.value)


class SettingPrincipal(PrincipalSettingsBase, CoreSettingsMixin, db.Model):
    principal_backref_name = 'in_settings_acls'

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    @return_ascii
    def __repr__(self):
        return '<SettingPrincipal({}, {}, {!r})>'.format(self.module, self.name, self.principal)
