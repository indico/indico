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

from flask import flash, request, session
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from indico.core.db import db
from indico.modules.attachments.views import WPEventAttachments
from indico.modules.attachments.forms import AddAttachmentsForm, AddLinkForm, CreateFolderForm
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.util.i18n import _, ngettext
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for, redirect_or_jsonify
from indico.web.util import jsonify_template, jsonify_data
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


def _get_attachment_list(linked_object):
    folders = (AttachmentFolder
               .find(linked_object=linked_object)
               .order_by(AttachmentFolder.is_default.desc(), db.func.lower(AttachmentFolder.title))
               .options(joinedload(AttachmentFolder.attachments))
               .all())
    if not folders:
        return {}
    # the default folder is never shown as a folder. instead, its
    # files are shown on the same level as other folders
    files = folders.pop(0).attachments if folders[0].is_default else []
    return {
        'folders': folders,
        'files': files
    }


def _render_attachment_list(linked_object):
    tpl = get_template_module('attachments/_attachments.html')
    return tpl.render_attachments(attachments=_get_attachment_list(linked_object), linked_object=linked_object)


class RHEventAttachments(RHConferenceModifBase):
    """Shows the attachments of an event"""

    def _process(self):
        return WPEventAttachments.render_template('attachments.html', self._conf, linked_object=self._conf,
                                                  attachments=_get_attachment_list(self._conf))


class RHEventAttachmentsUpload(RHConferenceModifBase):
    """Upload files"""

    def _process(self):
        form = AddAttachmentsForm(linked_object=self._conf)
        if form.validate_on_submit():
            files = request.files.getlist('file')
            for f in files:
                filename = secure_filename(f.filename) or 'attachment'
                folder = form.folder.data or AttachmentFolder.get_or_create_default(linked_object=self._conf)
                attachment = Attachment(folder=folder, user=session.user, title=f.filename, type=AttachmentType.file)
                attachment.file = AttachmentFile(user=session.user, filename=filename, content_type=f.mimetype)
                attachment.file.save(f.file)
                db.session.add(attachment)
            flash(ngettext("The attachment has been uploaded", "%(num)d attachments have been uploaded", len(files)),
                  'success')
            return jsonify_data(attachment_list=_render_attachment_list(self._conf))
        return jsonify_template('attachments/upload.html', event=self._conf, form=form)


class RHEventAttachmentsAddLink(RHConferenceModifBase):
    """Attach link"""

    def _process(self):
        form = AddLinkForm(linked_object=self._conf)
        if form.validate_on_submit():
            # TODO
            return jsonify_data(attachment_list=_render_attachment_list(self._conf))
        return WPEventAttachments.render_template('add_link.html', self._conf, event=self._conf, form=form)


class RHEventAttachmentsCreateFolder(RHConferenceModifBase):
    """Create a new empty folder"""

    def _process(self):
        form = CreateFolderForm()
        if form.validate_on_submit():
            folder = AttachmentFolder(linked_object=self._conf)
            form.populate_obj(folder, skip={'acl'})
            if folder.is_protected:
                folder.acl = form.acl.data
            db.session.add(folder)
            flash(_("Folder \"{name}\" created").format(name=folder.title), 'success')
            return redirect_or_jsonify(url_for('.index', self._conf),
                                       attachment_list=_render_attachment_list(self._conf))
        return WPEventAttachments.render_template('create_folder.html', self._conf, event=self._conf, form=form)
