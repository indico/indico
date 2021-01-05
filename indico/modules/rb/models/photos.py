# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.util.string import return_ascii


class Photo(db.Model):
    __tablename__ = 'photos'
    __table_args__ = {'schema': 'roombooking'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    data = db.Column(
        db.LargeBinary,
        nullable=True
    )

    # relationship backrefs:
    # - room (Room.photo)

    @return_ascii
    def __repr__(self):
        return u'<Photo({0})>'.format(self.id)
