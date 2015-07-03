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

from flask import current_app, redirect

from indico.modules.attachments.models.legacy_mapping import LegacyAttachmentFolderMapping, LegacyAttachmentMapping
from indico.web.flask.util import url_for
from MaKaC.webinterface.rh.base import RHSimple


def _clean_args(kwargs):
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
    mapping = LegacyAttachmentFolderMapping.find(**kwargs).first_or_404()
    return redirect(url_for('attachments.list_folder', mapping.folder), 302 if current_app.debug else 301)


@RHSimple.wrap_function
def compat_attachment(**kwargs):
    _clean_args(kwargs)
    mapping = LegacyAttachmentMapping.find(**kwargs).first_or_404()
    return redirect(mapping.attachment.download_url, 302 if current_app.debug else 301)
