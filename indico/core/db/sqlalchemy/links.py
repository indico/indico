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

from sqlalchemy.ext.hybrid import hybrid_property, Comparator

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.decorators import strict_classproperty
from indico.util.struct.enum import IndicoEnum


class LinkType(int, IndicoEnum):
    category = 1
    event = 2
    contribution = 3
    subcontribution = 4
    session = 5


_all_columns = {'category_id', 'event_id', 'contribution_id', 'subcontribution_id', 'session_id'}
_columns_for_types = {
    LinkType.category: {'category_id'},
    LinkType.event: {'event_id'},
    LinkType.contribution: {'event_id', 'contribution_id'},
    LinkType.subcontribution: {'event_id', 'contribution_id', 'subcontribution_id'},
    LinkType.session: {'event_id', 'session_id'},
}


def _make_checks(allowed_link_types):
    disallowed_link_types = set(LinkType) - allowed_link_types
    if disallowed_link_types:
        yield db.CheckConstraint(
            'link_type NOT IN ({})'.format(','.join(unicode(x.value) for x in disallowed_link_types)),
            'allowed_link_type'
        )
    for link_type in allowed_link_types:
        required_cols = _all_columns & _columns_for_types[link_type]
        forbidden_cols = _all_columns - required_cols
        criteria = ['{} IS NULL'.format(col) for col in forbidden_cols]
        criteria += ['{} IS NOT NULL'.format(col) for col in required_cols]
        condition = 'link_type != {} OR ({})'.format(link_type, ' AND '.join(criteria))
        yield db.CheckConstraint(condition, 'valid_{}_link'.format(link_type.name))


def _make_uniques(allowed_link_types, extra_criteria=None):
    for link_type in allowed_link_types:
        where = ['link_type = {}'.format(link_type.value)]
        if extra_criteria is not None:
            where += list(extra_criteria)
        yield db.Index(None, *_columns_for_types[link_type], unique=True,
                       postgresql_where=db.text(' AND '.join(where)))


class LinkMixin(object):
    #: The link types that are supported.  Can be overridden in the
    #: model using the mixin.  Affects the table structure, so any
    #: changes to it should go along with a migration step!
    allowed_link_types = frozenset(LinkType)
    #: If only one link per object should be allowed.  This may also
    #: be a string containing an SQL string to specify the criterion
    #: for the unique index to be applied, e.g. ``'is_foo = true'``.
    unique_links = False

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        args = tuple(_make_checks(cls.allowed_link_types))
        if cls.unique_links:
            extra_criteria = [cls.unique_links] if isinstance(cls.unique_links, basestring) else None
            args = args + tuple(_make_uniques(cls.allowed_link_types, extra_criteria))
        return args

    link_type = db.Column(
        PyIntEnum(LinkType),
        nullable=False
    )
    category_id = db.Column(
        db.Integer,
        nullable=True,
        index=True
    )
    event_id = db.Column(
        db.Integer,
        nullable=True,
        index=True
    )
    session_id = db.Column(
        db.String,
        nullable=True
    )
    contribution_id = db.Column(
        db.String,
        nullable=True
    )
    subcontribution_id = db.Column(
        db.String,
        nullable=True
    )

    @hybrid_property
    def linked_object(self):
        """Returns the linked object."""
        from MaKaC.conference import CategoryManager, ConferenceHolder
        if self.link_type == LinkType.category:
            return CategoryManager().getById(self.category_id, True)
        event = ConferenceHolder().getById(self.event_id, True)
        if event is None:
            return None
        if self.link_type == LinkType.event:
            return event
        elif self.link_type == LinkType.session:
            return event.getSessionById(self.session_id)
        elif self.link_type == LinkType.contribution:
            return event.getContributionById(self.contribution_id)
        elif self.link_type == LinkType.subcontribution:
            contribution = event.getContributionById(self.contribution_id)
            if contribution is None:
                return None
            return contribution.getSubContributionById(self.subcontribution_id)

    @linked_object.setter
    def linked_object(self, obj):
        from MaKaC.conference import Category, Conference, Contribution, SubContribution, Session
        self.category_id = self.event_id = self.session_id = self.contribution_id = self.subcontribution_id = None
        if isinstance(obj, Category):
            self.link_type = LinkType.category
            self.category_id = int(obj.id)
        elif isinstance(obj, Conference):
            self.link_type = LinkType.event
            self.event_id = int(obj.id)
        elif isinstance(obj, Session):
            self.link_type = LinkType.session
            self.event_id = int(obj.getConference().id)
            self.session_id = obj.id
        elif isinstance(obj, Contribution):
            self.link_type = LinkType.contribution
            self.event_id = int(obj.getConference().id)
            self.contribution_id = obj.id
        elif isinstance(obj, SubContribution):
            self.link_type = LinkType.subcontribution
            self.event_id = int(obj.getConference().id)
            self.contribution_id = obj.getContribution().id
            self.subcontribution_id = obj.id
        else:
            raise ValueError('Unexpected object type {}: {}'.format(type(obj), obj))

    @linked_object.comparator
    def linked_object(cls):
        return LinkedObjectComparator(cls)

    @property
    def link_repr(self):
        info = [('link_type', self.link_type.name if self.link_type is not None else 'None')]
        info.extend((key, getattr(self, key)) for key in _all_columns if getattr(self, key)is not None)
        return ', '.join('{}={}'.format(key, value) for key, value in info)


class LinkedObjectComparator(Comparator):
    def __init__(self, cls):
        self.cls = cls

    def __clause_element__(self):
        # just in case
        raise NotImplementedError

    def __eq__(self, other):
        from MaKaC.conference import Category, Conference, Contribution, SubContribution, Session
        if isinstance(other, Category):
            return db.and_(self.cls.link_type == LinkType.category,
                           self.cls.category_id == int(other.id))
        elif isinstance(other, Conference):
            return db.and_(self.cls.link_type == LinkType.event,
                           self.cls.event_id == int(other.id))
        elif isinstance(other, Session):
            return db.and_(self.cls.link_type == LinkType.session,
                           self.cls.event_id == int(other.getConference().id),
                           self.cls.session_id == other.id)
        elif isinstance(other, Contribution):
            return db.and_(self.cls.link_type == LinkType.contribution,
                           self.cls.event_id == int(other.getConference().id),
                           self.cls.contribution_id == other.id)
        elif isinstance(other, SubContribution):
            return db.and_(self.cls.link_type == LinkType.subcontribution,
                           self.cls.event_id == int(other.getConference().id),
                           self.cls.contribution_id == other.getContribution().id,
                           self.cls.subcontribution_id == other.id)
        else:
            raise ValueError('Unexpected object type {}: {}'.format(type(other), other))
