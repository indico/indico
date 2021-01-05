# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import current_app, redirect, request
from werkzeug.exceptions import NotFound

from indico.modules.attachments.controllers.util import SpecificAttachmentMixin
from indico.modules.attachments.models.legacy_mapping import LegacyAttachmentFolderMapping, LegacyAttachmentMapping
from indico.modules.events import LegacyEventMapping
from indico.util.string import is_legacy_id
from indico.web.flask.util import url_for
from indico.web.rh import RH, RHSimple


def _clean_args(kwargs):
    if 'event_id' not in kwargs:
        raise NotFound
    if is_legacy_id(kwargs['event_id']):
        mapping = LegacyEventMapping.find(legacy_event_id=kwargs['event_id']).first_or_404()
        kwargs['event_id'] = mapping.event_id
    if 'contrib_id' in kwargs:
        kwargs['contribution_id'] = kwargs.pop('contrib_id')
    if 'subcontrib_id' in kwargs:
        kwargs['subcontribution_id'] = kwargs.pop('subcontrib_id')
    # extension is just to make the links prettier
    kwargs.pop('ext', None)
    # session id is only used for actual sessions, not for stuff inside them
    if 'contribution_id' in kwargs:
        kwargs.pop('session_id', None)


@RHSimple.wrap_function
def compat_folder(**kwargs):
    _clean_args(kwargs)
    folder = LegacyAttachmentFolderMapping.find(**kwargs).first_or_404().folder
    if folder.is_deleted:
        raise NotFound
    return redirect(url_for('attachments.list_folder', folder), 302 if current_app.debug else 301)


def compat_folder_old():
    mapping = {'confId': 'event_id',
               'sessionId': 'session_id',
               'contribId': 'contrib_id',
               'subContId': 'subcontrib_id',
               'materialId': 'material_id'}
    kwargs = {mapping[k]: v for k, v in request.args.iteritems() if k in mapping}
    return compat_folder(**kwargs)


def _redirect_to_note(**kwargs):
    del kwargs['material_id']
    del kwargs['resource_id']
    kwargs['confId'] = kwargs.pop('event_id')
    return redirect(url_for('event_notes.view', **kwargs), 302 if current_app.debug else 301)


@RHSimple.wrap_function
def compat_attachment(**kwargs):
    _clean_args(kwargs)
    mapping = LegacyAttachmentMapping.find_first(**kwargs)
    if mapping is None:
        if kwargs['material_id'] == 'minutes' and kwargs['resource_id'] == 'minutes':
            return _redirect_to_note(**kwargs)
        raise NotFound
    attachment = mapping.attachment
    if attachment.is_deleted or attachment.folder.is_deleted:
        raise NotFound
    return redirect(attachment.download_url, 302 if current_app.debug else 301)


class RHCompatAttachmentNew(SpecificAttachmentMixin, RH):
    normalize_url_spec = dict(SpecificAttachmentMixin.normalize_url_spec,
                              endpoint='attachments.download')

    def _process(self):
        raise Exception('This RH should only perform URL normalization!')
