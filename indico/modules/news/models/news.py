# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii, slugify
from indico.web.flask.util import url_for


class NewsItem(db.Model):
    __tablename__ = 'news'
    __table_args__ = {'schema': 'indico'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    content = db.Column(
        db.Text,
        nullable=False
    )

    @locator_property
    def locator(self):
        return {'news_id': self.id}

    @locator.anchor_only
    def locator(self):
        return {'_anchor': self.anchor}

    @locator.slugged
    def locator(self):
        return {'news_id': self.id, 'slug': self.slug}

    @property
    def anchor(self):
        return 'news-{}'.format(self.id)

    @property
    def url(self):
        return url_for('news.display_item', self, slug=self.slug)

    @property
    def slug(self):
        return slugify(self.title, fallback=None)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.title)
