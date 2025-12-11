# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields

from indico.core.marshmallow import mm
from indico.modules.events.tracks.models.groups import TrackGroup
from indico.modules.events.tracks.models.principals import TrackPrincipal
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.tracks.settings import track_settings
from indico.util.marshmallow import PrincipalPermissionList


class TrackSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Track
        fields = ('id', 'title', 'code', 'description', 'position', 'track_group_id')


class TrackGroupSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = TrackGroup
        fields = ('id', 'title', 'code', 'description', 'position')


class TrackPermissionsSchema(mm.Schema):
    acl_entries = PrincipalPermissionList(TrackPrincipal)


class ProgramSchema(mm.Schema):
    program = fields.Method('_get_program')
    tracks = fields.List(fields.Nested(TrackSchema))
    track_groups = fields.List(fields.Nested(TrackGroupSchema))

    def _get_program(self, event):
        return track_settings.get(event, 'program')


track_schema = TrackSchema()
track_schema_basic = TrackSchema(only=('id', 'title', 'code'))
track_permissions_schema = TrackPermissionsSchema()
