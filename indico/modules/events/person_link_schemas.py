# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import operator

from marshmallow import SchemaOpts, ValidationError, fields, post_dump, post_load, pre_load, validates_schema
from sqlalchemy import inspect

from indico.core import signals
from indico.core.cache import make_scoped_cache
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.marshmallow import mm
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.contributions.models.persons import (AuthorType, ContributionPersonLink,
                                                                SubContributionPersonLink)
from indico.modules.events.models.persons import EventPersonLink
from indico.modules.events.persons.util import get_event_person
from indico.modules.events.sessions.models.persons import SessionBlockPersonLink
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.models.users import UserTitle
from indico.modules.users.schemas import AffiliationSchema
from indico.modules.users.util import get_user_by_email
from indico.util.i18n import _
from indico.util.marshmallow import ModelField
from indico.util.signals import values_from_signal


class PersonLinkOpts(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.person_link_cls = getattr(meta, 'person_link_cls', None)


class PersonLinkBaseSchema(mm.Schema):
    OPTIONS_CLASS = PersonLinkOpts

    class Meta:
        pass
        # unknown = EXCLUDE

    identifier = fields.String(load_only=True)
    type = fields.String(dump_default='person_link')
    person_id = fields.Int()
    user_id = fields.Int(attribute='person.user_id', dump_only=True)
    user_identifier = fields.String(attribute='person.user.identifier', dump_only=True)
    name = fields.String(attribute='display_full_name', dump_only=True)
    first_name = fields.String(load_default='')
    last_name = fields.String(required=True)
    _title = fields.Enum(UserTitle, data_key='title')
    affiliation = fields.String(load_default='')
    affiliation_link = ModelField(Affiliation, data_key='affiliation_id', load_default=None, load_only=True)
    affiliation_id = fields.Integer(load_default=None, dump_only=True)
    affiliation_meta = fields.Nested(AffiliationSchema, attribute='affiliation_link', dump_only=True)
    phone = fields.String(load_default='')
    address = fields.String(load_default='')
    email = fields.String(load_default='')
    display_order = fields.Int(load_default=0)
    avatar_url = fields.Function(lambda o: o.person.user.avatar_url if o.person.user else None, dump_only=True)
    roles = fields.List(fields.String(), load_only=True, load_default=list)

    @pre_load
    def load_nones(self, data, **kwargs):
        if not data.get('title'):
            data['title'] = UserTitle.none.name
        if not data.get('affiliation'):
            data['affiliation'] = ''
        if data.get('affiliation_id') == -1:
            # external search results with a predefined affiliation
            del data['affiliation_id']
        return data

    def _deserialize(self, data, many, **kwargs):
        if many:
            return super()._deserialize(data, many=many, **kwargs)
        data = super()._deserialize(data, many=many, **kwargs)
        data = self.ensure_affiliation_text(data, **kwargs)
        return self.get_person_link(data)

    def get_person_link(self, data):
        return get_person_link(
            data,
            person_link_cls=self.opts.person_link_cls,
            object=self.context.get('object'),
            event=self.context.get('event'),
            can_enter_manually=self.context.get('can_enter_manually', True),
            create_untrusted_persons=self.context.get('create_untrusted_persons', False),
            has_predefined_affiliations=has_predefined_affiliations(),
            extra_params=extra_params(),
        )

    def ensure_affiliation_text(self, data, **kwargs):
        if data['affiliation_link']:
            data['affiliation'] = data['affiliation_link'].name
        return data

    @post_dump
    def dump_type(self, data, **kwargs):
        if data['person_id'] is None:
            del data['type']
            del data['person_id']
        if data['title'] == UserTitle.none.name:
            data['title'] = None
        return data

    @post_dump(pass_many=True)
    def sort(self, data, many, **kwargs):
        if not many:
            return data
        return sorted(data, key=operator.itemgetter('display_order'))


@no_autoflush
def get_person_link(
    data,
    *,
    event=None,
    object=None,
    person_link_cls,
    can_enter_manually,
    create_untrusted_persons,
    has_predefined_affiliations,
    extra_params,
):
    identifier = data.get('identifier')
    affiliations_disabled = extra_params.get('disable_affiliations', False)
    if not can_enter_manually and not data.get('type'):
        raise ValidationError('Manually entered persons are not allowed')
    if identifier and identifier.startswith('ExternalUser:'):
        # if the data came from an external user, look up their affiliation if the names still match;
        # we do not have an affiliation ID yet since it may not exist in the local DB yet
        cache = make_scoped_cache('external-user')
        external_user_data = cache.get(identifier.removeprefix('ExternalUser:'), {})
        if not can_enter_manually:
            for key in ('first_name', 'last_name', 'email', 'affiliation', 'phone', 'address'):
                data[key] = external_user_data.get(key, '')
            data['_title'] = UserTitle.none
            data['affiliation_link'] = None
        if (
            not affiliations_disabled
            and (affiliation_data := external_user_data.get('affiliation_data'))
            and data['affiliation'] == affiliation_data['name']
        ):
            data['affiliation_link'] = Affiliation.get_or_create_from_data(affiliation_data)
            data['affiliation'] = data['affiliation_link'].name
    if not has_predefined_affiliations or affiliations_disabled:
        data['affiliation_link'] = None
    person = get_event_person(event, data, create_untrusted_persons=create_untrusted_persons, allow_external=True)
    person_link = None
    if object and inspect(person).persistent:
        person_link = person_link_cls.query.filter_by(person=person, object=object).first()
    if not person_link:
        person_link = person_link_cls(person=person)
    if not can_enter_manually:
        person_link.populate_from_dict(data, keys=('display_order',))
        return person_link
    person_link.populate_from_dict(
        data,
        keys=(
            'first_name',
            'last_name',
            'affiliation',
            'affiliation_link',
            'address',
            'phone',
            '_title',
            'display_order',
        ),
    )
    email = data.get('email', '').lower()
    if email != person_link.email:
        if not event or not event.persons.filter_by(email=email).first():
            person_link.person.email = email
            person_link.person.user = get_user_by_email(email)
            if inspect(person).persistent:
                signals.event.person_updated.send(person_link.person)
        else:
            raise ValidationError(_('There is already a person with the email {email}').format(email=email))
    return person_link


def get_author_type(roles):
    return next((AuthorType.get(a) for a in roles if AuthorType.get(a)), AuthorType.none)


def is_speaker(roles):
    return 'speaker' in roles


def is_submitter(roles):
    return 'submitter' in roles


# TODO: memoize?
def has_predefined_affiliations():
    return Affiliation.query.filter(~Affiliation.is_deleted).has_rows()


def extra_params():
    values = values_from_signal(signals.event.person_link_field_extra_params.send(), as_list=True)
    return {k: v for d in values for k, v in d.items()}


class ContributionPersonLinkSchema(PersonLinkBaseSchema):
    class Meta(PersonLinkBaseSchema.Meta):
        person_link_cls = ContributionPersonLink

    @validates_schema(pass_many=True)
    def _check_roles(self, data, many, **kwargs):
        person_links = data if many else [data]
        for person_link in person_links:
            if person_link.author_type == AuthorType.none and not person_link.is_speaker:
                raise ValidationError(_('{} has no role').format(person_link.full_name))

    def get_person_link(self, data):
        person_link = super().get_person_link(data)
        roles = data.get('roles', [])
        person_link.is_speaker = is_speaker(roles)
        person_link.author_type = get_author_type(roles)
        return person_link

    @post_dump(pass_original=True)
    def add_roles(self, data, orig, **kwargs):
        data['roles'] = [orig.author_type.name]
        if orig.is_speaker:
            data['roles'].append('speaker')
        if orig.is_submitter:
            data['roles'].append('submitter')
        return data

    @post_load(pass_many=True, pass_original=True)
    def add_submitter_info(self, data, orig, many, **kwargs):
        if not many:
            data = [data]
            orig = [orig]
        person_links = []
        for person_link, original_data in zip(data, orig, strict=True):
            roles = original_data['roles']
            person_links.append({'person_link': person_link, 'is_submitter': is_submitter(roles)})
        return person_links


class SubContributionPersonLinkSchema(PersonLinkBaseSchema):
    class Meta:
        person_link_cls = SubContributionPersonLink

    @post_dump(pass_original=True)
    def add_roles(self, data, person_link, **kwargs):
        data['roles'] = []
        if person_link.is_speaker:
            data['roles'].append('speaker')
        return data


class EventPersonLinkSchema(PersonLinkBaseSchema):
    class Meta:
        person_link_cls = EventPersonLink

    @post_dump(pass_original=True)
    def add_roles(self, data, person_link, **kwargs):
        data['roles'] = []
        if person_link.is_submitter:
            data['roles'].append('submitter')
        return data

    @post_load(pass_many=True, pass_original=True)
    def add_submitter_info(self, data, orig, many, **kwargs):
        if not many:
            data = [data]
            orig = [orig]
        person_links = []
        for person_link, original_data in zip(data, orig, strict=True):
            roles = original_data['roles']
            person_links.append({'person_link': person_link, 'is_submitter': is_submitter(roles)})
        return person_links


class AbstractPersonLinkSchema(PersonLinkBaseSchema):
    class Meta:
        person_link_cls = AbstractPersonLink

    @post_load(pass_many=True)
    def _check_roles(self, data, many, **kwargs):
        person_links = data if many else [data]
        for person_link in person_links:
            if person_link.author_type == AuthorType.none and not person_link.is_speaker:
                raise ValidationError(_('{} has no role').format(person_link.full_name))
        if self.context.get('require_primary_author') and not any(
            person_link.author_type == AuthorType.primary for person_link in person_links
        ):
            raise ValidationError(_('You must add at least one author'))
        if self.context.get('require_speaker') and not any(person_link.is_speaker for person_link in person_links):
            raise ValidationError(_('You must add at least one speaker'))

    def get_person_link(self, data, **kwargs):
        person_link = super().get_person_link(data)
        roles = data.get('roles', [])
        person_link.is_speaker = is_speaker(roles)
        person_link.author_type = get_author_type(roles)
        return person_link

    @post_dump(pass_original=True)
    def add_roles(self, data, person_link, **kwargs):
        data['roles'] = [person_link.author_type.name]
        if person_link.is_speaker:
            data['roles'].append('speaker')
        return data


class SessionBlockPersonLinkSchema(PersonLinkBaseSchema):
    class Meta:
        person_link_cls = SessionBlockPersonLink
