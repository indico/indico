# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.abstracts.models.abstracts import Abstract


@pytest.fixture
def create_abstract(db):
    """Return a callable that lets you create an abstract."""

    def _create_abstract(event, title, **kwargs):
        abstract = Abstract(event=event, title=title, **kwargs)
        db.session.add(abstract)
        db.session.flush()
        return abstract

    return _create_abstract
