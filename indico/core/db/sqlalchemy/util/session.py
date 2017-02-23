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

from functools import wraps

from flask_sqlalchemy import connection_stack

from indico.core.db import db


def update_session_options(db, session_options=None):
    """Replace the Flask-SQLAlchemy session with a new one using the given options."""
    if session_options is None:
        session_options = {}
    session_options.setdefault('scopefunc', connection_stack.__ident_func__)
    db.session = db.create_scoped_session(session_options)


def no_autoflush(fn):
    """Wraps the decorated function in a no-autoflush block"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with db.session.no_autoflush:
            return fn(*args, **kwargs)
    return wrapper
