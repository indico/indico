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
from indico.core.settings.models.base import JSONSettingsBase
from indico.util.decorators import strict_classproperty
from indico.util.string import return_ascii


class CategorySetting(JSONSettingsBase, db.Model):
    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        return (db.Index(None, 'category_id', 'module', 'name'),
                db.Index(None, 'category_id', 'module'),
                db.UniqueConstraint('category_id', 'module', 'name'),
                {'schema': 'categories'})

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        index=True,
        nullable=False
    )

    category = db.relationship(
        'Category',
        lazy=True,
        backref=db.backref(
            'settings',
            lazy='dynamic'
        )
    )

    @return_ascii
    def __repr__(self):
        return '<CategorySetting({}, {}, {}, {!r})>'.format(self.category_id, self.module, self.name, self.value)
