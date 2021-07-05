# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from authlib.common.security import generate_token
from authlib.oauth2.rfc6749 import list_to_scope
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.oauth.models.tokens import TokenModelBase
from indico.util.date_time import now_utc


class PersonalToken(TokenModelBase):
    """Personal access tokens."""

    __tablename__ = 'tokens'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_user_id_name_lower', cls.user_id, db.func.lower(cls.name), unique=True,
                         postgresql_where=db.text('revoked_dt IS NULL')),
                {'schema': 'users'})

    user_id = db.Column(
        db.ForeignKey('users.users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    revoked_dt = db.Column(
        UTCDateTime,
        nullable=True
    )

    user = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'personal_tokens',
            lazy='dynamic',
            cascade='all, delete-orphan',
            passive_deletes=True
        )
    )

    def __repr__(self):  # pragma: no cover
        return f'<PersonalToken({self.id}, {self.user_id}, {self.name}, {self.scopes})>'

    def check_client(self, client):
        # we do not belong to any client, so API-based introspection or revocation is not allowed
        raise NotImplementedError('this should never get called for personal tokens')

    def get_scope(self):
        # scopes are restricted by what's authorized for the particular user and what's whitelisted for the app
        return list_to_scope(sorted(self.scopes))

    def is_revoked(self):
        return self.revoked_dt is not None or self.user.is_blocked or self.user.is_deleted

    def generate_token(self):
        """Generate a new token string."""
        from indico.core.oauth.util import TOKEN_PREFIX_PERSONAL
        access_token = TOKEN_PREFIX_PERSONAL + generate_token(42)
        self.access_token = access_token
        return access_token

    def revoke(self):
        """Mark the token as revoked."""
        if self.revoked_dt is None:
            self.revoked_dt = now_utc()
