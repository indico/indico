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
from werkzeug.utils import secure_filename

from indico.core.db import db
from indico.core import signals
from indico.modules.attachments import logger
from indico.modules.attachments.controllers.util import SpecificAttachmentMixin, SpecificFolderMixin
from indico.modules.attachments.forms import (AddAttachmentFilesForm, AttachmentLinkForm, AttachmentFolderForm,
                                              EditAttachmentFileForm)
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.util import get_attached_items
from indico.util.i18n import _, ngettext
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_template, jsonify_data


def _render_attachment_list(linked_object):
    tpl = get_template_module('attachments/_attachments.html')
    return tpl.render_attachments(attachments=get_attached_items(linked_object), linked_object=linked_object)


class ManageAttachmentsMixin:
    """Shows the attachment management page"""
    wp = None

    def _process(self):
        return self.wp.render_template('attachments.html', self.object, linked_object=self.object,
                                       linked_object_type=self.object_type, attachments=get_attached_items(self.object))


class AddAttachmentFilesMixin:
    """Upload file attachments"""

    def _process(self):
        form = AddAttachmentFilesForm(linked_object=self.object)
        if form.validate_on_submit():
            files = request.files.getlist('file')
            folder = form.folder.data or AttachmentFolder.get_or_create_default(linked_object=self.object)
            for f in files:
                filename = secure_filename(f.filename) or 'attachment'
                attachment = Attachment(folder=folder, user=session.user, title=f.filename, type=AttachmentType.file,
                                        protection_mode=form.protection_mode.data)
                attachment.file = AttachmentFile(user=session.user, filename=filename, content_type=f.mimetype)
                attachment.file.save(f.file)
                db.session.add(attachment)
                logger.info('File attachment {} added by {}'.format(attachment, session.user))
                signals.attachments.attachment_created.send(attachment, user=session.user)
            flash(ngettext("The attachment has been uploaded", "%(num)d attachments have been uploaded", len(files)),
                  'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))
        return jsonify_template('attachments/upload.html', form=form, action=url_for('.upload', self.object))


class AddAttachmentLinkMixin:
    """Add link attachment"""

    def _process(self):
        form = AttachmentLinkForm(linked_object=self.object)
        if form.validate_on_submit():
            folder = form.folder.data or AttachmentFolder.get_or_create_default(linked_object=self.object)
            link = Attachment(user=session.user, type=AttachmentType.link)
            form.populate_obj(link, skip={'acl'})
            link.folder = folder
            if link.is_protected:
                link.acl = form.acl.data

            logger.info('Link attachment {} added by {}'.format(link, session.user))
            signals.attachments.attachment_created.send(link, user=session.user)
            flash(_("The link has been added"), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))
        return jsonify_template('attachments/add_link.html', form=form)


class EditAttachmentMixin(SpecificAttachmentMixin):
    """Edit an attachment"""

    def _process(self):
        defaults = FormDefaults(self.attachment, protected=self.attachment.is_protected)
        form_cls = EditAttachmentFileForm if self.attachment.type == AttachmentType.file else AttachmentLinkForm
        form = form_cls(linked_object=self.object, obj=defaults)
        if form.validate_on_submit():
            folder = form.folder.data or AttachmentFolder.get_or_create_default(linked_object=self.object)
            logger.info('Edited attachment {} by {}'.format(self.attachment, session.user))
            form.populate_obj(self.attachment, skip={'acl'})
            self.attachment.folder = folder
            if self.attachment.is_protected:
                self.attachment.acl = form.acl.data
            # files need special handling; links are already updated in `populate_obj`
            if self.attachment.type == AttachmentType.file:
                file = request.files['file'] if request.files else None
                if file:
                    self.attachment.file = AttachmentFile(user=session.user, filename=secure_filename(file.filename),
                                                          content_type=file.mimetype)
                    self.attachment.file.save(file.file)

            signals.attachments.attachment_updated.send(self.attachment, user=session.user)
            flash(_("The attachment has been updated"), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))

        template = ('attachments/upload.html' if self.attachment.type == AttachmentType.file else
                    'attachments/add_link.html')
        return jsonify_template(template, form=form, existing_attachment=self.attachment,
                                action=url_for('.modify_attachment', self.attachment))


class CreateFolderMixin:
    """Create a new empty folder"""

    def _process(self):
        form = AttachmentFolderForm(obj=FormDefaults(is_always_visible=True))
        if form.validate_on_submit():
            folder = AttachmentFolder(linked_object=self.object)
            form.populate_obj(folder, skip={'acl'})
            if folder.is_protected:
                folder.acl = form.acl.data
            db.session.add(folder)
            logger.info('Folder {} created by {}'.format(folder, session.user))
            signals.attachments.folder_created.send(folder, user=session.user)
            flash(_("Folder \"{name}\" created").format(name=folder.title), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))
        return jsonify_template('attachments/create_folder.html', form=form)


class EditFolderMixin(SpecificFolderMixin):
    """Edit a folder"""

    def _process(self):
        defaults = FormDefaults(self.folder, protected=self.folder.is_protected)
        form = AttachmentFolderForm(obj=defaults)
        if form.validate_on_submit():
            form.populate_obj(self.folder, skip={'acl'})
            if self.folder.is_protected:
                self.folder.acl = form.acl.data
            flash(_("Folder \"{name}\" updated").format(name=self.folder.title), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))
        return jsonify_template('attachments/create_folder.html', form=form)


class DeleteFolderMixin(SpecificFolderMixin):
    """Delete a folder"""

    def _process(self):
        self.folder.is_deleted = True
        logger.info('Folder {} deleted by {}'.format(self.folder, session.user))
        signals.attachments.folder_deleted.send(self.folder, user=session.user)
        flash(_("Folder \"{name}\" deleted").format(name=self.folder.title), 'success')
        return jsonify_data(attachment_list=_render_attachment_list(self.object))


class DeleteAttachmentMixin(SpecificAttachmentMixin):
    """Delete an attachment"""

    def _process(self):
        self.attachment = Attachment.get_one(request.view_args['attachment_id'])
        self.attachment.is_deleted = True
        logger.info('Deleted attachment {} by {}'.format(self.attachment, session.user))
        signals.attachments.attachment_deleted.send(self.attachment, user=session.user)
        flash(_("Attachment \"{name}\" deleted").format(name=self.attachment.title), 'success')
        return jsonify_data(attachment_list=_render_attachment_list(self.object))
