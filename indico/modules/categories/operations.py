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

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.categories import logger
from indico.modules.categories.models.categories import Category


def create_category(parent, data):
    category = Category(parent=parent)
    data.setdefault('default_event_themes', parent.default_event_themes)
    data.setdefault('timezone', parent.timezone)
    category.populate_from_dict(data)
    db.session.add(category)
    db.session.flush()
    signals.category.created.send(category)
    logger.info('Category %s created by %s', category, session.user)
    return category


def delete_category(category):
    category.is_deleted = True
    db.session.flush()
    signals.category.deleted.send(category)
    logger.info('Category %s deleted by %s', category, session.user)


def move_category(category, target_category):
    category.move(target_category)
    logger.info('Category %s moved to %s by %s', category, target_category, session.user)


def update_category(category, data, skip=()):
    category.populate_from_dict(data, skip=skip)
    db.session.flush()
    signals.category.updated.send(category)
    logger.info('Category %s updated by %s', category, session.user)
