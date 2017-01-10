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

from flask import session

from indico.core.db import db
from indico.modules.events.surveys import logger
from indico.modules.events.surveys.models.items import (SurveyQuestion, SurveySection, SurveyText)


def add_survey_question(section, field_cls, data):
    """Add a question to a survey.

    :param section: The `SurveySection` to which the question will be added.
    :param field_cls: The field class of this question.
    :param data: The `FieldConfigForm.data` to populate the question with.
    :return: The added `SurveyQuestion`.
    """
    question = SurveyQuestion()
    field = field_cls(question)
    field.update_object(data)
    section.children.append(question)
    db.session.flush()
    logger.info('Survey question %s added by %s', question, session.user)
    return question


def add_survey_text(section, data):
    """Add a text item to a survey.

    :param section: The `SurveySection` to which the question will be added.
    :param data: The `TextForm.data` to populate the question with.
    :return: The added `SurveyText`.
    """
    text = SurveyText()
    text.populate_from_dict(data)
    section.children.append(text)
    db.session.flush()
    logger.info('Survey text item %s added by %s', text, session.user)
    return text


def add_survey_section(survey, data):
    """Add a section to a survey.

    :param survey: The `Survey` to which the section will be added.
    :param data: Attributes of the new `SurveySection`.
    :return: The added `SurveySection`.
    """
    section = SurveySection(survey=survey)
    section.populate_from_dict(data)
    db.session.add(section)
    db.session.flush()
    logger.info('Survey section %s added by %s', section, session.user)
    return section
