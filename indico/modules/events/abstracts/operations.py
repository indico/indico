# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import session

from indico.core import signals
from indico.core.db import db
from indico.modules.events.abstracts import logger
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind
from indico.modules.events.util import set_custom_fields
from indico.util.fs import secure_filename


def create_abstract(event, abstract_data, custom_fields_data=None):
    abstract = Abstract(event_new=event, submitter=session.user)
    files = abstract_data.pop('attachments', [])
    abstract.populate_from_dict(abstract_data)
    if custom_fields_data:
        set_custom_fields(abstract, custom_fields_data)
    db.session.flush()
    for f in files:
        filename = secure_filename(f.filename, 'attachment')
        content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
        abstract_file = AbstractFile(filename=filename, content_type=content_type, abstract=abstract)
        abstract_file.save(f.file)
        db.session.flush()
    signals.event.abstract_created.send(abstract)
    logger.info('Abstract %s created by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.positive, 'Abstracts',
                           'Abstract "{}" has been created'.format(abstract.title), session.user)
    return abstract


def delete_abstract(abstract):
    abstract.is_deleted = True
    abstract.contribution = None
    db.session.flush()
    signals.event.abstract_deleted.send(abstract)
    logger.info('Abstract %s deleted by %s', abstract, session.user)
    abstract.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Abstracts',
                           'Abstract "{}" has been deleted'.format(abstract.title), session.user)
