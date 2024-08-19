# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import attrgetter

from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapper

from indico.core import signals
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime, db
from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.core.db.sqlalchemy.util.models import auto_table_args, override_attr
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.users.models.users import PersonMixin, UserTitle
from indico.util.decorators import strict_classproperty
from indico.util.locators import locator_property
from indico.util.string import format_repr


class PersonLinkMixin:
    person_link_relation_name = None
    person_link_backref_name = None

    @declared_attr
    def person_links(cls):
        return db.relationship(
            cls.person_link_relation_name,
            lazy=True,
            cascade='all, delete-orphan',
            backref=db.backref(
                cls.person_link_backref_name,
                lazy=True
            )
        )

    @property
    def sorted_person_links(self):
        return sorted(self.person_links, key=attrgetter('display_order_key'))

    @property
    def person_link_data(self):
        return {x: x.is_submitter for x in self.person_links}

    @person_link_data.setter
    @no_autoflush
    def person_link_data(self, value):
        # Revoke submission rights for removed persons
        for person_link in set(self.person_links) - value.keys():
            principal = person_link.person.principal
            if principal:
                self.update_principal(principal, del_permissions={'submit'})
        # Update person links
        self.person_links = list(value.keys())
        for person_link, is_submitter in value.items():
            person = person_link.person
            principal = person.principal
            if not principal:
                continue
            action = {'add_permissions': {'submit'}} if is_submitter else {'del_permissions': {'submit'}}
            self.update_principal(principal, **action)


class AuthorsSpeakersMixin:
    AUTHORS_SPEAKERS_DISPLAY_ORDER_ATTR = 'display_order_key'

    @property
    def speakers(self):
        return [person_link
                for person_link in sorted(self.person_links, key=attrgetter(self.AUTHORS_SPEAKERS_DISPLAY_ORDER_ATTR))
                if person_link.is_speaker]

    @property
    def primary_authors(self):
        from indico.modules.events.contributions.models.persons import AuthorType
        return [person_link
                for person_link in sorted(self.person_links, key=attrgetter(self.AUTHORS_SPEAKERS_DISPLAY_ORDER_ATTR))
                if person_link.author_type == AuthorType.primary]

    @property
    def secondary_authors(self):
        from indico.modules.events.contributions.models.persons import AuthorType
        return [person_link
                for person_link in sorted(self.person_links, key=attrgetter(self.AUTHORS_SPEAKERS_DISPLAY_ORDER_ATTR))
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
    #: the id of the underlying predefined affiliation
    affiliation_id = db.Column(
        db.ForeignKey('indico.affiliations.id'),
        nullable=True,
        index=True
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

    event = db.relationship(
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
    affiliation_link = db.relationship(
        'Affiliation',
        lazy=False,
        backref=db.backref(
            'event_person_affiliations',
            lazy='dynamic',
            cascade_backrefs=False
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
        return dict(self.event.locator, person_id=self.id)

    def __repr__(self):
        return format_repr(self, 'id', is_untrusted=False, _text=self.full_name)

    @property
    def principal(self):
        if self.user is not None:
            return self.user
        elif self.email:
            return EmailPrincipal(self.email)
        return None

    @property
    def identifier(self):
        return f'EventPerson:{self.id}'

    @classmethod
    def create_from_user(cls, user, event=None, is_untrusted=False):
        return EventPerson(user=user, event=event, first_name=user.first_name, last_name=user.last_name,
                           title=user._title, email=user.email, affiliation=user.affiliation,
                           affiliation_link=user.affiliation_link, address=user.address, phone=user.phone,
                           is_untrusted=is_untrusted)

    @classmethod
    def for_user(cls, user, event=None, is_untrusted=False):
        """Return EventPerson for a matching User in Event creating if needed."""
        person = event.persons.filter_by(user=user).first() if event else None
        email_person = event.persons.filter(EventPerson.email.in_(user.all_emails)).first() if event else None
        if not person and email_person:
            if email_person.user is None:
                email_person.user = user
            assert email_person.user == user
            person = email_person
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
                event_person.user = target
            else:
                existing.merge_person_info(event_person)
                db.session.delete(event_person)
        db.session.flush()

    @classmethod
    def link_user_by_email(cls, user):
        """
        Link all email-based persons matching the user's
        email addresses with the user.

        :param user: A User object.
        """
        from indico.modules.events.models.events import Event
        query = (cls.query
                 .join(EventPerson.event)
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

    def get_unsynced_data(self):
        """Return data no longer in sync with the user."""
        if not self.user:
            return {}
        fields = ('first_name', 'last_name', '_title', 'email', 'affiliation', 'affiliation_link', 'address', 'phone')
        changes = {}
        for field in fields:
            person_data = getattr(self, field)
            user_data = getattr(self.user, field)
            if person_data != user_data:
                changes[field] = (person_data, user_data)
        return changes

    def sync_user(self, *, notify=True):
        """Update all person data based on the current user data.

        :param notify: Whether to trigger the ``person_updated`` signal.
        """
        if not self.user:
            return
        fields = ('first_name', 'last_name', '_title', 'email', 'affiliation', 'affiliation_link', 'address', 'phone')
        has_changes = False
        for field in fields:
            new = getattr(self.user, field)
            if getattr(self, field) != new:
                setattr(self, field, new)
                has_changes = True
        if notify and has_changes:
            signals.event.person_updated.send(self)

    @no_autoflush
    def merge_person_info(self, other):
        from indico.modules.events.contributions.models.persons import AuthorType
        for column_name in ('_title', 'affiliation', 'address', 'phone', 'first_name', 'last_name'):
            value = getattr(self, column_name) or getattr(other, column_name)
            setattr(self, column_name, value)

        for event_link in other.event_links[:]:
            existing_event_link = next((link for link in self.event_links if link.event_id == event_link.event_id),
                                       None)
            if existing_event_link is None:
                event_link.person = self
            else:
                other.event_links.remove(event_link)

        for abstract_link in other.abstract_links[:]:
            existing_abstract_link = next((link for link in self.abstract_links
                                           if link.abstract_id == abstract_link.abstract_id), None)

            if existing_abstract_link is None:
                abstract_link.person = self
            else:
                existing_abstract_link.is_speaker |= abstract_link.is_speaker
                existing_abstract_link.author_type = AuthorType.get_highest(existing_abstract_link.author_type,
                                                                            abstract_link.author_type)
                other.abstract_links.remove(abstract_link)

        for contribution_link in other.contribution_links[:]:
            existing_contribution_link = next((link for link in self.contribution_links
                                               if link.contribution_id == contribution_link.contribution_id), None)

            if existing_contribution_link is None:
                contribution_link.person = self
            else:
                existing_contribution_link.is_speaker |= contribution_link.is_speaker
                existing_contribution_link.author_type = AuthorType.get_highest(existing_contribution_link.author_type,
                                                                                contribution_link.author_type)
                other.contribution_links.remove(contribution_link)

        for subcontribution_link in other.subcontribution_links[:]:
            existing_subcontribution_link = next(
                (link for link in self.subcontribution_links
                 if link.subcontribution_id == subcontribution_link.subcontribution_id), None)
            if existing_subcontribution_link is None:
                subcontribution_link.person = self
            else:
                other.subcontribution_links.remove(subcontribution_link)

        for session_block_link in other.session_block_links[:]:
            existing_session_block_link = next((link for link in self.session_block_links
                                                if link.session_block_id == session_block_link.session_block_id),
                                               None)
            if existing_session_block_link is None:
                session_block_link.person = self
            else:
                other.session_block_links.remove(session_block_link)

        db.session.flush()

    def has_role(self, role, obj):
        """Whether the person has a role in the ACL list of a given object."""
        principals = [x for x in obj.acl_entries if x.has_management_permission(role, explicit=True)]
        return any(x
                   for x in principals
                   if ((self.user_id is not None and self.user_id == x.user_id) or
                       (self.email is not None and self.email == x.email)))

    @property
    def has_links(self):
        """Whether the person is an author, speaker, etc., in the event."""
        chairpersons = {link.person for link in self.event.person_links}
        return (
            self in chairpersons or
            # Check regardless of the abstract feature being enabled
            any(link for link in self.abstract_links if not link.abstract.is_deleted) or
            any(link for link in self.session_block_links if not link.session_block.session.is_deleted) or
            any(link for link in self.contribution_links if not link.contribution.is_deleted) or
            any(link for link in self.subcontribution_links if (not link.subcontribution.is_deleted and
                                                                not link.subcontribution.contribution.is_deleted))
        )


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
    def _title_col(cls):
        return db.Column(
            'title',
            PyIntEnum(UserTitle),
            nullable=True
        )

    @declared_attr
    def _affiliation_id(cls):
        return db.Column(
            'affiliation_id',
            db.ForeignKey('indico.affiliations.id'),
            nullable=True,
            index=True
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
    def _affiliation_link(cls):
        return db.relationship(
            'Affiliation',
            lazy=False,
            backref=db.backref(
                cls.person_link_backref_name,
                cascade_backrefs=False,
                lazy='dynamic',
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

    @property
    def display_order_key_lastname(self):
        return self.display_order, self.last_name, self.first_name

    @hybrid_property
    def object(self):
        return getattr(self, self.object_relationship_name)

    first_name = override_attr('first_name', 'person')
    last_name = override_attr('last_name', 'person')
    title = override_attr('title', 'person', fget=lambda self, __: self._get_title())
    _title = override_attr('_title', 'person', own_attr_name='_title_col')
    affiliation = override_attr('affiliation', 'person')
    affiliation_id = override_attr('affiliation_id', 'person', check_attr_name='_affiliation')
    affiliation_link = override_attr('affiliation_link', 'person', check_attr_name='_affiliation')
    address = override_attr('address', 'person')
    phone = override_attr('phone', 'person')

    def __init__(self, *args, **kwargs):
        # Needed in order to ensure `person` is set before the overridable attrs
        self.person = kwargs.pop('person', None)
        super().__init__(*args, **kwargs)


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
            raise Exception('No event to check submission rights against')
        return self.person.has_role('submit', self.event)

    def __repr__(self):
        return format_repr(self, 'id', 'person_id', 'event_id', _text=self.full_name)


@listens_for(mapper, 'after_configured', once=True)
def _mapper_configured():
    @listens_for(EventPersonLink.event, 'set')
    def _associate_event_person(target, value, *unused):
        if value is None:
            return
        if target.person.event is None:
            target.person.event = value
        else:
            assert target.person.event == value

    @listens_for(EventPerson.event_links, 'append')
    @listens_for(EventPerson.session_block_links, 'append')
    @listens_for(EventPerson.contribution_links, 'append')
    @listens_for(EventPerson.subcontribution_links, 'append')
    def _mark_not_untrusted(target, value, *unused):
        target.is_untrusted = False
