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

import json

from flask import request, flash, session, jsonify
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import NotFound

from indico.core.db import db
from indico.modules.events.surveys import logger
from indico.modules.events.surveys.controllers.management import RHManageSurveyBase, RHManageSurveysBase
from indico.modules.events.surveys.fields import get_field_types
from indico.modules.events.surveys.forms import TextForm, SectionForm, ImportQuestionnaireForm
from indico.modules.events.surveys.models.items import (SurveyItem, SurveyItemType, SurveySection, SurveyText,
                                                        SurveyQuestion)
from indico.modules.events.surveys.models.surveys import Survey
from indico.modules.events.surveys.operations import add_survey_section, add_survey_question, add_survey_text
from indico.modules.events.surveys.util import make_survey_form
from indico.modules.events.surveys.views import WPManageSurvey
from indico.util.i18n import _, ngettext
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHManageSurveyQuestionnaire(RHManageSurveyBase):
    """Manage the questionnaire of a survey (question overview page)"""

    def _process(self):
        field_types = get_field_types()
        preview_form = make_survey_form(self.survey)()
        return WPManageSurvey.render_template('management/survey_questionnaire.html', self._conf, survey=self.survey,
                                              field_types=field_types, preview_form=preview_form)


class RHExportSurveyQuestionnaire(RHManageSurveyBase):
    """Export the questionnaire to JSON format"""

    def _process(self):
        sections = [section.to_dict() for section in self.survey.sections]
        response = jsonify(version=1, sections=sections)
        response.headers['Content-Disposition'] = 'attachment; filename="survey.json"'
        return response


class RHImportSurveyQuestionnaire(RHManageSurveyBase):
    """Import a questionnaire in JSON format"""

    def _remove_false_values(self, data):
        # The forms consider a missing key as False (and a False value as True)
        for key, value in data.items():
            if value is False:
                del data[key]

    def _import_data(self, data):
        if data['version'] != 1:
            raise ValueError("Unsupported document format")

        # If the survey currently contains only one empty section, remove it.
        if len(self.survey.items) == 1 and isinstance(self.survey.items[0], SurveySection):
            db.session.delete(self.survey.items[0])

        for section in data['sections']:
            self._import_section(section)

    def _import_section(self, data):
        self._remove_false_values(data)
        form = SectionForm(formdata=MultiDict(data.items()), csrf_enabled=False)
        if form.validate():
            section = add_survey_section(self.survey, form.data)
            for item in data['content']:
                self._import_section_item(section, item)
        else:
            raise ValueError('Invalid section')

    def _import_section_item(self, section, data):
        self._remove_false_values(data)
        if data['type'] == 'text':
            form = TextForm(formdata=MultiDict(data.items()), csrf_enabled=False)
            if form.validate():
                add_survey_text(section, form.data)
            else:
                raise ValueError('Invalid text item')
        elif data['type'] == 'question':
            for key, value in data['field_data'].iteritems():
                if value is not None:
                    data[key] = value
            field_cls = get_field_types()[data['field_type']]
            data = field_cls.process_imported_data(data)
            form = field_cls.create_config_form(formdata=MultiDict(data.items()), csrf_enabled=False)
            if not form.validate():
                raise ValueError('Invalid question')
            add_survey_question(section, field_cls, form.data)

    def _process(self):
        form = ImportQuestionnaireForm()
        if form.validate_on_submit():
            try:
                data = json.load(form.json_file.data.file)
                self._import_data(data)
            except ValueError as exception:
                logger.info('%s tried to import an invalid JSON file: %s', session.user, exception.message)
                flash(_("Invalid file selected."), 'error')
            else:
                flash(_("The questionnaire has been imported."), 'success')
                logger.info('Questionnaire imported from JSON document by %s', session.user)
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_form(form, form_header_kwargs={'action': request.relative_url})


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
            section = add_survey_section(self.survey, form.data)
            if section.title:
                message = _('Section "{title}" added').format(title=section.title)
            else:
                message = _('Standalone section added')
            flash(message, 'success')
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('forms/form_common_fields_first.html', form=form)


class RHEditSurveySection(RHManageSurveySectionBase):
    """Edit a survey section"""

    def _process(self):
        form = SectionForm(obj=FormDefaults(self.section))
        if form.validate_on_submit():
            old_title = self.section.title
            form.populate_obj(self.section)
            db.session.flush()
            if old_title:
                message = _('Section "{title}" updated').format(title=old_title)
            else:
                message = _('Standalone section updated')
            flash(message, 'success')
            logger.info('Survey section %s modified by %s', self.section, session.user)
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('forms/form_common_fields_first.html', form=form)


class RHDeleteSurveySection(RHManageSurveySectionBase):
    """Delete a survey section and all its questions"""

    def _process(self):
        db.session.delete(self.section)
        db.session.flush()
        if self.section.title:
            message = _('Section "{title}" deleted').format(title=self.section.title)
        else:
            message = _('Standalone section deleted')
        flash(message, 'success')
        logger.info('Survey section %s deleted by %s', self.section, session.user)
        return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))


class RHAddSurveyText(RHManageSurveySectionBase):
    """Add a new text item to a survey"""

    def _process(self):
        form = TextForm()
        if form.validate_on_submit():
            add_survey_text(self.section, form.data)
            flash(_('Text item added'), 'success')
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('forms/form_common_fields_first.html', form=form)


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
        return jsonify_template('forms/form_common_fields_first.html', form=form)


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

        form = field_cls.create_config_form()
        try:
            clone_id = int(request.args['clone'])
        except (KeyError, ValueError):
            pass
        else:
            try:
                question_to_clone = SurveyQuestion.query.with_parent(self.survey).filter_by(id=clone_id).one()
                form = question_to_clone.field.create_config_form(
                    obj=FormDefaults(question_to_clone, **question_to_clone.field.copy_field_data()))
            except NoResultFound:
                pass

        if form.validate_on_submit():
            question = add_survey_question(self.section, field_cls, form.data)
            flash(_('Question "{title}" added').format(title=question.title), 'success')
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('forms/form_common_fields_first.html', form=form)


class RHEditSurveyQuestion(RHManageSurveyQuestionBase):
    """Edit a survey question"""

    def _process(self):
        form = self.question.field.create_config_form(obj=FormDefaults(self.question, **self.question.field_data))
        if form.validate_on_submit():
            old_title = self.question.title
            self.question.field.update_object(form.data)
            db.session.flush()
            flash(_('Question "{title}" updated').format(title=old_title), 'success')
            logger.info('Survey question %s modified by %s', self.question, session.user)
            return jsonify_data(questionnaire=_render_questionnaire_preview(self.survey))
        return jsonify_template('forms/form_common_fields_first.html', form=form)


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
