# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from io import BytesIO

import pytest

from indico.core.db import db
from indico.core.db.sqlalchemy.util.management import DEFAULT_TICKET_DATA
from indico.modules.designer import TemplateType
from indico.modules.designer.models.images import DesignerImageFile
from indico.modules.designer.models.templates import DesignerTemplate


# https://github.com/mathiasbynens/small/blob/master/bmp.bmp
DUMMY_BMP_IMAGE = (b'BM\x1e\x00\x00\x00\x00\x00\x00\x00\x1a\x00\x00\x00\x0c\x00'
                   b'\x00\x00\x01\x00\x01\x00\x01\x00\x18\x00\x00\x00\xff\x00')


@pytest.fixture
def create_dummy_designer_template(db):
    def _create(title, *, event=None, category=None, type=TemplateType.badge, data=DEFAULT_TICKET_DATA, **kwargs):
        assert event or category
        template = DesignerTemplate(title=title, event=event, category=category, type=type, data=data, **kwargs)
        db.session.flush()
        return template
    return _create


@pytest.fixture
def dummy_designer_template(dummy_event, create_dummy_designer_template):
    return create_dummy_designer_template('Default ticket', event=dummy_event, type=TemplateType.badge)


@pytest.fixture
def dummy_designer_image_file(dummy_designer_template):
    image = DesignerImageFile(filename='designer-image.bmp', content_type='image/bmp', template=dummy_designer_template)
    image.save(BytesIO(DUMMY_BMP_IMAGE))
    db.session.flush()
    return image
