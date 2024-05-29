# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import Schema, fields, post_dump
from speaklater import _LazyString

from indico.core.marshmallow import mm
from indico.core.oauth.models.applications import OAuthApplication, OAuthApplicationUserLink
from indico.core.oauth.models.personal_tokens import PersonalToken
from indico.modules.api.models.keys import APIKey
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.auth.models.identities import Identity
from indico.modules.categories.models.categories import Category
from indico.modules.events import Event
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.editing.models.editable import Editable, EditableState, EditableType
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision, RevisionType
from indico.modules.events.notes.models.notes import EventNote, EventNoteRevision
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.papers import PaperRevisionState
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.static.models.static import StaticSite
from indico.modules.events.surveys.schemas import SurveySubmissionSchema
from indico.modules.rb.models.rooms import Room
from indico.modules.receipts.models.files import ReceiptFile
from indico.modules.users import User
from indico.modules.users.export import (build_storage_path, get_abstracts, get_attachments, get_contributions,
                                         get_editables, get_note_revisions, get_papers, get_registrations,
                                         get_subcontributions, get_survey_submissions)
from indico.modules.users.models.export import DataExportOptions, DataExportRequest
from indico.modules.users.models.users import NameFormat, UserTitle
from indico.modules.users.schemas import AffiliationSchema
from indico.util.marshmallow import NoneValueEnumField
from indico.web.flask.util import url_for


class DataExportRequestSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = DataExportRequest
        fields = ('state', 'requested_dt', 'selected_options', 'max_size_exceeded', 'url')

    selected_options = fields.List(fields.Enum(DataExportOptions))


class PersonalTokenExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = PersonalToken
        fields = ('name', 'revoked_dt', 'created_dt', 'last_used_dt', 'last_used_ip', 'use_count', 'scopes')

    scopes = fields.Function(lambda token: sorted(token.scopes))


class APIKeyExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = APIKey
        fields = ('is_active', 'is_blocked', 'is_persistent_allowed', 'created_dt', 'last_used_dt', 'last_used_ip',
                  'last_used_uri', 'last_used_auth', 'use_count')


class OAuthApplicationExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = OAuthApplication
        fields = ('name', 'description')


class OAuthApplicationUserLinkExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = OAuthApplicationUserLink
        fields = ('scopes', 'application')

    application = fields.Nested(OAuthApplicationExportSchema)


class IdentityExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Identity
        fields = ('provider', 'identifier', 'data', 'last_login_dt', 'last_login_ip')

    data = fields.Dict(attribute='_data')


class EventExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'url')

    url = fields.Function(lambda event: url_for('events.display', event, _external=True))


class CategoryExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        fields = ('id', 'title', 'url')

    url = fields.Function(lambda category: url_for('categories.display', category, _external=True))


class RoomExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Room
        fields = ('id', 'name', 'verbose_name', 'building', 'floor', 'number',
                  'location_name', 'site', 'map_url')


class StaticSiteExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = StaticSite
        fields = ('id', 'event_id', 'event_url', 'state', 'requested_dt', 'url')

    url = fields.Function(lambda site: url_for('static_site.download', site, _external=True))
    event_url = fields.Function(lambda site: url_for('events.display', site.event, _external=True))


class RegistrationFileExportSchema(Schema):
    class Meta:
        fields = ('registration_id', 'field_data_id', 'filename', 'md5', 'url', '_archive_path')

    url = fields.Function(lambda data: url_for('event_registration.manage_registration_file', data.locator.file,
                                               _external=True))
    _archive_path = fields.Function(lambda file: build_storage_path(file))


class ReceiptFileExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = ReceiptFile
        fields = ('file_id', 'is_deleted', 'filename', '_archive_path')

    filename = fields.String(attribute='file.filename')
    url = fields.String(attribute='file.signed_download_url')
    _archive_path = fields.Function(lambda file: build_storage_path(file))


class RegistrationDataExportSchema(Schema):
    title = fields.Function(lambda data: data.field_data.field.title)
    description = fields.Function(lambda data: data.field_data.field.description)
    data = fields.Method('_get_data')

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
        """For file fields, export also the file metadata."""
        if original.filename:
            file_data = RegistrationFileExportSchema().dump(original)
            return data | {'file': file_data}
        else:
            return data


class RegistrationExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Registration
        fields = ('id', 'url', 'event_id', 'event_title', 'event_url', 'state', 'currency', 'price', 'submitted_dt',
                  'email', 'first_name', 'last_name', 'is_deleted', 'checked_in', 'checked_in_dt', 'rejection_reason',
                  'consent_to_publish', 'created_by_manager', 'fields', 'documents')

    price = fields.Decimal(as_string=True)
    url = fields.Function(lambda reg: url_for('event_registration.registration_details', reg, _external=True))
    event_title = fields.Function(lambda reg: reg.event.title)
    event_url = fields.Function(lambda reg: url_for('events.display', reg.event, _external=True))
    documents = fields.List(fields.Nested(ReceiptFileExportSchema), attribute='receipt_files')
    fields = fields.Method('_serialize_data')

    def _serialize_data(self, registration):
        registration_data = [data for data in registration.data if not data.field_data.field.parent.is_manager_only]
        return RegistrationDataExportSchema(many=True).dump(registration_data)


class SubContributionExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SubContribution
        fields = ('id', 'contribution_id', 'subcontribution_id', 'title', 'description',
                  'url', 'event_url', 'duration', 'venue_name', 'room_name',
                  'is_deleted')

    duration = fields.TimeDelta(precision=fields.TimeDelta.MINUTES)
    url = fields.Function(lambda subcontrib: url_for('contributions.display_subcontribution', subcontrib,
                                                     _external=True))
    event_url = fields.Function(lambda subcontrib: url_for('events.display', subcontrib.contribution.event,
                                                           _external=True))


class ContributionExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'contribution_type', 'event_id', 'event_title', 'title', 'description',
                  'url', 'event_url', 'start_dt', 'end_dt', 'duration', 'venue_name', 'room_name', 'address',
                  'keywords', 'is_deleted', 'is_author', 'is_speaker', 'note_id')

    duration = fields.TimeDelta(precision=fields.TimeDelta.MINUTES)
    url = fields.Function(lambda contrib: url_for('contributions.display_contribution', contrib, _external=True))
    event_url = fields.Function(lambda contrib: url_for('events.display', contrib.event, _external=True))
    is_author = fields.Method('_is_author')
    is_speaker = fields.Method('_is_speaker')
    note_id = fields.Integer(attribute='note.id')

    def _is_author(self, contrib):
        user = self.context['user']
        return any(link.is_author for link in contrib.person_links if link.person.user == user)

    def _is_speaker(self, contrib):
        user = self.context['user']
        return any(link.is_speaker for link in contrib.person_links if link.person.user == user)


class AbstractFileExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = AbstractFile
        fields = ('id', 'filename', 'md5', 'url', '_archive_path')

    url = fields.Function(lambda f: url_for('abstracts.download_attachment', f, management=False, _external=True))
    _archive_path = fields.Function(lambda file: build_storage_path(file))


class AbstractExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Abstract
        fields = ('id', 'contribution_id', 'event_id', 'title', 'description', 'files',
                  'submission_comment', 'submitted_dt', 'state', 'url', 'event_url')

    description = fields.String(attribute='_description')
    state = fields.Enum(AbstractState)
    url = fields.Function(lambda abstract: url_for('abstracts.display_abstract', abstract, management=False,
                                                   _external=True))
    event_url = fields.Function(lambda abstract: url_for('events.display', abstract.event, _external=True))
    files = fields.List(fields.Nested(AbstractFileExportSchema))


class PaperFileExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = PaperFile
        fields = ('id', 'filename', 'md5', 'url', '_archive_path')

    url = fields.Function(lambda f: url_for('papers.download_file', f.paper.contribution, f, _external=True))
    path = fields.Function(lambda file: build_storage_path(file))


class PaperExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Contribution
        fields = ('id', 'title', 'description', 'submitted_dt', 'url', 'event_url', 'files')

    submitted_dt = fields.Method('_get_submitted_dt')
    state = fields.Enum(PaperRevisionState)
    url = fields.Function(lambda paper: url_for('papers.paper_timeline', paper, _external=True))
    event_url = fields.Function(lambda paper: url_for('events.display', paper.event, _external=True))
    files = fields.List(fields.Nested(PaperFileExportSchema))

    def _get_submitted_dt(self, paper):
        return fields.DateTime().serialize('submitted_dt', paper.revisions[0])


class PersonalDataExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'full_name', 'title', 'email', 'secondary_emails',
                  'affiliation', 'affiliation_link', 'phone', 'avatar_url', 'picture_metadata', 'picture_source',
                  'favorite_events', 'favorite_categories')

    title = NoneValueEnumField(UserTitle, none_value=UserTitle.none, attribute='_title')
    secondary_emails = fields.Function(lambda user: list(user.secondary_emails))
    affiliation_link = fields.Nested(AffiliationSchema, exclude=('meta',))
    favorite_events = fields.List(fields.Nested(EventExportSchema))
    favorite_categories = fields.List(fields.Nested(CategoryExportSchema))


class RoomBookingExportSchema(Schema):
    from indico.modules.rb.schemas import ReservationSchema

    favorite_rooms = fields.List(fields.Nested(RoomExportSchema))
    owned_rooms = fields.List(fields.Nested(RoomExportSchema))
    reservations = fields.List(fields.Nested(ReservationSchema))
    reservations_booked_for = fields.List(fields.Nested(ReservationSchema))


class MiscDataExportSchema(Schema):
    created_events = fields.List(fields.Nested(EventExportSchema))
    static_sites = fields.List(fields.Nested(StaticSiteExportSchema))
    identities = fields.List(fields.Nested(IdentityExportSchema))
    personal_tokens = fields.List(fields.Nested(PersonalTokenExportSchema))
    api_key = fields.Nested(APIKeyExportSchema)
    old_api_keys = fields.List(fields.Nested(APIKeyExportSchema))
    oauth_applications = fields.List(fields.Nested(OAuthApplicationUserLinkExportSchema), attribute='oauth_app_links')


class AttachmentFileExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = AttachmentFile
        fields = ('id', 'filename', 'md5', '_archive_path')

    _archive_path = fields.Function(lambda file: build_storage_path(file))


class AttachmentExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Attachment
        fields = ('id', 'folder_id', 'folder', 'title', 'url', 'link_url',
                  'type', 'modified_dt', 'description')

    url = fields.String(attribute='absolute_download_url')
    type = fields.Enum(AttachmentType)

    @post_dump(pass_original=True)
    def _add_file(self, data, original, **kwargs):
        """Export the attached file if there is one."""
        if original.file:
            file_data = AttachmentFileExportSchema().dump(original.file)
            return data | {'file': file_data}


class EditableFileExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EditingRevisionFile
        fields = ('filename', 'md5', 'signed_download_url', '_archive_path')

    filename = fields.String(attribute='file.filename')
    md5 = fields.String(attribute='file.md5')
    signed_download_url = fields.String(attribute='file.signed_download_url')
    _archive_path = fields.Function(lambda file: build_storage_path(file))


class EditingRevisionExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EditingRevision
        fields = ('id', 'created_dt', 'type', 'is_undone', 'comment', 'files')

    type = fields.Enum(RevisionType)
    comment = fields.String()  # Coerce MarkdownText to string
    files = fields.List(fields.Nested(EditableFileExportSchema))


class EditableExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Editable
        fields = ('id', 'type', 'contribution_id', 'contribution_title', 'state', 'revisions')

    type = fields.Enum(EditableType)
    contribution_title = fields.Function(lambda editable: editable.contribution.title)
    state = fields.Enum(EditableState, attribute='latest_revision.state')
    revisions = fields.List(fields.Nested(EditingRevisionExportSchema))


class LinkedNoteExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventNote
        fields = ('id', 'is_deleted', 'current_revision_id', 'link_type', 'event_id', 'linked_event_id',
                  'contribution_id', 'subcontribution_id', 'session_id')


class EventNoteRevisionExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = EventNoteRevision
        fields = ('id', 'source', 'render_mode', 'created_dt', 'note')

    note = fields.Nested(LinkedNoteExportSchema)


class SettingsExportSchema(Schema):
    class Meta:
        fields = ('add_ical_alerts', 'add_ical_alerts_mins', 'force_language', 'force_timezone',
                  'lang', 'name_format', 'show_future_events', 'show_past_events',
                  'suggest_categories', 'synced_fields', 'timezone', 'use_markdown_for_minutes',
                  'use_previewer_pdf', 'mastodon_server_url')

    name_format = fields.Function(lambda settings: NameFormat(settings['name_format']).name)


class UserDataExportSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('personal_data', 'settings', 'contributions', 'subcontributions', 'registrations', 'room_booking',
                  'survey_submissions', 'abstracts', 'papers', 'miscellaneous', 'editables', 'attachments',
                  'note_revisions')

    personal_data = fields.Function(lambda user: PersonalDataExportSchema().dump(user))
    settings = fields.Method('_get_settings')
    contributions = fields.Method('_get_contributions')
    subcontributions = fields.Method('_get_subcontributions')
    registrations = fields.Method('_get_registrations')
    room_booking = fields.Function(lambda user: RoomBookingExportSchema().dump(user))
    survey_submissions = fields.Method('_get_survey_submissions')
    abstracts = fields.Method('_get_abstracts')
    papers = fields.Method('_get_papers')
    attachments = fields.Method('_get_attachments')
    editables = fields.Method('_get_editables')
    note_revisions = fields.Method('_get_note_revisions')
    miscellaneous = fields.Function(lambda user: MiscDataExportSchema().dump(user))

    def _get_settings(self, user):
        settings = user.settings.get_all()
        return SettingsExportSchema().dump(settings)

    def _get_contributions(self, user):
        contribs = get_contributions(user)
        return ContributionExportSchema(many=True, context={'user': user}).dump(contribs)

    def _get_subcontributions(self, user):
        subcontribs = get_subcontributions(user)
        return SubContributionExportSchema(many=True, context={'user': user}).dump(subcontribs)

    def _get_registrations(self, user):
        registrations = get_registrations(user)
        return RegistrationExportSchema(many=True).dump(registrations)

    def _get_abstracts(self, user):
        abstracts = get_abstracts(user)
        return AbstractExportSchema(many=True).dump(abstracts)

    def _get_survey_submissions(self, user):
        survey_submissions = get_survey_submissions(user)
        return SurveySubmissionSchema(many=True).dump(survey_submissions)

    def _get_papers(self, user):
        papers = get_papers(user)
        return PaperExportSchema(many=True).dump(papers)

    def _get_attachments(self, user):
        attachments = get_attachments(user)
        return AttachmentExportSchema(many=True).dump(attachments)

    def _get_editables(self, user):
        editables = get_editables(user)
        return EditableExportSchema(many=True).dump(editables)

    def _get_note_revisions(self, user):
        note_revisions = get_note_revisions(user)
        return EventNoteRevisionExportSchema(many=True).dump(note_revisions)

    @post_dump
    def _update_storage_paths(self, data, **kwargs):
        include_files = self.context.get('include_files', False)
        return update_storage_paths(data, include_files)


def update_storage_paths(data, include_files):
    """Recursively filter out or rename storage paths in the user schema."""
    if isinstance(data, list):
        return [update_storage_paths(item, include_files) for item in data]
    elif isinstance(data, dict):
        data = {key: update_storage_paths(value, include_files) for key, value in data.items()}
        if '_archive_path' in data:
            if include_files:
                data['archive_path'] = data['_archive_path']
            del data['_archive_path']
        return data
    else:
        return data
