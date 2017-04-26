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

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.designer import TemplateType, DEFAULT_CONFIG
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


TEMPLATE_DEFAULTS = {
    'items': [],
    'background_position': 'stretch'
}


class DesignerTemplate(db.Model):
    __tablename__ = 'designer_templates'
    __table_args__ = (db.CheckConstraint("(event_id IS NULL) != (category_id IS NULL)", 'event_xor_category_id_null'),
                      {'schema': 'indico'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    type = db.Column(
        PyIntEnum(TemplateType),
        nullable=False
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=True
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        index=True,
        nullable=True
    )
    data = db.Column(
        JSON,
        nullable=False
    )
    background_image_id = db.Column(
        db.Integer,
        db.ForeignKey('indico.designer_image_files.id'),
        index=False,
        nullable=True
    )

    category = db.relationship(
        'Category',
        lazy=True,
        backref=db.backref(
            'designer_templates',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'designer_templates',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    background_image = db.relationship(
        'DesignerImageFile',
        lazy=True,
        foreign_keys=background_image_id,
        post_update=True
    )

    # relationship backrefs:
    # - images (DesignerImageFile.template)

    def __init__(self, **kwargs):
        data = kwargs.pop('data', None)
        tpl_type = kwargs.get('type')
        if data is None:
            data = {
                'items': [],
                'background_position': 'stretch'
            }
            size = DEFAULT_CONFIG[tpl_type]['tpl_size']
            data.update({'width': size[0], 'height': size[1]})
        super(DesignerTemplate, self).__init__(data=data, **kwargs)

    @property
    def owner(self):
        return self.event_new if self.event_new else self.category

    @locator_property
    def locator(self):
        return dict(self.owner.locator, template_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'category_id', _text=self.title)
