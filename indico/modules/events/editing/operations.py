# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.editing import logger
from indico.modules.events.editing.models.editable import Editable
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision, InitialRevisionState


def create_new_editable(contrib, type_, submitter, files):
    editable = Editable(contribution=contrib, type=type_)
    editable_files = [
        EditingRevisionFile(file=file, file_type=file_type)
        for file_type, file_list in files.viewitems()
        for file in file_list
    ]
    for ef in editable_files:
        ef.file.claim(contrib_id=contrib.id, editable_type=type_.name)
    revision = EditingRevision(submitter=submitter,
                               initial_state=InitialRevisionState.ready_for_review,
                               files=editable_files)
    editable.revisions.append(revision)
    logger.info('Editable [%s] created by %s for %s', type_.name, submitter, contrib)
    return editable
