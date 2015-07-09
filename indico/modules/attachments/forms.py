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
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Optional

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import PrincipalListField, IndicoSelectMultipleCheckboxField
from indico.web.forms.validators import UsedIf
from indico.web.forms.widgets import SwitchWidget


class AttachmentFormBase(IndicoForm):
    protected = BooleanField(_("Protected"), widget=SwitchWidget(),
                             description=_("By default, the materials will inherit the protection of the parent. "
                                           "Checking this field will restrict all access. The protection can be "
                                           "modified later on from the material settings."))

    folder = QuerySelectField(_("Folder"), allow_blank=True, blank_text=_("No folder selected"), get_label='title',
                              description=_("Adding materials to folders allow grouping and easier permission "
                                            "management."))

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
    acl = PrincipalListField(_("Grant Access To"), [UsedIf(lambda form, field: form.protected.data)],
                             groups=True, serializable=False, allow_external=True,
                             description=_("The list of users and groups with access to the material"))


class AddAttachmentFilesForm(AttachmentFormBase):
    pass


class EditAttachmentFileForm(EditAttachmentFormBase):
    pass


class AttachmentLinkFormMixin(object):
    title = StringField(_("Title"), [DataRequired()])
    link_url = URLField(_("URL"), [DataRequired()])


class AddAttachmentLinkForm(AttachmentLinkFormMixin, AttachmentFormBase):
    pass


class EditAttachmentLinkForm(AttachmentLinkFormMixin, EditAttachmentFormBase):
    pass


class AttachmentFolderForm(IndicoForm):
    title = StringField(_("Name"), [DataRequired()], description=_("The name of the folder."))
    description = TextAreaField(_("Description"), description=_("Description of the folder and its content"))
    protected = BooleanField(_("Protected"), widget=SwitchWidget(),
                             description=_("By default, the folder will inherit the protection of the event. "
                                           "Checking this field will restrict all access. The protection can be "
                                           "modified later on from the folder settings."))
    acl = PrincipalListField(_("Grant Access To"), [UsedIf(lambda form, field: form.protected.data)],
                             groups=True, serializable=False, allow_external=True,
                             description=_("The list of users and groups with access to the folder"))
    is_always_visible = BooleanField(_("Always Visible"), widget=SwitchWidget(),
                                     description=_("By default, folders are always visible, even if a user cannot "
                                                   "access them. You can disable this behavior here, hiding the folder "
                                                   "for anyone who does not have permission to access it."))

    @generated_data
    def protection_mode(self):
        return ProtectionMode.protected if self.protected.data else ProtectionMode.inheriting


class AttachmentPackageForm(IndicoForm):
    added_since = DateField(_('Added Since'), [Optional()], parse_kwargs={'dayfirst': True},
                            description=_('Include only attachments uploaded after this date'))
    sessions = IndicoSelectMultipleCheckboxField(_('Sessions'),
                                                 description=_('Include attachments from selected sessions'))
    contributions = IndicoSelectMultipleCheckboxField(_('Contributions'),
                                                      description=_('Include attachments from selected contributions'))
