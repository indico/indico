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
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import noload

from indico.core.db.sqlalchemy import db, PyIntEnum
from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.core.db.sqlalchemy.util.models import auto_table_args, override_attr
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.users.models.users import UserTitle, PersonMixin
from indico.util.decorators import strict_classproperty
from indico.util.string import return_ascii, format_repr


class PersonLinkDataMixin(object):
    @property
    def person_link_data(self):
        return {x: x.is_submitter for x in self.person_links}

    @person_link_data.setter
    @no_autoflush
    def person_link_data(self, value):
        self.person_links = value.keys()
        for person_link, is_submitter in value.iteritems():
            person = person_link.person
            principal = person.user if person.user is not None else EmailPrincipal(person.email)
            action = {'add_roles': {'submit'}} if is_submitter else {'del_roles': {'submit'}}
            self.update_principal(principal, **action)


class EventPerson(PersonMixin, db.Model):
    """A person inside an event, e.g. a speaker/author etc."""

    __tablename__ = 'persons'
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id'),
                      db.CheckConstraint('email = lower(email)', 'lowercase_email'),
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
        index=True,
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

    @classmethod
    def link_user_by_email(cls, user):
        """
        Links all email-based persons matching the user's
        email addresses with the user.

        :param user: A User object.
        """
        from indico.modules.events.models.events import Event
        query = (cls.query
                 .options(noload('*'))
                 .join(EventPerson.event_new)
                 .filter(~Event.is_deleted,
                         cls.email.in_(user.all_emails),
                         cls.user_id.is_(None)))
        for event_person in query:
            existing = (cls.query
                        .options(noload('*'))
                        .filter_by(user_id=user.id, event_id=event_person.event_id)
                        .one_or_none())
            if existing is None:
                event_person.user = user
            else:
                existing.merge_person_info(event_person)
                db.session.delete(event_person)
        db.session.flush()

    def merge_person_info(self, other):
        from indico.modules.events.contributions.models.persons import AuthorType
        for column_name in {'_title', 'affiliation', 'address', 'phone', 'first_name', 'last_name'}:
            value = getattr(self, column_name) or getattr(other, column_name)
            setattr(self, column_name, value)

        def _get_author_type(src_link, dest_link):
            if AuthorType.primary in (src_link.author_type, dest_link.author_type):
                return AuthorType.primary
            elif src_link.author_type == AuthorType.none:
                return dest_link.author_type
            else:
                return src_link.author_type

        for event_link in other.event_links:
            existing_event_link = self.event_links.filter_by(event_id=event_link.event_id).one_or_none()
            if existing_event_link is None:
                event_link.person = self
            else:
                db.session.delete(event_link)

        for contribution_link in other.contribution_links:
            existing_contribution_link = (self.contribution_links
                                          .filter_by(contribution_id=contribution_link.contribution_id)
                                          .one_or_none())
            if existing_contribution_link is None:
                contribution_link.person = self
            else:
                existing_contribution_link.is_speaker |= contribution_link.is_speaker
                existing_contribution_link.author_type = _get_author_type(existing_contribution_link, contribution_link)
                db.session.delete(contribution_link)

        for subcontribution_link in other.subcontribution_links:
            existing_subcontribution_link = (self.subcontribution_links
                                             .filter_by(subcontribution_id=subcontribution_link.subcontribution_id)
                                             .one_or_none())
            if existing_subcontribution_link is None:
                subcontribution_link.person = self
            else:
                db.session.delete(subcontribution_link)
        db.session.flush()

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
    #: The name of the relationship pointing to the object the person is linked to
    object_relationship_name = None

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        return (db.UniqueConstraint('person_id', *cls.person_link_unique_columns),)

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='events')

    @declared_attr
    def id(cls):
        return db.Column(
            db.Integer,
            primary_key=True
        )

    @declared_attr
    def person_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('events.persons.id'),
            index=True,
            nullable=False
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

    @property
    def email(self):
        return self.person.email

    @hybrid_property
    def object(self):
        return getattr(self, self.object_relationship_name)

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
    object_relationship_name = 'event'

    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )

    # relationship backrefs:
    # - event (Event.person_links)

    @property
    def is_submitter(self):
        if not self.event:
            raise Exception("No event to check submission rights against")
        return self.person.has_role('submit', self.event)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'person_id', 'event_id', _text=self.full_name)
