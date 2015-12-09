# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import csv
from io import BytesIO

from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.colors import ColorTuple
from indico.modules.events.sessions.models.sessions import Session


def get_colors():
    return [
        ColorTuple('#1D041F', '#EEE0EF'),
        ColorTuple('#253F08', '#E3F2D3'),
        ColorTuple('#1F1F02', '#FEFFBF'),
        ColorTuple('#202020', '#DFE555'),
        ColorTuple('#1F1D04', '#FFEC1F'),
        ColorTuple('#0F264F', '#DFEBFF'),
        ColorTuple('#EFF5FF', '#0D316F'),
        ColorTuple('#F1FFEF', '#1A3F14'),
        ColorTuple('#FFFFFF', '#5F171A'),
        ColorTuple('#272F09', '#D9DFC3'),
        ColorTuple('#FFEFFF', '#4F144E'),
        ColorTuple('#FFEDDF', '#6F390D'),
        ColorTuple('#021F03', '#8EC473'),
        ColorTuple('#03070F', '#92B6DB'),
        ColorTuple('#151515', '#DFDFDF'),
        ColorTuple('#1F1100', '#ECC495'),
        ColorTuple('#0F0202', '#B9CBCA'),
        ColorTuple('#0D1E1F', '#C2ECEF'),
        ColorTuple('#000000', '#D0C296'),
        ColorTuple('#202020', '#EFEBC2')
    ]


def get_active_sessions(event):
    return (event.sessions
            .filter_by(is_deleted=False)
            .order_by(db.func.lower(Session.title))
            .all())


def can_manage_sessions(user, event, role=None):
    """Check whether a user can manage any sessions in an event"""
    return event.can_manage(user) or any(s.can_manage(user, role)
                                         for s in event.sessions.options(joinedload('acl_entries')))


def generate_csv_from_sessions(sessions):
    """Generate a CSV file from a given session list.

    :param sessions: The list of sessions to include in the file
    """
    column_names = ['ID', 'Title', 'Description', 'Code']
    buf = BytesIO()
    writer = csv.DictWriter(buf, fieldnames=column_names)
    writer.writeheader()
    for sess in sessions:
        row = {'ID': sess.friendly_id, 'Title': sess.title.encode('utf-8'),
               'Description': sess.description.encode('utf-8'), 'Code': sess.code.encode('utf-8')}
        writer.writerow(row)
    buf.seek(0)
    return buf
