# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import uuid

from flask import jsonify, request, session
from werkzeug.exceptions import Forbidden

from indico.legacy.common.cache import GenericCache
from indico.modules.events.editing.controllers.base import RHEditablesBase, RHEditableTypeManagementBase
from indico.modules.events.editing.models.editable import Editable
from indico.modules.events.editing.operations import assign_editor, generate_editables_zip, unassign_editor
from indico.util.i18n import _
from indico.util.marshmallow import Principal
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for


archive_cache = GenericCache('editables-archive')


class RHPrepareEditablesArchive(RHEditablesBase):
    def _process(self):
        key = unicode(uuid.uuid4())
        data = [editable.id for editable in self.editables]
        archive_cache.set(key, data, time=1800)
        download_url = url_for('.download_archive', self.event, type=self.editable_type.name, uuid=key)
        return jsonify(download_url=download_url)


class RHDownloadArchive(RHEditableTypeManagementBase):
    def _process(self):
        editable_ids = archive_cache.get(unicode(request.view_args['uuid']), [])
        editables = Editable.query.filter(Editable.id.in_(editable_ids)).all()
        return generate_editables_zip(editables)


class RHAssignEditor(RHEditablesBase):
    @use_kwargs({
        'editor': Principal(required=True)
    })
    def _process_args(self, editor):
        RHEditablesBase._process_args(self)
        if (not self.event.can_manage(editor, self.editable_type.editor_permission)
                and not self.event.can_manage(editor, 'editing_manager')):
            raise Forbidden(_('This user is not an editor of the {} type').format(self.editable_type.name))

        self.editor = editor

    def _process(self):
        for editable in self.editables:
            assign_editor(editable, self.editor)
        return '', 204


class RHAssignMyselfAsEditor(RHEditablesBase):
    def _check_access(self):
        RHEditablesBase._check_access(self)
        if (not self.event.can_manage(session.user, self.editable_type.editor_permission)
                and not self.event.can_manage(session.user, 'editing_manager')):
            raise Forbidden(_('You are not an editor of the {} type').format(self.editable_type.name))

    def _process(self):
        for editable in self.editables:
            assign_editor(editable, session.user)
        return '', 204


class RHUnassignEditor(RHEditablesBase):
    def _process(self):
        for editable in self.editables:
            unassign_editor(editable)
        return '', 204
