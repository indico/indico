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

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import escape_like, preprocess_ts_string
from indico.util.decorators import strict_classproperty


class SearchableTitleMixin(object):
    """Mixin to add a fulltext-searchable title column."""

    #: Whether the title column may not be empty
    title_required = True

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        args = [
            db.Index('ix_{}_title_fts'.format(cls.__tablename__), db.func.to_tsvector('simple', cls.title),
                     postgresql_using='gin')
        ]
        if cls.title_required:
            args.append(db.CheckConstraint("title != ''", 'valid_title'))
        return tuple(args)

    @declared_attr
    def title(cls):
        return db.Column(
            db.String,
            nullable=False
        )

    @classmethod
    def title_matches(cls, search_string, exact=False):
        """Check whether the title matches a search string.

        To be used in a SQLAlchemy `filter` call.

        :param search_string: A string to search for
        :param exact: Whether to search for the exact string
        """
        crit = db.func.to_tsvector('simple', cls.title).match(preprocess_ts_string(search_string),
                                                              postgresql_regconfig='simple')
        if exact:
            crit = crit & cls.title.ilike('%{}%'.format(escape_like(search_string)))
        return crit
