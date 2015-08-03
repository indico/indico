# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.web.forms.base import IndicoForm


def make_survey_form(questions):
    """Creates a WTForm from survey questions.

    Each question will use a field named ``question_ID``.

    :param questions: An iterable containing `SurveyQuestion`
                      objects.  The questions are expected to be
                      sorted according to their `position` attribute.
    :return: An `IndicoForm` subclass.
    """
    form_class = type(b'SurveyForm', (IndicoForm,), {})
    for question in questions:
        name = 'question_{}'.format(question.id)
        field_impl = question.field
        if field_impl is None:
            # field definition is not available anymore
            continue
        setattr(form_class, name, field_impl.get_wtforms_field())
    return form_class
