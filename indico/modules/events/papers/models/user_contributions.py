# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.core.db import db


_paper_judges = db.Table(
    'judges',
    db.metadata,
    db.Column(
        'contribution_id',
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_paper_reviewing'
)


_paper_content_reviewers = db.Table(
    'content_reviewers',
    db.metadata,
    db.Column(
        'contribution_id',
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_paper_reviewing'
)


_paper_layout_reviewers = db.Table(
    'layout_reviewers',
    db.metadata,
    db.Column(
        'contribution_id',
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        autoincrement=False,
        index=True
    ),
    schema='event_paper_reviewing'
)
