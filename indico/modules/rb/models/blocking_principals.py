# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args


class BlockingPrincipal(PrincipalMixin, db.Model):
    __tablename__ = 'blocking_principals'
    principal_backref_name = 'in_blocking_acls'
    unique_columns = ('blocking_id',)

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='roombooking')

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    blocking_id = db.Column(
        db.Integer,
        db.ForeignKey('roombooking.blockings.id'),
        nullable=False
    )

    # relationship backrefs:
    # - blocking (Blocking._allowed)

    def __repr__(self):
        return '<BlockingPrincipal({}, {}, {})>'.format(
            self.id,
            self.blocking_id,
            self.principal
        )
