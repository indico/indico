# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.papers import Paper
from indico.modules.events.papers.models.revisions import PaperRevision


@pytest.fixture
def dummy_paper(dummy_contribution):
    """Create a dummy paper."""
    return Paper(dummy_contribution)


@pytest.fixture
def create_paper_revision(db):
    """Return a callable which lets you create paper revisions."""
    def _create_paper_revision(paper, submitter):
        revision = PaperRevision(paper=paper, submitter=submitter)
        db.session.flush()
        return revision
    return _create_paper_revision


@pytest.fixture
def dummy_paper_revision(dummy_user, dummy_paper, create_paper_revision):
    """Create a dummy paper revision."""
    return create_paper_revision(dummy_paper, submitter=dummy_user)


@pytest.fixture
def create_paper_file(db):
    """Return a callable which lets you create paper files."""
    def _create_paper_file(revision, file, **kwargs):
        paper_file = PaperFile(filename=file.filename, content_type=file.content_type,
                               paper_revision=revision,
                               _contribution=revision._contribution, **kwargs)
        with file.open() as f:
            paper_file.save(f)
        db.session.flush()
        return paper_file
    return _create_paper_file


@pytest.fixture
def dummy_paper_file(create_paper_file, dummy_paper_revision, dummy_file):
    """Create a dummy paper file."""
    return create_paper_file(dummy_paper_revision, dummy_file, id=420)
