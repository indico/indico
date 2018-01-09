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

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.event import listens_for

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.events.surveys.fields import get_field_types
from indico.util.string import return_ascii, text_to_repr
from indico.util.struct.enum import IndicoEnum


def _get_next_position(context):
    """Get the next question position for the event."""
    survey_id = context.current_parameters['survey_id']
    parent_id = context.current_parameters['parent_id']
    res = db.session.query(db.func.max(SurveyItem.position)).filter_by(survey_id=survey_id, parent_id=parent_id).one()
    return (res[0] or 0) + 1


def _get_item_default_title(context):
    return '' if context.current_parameters['type'] == SurveyItemType.section else None


class SurveyItemType(int, IndicoEnum):
    question = 1
    section = 2
    text = 3


class SurveyItem(db.Model):
    __tablename__ = 'items'
    __table_args__ = (db.CheckConstraint("type != {type} OR ("
                                         "title IS NOT NULL AND "
                                         "is_required IS NOT NULL AND "
                                         "field_type IS NOT NULL AND "
                                         "parent_id IS NOT NULL AND "
                                         "display_as_section IS NULL)"
                                         .format(type=SurveyItemType.question), 'valid_question'),
                      db.CheckConstraint("type != {type} OR ("
                                         "title IS NOT NULL AND "
                                         "is_required IS NULL AND "
                                         "field_type IS NULL AND "
                                         "field_data::text = '{{}}' AND "
                                         "parent_id IS NULL AND "
                                         "display_as_section IS NOT NULL)"
                                         .format(type=SurveyItemType.section), 'valid_section'),
                      db.CheckConstraint("type != {type} OR ("
                                         "title IS NULL AND "
                                         "is_required IS NULL AND "
                                         "field_type IS NULL AND "
                                         "field_data::text = '{{}}' AND "
                                         "parent_id IS NOT NULL AND "
                                         "display_as_section IS NULL)"
                                         .format(type=SurveyItemType.text), 'valid_text'),
                      {'schema': 'event_surveys'})
    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': None
    }

    #: The ID of the item
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the survey
    survey_id = db.Column(
        db.Integer,
        db.ForeignKey('event_surveys.surveys.id'),
        index=True,
        nullable=False,
    )
    #: The ID of the parent section item (NULL for top-level items, i.e. sections)
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey('event_surveys.items.id'),
        index=True,
        nullable=True,
    )
    #: The position of the item in the survey form
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )
    #: The type of the survey item
    type = db.Column(
        PyIntEnum(SurveyItemType),
        nullable=False
    )
    #: The title of the item
    title = db.Column(
        db.String,
        nullable=True,
        default=_get_item_default_title
    )
    #: The description of the item
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: If a section should be rendered as a section
    display_as_section = db.Column(
        db.Boolean,
        nullable=True
    )

    # The following columns are only used for SurveyQuestion objects, but by
    # specifying them here we can access them withouy an extra query when we
    # query SurveyItem objects directly instead of going through a subclass.
    # This is done e.g. when using the Survey.top_level_items relationship.

    #: If the question must be answered (wtforms DataRequired)
    is_required = db.Column(
        db.Boolean,
        nullable=True
    )
    #: The type of the field used for the question
    field_type = db.Column(
        db.String,
        nullable=True
    )
    #: Field-specific data (such as choices for multi-select fields)
    field_data = db.Column(
        JSON,
        nullable=False,
        default={}
    )

    # relationship backrefs:
    # - parent (SurveySection.children)
    # - survey (Survey.items)

    def to_dict(self):
        """Return a json-serializable representation of this object.

        Subclasses must add their own data to the dict.
        """
        return {'type': self.type.name, 'title': self.title, 'description': self.description}


class SurveyQuestion(SurveyItem):
    __mapper_args__ = {
        'polymorphic_identity': SurveyItemType.question
    }

    # relationship backrefs:
    # - answers (SurveyAnswer.question)

    @property
    def field(self):
        try:
            impl = get_field_types()[self.field_type]
        except KeyError:
            return None
        return impl(self)

    @property
    def locator(self):
        return dict(self.survey.locator, section_id=self.parent_id, question_id=self.id)

    @property
    def not_empty_answers(self):
        return [a for a in self.answers if not a.is_empty]

    def get_summary(self, **kwargs):
        """Returns the summary of answers submitted for this question."""
        if self.field:
            return self.field.get_summary(**kwargs)

    @return_ascii
    def __repr__(self):
        return '<SurveyQuestion({}, {}, {}, {})>'.format(self.id, self.survey_id, self.field_type, self.title)

    def to_dict(self):
        data = super(SurveyQuestion, self).to_dict()
        data.update({'is_required': self.is_required, 'field_type': self.field_type,
                     'field_data': self.field.copy_field_data()})
        return data


class SurveySection(SurveyItem):
    __mapper_args__ = {
        'polymorphic_identity': SurveyItemType.section
    }

    #: The child items of this section
    children = db.relationship(
        'SurveyItem',
        order_by='SurveyItem.position',
        cascade='all, delete-orphan',
        backref=db.backref(
            'parent',
            remote_side=[SurveyItem.id]
        )
    )

    @property
    def locator(self):
        return dict(self.survey.locator, section_id=self.id)

    @return_ascii
    def __repr__(self):
        return '<SurveySection({}, {}, {})>'.format(self.id, self.survey_id, self.title)

    def to_dict(self):
        data = super(SurveySection, self).to_dict()
        content = [child.to_dict() for child in self.children]
        data.update({'content': content, 'display_as_section': self.display_as_section})
        if not self.display_as_section:
            del data['title']
            del data['description']
        return data


class SurveyText(SurveyItem):
    __mapper_args__ = {
        'polymorphic_identity': SurveyItemType.text
    }

    @property
    def locator(self):
        return dict(self.survey.locator, section_id=self.parent_id, text_id=self.id)

    @return_ascii
    def __repr__(self):
        desc = text_to_repr(self.description)
        return '<SurveyText({}, {}): "{}")>'.format(self.id, self.survey_id, desc)

    def to_dict(self):
        data = super(SurveyText, self).to_dict()
        del data['title']
        return data


@listens_for(SurveySection.children, 'append')
def _set_survey(target, value, *unused):
    if value.survey is None and target.survey is not None:
        value.survey = target.survey
    assert value.survey in {target.survey, None}
