# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from wtforms.fields import BooleanField, TextAreaField, URLField
from wtforms.fields.simple import HiddenField, StringField
from wtforms.validators import DataRequired, Optional, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.settings import AttachmentPackageAccess
from indico.modules.attachments.util import get_default_folder_names
from indico.modules.core.captcha import WTFCaptchaField
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import (AccessControlListField, EditableFileField, FileField, IndicoDateField,
                                     IndicoRadioField, IndicoSelectMultipleCheckboxField)
from indico.web.forms.fields.enums import IndicoEnumSelectField
from indico.web.forms.validators import HiddenUnless, UsedIf
from indico.web.forms.widgets import SwitchWidget, TypeaheadWidget


def _is_user_search_allowed(obj):
    # If public user search is disabled, we require full management access on the object
    # so people who are just submitters (typically those are speakers not involved in
    # organizing the event) do not get access to the user search.
    return config.ALLOW_PUBLIC_USER_SEARCH or obj.can_manage(session.user)


class AttachmentFormBase(IndicoForm):
    protected = BooleanField(_('Protected'), widget=SwitchWidget())
    folder = QuerySelectField(_('Folder'), allow_blank=True, blank_text=_('No folder selected'), get_label='title',
                              description=_('Adding materials to folders allow grouping and easier permission '
                                            'management.'))
    acl = AccessControlListField(_('Access control list'), [UsedIf(lambda form, field: form.protected.data)],
                                 allow_groups=True, allow_external_users=True, allow_event_roles=True,
                                 allow_category_roles=True, allow_registration_forms=True,
                                 event=lambda form: form.event,
                                 description=_('The list of users and groups allowed to access the material'))

    def __init__(self, *args, linked_object, **kwargs):
        self.event = getattr(linked_object, 'event', None)  # not present in categories
        super().__init__(*args, **kwargs)
        # this also tells the ACL field to not provide a search token, even though
        # the field should not be displayed anyway
        self.allow_user_search = _is_user_search_allowed(linked_object)
        self.folder.query = (AttachmentFolder.query
                             .filter_by(object=linked_object, is_default=False, is_deleted=False)
                             .order_by(db.func.lower(AttachmentFolder.title)))
        if self.event and self.event.is_unlisted:
            self.acl.allow_category_roles = False
        if not self.allow_user_search:
            del self.acl

    @generated_data
    def protection_mode(self):
        return ProtectionMode.protected if self.protected.data else ProtectionMode.inheriting


class EditAttachmentFormBase(AttachmentFormBase):
    title = StringField(_('Title'), [DataRequired()])
    description = TextAreaField(_('Description'))


class AddAttachmentFilesForm(AttachmentFormBase):
    files = FileField(_('Files'), multiple_files=True)


def _get_file_data(attachment):
    file = attachment.file
    return {
        'url': url_for('attachments.download', attachment, filename=file.filename, from_preview='1'),
        'filename': file.filename,
        'size': file.size,
        'content_type': file.content_type
    }


class EditAttachmentFileForm(EditAttachmentFormBase):
    file = EditableFileField(_('File'), add_remove_links=False, get_metadata=_get_file_data,
                             description=_('Already uploaded file. Replace it by adding a new file.'))


class AttachmentLinkFormMixin:
    title = StringField(_('Title'), [DataRequired()])
    link_url = URLField(_('URL'), [DataRequired()])


class AddAttachmentLinkForm(AttachmentLinkFormMixin, AttachmentFormBase):
    pass


class EditAttachmentLinkForm(AttachmentLinkFormMixin, EditAttachmentFormBase):
    pass


class AttachmentFolderForm(IndicoForm):
    title = HiddenField(_('Name'), [DataRequired()], widget=TypeaheadWidget(),
                        description=_('The name of the folder.'))
    description = TextAreaField(_('Description'), description=_('Description of the folder and its content'))
    protected = BooleanField(_('Protected'), widget=SwitchWidget())
    acl = AccessControlListField(_('Access control list'), [UsedIf(lambda form, field: form.protected.data)],
                                 allow_groups=True, allow_external_users=True, allow_event_roles=True,
                                 allow_category_roles=True, allow_registration_forms=True,
                                 event=lambda form: form.event,
                                 description=_('The list of users and groups allowed to access the folder'))
    is_always_visible = BooleanField(_('Always Visible'),
                                     [HiddenUnless('is_hidden', value=False)],
                                     widget=SwitchWidget(),
                                     description=_('By default, folders are always visible, even if a user cannot '
                                                   'access them. You can disable this behavior here, hiding the folder '
                                                   'for anyone who does not have permission to access it.'))
    is_hidden = BooleanField(_('Always hidden'),
                             [HiddenUnless('is_always_visible', value=False)],
                             widget=SwitchWidget(),
                             description=_('Always hide the folder and its contents from public display areas of '
                                           'the event. You can use this for folders to store non-image files used '
                                           'e.g. in download links. The access permissions still apply.'))

    def __init__(self, *args, linked_object, **kwargs):
        self.linked_object = linked_object
        self.event = getattr(self.linked_object, 'event', None)  # not present in categories
        super().__init__(*args, **kwargs)
        self.title.choices = self._get_title_suggestions()
        # this also tells the ACL field to not provide a search token, even though
        # the field should not be displayed anyway
        self.allow_user_search = _is_user_search_allowed(linked_object)
        if self.event and self.event.is_unlisted:
            self.acl.allow_category_roles = False
        if not self.allow_user_search:
            del self.acl

    def _get_title_suggestions(self):
        query = db.session.query(AttachmentFolder.title).filter_by(is_deleted=False, is_default=False,
                                                                   object=self.linked_object)
        existing = {x[0] for x in query}
        suggestions = set(get_default_folder_names()) - existing
        if self.title.data:
            suggestions.add(self.title.data)
        return sorted(suggestions)

    def validate_is_always_visible(self, field):
        if self.is_always_visible.data and self.is_hidden.data:
            raise ValidationError('These two options cannot be used at the same time')

    validate_is_hidden = validate_is_always_visible

    @generated_data
    def protection_mode(self):
        return ProtectionMode.protected if self.protected.data else ProtectionMode.inheriting


class AttachmentPackageForm(IndicoForm):
    added_since = IndicoDateField(_('Added Since'), [Optional()],
                                  description=_('Include only attachments uploaded after this date'))

    filter_type = IndicoRadioField(_('Include'), [DataRequired()])

    sessions = IndicoSelectMultipleCheckboxField(_('Sessions'),
                                                 [UsedIf(lambda form, _: form.filter_type.data == 'sessions'),
                                                  DataRequired()],
                                                 description=_('Include materials from selected sessions'),
                                                 coerce=int)
    contributions = IndicoSelectMultipleCheckboxField(_('Contributions'),
                                                      [UsedIf(lambda form, _: form.filter_type.data == 'contributions'),
                                                       DataRequired()],
                                                      description=_('Include materials from selected contributions'),
                                                      coerce=int)
    dates = IndicoSelectMultipleCheckboxField(_('Events scheduled on'),
                                              [UsedIf(lambda form, _: form.filter_type.data == 'dates'),
                                               DataRequired()],
                                              description=_('Include materials from sessions/contributions scheduled '
                                                            'on the selected dates'))
    captcha = WTFCaptchaField()


class EventAttachmentPermissionsForm(IndicoForm):
    managers_only = BooleanField(_('Upload: Managers only'), widget=SwitchWidget(),
                                 description=_('Only allow managers to upload materials to the event, '
                                               'contributions and sessions.'))
    generate_package = IndicoEnumSelectField(_('Material packages'), enum=AttachmentPackageAccess,
                                             description=_('Specify who can generate a material package.'))
