# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime

from sqlalchemy.dialects.postgresql import INET, JSONB
from werkzeug.datastructures import MultiDict

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import as_utc, now_utc
from indico.util.passwords import PasswordProperty


class Identity(db.Model):
    """Identities of Indico users."""
    __tablename__ = 'identities'
    __table_args__ = (db.UniqueConstraint('provider', 'identifier'),
                      {'schema': 'users'})

    #: the unique id of the identity
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: the id of the user this identity belongs to
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False
    )
    #: the provider name of the identity
    provider = db.Column(
        db.String,
        nullable=False
    )
    #: the unique identifier of the user within its provider
    identifier = db.Column(
        db.String,
        nullable=False
    )
    #: internal data used by the flask-multipass system
    multipass_data = db.Column(
        JSONB,
        nullable=False,
        default=lambda: None
    )
    #: the user data from the user provider
    _data = db.Column(
        'data',
        JSONB,
        nullable=False,
        default={}
    )
    #: the hash of the password in case of a local identity
    password_hash = db.Column(
        db.String
    )
    #: the password of the user in case of a local identity
    password = PasswordProperty('password_hash')
    #: the timestamp of the latest login
    last_login_dt = db.Column(
        UTCDateTime
    )
    #: the ip address that was used for the latest login
    last_login_ip = db.Column(
        INET
    )

    # relationship backrefs:
    # - user (User.identities)

    @property
    def data(self):
        data = MultiDict()
        data.update(self._data)
        return data

    @data.setter
    def data(self, data):
        self._data = dict(data.lists())

    @property
    def locator(self):
        return {'identity': self.id}

    @property
    def safe_last_login_dt(self):
        """last_login_dt that is safe for sorting (no None values)."""
        return self.last_login_dt or as_utc(datetime(1970, 1, 1))

    def register_login(self, ip):
        """Update the last login information."""
        self.last_login_dt = now_utc()
        self.last_login_ip = ip

    def __repr__(self):
        return f'<Identity({self.id}, {self.user_id}, {self.provider}, {self.identifier})>'
