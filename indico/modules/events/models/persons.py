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

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db.sqlalchemy import db, PyIntEnum
from indico.core.db.sqlalchemy.util.models import auto_table_args, override_attr
from indico.modules.users.models.users import UserTitle, PersonMixin
from indico.util.decorators import strict_classproperty
from indico.util.string import return_ascii, format_repr


class EventPerson(PersonMixin, db.Model):
    """A person inside an event, e.g. a speaker/author etc."""

    __tablename__ = 'persons'
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id'),
                      db.Index(None, 'event_id', 'email', unique=True, postgresql_where=db.text("email != ''")),
                      {'schema': 'events'})

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
            cascade_backrefs=False,
            lazy='dynamic'
        )
    )
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'event_persons',
            cascade_backrefs=False,
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - contribution_links (ContributionPersonLink.person)
    # - event_links (EventPersonLink.person)
    # - session_block_links (SessionBlockPersonLink.person)
    # - subcontribution_links (SubContributionPersonLink.person)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.full_name)

    @classmethod
    def create_from_user(cls, user, event):
        return EventPerson(user=user, event_new=event, first_name=user.first_name, last_name=user.last_name,
                           email=user.email, affiliation=user.affiliation, address=user.address, phone=user.phone)

    @classmethod
    def for_user(cls, user, event):
        """Return EventPerson for a matching User in Event creating if needed"""
        person = event.persons.filter_by(user=user).first()
        return person or cls.create_from_user(user, event)

    def has_role(self, role, obj):
        """Whether the person has a role in the ACL list of a given object"""
        principals = [x for x in obj.acl_entries if x.has_management_role(role, explicit=True)]
        return any(x for x in principals if self.user_id == x.user_id or self.email == x.email)


class PersonLinkBase(PersonMixin, db.Model):
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
    def _first_name(cls):
        return db.Column(
            'first_name',
            db.String,
            nullable=True
        )

    @declared_attr
    def _last_name(cls):
        return db.Column(
            'last_name',
            db.String,
            nullable=True
        )

    @declared_attr
    def _title(cls):
        return db.Column(
            'title',
            PyIntEnum(UserTitle),
            nullable=True
        )

    @declared_attr
    def _affiliation(cls):
        return db.Column(
            'affiliation',
            db.String,
            nullable=True
        )

    @declared_attr
    def _address(cls):
        return db.Column(
            'address',
            db.Text,
            nullable=True
        )

    @declared_attr
    def _phone(cls):
        return db.Column(
            'phone',
            db.String,
            nullable=True
        )

    @declared_attr
    def person(cls):
        return db.relationship(
            'EventPerson',
            lazy=False,
            backref=db.backref(
                cls.person_link_backref_name,
                cascade='all, delete-orphan',
                cascade_backrefs=False,
                lazy='dynamic'
            )
        )

    first_name = override_attr('first_name', 'person')
    last_name = override_attr('last_name', 'person')
    title = override_attr('title', 'person', fget=lambda self, __: self._get_title())
    affiliation = override_attr('affiliation', 'person')
    address = override_attr('address', 'person')
    phone = override_attr('phone', 'person')

    def __init__(self, *args, **kwargs):
        # Needed in order to ensure `person` is set before the overridable attrs
        self.person = kwargs.pop('person', None)
        super(PersonLinkBase, self).__init__(*args, **kwargs)


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
        return format_repr(self, 'event_id', 'person_id', _text=self.full_name)
