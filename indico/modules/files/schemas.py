# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.marshmallow import mm
from indico.modules.files.models.files import File


class FileSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = File
        fields = ('claimed', 'content_type', 'created_dt', 'filename', 'size', 'uuid')


class BasicFileSchema(FileSchema):
    class Meta:
        fields = ('filename', 'size', 'uuid')
