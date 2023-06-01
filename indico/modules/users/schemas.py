# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import Schema, fields, post_dump, post_load, validate
from marshmallow.fields import DateTime, Dict, Enum, Function, List, Method, Nested, String, TimeDelta
from speaklater import _LazyString

from indico.core.marshmallow import mm
from indico.core.oauth.models.applications import OAuthApplication
from indico.core.oauth.models.personal_tokens import PersonalToken
from indico.modules.attachments.models.attachments import Attachment, AttachmentType
from indico.modules.auth.models.identities import Identity
from indico.modules.categories.models.categories import Category
from indico.modules.events import Event
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.papers import PaperRevisionState
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.modules.events.static.models.static import StaticSite
from indico.modules.events.surveys.schemas import SurveySubmissionSchema
from indico.modules.rb.models.rooms import Room
from indico.modules.users import User
from indico.modules.users.export import (get_abstracts, get_attachments, get_contributions, get_papers,
                                         get_subcontributions)
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.models.export import DataExportOptions, DataExportRequest
from indico.modules.users.models.users import NameFormat, UserTitle, syncable_fields
from indico.util.countries import get_country
from indico.util.marshmallow import ModelField, NoneValueEnumField
from indico.web.flask.util import url_for


class AffiliationSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Affiliation
        fields = ('id', 'name', 'street', 'postcode', 'city', 'country_code', 'meta')

    @post_dump
    def add_country_name(self, data, **kwargs):
        data['country_name'] = get_country(data['country_code']) or ''
        return data


class UserSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('id', 'identifier', 'first_name', 'last_name', 'email', 'affiliation', 'affiliation_id',
                  'title', 'affiliation_meta', 'full_name', 'phone', 'avatar_url')

    affiliation_id = fields.Integer(load_default=None, dump_only=True)
    affiliation_meta = fields.Nested(AffiliationSchema, attribute='affiliation_link', dump_only=True)
    title = NoneValueEnumField(UserTitle, none_value=UserTitle.none, attribute='_title')


class UserPersonalDataSchema(mm.SQLAlchemyAutoSchema):
    title = NoneValueEnumField(UserTitle, none_value=UserTitle.none, attribute='_title')
    email = String(dump_only=True)
    synced_fields = List(String(validate=validate.OneOf(syncable_fields)))
    affiliation_link = ModelField(Affiliation, data_key='affiliation_id', load_default=None, load_only=True)
    affiliation_data = fields.Function(lambda u: {'id': u.affiliation_id, 'text': u.affiliation}, dump_only=True)

    class Meta:
        model = User
        # XXX: this schema is also used for updating a user's personal data, so the fields here must
        # under no circumstances include sensitive fields that should not be modifiable by a user!
        fields = ('title', 'first_name', 'last_name', 'email', 'address', 'phone', 'synced_fields',
                  'affiliation', 'affiliation_data', 'affiliation_link')

    @post_dump
    def sort_synced_fields(self, data, **kwargs):
        data['synced_fields'].sort()
        return data

    @post_load
    def ensure_affiliation_text(self, data, **kwargs):
        if affiliation_link := data.get('affiliation_link'):
            data['affiliation'] = affiliation_link.name
        elif 'affiliation' in data:
            # clear link if we update only the affiliation text for some reason
            data['affiliation_link'] = None
        return data


class BasicCategorySchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        fields = ('id', 'title', 'url', 'chain_titles')


class FavoriteEventSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'label_markup', 'url', 'location', 'chain_titles', 'start_dt', 'end_dt')

    location = fields.String(attribute='event.location.venue_name')
    chain_titles = fields.List(fields.String(), attribute='category.chain_titles')
    label_markup = fields.Function(lambda e: e.get_label_markup('mini'))


# Schemas for user data export

class DataExportRequestSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = DataExportRequest
        fields = ('state', 'requested_dt', 'selected_options', 'max_size_exceeded', 'url')

    selected_options = List(Enum(DataExportOptions))


class PersonalTokenExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = PersonalToken
        fields = ('name', 'revoked_dt', 'created_dt', 'last_used_dt', 'last_used_ip', 'use_count', 'scopes')

    scopes = Function(lambda token: sorted(list(token.scopes)))


class OAuthApplicationExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = OAuthApplication
        fields = ('name', 'description', 'allowed_scopes', 'redirect_uris', 'is_enabled', 'is_trusted',
                  'allow_pkce_flow')


class IdentityExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Identity
        fields = ('provider', 'identifier', 'data', 'last_login_dt', 'last_login_ip')

    data = Dict(attribute='_data')


class EventExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'url')

    url = Function(lambda event: url_for('events.display', event, _external=True))


class CategoryExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        fields = ('id', 'title', 'url')

    url = Function(lambda category: url_for('categories.display', category, _external=True))


class RoomExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Room
        fields = ('id', 'name', 'verbose_name', 'building', 'floor', 'number',
                  'location_name', 'site', 'map_url')


class StaticSiteExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = StaticSite
        fields = ('id', 'event_id', 'event_url', 'state', 'requested_dt', 'url')

    url = Function(lambda site: url_for('static_site.download', site, _external=True))
    event_url = Function(lambda site: url_for('events.display', site.event, _external=True))


class RegistrationTagExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = RegistrationTag
        fields = ('title',)


class RegistrationFileExportSchema(Schema):
    class Meta:
        fields = ('registration_id', 'field_data_id', 'filename', 'md5', 'url')

    url = Function(lambda data: url_for('event_registration.registration_file', data.locator.file, _external=True))


class RegistrationDataExportSchema(Schema):
    title = Function(lambda data: data.field_data.field.title)
    description = Function(lambda data: data.field_data.field.description)
    data = Method('_get_data')

    def _get_data(self, data):
        friendly_data = data.field_data.field.get_friendly_data(data, for_humans=True)
        return self._strip_lazy_strings(friendly_data)

    def _strip_lazy_strings(self, data):
        if isinstance(data, _LazyString):
            return str(data)
        elif isinstance(data, dict):
            return {k: self._strip_lazy_strings(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._strip_lazy_strings(v) for v in data]
        else:
            return data

    @post_dump(pass_original=True)
    def _add_file(self, data, original, **kwargs):
        """For file fields, export also the file metadata"""
        if original.filename:
            file_data = RegistrationFileExportSchema().dump(original)
            return data | {'file': file_data}


class RegistrationExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Registration
        fields = ('id', 'url', 'event_id', 'event_title', 'event_url', 'state', 'currency', 'price', 'submitted_dt',
                  'email', 'first_name', 'last_name', 'is_deleted', 'checked_in', 'checked_in_dt', 'rejection_reason',
                  'consent_to_publish', 'created_by_manager', 'tags', 'data')

    price = fields.Decimal(as_string=True)
    url = Function(lambda reg: url_for('event_registration.registration_details', reg, _external=True))
    event_title = Function(lambda reg: reg.event.title)
    event_url = Function(lambda reg: url_for('events.display', reg.event, _external=True))
    tags = List(Nested(RegistrationTagExportSchema))
    data = Method('_serialize_data')

    def _serialize_data(self, registration):
        registration_data = [data for data in registration.data if not data.field_data.field.is_manager_only]
        return RegistrationDataExportSchema(many=True).dump(registration_data)


class SubContributionExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SubContribution
        fields = ('id', 'contribution_id', 'subcontribution_id', 'title', 'description',
                  'url', 'event_url', 'duration', 'venue_name', 'room_name',
                  'minutes', 'is_deleted')

    duration = TimeDelta(precision=TimeDelta.MINUTES)
    minutes = Method('_get_minutes')
    url = Function(lambda subcontrib: url_for('contributions.display_subcontribution', subcontrib, _external=True))
    event_url = Function(lambda subcontrib: url_for('events.display', subcontrib.contribution.event, _external=True))

    def _get_minutes(self, subcontrib):
        if note := subcontrib.note:
            return note.current_revision.html


class ContributionExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'contribution_type', 'event_id', 'event_title', 'title', 'description',
                  'url', 'event_url', 'start_dt', 'end_dt', 'duration', 'venue_name', 'room_name', 'address',
                  'minutes', 'keywords', 'is_deleted', 'is_author', 'is_speaker')

    duration = TimeDelta(precision=TimeDelta.MINUTES)
    url = Function(lambda contrib: url_for('contributions.display_contribution', contrib, _external=True))
    event_url = Function(lambda contrib: url_for('events.display', contrib.event, _external=True))
    is_author = Method('_is_author')
    is_speaker = Method('_is_speaker')
    minutes = Method('_get_minutes')

    def _is_author(self, contrib):
        user = self.context['user']
        return any(link.is_author for link in contrib.person_links if link.person.user == user)

    def _is_speaker(self, contrib):
        user = self.context['user']
        return any(link.is_speaker for link in contrib.person_links if link.person.user == user)

    def _get_minutes(self, contrib):
        if note := contrib.note:
            return note.current_revision.html


class AbstractFileExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = AbstractFile
        fields = ('id', 'filename', 'url')

    url = Function(lambda f: url_for('abstracts.download_attachment', f, management=False, _external=True))


class AbstractExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Abstract
        fields = ('id', 'contribution_id', 'event_id', 'title', 'description', 'files',
                  'submission_comment', 'submitted_dt', 'state', 'url', 'event_url')

    description = String(attribute='_description')
    state = Enum(AbstractState)
    url = Function(lambda abstract: url_for('abstracts.display_abstract', abstract, management=False, _external=True))
    event_url = Function(lambda abstract: url_for('events.display', abstract.event, _external=True))
    files = List(Nested(AbstractFileExportSchema))


class PaperFileExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = PaperFile
        fields = ('id', 'filename', 'url')

    url = Function(lambda f: url_for('papers.download_file', f.paper.contribution, f, _external=True))


class PaperExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'description', 'submitted_dt', 'url', 'event_url', 'files')

    submitted_dt = Method('_get_submitted_dt')
    state = Enum(PaperRevisionState)
    url = Function(lambda paper: url_for('papers.paper_timeline', paper, _external=True))
    event_url = Function(lambda paper: url_for('events.display', paper.event, _external=True))
    files = List(Nested(PaperFileExportSchema))

    def _get_submitted_dt(self, paper):
        return DateTime().serialize('submitted_dt', paper.revisions[0])


class PersonalDataExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'full_name', 'title', 'email', 'secondary_emails',
                  'affiliation', 'phone', 'avatar_url', 'picture_metadata', 'picture_source',
                  'favorite_events', 'favorite_categories')

    title = NoneValueEnumField(UserTitle, none_value=UserTitle.none, attribute='_title')
    secondary_emails = Function(lambda user: list(user.secondary_emails))
    affiliation = Nested(AffiliationSchema, attribute='affiliation_link')
    favorite_events = List(Nested(EventExportSchema))
    favorite_categories = List(Nested(CategoryExportSchema))


class RoomBookingExportSchema(Schema):
    from indico.modules.rb.schemas import ReservationSchema

    favorite_rooms = List(Nested(RoomExportSchema))
    owned_rooms = List(Nested(RoomExportSchema))
    reservations = List(Nested(ReservationSchema))


class MiscDataExportSchema(Schema):
    created_events = List(Nested(EventExportSchema))
    static_sites = List(Nested(StaticSiteExportSchema))
    identities = List(Nested(IdentityExportSchema))
    personal_tokens = List(Nested(PersonalTokenExportSchema))
    oauth_applications = Method('_serialize_oauth_apps')

    def _serialize_oauth_apps(self, user):
        oauth_apps = [link.application for link in user.oauth_app_links]
        return OAuthApplicationExportSchema(many=True).dump(oauth_apps)


class AttachmentExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Attachment
        fields = ('id', 'folder_id', 'folder', 'title', 'url', 'link_url',
                  'type', 'modified_dt', 'description')

    url = String(attribute='absolute_download_url')
    type = Enum(AttachmentType)


class SettingsExportSchema(Schema):
    class Meta:
        fields = ('add_ical_alerts', 'add_ical_alerts_mins', 'force_language', 'force_timezone',
                  'lang', 'name_format', 'show_future_events', 'show_past_events',
                  'suggest_categories', 'synced_fields', 'timezone', 'use_markdown_for_minutes',
                  'use_previewer_pdf')

    name_format = Function(lambda settings: NameFormat(settings['name_format']).name)


class UserDataExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('personal_data', 'settings', 'contributions', 'subcontributions', 'registrations', 'room_booking',
                  'survey_submissions', 'abstracts', 'papers', 'miscellaneous', 'attachments')

    personal_data = Function(lambda user: PersonalDataExportSchema().dump(user))
    settings = Method('_get_settings')
    contributions = Method('_get_contributions')
    subcontributions = Method('_get_subcontributions')
    registrations = List(Nested(RegistrationExportSchema))
    room_booking = Function(lambda user: RoomBookingExportSchema().dump(user))
    survey_submissions = List(Nested(SurveySubmissionSchema))
    abstracts = Method('_get_abstracts')
    papers = Method('_get_papers')
    attachments = Method('_get_attachments')
    miscellaneous = Function(lambda user: MiscDataExportSchema().dump(user))

    def _get_settings(self, user):
        settings = user.settings.get_all()
        return SettingsExportSchema().dump(settings)

    def _get_contributions(self, user):
        contribs = get_contributions(user)
        return ContributionExportSchema(many=True, context={'user': user}).dump(contribs)

    def _get_subcontributions(self, user):
        subcontribs = get_subcontributions(user)
        return SubContributionExportSchema(many=True, context={'user': user}).dump(subcontribs)

    def _get_abstracts(self, user):
        abstracts = get_abstracts(user)
        return AbstractExportSchema(many=True).dump(abstracts)

    def _get_papers(self, user):
        papers = get_papers(user)
        return PaperExportSchema(many=True).dump(papers)

    def _get_attachments(self, user):
        attachments = get_attachments(user)
        return AttachmentExportSchema(many=True).dump(attachments)
