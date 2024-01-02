# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.editing.models.editable import Editable, EditableType
from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.models.revision_files import EditingRevisionFile
from indico.modules.events.editing.models.revisions import EditingRevision, RevisionType
from indico.util.date_time import now_utc


@pytest.fixture
def create_editable(db):
    """Return a callable which lets you create editables."""
    def _create_editable(contribution, type, **kwargs):
        editable = Editable(contribution=contribution, type=type, **kwargs)
        db.session.flush()
        return editable
    return _create_editable


@pytest.fixture
def dummy_editable(dummy_contribution, create_editable):
    """Create a dummy editable."""
    return create_editable(dummy_contribution, EditableType.paper, id=420)


@pytest.fixture
def create_editing_revision(db):
    """Return a callable which lets you create editing revisions."""
    def _create_editing_revision(editable, user, type, created_dt, **kwargs):
        revision = EditingRevision(editable=editable, user=user, type=type, created_dt=created_dt, **kwargs)
        db.session.flush()
        return revision
    return _create_editing_revision


@pytest.fixture
def dummy_editing_revision(dummy_user, dummy_editable, create_editing_revision):
    """Create a dummy editing revision."""
    return create_editing_revision(dummy_editable, user=dummy_user, id=420, type=RevisionType.acceptance,
                                   created_dt=now_utc())


@pytest.fixture
def create_editing_file_type(db):
    """Return a callable which lets you create editing file types."""
    def _create_editing_file_type(name, extensions, type, **kwargs):
        file_type = EditingFileType(name=name, extensions=extensions, type=type, **kwargs)
        db.session.add(file_type)
        db.session.flush()
        return file_type
    return _create_editing_file_type


@pytest.fixture
def dummy_editing_file_type(create_editing_file_type):
    """Create a dummy editing file type."""
    return create_editing_file_type(id=420, name='TXT', extensions=['txt'], type=EditableType.paper)


@pytest.fixture
def create_editing_revision_file(db):
    """Return a callable which lets you create editing revision files."""
    def _create_paper_file(revision, file, **kwargs):
        revision_file = EditingRevisionFile(revision=revision, file=file, **kwargs)
        file.claim()
        db.session.flush()
        return revision_file
    return _create_paper_file


@pytest.fixture
def dummy_editing_revision_file(dummy_editing_revision, dummy_file, create_editing_revision_file):
    """Create a dummy editing revision file."""
    return create_editing_revision_file(dummy_editing_revision, dummy_file)
