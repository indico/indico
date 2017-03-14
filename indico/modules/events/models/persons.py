# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from operator import attrgetter

from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapper

from indico.core.db.sqlalchemy import db, PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.core.db.sqlalchemy.util.models import auto_table_args, override_attr
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.users.models.users import UserTitle, PersonMixin
from indico.util.decorators import strict_classproperty
from indico.util.locators import locator_property
from indico.util.string import return_ascii, format_repr


class PersonLinkDataMixin(object):
    @property
    def person_link_data(self):
        return {x: x.is_submitter for x in self.person_links}

    @person_link_data.setter
    @no_autoflush
    def person_link_data(self, value):
        # Revoke submission rights for removed persons
        for person_link in set(self.person_links) - value.viewkeys():
            principal = person_link.person.principal
            if principal:
                self.update_principal(principal, del_roles={'submit'})
        # Update person links
        self.person_links = value.keys()
        for person_link, is_submitter in value.iteritems():
            person = person_link.person
            principal = person.principal
            if not principal:
                continue
            action = {'add_roles': {'submit'}} if is_submitter else {'del_roles': {'submit'}}
            self.update_principal(principal, **action)


class AuthorsSpeakersMixin(object):
    @property
    def speakers(self):
        return [person_link
                for person_link in sorted(self.person_links, key=attrgetter('display_order_key'))
                if person_link.is_speaker]

    @property
    def primary_authors(self):
        from indico.modules.events.contributions.models.persons import AuthorType
        return [person_link
                for person_link in sorted(self.person_links, key=attrgetter('display_order_key'))
                if person_link.author_type == AuthorType.primary]

    @property
    def secondary_authors(self):
        from indico.modules.events.contributions.models.persons import AuthorType
        return [person_link
                for person_link in sorted(self.person_links, key=attrgetter('display_order_key'))
                if person_link.author_type == AuthorType.secondary]


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
    invited_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    is_untrusted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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
    # - abstract_links (AbstractPersonLink.person)
    # - contribution_links (ContributionPersonLink.person)
    # - event_links (EventPersonLink.person)
    # - session_block_links (SessionBlockPersonLink.person)
    # - subcontribution_links (SubContributionPersonLink.person)

    @locator_property
    def locator(self):
        return dict(self.event_new.locator, person_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', is_untrusted=False, _text=self.full_name)

    @property
    def principal(self):
        if self.user is not None:
            return self.user
        elif self.email:
            return EmailPrincipal(self.email)
        return None

    @classmethod
    def create_from_user(cls, user, event=None, is_untrusted=False):
        return EventPerson(user=user, event_new=event, first_name=user.first_name, last_name=user.last_name,
                           email=user.email, affiliation=user.affiliation, address=user.address, phone=user.phone,
                           is_untrusted=is_untrusted)

    @classmethod
    def for_user(cls, user, event=None, is_untrusted=False):
        """Return EventPerson for a matching User in Event creating if needed"""
        person = event.persons.filter_by(user=user).first() if event else None
        return person or cls.create_from_user(user, event, is_untrusted=is_untrusted)

    @classmethod
    def merge_users(cls, target, source):
        """Merge the EventPersons of two users.

        :param target: The target user of the merge
        :param source: The user that is being merged into `target`
        """
        existing_persons = {ep.event_id: ep for ep in target.event_persons}
        for event_person in source.event_persons:
            existing = existing_persons.get(event_person.event_id)
            if existing is None:
                assert event_person.email in target.all_emails
                event_person.user = target
            else:
                existing.merge_person_info(event_person)
                db.session.delete(event_person)
        db.session.flush()

    @classmethod
    def link_user_by_email(cls, user):
        """
        Links all email-based persons matching the user's
        email addresses with the user.

        :param user: A User object.
        """
        from indico.modules.events.models.events import Event
        query = (cls.query
                 .join(EventPerson.event_new)
                 .filter(~Event.is_deleted,
                         cls.email.in_(user.all_emails),
                         cls.user_id.is_(None)))
        for event_person in query:
            existing = (cls.query
                        .filter_by(user_id=user.id, event_id=event_person.event_id)
                        .one_or_none())
            if existing is None:
                event_person.user = user
            else:
                existing.merge_person_info(event_person)
                db.session.delete(event_person)
        db.session.flush()

    @no_autoflush
    def merge_person_info(self, other):
        from indico.modules.events.contributions.models.persons import AuthorType
        for column_name in {'_title', 'affiliation', 'address', 'phone', 'first_name', 'last_name'}:
            value = getattr(self, column_name) or getattr(other, column_name)
            setattr(self, column_name, value)

        for event_link in other.event_links:
            existing_event_link = next((link for link in self.event_links if link.event_id == event_link.event_id),
                                       None)
            if existing_event_link is None:
                event_link.person = self
            else:
                other.event_links.remove(event_link)

        for abstract_link in other.abstract_links:
            existing_abstract_link = next((link for link in self.abstract_links
                                           if link.abstract_id == abstract_link.abstract_id), None)

            if existing_abstract_link is None:
                abstract_link.person = self
            else:
                existing_abstract_link.is_speaker |= abstract_link.is_speaker
                existing_abstract_link.author_type = AuthorType.get_highest(existing_abstract_link.author_type,
                                                                            abstract_link.author_type)
                other.abstract_links.remove(abstract_link)

        for contribution_link in other.contribution_links:
            existing_contribution_link = next((link for link in self.contribution_links
                                               if link.contribution_id == contribution_link.contribution_id), None)

            if existing_contribution_link is None:
                contribution_link.person = self
            else:
                existing_contribution_link.is_speaker |= contribution_link.is_speaker
                existing_contribution_link.author_type = AuthorType.get_highest(existing_contribution_link.author_type,
                                                                                contribution_link.author_type)
                other.contribution_links.remove(contribution_link)

        for subcontribution_link in other.subcontribution_links:
            existing_subcontribution_link = next(
                (link for link in self.subcontribution_links
                 if link.subcontribution_id == subcontribution_link.subcontribution_id), None)
            if existing_subcontribution_link is None:
                subcontribution_link.person = self
            else:
                other.subcontribution_links.remove(subcontribution_link)

        for session_block_link in other.session_block_links:
            existing_session_block_link = next((link for link in self.session_block_links
                                                if link.session_block_id == session_block_link.session_block_id),
                                               None)
            if existing_session_block_link is None:
                session_block_link.person = self
            else:
                other.session_block_links.remove(session_block_link)

        db.session.flush()

    def has_role(self, role, obj):
        """Whether the person has a role in the ACL list of a given object"""
        principals = [x for x in obj.acl_entries if x.has_management_role(role, explicit=True)]
        return any(x
                   for x in principals
                   if ((self.user_id is not None and self.user_id == x.user_id) or
                       (self.email is not None and self.email == x.email)))


class PersonLinkBase(PersonMixin, db.Model):
    """Base class for EventPerson associations."""

    __abstract__ = True
    __auto_table_args = {'schema': 'events'}
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
        return auto_table_args(cls)

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
                lazy=True
            )
        )

    @declared_attr
    def display_order(cls):
        return db.Column(
            db.Integer,
            nullable=False,
            default=0
        )

    @property
    def email(self):
        return self.person.email

    @property
    def display_order_key(self):
        return self.display_order, self.display_full_name

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


@listens_for(mapper, 'after_configured', once=True)
def _mapper_configured():
    @listens_for(EventPersonLink.event, 'set')
    def _associate_event_person(target, value, *unused):
        if value is None:
            return
        if target.person.event_new is None:
            target.person.event_new = value
        else:
            assert target.person.event_new == value

    @listens_for(EventPerson.event_links, 'append')
    @listens_for(EventPerson.session_block_links, 'append')
    @listens_for(EventPerson.contribution_links, 'append')
    @listens_for(EventPerson.subcontribution_links, 'append')
    def _mark_not_untrusted(target, value, *unused):
        target.is_untrusted = False
