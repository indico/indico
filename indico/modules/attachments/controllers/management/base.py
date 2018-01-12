# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import flash, render_template, request, session

from indico.core import signals
from indico.core.db import db
from indico.modules.attachments import logger
from indico.modules.attachments.controllers.util import SpecificAttachmentMixin, SpecificFolderMixin
from indico.modules.attachments.forms import (AddAttachmentFilesForm, AddAttachmentLinkForm, AttachmentFolderForm,
                                              EditAttachmentFileForm, EditAttachmentLinkForm)
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.operations import add_attachment_link
from indico.modules.attachments.util import get_attached_items
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.util.string import to_unicode
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_template


def _render_attachment_list(linked_object):
    tpl = get_template_module('attachments/_attachments.html')
    return tpl.render_attachments(attachments=get_attached_items(linked_object), linked_object=linked_object)


def _render_protection_message(linked_object):
    return render_template('attachments/_protection_message.html', parent=_get_parent_info(linked_object))


def _get_parent_info(parent):
    parent_data = {'is_protected': parent.is_protected,
                   'title': parent.title}
    if isinstance(parent, db.m.Event):
        parent_data['type'] = _('Event')
    elif isinstance(parent, db.m.Session):
        parent_data['type'] = _('Session')
    elif isinstance(parent, db.m.Contribution):
        parent_data['type'] = _('Contribution')
    elif isinstance(parent, db.m.SubContribution):
        parent_data['type'] = _('Sub contribution')
    elif isinstance(parent, db.m.Category):
        parent_data['type'] = _('Category')
    return parent_data


def _get_folders_protection_info(linked_object):
    folders = AttachmentFolder.find(object=linked_object, is_deleted=False)
    return {folder.id: folder.is_self_protected for folder in folders}


class ManageAttachmentsMixin:
    """Shows the attachment management page"""
    wp = None

    def _process(self):
        tpl_args = {'linked_object': self.object, 'linked_object_type': self.object_type,
                    'attachments': get_attached_items(self.object)}
        if self.object_type == 'event':
            return self.wp.render_template('attachments.html', self.event, **tpl_args)
        elif self.object_type == 'category' and not request.is_xhr:
            return self.wp.render_template('management/attachments.html', self.category, 'attachments', **tpl_args)
        else:
            return jsonify_template('attachments/attachments.html', **tpl_args)


class AddAttachmentFilesMixin:
    """Upload file attachments"""

    def _process(self):
        form = AddAttachmentFilesForm(linked_object=self.object)
        if form.validate_on_submit():
            files = form.files.data
            folder = form.folder.data or AttachmentFolder.get_or_create_default(linked_object=self.object)
            for f in files:
                filename = secure_filename(f.filename, 'attachment')
                attachment = Attachment(folder=folder, user=session.user, title=to_unicode(f.filename),
                                        type=AttachmentType.file, protection_mode=form.protection_mode.data)
                if attachment.is_self_protected:
                    attachment.acl = form.acl.data
                content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
                attachment.file = AttachmentFile(user=session.user, filename=filename, content_type=content_type)
                attachment.file.save(f.stream)
                db.session.add(attachment)
                db.session.flush()
                logger.info('Attachment %s uploaded by %s', attachment, session.user)
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
            add_attachment_link(form.data, self.object)
            flash(_("The link has been added"), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))
        return jsonify_template('attachments/add_link.html', form=form,
                                protection_message=_render_protection_message(self.object),
                                folders_protection_info=_get_folders_protection_info(self.object))


class EditAttachmentMixin(SpecificAttachmentMixin):
    """Edit an attachment"""

    def _process(self):
        defaults = FormDefaults(self.attachment, protected=self.attachment.is_self_protected, skip_attrs={'file'})
        if self.attachment.type == AttachmentType.file:
            form = EditAttachmentFileForm(linked_object=self.object, obj=defaults, file=self.attachment)
        else:
            form = EditAttachmentLinkForm(linked_object=self.object, obj=defaults)

        if form.validate_on_submit():
            folder = form.folder.data or AttachmentFolder.get_or_create_default(linked_object=self.object)
            logger.info('Attachment %s edited by %s', self.attachment, session.user)
            form.populate_obj(self.attachment, skip={'acl', 'file'})
            self.attachment.folder = folder
            if self.attachment.is_self_protected:
                # can't use `=` because of https://bitbucket.org/zzzeek/sqlalchemy/issues/3583
                self.attachment.acl |= form.acl.data
                self.attachment.acl &= form.acl.data
            # files need special handling; links are already updated in `populate_obj`
            if self.attachment.type == AttachmentType.file:
                file = form.file.data['added']
                if file:
                    self.attachment.file = AttachmentFile(user=session.user, content_type=file.mimetype,
                                                          filename=secure_filename(file.filename, 'attachment'))
                    self.attachment.file.save(file.stream)

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
            folder = AttachmentFolder(object=self.object)
            form.populate_obj(folder, skip={'acl'})
            if folder.is_self_protected:
                folder.acl = form.acl.data
            db.session.add(folder)
            logger.info('Folder %s created by %s', folder, session.user)
            signals.attachments.folder_created.send(folder, user=session.user)
            flash(_("Folder \"{name}\" created").format(name=folder.title), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))
        return jsonify_template('attachments/create_folder.html', form=form,
                                protection_message=_render_protection_message(self.object))


class EditFolderMixin(SpecificFolderMixin):
    """Edit a folder"""

    def _process(self):
        defaults = FormDefaults(self.folder, protected=self.folder.is_self_protected)
        form = AttachmentFolderForm(obj=defaults, linked_object=self.object)
        if form.validate_on_submit():
            form.populate_obj(self.folder, skip={'acl'})
            if self.folder.is_self_protected:
                # can't use `=` because of https://bitbucket.org/zzzeek/sqlalchemy/issues/3583
                self.folder.acl |= form.acl.data
                self.folder.acl &= form.acl.data
            logger.info('Folder %s edited by %s', self.folder, session.user)
            signals.attachments.folder_updated.send(self.folder, user=session.user)
            flash(_("Folder \"{name}\" updated").format(name=self.folder.title), 'success')
            return jsonify_data(attachment_list=_render_attachment_list(self.object))
        return jsonify_template('attachments/create_folder.html', form=form,
                                protection_message=_render_protection_message(self.object))


class DeleteFolderMixin(SpecificFolderMixin):
    """Delete a folder"""

    def _process(self):
        self.folder.is_deleted = True
        logger.info('Folder %s deleted by %s', self.folder, session.user)
        signals.attachments.folder_deleted.send(self.folder, user=session.user)
        flash(_("Folder \"{name}\" deleted").format(name=self.folder.title), 'success')
        return jsonify_data(attachment_list=_render_attachment_list(self.object))


class DeleteAttachmentMixin(SpecificAttachmentMixin):
    """Delete an attachment"""

    def _process(self):
        self.attachment.is_deleted = True
        logger.info('Attachment %s deleted by %s', self.attachment, session.user)
        signals.attachments.attachment_deleted.send(self.attachment, user=session.user)
        flash(_("Attachment \"{name}\" deleted").format(name=self.attachment.title), 'success')
        return jsonify_data(attachment_list=_render_attachment_list(self.object))
