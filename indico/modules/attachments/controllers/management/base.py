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

import mimetypes

from flask import flash, request, session, render_template

from indico.core import signals
from indico.core.db import db
from indico.modules.attachments import logger
from indico.modules.attachments.controllers.util import SpecificAttachmentMixin, SpecificFolderMixin
from indico.modules.attachments.forms import (AddAttachmentFilesForm, AddAttachmentLinkForm, AttachmentFolderForm,
                                              EditAttachmentFileForm, EditAttachmentLinkForm)
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.util import get_attached_items
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_template, jsonify_data


def _render_attachment_list(linked_object):
    tpl = get_template_module('attachments/_attachments.html')
    return tpl.render_attachments(attachments=get_attached_items(linked_object), linked_object=linked_object)


def _render_protection_message(linked_object):
    return render_template('attachments/_protection_message.html', parent=_get_parent_info(linked_object))


def _get_parent_info(parent):
    from MaKaC.conference import Conference, Session, Contribution, SubContribution, Category
    parent_data = {'is_protected': parent.isProtected()}
    if isinstance(parent, Conference):
        parent_data['type'] = _('Event')
    elif isinstance(parent, Session):
        parent_data['type'] = _('Session')
    elif isinstance(parent, Contribution):
        parent_data['type'] = _('Contribution')
    elif isinstance(parent, SubContribution):
        parent_data['type'] = _('Sub contribution')
    elif isinstance(parent, Category):
        parent_data['type'] = _('Category')
    parent_data['title'] = parent.name if isinstance(parent, Category) else parent.title
    return parent_data


def _get_folders_protection_info(linked_object):
    folders = AttachmentFolder.find(linked_object=linked_object, is_deleted=False)
    return {folder.id: folder.is_protected for folder in folders}


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
                filename = secure_filename(f.filename, 'attachment')
                attachment = Attachment(folder=folder, user=session.user, title=f.filename, type=AttachmentType.file,
                                        protection_mode=form.protection_mode.data)
                if attachment.is_protected:
                    attachment.acl = form.acl.data
                content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
                attachment.file = AttachmentFile(user=session.user, filename=filename, content_type=content_type)
                attachment.file.save(f.file)
                db.session.add(attachment)
                db.session.flush()
                logger.info('Attachment {} uploaded by {}'.format(attachment, session.user))
                signals.attachments.attachment_created.send(attachment, user=session.user)
            flash(ngettext("The attachment has been uploaded", "{count} attachments have been uploaded", len(files))
                  .format(count=len(files)), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))
        return jsonify_template('attachments/upload.html', form=form, action=url_for('.upload', self.object),
                                protection_message=_render_protection_message(self.object),
                                folders_protection_info=_get_folders_protection_info(self.object))


class AddAttachmentLinkMixin:
    """Add link attachment"""

    def _process(self):
        form = AddAttachmentLinkForm(linked_object=self.object)
        if form.validate_on_submit():
            folder = form.folder.data or AttachmentFolder.get_or_create_default(linked_object=self.object)
            link = Attachment(user=session.user, type=AttachmentType.link)
            form.populate_obj(link, skip={'acl'})
            if link.is_protected:
                link.acl = form.acl.data
            link.folder = folder

            db.session.flush()
            logger.info('Attachment {} added by {}'.format(link, session.user))
            signals.attachments.attachment_created.send(link, user=session.user)
            flash(_("The link has been added"), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))
        return jsonify_template('attachments/add_link.html', form=form,
                                protection_message=_render_protection_message(self.object),
                                folders_protection_info=_get_folders_protection_info(self.object))


class EditAttachmentMixin(SpecificAttachmentMixin):
    """Edit an attachment"""

    def _process(self):
        defaults = FormDefaults(self.attachment, protected=self.attachment.is_protected, skip_attrs={'file'})
        form_cls = EditAttachmentFileForm if self.attachment.type == AttachmentType.file else EditAttachmentLinkForm
        file_ = self.attachment.file

        # file_attrs has to be manually "serialized", since it's going to be converted to JSON
        file_attrs = {
            'url': url_for('attachments.download', self.attachment,
                           filename=self.attachment.file.filename, from_preview='1'),
            'filename': file_.filename,
            'size': file_.size,
            'content_type': file_.content_type
        }

        form = form_cls(linked_object=self.object, obj=defaults, file=file_attrs)

        if form.validate_on_submit():
            folder = form.folder.data or AttachmentFolder.get_or_create_default(linked_object=self.object)
            logger.info('Attachment {} edited by {}'.format(self.attachment, session.user))
            form.populate_obj(self.attachment, skip={'acl', 'file'})
            self.attachment.folder = folder
            if self.attachment.is_protected:
                self.attachment.acl = form.acl.data
            # files need special handling; links are already updated in `populate_obj`
            if self.attachment.type == AttachmentType.file:
                file = request.files['file'] if request.files else None
                if file:
                    self.attachment.file = AttachmentFile(user=session.user, content_type=file.mimetype,
                                                          filename=secure_filename(file.filename, 'attachment'))
                    self.attachment.file.save(file.file)

            signals.attachments.attachment_updated.send(self.attachment, user=session.user)
            flash(_("The attachment \"{name}\" has been updated").format(name=self.attachment.title), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))

        template = ('attachments/upload.html' if self.attachment.type == AttachmentType.file else
                    'attachments/add_link.html')
        return jsonify_template(template, form=form, existing_attachment=self.attachment,
                                action=url_for('.modify_attachment', self.attachment),
                                protection_message=_render_protection_message(self.object),
                                folders_protection_info=_get_folders_protection_info(self.object))


class CreateFolderMixin:
    """Create a new empty folder"""

    def _process(self):
        form = AttachmentFolderForm(obj=FormDefaults(is_always_visible=True), linked_object=self.object)
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
        return jsonify_template('attachments/create_folder.html', form=form,
                                protection_message=_render_protection_message(self.object))


class EditFolderMixin(SpecificFolderMixin):
    """Edit a folder"""

    def _process(self):
        defaults = FormDefaults(self.folder, protected=self.folder.is_protected)
        form = AttachmentFolderForm(obj=defaults, linked_object=self.object)
        if form.validate_on_submit():
            form.populate_obj(self.folder, skip={'acl'})
            if self.folder.is_protected:
                self.folder.acl = form.acl.data
            logger.info('Folder {} edited by {}'.format(self.folder, session.user))
            signals.attachments.folder_updated.send(self.folder, user=session.user)
            flash(_("Folder \"{name}\" updated").format(name=self.folder.title), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))
        return jsonify_template('attachments/create_folder.html', form=form,
                                protection_message=_render_protection_message(self.object))


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
        self.attachment.is_deleted = True
        logger.info('Attachment {} deleted by {}'.format(self.attachment, session.user))
        signals.attachments.attachment_deleted.send(self.attachment, user=session.user)
        flash(_("Attachment \"{name}\" deleted").format(name=self.attachment.title), 'success')
        return jsonify_data(attachment_list=_render_attachment_list(self.object))
