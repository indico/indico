# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import request, flash, session, jsonify
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events.surveys import logger
from indico.modules.events.surveys.controllers.management import RHManageSurveyBase, RHManageSurveysBase
from indico.modules.events.surveys.fields import get_field_types
from indico.modules.events.surveys.forms import TextForm, SectionForm
from indico.modules.events.surveys.models.items import (SurveyItem, SurveyItemType, SurveySection, SurveyText,
                                                        SurveyQuestion)
from indico.modules.events.surveys.models.surveys import Survey
from indico.modules.events.surveys.util import make_survey_form
from indico.modules.events.surveys.views import WPManageSurvey
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_template


class RHManageSurveyQuestionnaire(RHManageSurveyBase):
    """Manage the questionnaire of a survey (question overview page)"""

    def _process(self):
        field_types = get_field_types()
        preview_form = make_survey_form(self.survey)()
        return WPManageSurvey.render_template('management/survey_questionnaire.html', self.event, survey=self.survey,
                                              field_types=field_types, preview_form=preview_form)


class RHManageSurveySectionBase(RHManageSurveysBase):
    """Base class for RHs that deal with a specific survey section"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.section
        },
        'preserved_args': {'type'}
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        self.section = SurveySection.find_one(SurveySection.id == request.view_args['section_id'], ~Survey.is_deleted,
                                              _join=SurveySection.survey, _eager=SurveySection.survey)
        self.survey = self.section.survey


class RHManageSurveyTextBase(RHManageSurveysBase):
    """Base class for RHs that deal with a specific survey text item"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.text
        }
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        self.text = SurveyText.find_one(SurveyText.id == request.view_args['text_id'], ~Survey.is_deleted,
                                        _join=SurveyText.survey, _eager=SurveyText.survey)
        self.survey = self.text.survey


class RHManageSurveyQuestionBase(RHManageSurveysBase):
    """Base class for RHs that deal with a specific survey question"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.question
        }
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        self.question = SurveyQuestion.find_one(SurveyQuestion.id == request.view_args['question_id'],
                                                ~Survey.is_deleted,
                                                _join=SurveyQuestion.survey, _eager=SurveyQuestion.survey)
        self.survey = self.question.survey


class RHAddSurveySection(RHManageSurveyBase):
    """Add a new section to a survey"""

    def _process(self):
        form = SectionForm()
        if form.validate_on_submit():
            section = SurveySection(survey=self.survey)
            form.populate_obj(section)
            db.session.add(section)
            db.session.flush()
            flash(_('Section "{title}" added').format(title=section.title), 'success')
            logger.info('Survey section %s added by %s', section, session.user)
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHEditSurveySection(RHManageSurveySectionBase):
    """Edit a survey section"""

    def _process(self):
        form = SectionForm(obj=FormDefaults(self.section))
        if form.validate_on_submit():
            old_title = self.section.title
            form.populate_obj(self.section)
            db.session.flush()
            flash(_('Section "{title}" updated').format(title=old_title), 'success')
            logger.info('Survey section %s modified by %s', self.section, session.user)
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHDeleteSurveySection(RHManageSurveySectionBase):
    """Delete a survey section and all its questions"""

    def _process(self):
        db.session.delete(self.section)
        db.session.flush()
        flash(_('Section "{title}" deleted').format(title=self.section.title), 'success')
        logger.info('Survey section %s deleted by %s', self.section, session.user)
        return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))


class RHAddSurveyText(RHManageSurveySectionBase):
    """Add a new text item to a survey"""

    def _process(self):
        form = TextForm()
        if form.validate_on_submit():
            text = SurveyText()
            form.populate_obj(text)
            self.section.children.append(text)
            db.session.flush()
            flash(_('Text item added'), 'success')
            logger.info('Survey text item %s added by %s', text, session.user)
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHEditSurveyText(RHManageSurveyTextBase):
    """Edit a survey text item"""

    def _process(self):
        form = TextForm(obj=FormDefaults(self.text))
        if form.validate_on_submit():
            form.populate_obj(self.text)
            db.session.flush()
            flash(_('Text item updated'), 'success')
            logger.info('Survey text item %s modified by %s', self.text, session.user)
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHDeleteSurveyText(RHManageSurveyTextBase):
    """Delete a survey text item"""

    def _process(self):
        db.session.delete(self.text)
        db.session.flush()
        flash(_('Text item deleted'), 'success')
        logger.info('Survey question %s deleted by %s', self.text, session.user)
        return jsonify_data(questionnaire=_render_questionnaire_preview(self.text.survey))


class RHAddSurveyQuestion(RHManageSurveySectionBase):
    """Add a new question to a survey"""

    def _process(self):
        try:
            field_cls = get_field_types()[request.view_args['type']]
        except KeyError:
            raise NotFound

        clone_id = request.args.get('clone')
        form = None
        if clone_id is not None:
            try:
                question_to_clone = SurveyQuestion.query.with_parent(self.survey).filter_by(id=int(clone_id)).one()
                form = question_to_clone.field.config_form(
                        obj=FormDefaults(question_to_clone, **question_to_clone.field.copy_field_data()))
            except (NoResultFound, ValueError):
                pass
        if form is None:
            form = field_cls.config_form()

        if form.validate_on_submit():
            question = SurveyQuestion()
            field_cls(question).save_config(form)
            self.section.children.append(question)
            db.session.flush()
            flash(_('Question "{title}" added').format(title=question.title), 'success')
            logger.info('Survey question %s added by %s', question, session.user)
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHEditSurveyQuestion(RHManageSurveyQuestionBase):
    """Edit a survey question"""

    def _process(self):
        form = self.question.field.config_form(obj=FormDefaults(self.question, **self.question.field_data))
        if form.validate_on_submit():
            old_title = self.question.title
            self.question.field.save_config(form)
            db.session.flush()
            flash(_('Question "{title}" updated').format(title=old_title), 'success')
            logger.info('Survey question %s modified by %s', self.question, session.user)
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('events/surveys/management/edit_survey_item.html', form=form)


class RHDeleteSurveyQuestion(RHManageSurveyQuestionBase):
    """Delete a survey question"""

    def _process(self):
        db.session.delete(self.question)
        db.session.flush()
        flash(_('Question "{title}" deleted').format(title=self.question.title), 'success')
        logger.info('Survey question %s deleted by %s', self.question, session.user)
        return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))


class RHSortSurveyItems(RHManageSurveyBase):
    """Sort survey items/sections and/or move items them between sections"""

    def _sort_sections(self):
        sections = {section.id: section for section in self.survey.sections}
        section_ids = map(int, request.form.getlist('section_ids'))
        for position, section_id in enumerate(section_ids, 1):
            sections[section_id].position = position
        logger.info('Sections in %s reordered by %s', self.survey, session.user)

    def _sort_items(self):
        section = SurveySection.find_one(survey=self.survey, id=request.form['section_id'],
                                         _eager=SurveySection.children)
        section_items = {x.id: x for x in section.children}
        item_ids = map(int, request.form.getlist('item_ids'))
        changed_section = None
        for position, item_id in enumerate(item_ids, 1):
            try:
                section_items[item_id].position = position
            except KeyError:
                # item is not in section, was probably moved
                item = SurveyItem.find_one(SurveyItem.survey == self.survey, SurveyItem.id == item_id,
                                           SurveyItem.type != SurveyItemType.section, _eager=SurveyItem.parent)
                changed_section = item.parent
                item.position = position
                item.parent = section
                logger.info('Item %s moved to section %s by %s', item, section, session.user)
        logger.info('Items in %s reordered by %s', section, session.user)
        if changed_section is not None:
            for position, item in enumerate(changed_section.children, 1):
                item.position = position

    def _process(self):
        mode = request.form['mode']
        if mode == 'sections':
            self._sort_sections()
        elif mode == 'items':
            self._sort_items()
        db.session.flush()
        return jsonify(success=True)


def _render_questionnaire_preview(survey):
    # load the survey once again with all the necessary data
    survey = (Survey
              .find(id=survey.id)
              .options(joinedload(Survey.sections).joinedload(SurveySection.children))
              .one())
    tpl = get_template_module('events/surveys/management/_questionnaire_preview.html')
    form = make_survey_form(survey)()
    return tpl.render_questionnaire_preview(survey, form, get_field_types())
