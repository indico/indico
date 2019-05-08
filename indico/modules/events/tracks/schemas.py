# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.marshmallow import mm
from indico.modules.events.tracks.models.tracks import Track


class TrackSchema(mm.ModelSchema):
    class Meta:
        model = Track
        fields = ('id', 'title', 'code', 'description')


track_schema = TrackSchema()
track_schema_basic = TrackSchema(only=('id', 'title', 'code'))
