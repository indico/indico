# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db


class LegacyCategoryMapping(db.Model):
    """Legacy category ID mapping.

    Legacy categories have non-numeric IDs which are not supported by
    any new code. This mapping maps them to proper integer IDs to
    avoid breaking things.
    """

    __tablename__ = 'legacy_id_map'
    __table_args__ = {'schema': 'categories'}

    legacy_category_id = db.Column(
        db.String,
        primary_key=True,
        index=True
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        index=True,
        primary_key=True,
        autoincrement=False
    )

    category = db.relationship(
        'Category',
        lazy=True,
        backref=db.backref(
            'legacy_mapping',
            uselist=False,
            lazy=True
        )
    )

    def __repr__(self):
        return f'<LegacyCategoryMapping({self.legacy_category_id}, {self.category_id})>'
