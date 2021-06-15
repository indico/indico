# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.util.queries import escape_like, preprocess_ts_string
from indico.util.decorators import strict_classproperty


def make_fts_index(model, column_name, db_column_name=None):
    if db_column_name is None:
        db_column_name = column_name
    return db.Index(
        f'ix_{model.__tablename__}_{db_column_name}_fts',
        db.func.to_tsvector('simple', getattr(model, column_name)),
        postgresql_using='gin'
    )


def fts_matches(column, search_string, *, exact=False):
    """Check whether a fts-indexed column matches a search string.

    To be used in a SQLAlchemy `filter` call.

    :param column: The column to search in
    :param search_string: A string to search for
    :param exact: Whether to search for the exact string
    """
    crit = db.func.to_tsvector('simple', column).match(preprocess_ts_string(search_string),
                                                       postgresql_regconfig='simple')
    if exact:
        crit = crit & column.ilike(escape_like(search_string))
    return crit


class SearchableTitleMixin:
    """Mixin to add a fulltext-searchable title column."""

    #: Whether the title column may not be empty
    title_required = True

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        args = [make_fts_index(cls, 'title')]
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
        return fts_matches(cls.title, search_string, exact=exact)
