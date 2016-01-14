# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from functools import partial
from itertools import chain

from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declared_attr
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


_all_columns = {'category_id', 'linked_event_id', 'contribution_id', 'subcontribution_id', 'session_id'}
_columns_for_types = {
    LinkType.category: {'category_id'},
    LinkType.event: {'linked_event_id'},
    LinkType.contribution: {'contribution_id'},
    LinkType.subcontribution: {'subcontribution_id'},
    LinkType.session: {'session_id'},
}


def _make_checks(allowed_link_types):
    available_columns = set(chain.from_iterable(cols for type_, cols in _columns_for_types.iteritems()
                                                if type_ in allowed_link_types))
    yield db.CheckConstraint('(event_id IS NULL) = (link_type = {})'.format(LinkType.category), 'valid_event_id')
    for link_type in allowed_link_types:
        required_cols = available_columns & _columns_for_types[link_type]
        forbidden_cols = available_columns - required_cols
        criteria = ['{} IS NULL'.format(col) for col in sorted(forbidden_cols)]
        criteria += ['{} IS NOT NULL'.format(col) for col in sorted(required_cols)]
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
    #: The name of the backref that's added to the Event model to
    #: access *all* linked objects
    events_backref_name = None
    #: The name of the backref that's added to the linked objects
    link_backref_name = None
    #: The laziness of the backref that's added to the linked objects
    link_backref_lazy = True

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        args = tuple(_make_checks(cls.allowed_link_types))
        if cls.unique_links:
            extra_criteria = [cls.unique_links] if isinstance(cls.unique_links, basestring) else None
            args = args + tuple(_make_uniques(cls.allowed_link_types, extra_criteria))
        return args

    @classmethod
    def register_link_events(cls):
        """Registers sqlalchemy events needed by this mixin.

        Call this method after the definition of a model which uses
        this mixin class.
        """
        event_mapping = {cls.session: lambda x: x.event_new,
                         cls.contribution: lambda x: x.event_new,
                         cls.subcontribution: lambda x: x.contribution.event_new,
                         cls.linked_event: lambda x: x}

        type_mapping = {cls.category_id: LinkType.category,
                        cls.linked_event: LinkType.event,
                        cls.session: LinkType.session,
                        cls.contribution: LinkType.contribution,
                        cls.subcontribution: LinkType.subcontribution}

        def _set_link_type(link_type, target, value, *unused):
            if value is not None:
                target.link_type = link_type

        def _set_event_obj(fn, target, value, *unused):
            if value is not None:
                event = fn(value)
                assert event is not None
                target.event_new = event

        for rel, fn in event_mapping.iteritems():
            if rel is not None:
                listen(rel, 'set', partial(_set_event_obj, fn))

        for rel, link_type in type_mapping.iteritems():
            if rel is not None:
                listen(rel, 'set', partial(_set_link_type, link_type))

    @declared_attr
    def link_type(cls):
        return db.Column(
            PyIntEnum(LinkType, exclude_values=set(LinkType) - cls.allowed_link_types),
            nullable=False
        )

    @declared_attr
    def category_id(cls):
        if LinkType.category in cls.allowed_link_types:
            return db.Column(
                db.Integer,
                nullable=True,
                index=True
            )

    @declared_attr
    def event_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('events.events.id'),
            nullable=True,
            index=True
        )

    @declared_attr
    def linked_event_id(cls):
        if LinkType.event in cls.allowed_link_types:
            return db.Column(
                db.Integer,
                db.ForeignKey('events.events.id'),
                nullable=True,
                index=True
            )

    @declared_attr
    def session_id(cls):
        if LinkType.session in cls.allowed_link_types:
            return db.Column(
                db.Integer,
                db.ForeignKey('events.sessions.id'),
                nullable=True,
                index=True
            )

    @declared_attr
    def contribution_id(cls):
        if LinkType.contribution in cls.allowed_link_types:
            return db.Column(
                db.Integer,
                db.ForeignKey('events.contributions.id'),
                nullable=True,
                index=True
            )

    @declared_attr
    def subcontribution_id(cls):
        if LinkType.subcontribution in cls.allowed_link_types:
            return db.Column(
                db.Integer,
                db.ForeignKey('events.subcontributions.id'),
                nullable=True,
                index=True
            )

    @declared_attr
    def event_new(cls):
        return db.relationship(
            'Event',
            foreign_keys=cls.event_id,
            lazy=True,
            backref=db.backref(
                cls.events_backref_name,
                lazy='dynamic'
            )
        )

    @declared_attr
    def linked_event(cls):
        if LinkType.event in cls.allowed_link_types:
            return db.relationship(
                'Event',
                foreign_keys=cls.linked_event_id,
                lazy=True,
                backref=db.backref(
                    cls.link_backref_name,
                    cascade='all, delete-orphan',
                    uselist=(cls.unique_links != True),  # noqa
                    lazy=cls.link_backref_lazy
                )
            )

    @declared_attr
    def session(cls):
        if LinkType.session in cls.allowed_link_types:
            return db.relationship(
                'Session',
                lazy=True,
                backref=db.backref(
                    cls.link_backref_name,
                    cascade='all, delete-orphan',
                    uselist=(cls.unique_links != True),  # noqa
                    lazy=cls.link_backref_lazy
                )
            )

    @declared_attr
    def contribution(cls):
        if LinkType.contribution in cls.allowed_link_types:
            return db.relationship(
                'Contribution',
                lazy=True,
                backref=db.backref(
                    cls.link_backref_name,
                    cascade='all, delete-orphan',
                    uselist=(cls.unique_links != True),  # noqa
                    lazy=cls.link_backref_lazy
                )
            )

    @declared_attr
    def subcontribution(cls):
        if LinkType.subcontribution in cls.allowed_link_types:
            return db.relationship(
                'SubContribution',
                lazy=True,
                backref=db.backref(
                    cls.link_backref_name,
                    cascade='all, delete-orphan',
                    uselist=(cls.unique_links != True),  # noqa
                    lazy=cls.link_backref_lazy
                )
            )

    @hybrid_property
    def object(self):
        from MaKaC.conference import CategoryManager
        if self.link_type == LinkType.category:
            return CategoryManager().getById(self.category_id, True)
        elif self.link_type == LinkType.event:
            return self.event_new
        elif self.link_type == LinkType.session:
            return self.session
        elif self.link_type == LinkType.contribution:
            return self.contribution
        elif self.link_type == LinkType.subcontribution:
            return self.subcontribution

    @object.setter
    def object(self, obj):
        from MaKaC.conference import Category
        self.category = self.event_new = self.session = self.contribution = self.subcontribution = None
        if isinstance(obj, Category):
            self.category_id = int(obj.id)
        elif isinstance(obj, db.m.Event):
            self.linked_event = obj
        elif isinstance(obj, db.m.Session):
            self.session = obj
        elif isinstance(obj, db.m.Contribution):
            self.contribution = obj
        elif isinstance(obj, db.m.SubContribution):
            self.subcontribution = obj
        else:
            raise TypeError('Unexpected object: {}'.format(obj))

    @object.comparator
    def object(cls):
        return LinkedObjectComparator(cls)

    @property
    def link_repr(self):
        """A kwargs-style string suitable for the object's repr"""
        info = [('link_type', self.link_type.name if self.link_type is not None else 'None')]
        info.extend((key, getattr(self, key)) for key in _all_columns if getattr(self, key)is not None)
        return ', '.join('{}={}'.format(key, value) for key, value in info)

    @property
    def link_event_log_data(self):
        """
        Returns a dict containing information about the linked object
        suitable for the event log.

        It does not return any information for an object linked to a
        category or the event itself.
        """
        data = {}
        if self.link_type == LinkType.session:
            data['Session'] = self.session.title
        elif self.link_type == LinkType.contribution:
            data['Contribution'] = self.contribution.title
        elif self.link_type == LinkType.subcontribution:
            data['Contribution'] = self.subcontribution.contribution.title
            data['Subcontribution'] = self.subcontribution.title
        return data


class LinkedObjectComparator(Comparator):
    def __init__(self, cls):
        self.cls = cls

    def __clause_element__(self):
        # just in case
        raise NotImplementedError

    def __eq__(self, other):
        from MaKaC.conference import Category
        if isinstance(other, Category):
            return db.and_(self.cls.link_type == LinkType.category,
                           self.cls.category_id == int(other.id))
        elif isinstance(other, db.m.Event):
            return db.and_(self.cls.link_type == LinkType.event,
                           self.cls.linked_event_id == other.id)
        elif isinstance(other, db.m.Session):
            return db.and_(self.cls.link_type == LinkType.session,
                           self.cls.session_id == other.id)
        elif isinstance(other, db.m.Contribution):
            return db.and_(self.cls.link_type == LinkType.contribution,
                           self.cls.contribution_id == other.id)
        elif isinstance(other, db.m.SubContribution):
            return db.and_(self.cls.link_type == LinkType.subcontribution,
                           self.cls.subcontribution_id == other.id)
        else:
            raise ValueError('Unexpected object type {}: {}'.format(type(other), other))
