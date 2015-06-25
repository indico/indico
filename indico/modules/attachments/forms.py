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
from wtforms.fields import BooleanField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired

from indico.core.db import db
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget


class AddAttachmentsForm(IndicoForm):
    protected = BooleanField(_('Protected'), widget=SwitchWidget(),
                             description=_('By default, the attachments will inherit the protection of the parent. '
                                           'Checking this field will restrict all access. The protection can be '
                                           'modified later on from the attachment settings.'))

    folder = QuerySelectField(_('Folder'), allow_blank=True, blank_text=_('No folder selected'), get_label='title',
                              description=_('Adding attachments to folders allow grouping and easier permission '
                                            'management.'))

    def __init__(self, *args, **kwargs):
        linked_object = kwargs.pop('linked_object')
        super(AddAttachmentsForm, self).__init__(*args, **kwargs)
        self.folder.query = (AttachmentFolder.find(linked_object=linked_object)
                                             .order_by(db.func.lower(AttachmentFolder.title)))


class AddLinkForm(AddAttachmentsForm):
    link = URLField(_('URL'), [DataRequired()])
