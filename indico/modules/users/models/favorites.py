# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.event import listens_for
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import mapper

from indico.core.db import db
from indico.util.string import return_ascii

from MaKaC.conference import CategoryManager


class FavoriteBase(object):
    __table_args__ = {'schema': 'users'}
    _type = None  #: name of the favorite; used in backref names, should be a plural form

    @declared_attr
    def user_id(cls):
        """The id of the user owning this favorite"""
        return db.Column(
            db.Integer,
            db.ForeignKey('users.users.id'),
            nullable=False,
            index=True,
            primary_key=True,
            autoincrement=False
        )

    @declared_attr
    def user(cls):
        """The user owning this favorite"""
        return db.relationship(
            'User',
            lazy=False,
            foreign_keys=lambda: [cls.user_id],
            backref=db.backref(
                '_favorite_{}'.format(cls._type),
                lazy=True,
                cascade='all, delete-orphan'
            )
        )

    @property
    def target(self):
        """The favorited object"""
        raise NotImplementedError('target property/relationship is not defined')

    @return_ascii
    def __repr__(self):
        return '<{}({}, {})>'.format(type(self).__name__, self.user_id, self.target)


class FavoriteUser(FavoriteBase, db.Model):
    __tablename__ = 'favorite_users'
    _type = 'users'

    #: the id of the favorited user
    target_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        primary_key=True,
        autoincrement=False
    )

    #: the favorited user
    target = db.relationship(
        'User',
        lazy=False,
        foreign_keys=[target_id],
        backref=db.backref(
            '_favorite_of',
            lazy=True,
            cascade='all, delete-orphan'
        )
    )


class FavoriteCategory(FavoriteBase, db.Model):
    __tablename__ = 'favorite_categories'
    _type = 'categories'

    #: the id of the favorited category
    target_id = db.Column(
        db.String,
        nullable=False,
        primary_key=True
    )

    @property
    def target(self):
        """The favorited category"""
        try:
            return CategoryManager().getById(self.target_id)
        except KeyError:
            return None

    @target.setter
    def target(self, value):
        self.target_id = value.id


@listens_for(mapper, 'after_configured')
def _add_association_proxies():
    """Create association proxies in the related classes of each favorite.

    This is done in a central place so the User model itself doesn't have to be modified
    when adding new favorite types.
    """
    for name, cls in db.Model._decl_class_registry.iteritems():
        if getattr(cls, '__table__', None) is None or not issubclass(cls, FavoriteBase):
            continue
        # User.favorite_XXX
        attr = 'favorite_{}'.format(cls._type)
        setattr(cls.user.mapper.class_, attr,
                association_proxy('_' + attr, 'target', creator=lambda x, cls=cls: cls(target=x)))
        # Whatever.favorite_of - if Whatever is already in the DB, and not e.g. a ZODB object
        if hasattr(cls.target, 'mapper'):
            assert not hasattr(cls.target.mapper.class_, 'favorite_of')
            setattr(cls.target.mapper.class_, 'favorite_of',
                    association_proxy('_favorite_of', 'user', creator=lambda x, cls=cls: cls(user=x)))
