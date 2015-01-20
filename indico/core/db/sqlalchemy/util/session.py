## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from flask_sqlalchemy import connection_stack


def update_session_options(db, session_options=None):
    """Replaces the Flask-SQLAlchemy session a new one using the given options.

    This can be used when you want a session that does not use the ZopeTransaction extension.
    """
    if session_options is None:
        session_options = {}
    session_options.setdefault(
        'scopefunc', connection_stack.__ident_func__
    )
    db.session = db.create_scoped_session(session_options)
