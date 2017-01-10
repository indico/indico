# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from marshmallow.fields import Nested, Float

from indico.core.marshmallow import mm
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.contributions.schemas import contribution_type_schema_basic, ContributionFieldValueSchema
from indico.modules.events.schemas import PersonLinkSchema
from indico.modules.events.tracks.schemas import track_schema_basic
from indico.modules.users.schemas import UserSchema

_basic_abstract_fields = ('id', 'friendly_id', 'title')


class AbstractSchema(mm.ModelSchema):
    submitter = Nested(UserSchema)
    judge = Nested(UserSchema)
    modified_by = Nested(UserSchema)
    duplicate_of = Nested('self', only=_basic_abstract_fields)
    merged_into = Nested('self', only=_basic_abstract_fields)
    submitted_contrib_type = Nested(contribution_type_schema_basic)
    accepted_contrib_type = Nested(contribution_type_schema_basic)
    accepted_track = Nested(track_schema_basic)
    submitted_for_tracks = Nested(track_schema_basic, many=True)
    reviewed_for_tracks = Nested(track_schema_basic, many=True)
    persons = Nested(PersonLinkSchema, attribute='person_links', many=True)
    custom_fields = Nested(ContributionFieldValueSchema, attribute='field_values', many=True)
    score = Float()
    # XXX: should we add comments and reviews too at some point?

    class Meta:
        model = Abstract
        fields = ('id', 'friendly_id',
                  'title', 'content',
                  'submitted_dt', 'modified_dt', 'judgment_dt',
                  'state',
                  'submitter', 'modified_by', 'judge',
                  'submission_comment', 'judgment_comment',
                  'submitted_contrib_type', 'accepted_contrib_type',
                  'accepted_track', 'submitted_for_tracks', 'reviewed_for_tracks',
                  'duplicate_of', 'merged_into',
                  'persons', 'custom_fields',
                  'score')


abstracts_schema = AbstractSchema(many=True)
