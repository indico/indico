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


from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.ext.dateutil.fields import DateField
from wtforms.fields import BooleanField, TextAreaField
from wtforms.fields.html5 import URLField
from wtforms.fields.simple import StringField, HiddenField
from wtforms.validators import DataRequired, Optional

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.util import get_default_folder_names
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import PrincipalListField, IndicoSelectMultipleCheckboxField, IndicoRadioField
from indico.web.forms.validators import UsedIf, HiddenUnless
from indico.web.forms.widgets import SwitchWidget, TypeaheadWidget, DropzoneWidget


class AttachmentFormBase(IndicoForm):
    protected = BooleanField(_("Protected"), widget=SwitchWidget())
    folder = QuerySelectField(_("Folder"), allow_blank=True, blank_text=_("No folder selected"), get_label='title',
                              description=_("Adding materials to folders allow grouping and easier permission "
                                            "management."))
    acl = PrincipalListField(_("Grant Access To"), [UsedIf(lambda form, field: form.protected.data)],
                             groups=True, serializable=False, allow_external=True,
                             description=_("The list of users and groups with access to the material"))

    def __init__(self, *args, **kwargs):
        linked_object = kwargs.pop('linked_object')
        super(AttachmentFormBase, self).__init__(*args, **kwargs)
        self.folder.query = (AttachmentFolder
                             .find(linked_object=linked_object, is_default=False, is_deleted=False)
                             .order_by(db.func.lower(AttachmentFolder.title)))

    @generated_data
    def protection_mode(self):
        return ProtectionMode.protected if self.protected.data else ProtectionMode.inheriting


class EditAttachmentFormBase(AttachmentFormBase):
    title = StringField(_("Title"), [DataRequired()])
    description = TextAreaField(_("Description"))


class AddAttachmentFilesForm(AttachmentFormBase):
    files = HiddenField(_("Files"), widget=DropzoneWidget(submit_form=False))


class EditAttachmentFileForm(EditAttachmentFormBase):
    file = HiddenField(_("File"), widget=DropzoneWidget(max_files=1, submit_form=False),
                       description=_("Already uploaded file. Replace it by adding a new file."))


class AttachmentLinkFormMixin(object):
    title = StringField(_("Title"), [DataRequired()])
    link_url = URLField(_("URL"), [DataRequired()])


class AddAttachmentLinkForm(AttachmentLinkFormMixin, AttachmentFormBase):
    pass


class EditAttachmentLinkForm(AttachmentLinkFormMixin, EditAttachmentFormBase):
    pass


class AttachmentFolderForm(IndicoForm):
    title = HiddenField(_("Name"), [DataRequired()], widget=TypeaheadWidget(),
                        description=_("The name of the folder."))
    description = TextAreaField(_("Description"), description=_("Description of the folder and its content"))
    protected = BooleanField(_("Protected"), widget=SwitchWidget())
    acl = PrincipalListField(_("Grant Access To"), [UsedIf(lambda form, field: form.protected.data)],
                             groups=True, serializable=False, allow_external=True,
                             description=_("The list of users and groups with access to the folder"))
    is_always_visible = BooleanField(_("Always Visible"), widget=SwitchWidget(),
                                     description=_("By default, folders are always visible, even if a user cannot "
                                                   "access them. You can disable this behavior here, hiding the folder "
                                                   "for anyone who does not have permission to access it."))

    def __init__(self, *args, **kwargs):
        self.linked_object = kwargs.pop('linked_object')
        super(AttachmentFolderForm, self).__init__(*args, **kwargs)
        self.title.choices = self._get_title_suggestions()

    def _get_title_suggestions(self):
        query = db.session.query(AttachmentFolder.title).filter_by(is_deleted=False, is_default=False,
                                                                   linked_object=self.linked_object)
        existing = set(x[0] for x in query)
        suggestions = set(get_default_folder_names()) - existing
        if self.title.data:
            suggestions.add(self.title.data)
        return sorted(suggestions)

    @generated_data
    def protection_mode(self):
        return ProtectionMode.protected if self.protected.data else ProtectionMode.inheriting


class AttachmentPackageForm(IndicoForm):
    added_since = DateField(_('Added Since'), [Optional()], parse_kwargs={'dayfirst': True},
                            description=_('Include only attachments uploaded after this date'))

    filter_type = IndicoRadioField(_('Include'), [DataRequired()])

    sessions = IndicoSelectMultipleCheckboxField(_('Sessions'), [HiddenUnless('filter_type', 'sessions'),
                                                                 DataRequired()],
                                                 description=_('Include materials from selected sessions'))
    contributions = IndicoSelectMultipleCheckboxField(_('Contributions'),
                                                      [HiddenUnless('filter_type', 'contributions'), DataRequired()],
                                                      description=_('Include materials from selected contributions'))
    dates = IndicoSelectMultipleCheckboxField(_('Events scheduled on'), [HiddenUnless('filter_type', 'dates'),
                                                                         DataRequired()],
                                              description=_('Include materials from sessions/contributions scheduled '
                                                            'on the selected dates'))
