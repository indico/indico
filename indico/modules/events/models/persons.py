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

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db.sqlalchemy import db, PyIntEnum
from indico.core.db.sqlalchemy.util.models import auto_table_args, get_default_values
from indico.modules.users.models.users import UserTitle
from indico.util.decorators import strict_classproperty
from indico.util.string import return_ascii, format_repr, format_full_name


class EventPerson(db.Model):
    """A person inside an event, e.g. a speaker/author etc."""

    __tablename__ = 'persons'
    __table_args__ = {'schema': 'events'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=True,
        index=True
    )
    first_name = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    last_name = db.Column(
        db.String,
        nullable=False
    )
    email = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    # the title of the user - you usually want the `title` property!
    _title = db.Column(
        'title',
        PyIntEnum(UserTitle),
        nullable=False,
        default=UserTitle.none
    )
    affiliation = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    address = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    phone = db.Column(
        db.String,
        nullable=False,
        default=''
    )

    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'persons',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'event_persons',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - contribution_links (ContributionPersonLink.person)
    # - event_links (EventPersonLink.person)
    # - session_block_links (SessionBlockPersonLink.person)
    # - subcontribution_links (SubContributionPersonLink.person)

    @hybrid_property
    def title(self):
        """the title of the person"""
        if self._title is None:
            return get_default_values(type(self))['_title'].title
        return self._title.title

    @title.expression
    def title(cls):
        return cls._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def full_name(self):
        """Returns the person's name in 'Firstname Lastname' notation."""
        return self.get_full_name(last_name_first=False, last_name_upper=False, abbrev_first_name=False)

    def get_full_name(self, last_name_first=True, last_name_upper=True, abbrev_first_name=True, show_title=False):
        """Returns the person's name in the specified notation.

        Note: Do not use positional arguments when calling this method.
        Always use keyword arguments!

        :param last_name_first: if "lastname, firstname" instead of
                                "firstname lastname" should be used
        :param last_name_upper: if the last name should be all-uppercase
        :param abbrev_first_name: if the first name should be abbreviated to
                                  use only the first character
        :param show_title: if the title of the person should be included
        """
        return format_full_name(self.first_name, self.last_name, self.title,
                                last_name_first=last_name_first, last_name_upper=last_name_upper,
                                abbrev_first_name=abbrev_first_name, show_title=show_title)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.full_name)


class PersonLinkBase(db.Model):
    """Base class for EventPerson associations."""

    __abstract__ = True
    #: The name of the backref on the `EventPerson`
    person_link_backref_name = None
    #: The columns which should be included in the unique constraint.
    person_link_unique_columns = None

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        return (db.UniqueConstraint('person_id', *cls.person_link_unique_columns),)

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='events')

    @declared_attr
    def person_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('events.persons.id'),
            primary_key=True,
            index=True
        )

    @declared_attr
    def person(cls):
        return db.relationship(
            'EventPerson',
            lazy=False,
            backref=db.backref(
                cls.person_link_backref_name,
                cascade='all, delete-orphan',
                lazy='dynamic'
            )
        )


class EventPersonLink(PersonLinkBase):
    """Association between EventPerson and Event.

    Chairperson or speaker (lecture)
    """

    __tablename__ = 'event_person_links'
    __auto_table_args = {'schema': 'events'}
    person_link_backref_name = 'event_links'
    person_link_unique_columns = ('event_id',)

    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        primary_key=True,
        index=True
    )

    # relationship backrefs:
    # - event (Event.person_links)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'event_id', 'person_id', _text=self.person.full_name)
