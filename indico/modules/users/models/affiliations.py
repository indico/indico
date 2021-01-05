# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.unaccent import define_unaccented_lowercase_index
from indico.util.string import return_ascii


class UserAffiliation(db.Model):
    __tablename__ = 'affiliations'
    __table_args__ = {'schema': 'users'}

    #: the unique id of the affiliations
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: the id of the associated user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )

    #: the affiliation
    name = db.Column(
        db.String,
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - user (User._affiliation)

    @return_ascii
    def __repr__(self):
        return '<UserAffiliation({}, {}, {})>'.format(self.id, self.name, self.user)


define_unaccented_lowercase_index(UserAffiliation.name)
