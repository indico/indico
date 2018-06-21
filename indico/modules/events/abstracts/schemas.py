# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from marshmallow.fields import Float, Nested

from indico.core.marshmallow import mm
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.comments import AbstractComment
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.models.review_questions import AbstractReviewQuestion
from indico.modules.events.abstracts.models.review_ratings import AbstractReviewRating
from indico.modules.events.abstracts.models.reviews import AbstractReview
from indico.modules.events.contributions.schemas import ContributionFieldValueSchema, contribution_type_schema_basic
from indico.modules.events.tracks.schemas import track_schema_basic
from indico.modules.users.schemas import UserSchema


_basic_abstract_fields = ('id', 'friendly_id', 'title')


class AbstractCommentSchema(mm.ModelSchema):
    user = Nested(UserSchema)
    modified_by = Nested(UserSchema)

    class Meta:
        model = AbstractComment
        fields = ('id', 'visibility', 'text',
                  'created_dt', 'user',
                  'modified_dt', 'modified_by')


class AbstractReviewQuestionSchema(mm.ModelSchema):
    class Meta:
        model = AbstractReviewQuestion
        fields = ('id', 'no_score', 'position', 'title')


class AbstractReviewRatingSchema(mm.ModelSchema):
    class Meta:
        model = AbstractReviewRating
        fields = ('question', 'value')


class AbstractReviewSchema(mm.ModelSchema):
    track = Nested(track_schema_basic)
    user = Nested(UserSchema)
    proposed_related_abstract = Nested('AbstractSchema', only=_basic_abstract_fields)
    proposed_contrib_type = Nested(contribution_type_schema_basic, attribute='proposed_contribution_type')
    proposed_tracks = Nested(track_schema_basic, many=True)
    ratings = Nested(AbstractReviewRatingSchema, many=True)

    class Meta:
        model = AbstractReview
        fields = ('id', 'track', 'user', 'comment', 'created_dt', 'modified_dt',
                  'proposed_action', 'proposed_contrib_type', 'proposed_related_abstract', 'proposed_tracks',
                  'ratings')


class AbstractPersonLinkSchema(mm.ModelSchema):
    class Meta:
        model = AbstractPersonLink
        fields = ('id', 'person_id', 'email', 'first_name', 'last_name', 'title', 'affiliation', 'address', 'phone',
                  'is_speaker', 'author_type')


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
    persons = Nested(AbstractPersonLinkSchema, attribute='person_links', many=True)
    custom_fields = Nested(ContributionFieldValueSchema, attribute='field_values', many=True)
    score = Float()
    comments = Nested(AbstractCommentSchema, many=True)
    reviews = Nested(AbstractReviewSchema, many=True)

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
                  'score', 'comments', 'reviews')


abstracts_schema = AbstractSchema(many=True)
abstract_review_questions_schema = AbstractReviewQuestionSchema(many=True)
