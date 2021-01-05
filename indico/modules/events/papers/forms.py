# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import time

from flask import request
from wtforms.fields import BooleanField, HiddenField, IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, Optional, ValidationError

from indico.modules.events.papers.fields import PaperEmailSettingsField
from indico.modules.events.papers.models.reviews import PaperAction
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (EditableFileField, FileField, HiddenEnumField, HiddenFieldList,
                                     IndicoDateTimeField, IndicoMarkdownField, IndicoTagListField)
from indico.web.forms.fields.principals import PrincipalListField
from indico.web.forms.util import inject_validators
from indico.web.forms.validators import HiddenUnless, LinkedDateTime, UsedIf
from indico.web.forms.widgets import SwitchWidget


def make_competences_form(event):
    form_class = type(b'PaperCompetencesForm', (IndicoForm,), {})
    for entry in event.cfp.assignees:
        name = 'competences_{}'.format(entry.id)
        field = IndicoTagListField('Competences')
        setattr(form_class, name, field)
    return form_class


class PaperTeamsForm(IndicoForm):
    managers = PrincipalListField(_('Paper managers'), allow_groups=True, allow_emails=True,
                                  description=_('List of users allowed to manage the call for papers'))
    judges = PrincipalListField(_('Judges'),
                                description=_('List of users allowed to judge papers'))
    content_reviewers = PrincipalListField(_('Content reviewers'),
                                           description=_('List of users allowed to review the content of '
                                                         'the assigned papers'))
    layout_reviewers = PrincipalListField(_('Layout reviewers'),
                                          description=_('List of users allowed to review the layout of the '
                                                        'assigned papers'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(PaperTeamsForm, self).__init__(*args, **kwargs)
        if not self.event.cfp.content_reviewing_enabled:
            del self.content_reviewers
        if not self.event.cfp.layout_reviewing_enabled:
            del self.layout_reviewers


class PapersScheduleForm(IndicoForm):
    start_dt = IndicoDateTimeField(_("Start"), [Optional()], default_time=time(0, 0),
                                   description=_("The moment users can start submitting papers"))
    end_dt = IndicoDateTimeField(_("End"), [Optional(), LinkedDateTime('start_dt')], default_time=time(23, 59),
                                 description=_("The moment the submission process ends"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(PapersScheduleForm, self).__init__(*args, **kwargs)


class BulkPaperJudgmentForm(IndicoForm):
    judgment = HiddenEnumField(enum=PaperAction)
    contribution_id = HiddenFieldList()
    submitted = HiddenField()
    judgment_comment = TextAreaField(_("Comment"), render_kw={'placeholder': _("Leave a comment for the submitter..."),
                                                              'class': 'grow'})

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(BulkPaperJudgmentForm, self).__init__(*args, **kwargs)

    def is_submitted(self):
        return super(BulkPaperJudgmentForm, self).is_submitted() and 'submitted' in request.form


class PaperReviewingSettingsForm(IndicoForm):
    """Settings form for paper reviewing."""

    RATING_FIELDS = ('scale_lower', 'scale_upper')

    announcement = IndicoMarkdownField(_('Announcement'), editor=True)
    scale_lower = IntegerField(_("Scale (from)"), [UsedIf(lambda form, field: not form.has_ratings), InputRequired()])
    scale_upper = IntegerField(_("Scale (to)"), [UsedIf(lambda form, field: not form.has_ratings), InputRequired()])
    email_settings = PaperEmailSettingsField(_("Email notifications"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.has_ratings = kwargs.pop('has_ratings', False)
        super(PaperReviewingSettingsForm, self).__init__(*args, **kwargs)
        if self.has_ratings:
            self.scale_upper.warning = _("Some reviewers have already submitted ratings so the scale cannot be changed "
                                         "anymore.")

    def validate_scale_upper(self, field):
        lower = self.scale_lower.data
        upper = self.scale_upper.data
        if lower is None or upper is None:
            return
        if lower >= upper:
            raise ValidationError(_("The scale's 'to' value must be greater than the 'from' value."))
        if upper - lower > 20:
            raise ValidationError(_("The difference between 'to' and' from' may not be greater than 20."))

    @property
    def data(self):
        data = super(PaperReviewingSettingsForm, self).data
        if self.has_ratings:
            for key in self.RATING_FIELDS:
                del data[key]
        return data


class PaperSubmissionForm(IndicoForm):
    files = FileField(_("Files"), [DataRequired()], multiple_files=True)


def _get_template_data(tpl):
    return {
        'filename': tpl.filename,
        'size': tpl.size,
        'content_type': tpl.content_type,
        'url': url_for('.download_template', tpl)
    }


class PaperTemplateForm(IndicoForm):
    name = StringField(_("Name"), [DataRequired()])
    description = TextAreaField(_("Description"))
    template = EditableFileField(_("Template"), add_remove_links=False, added_only=True,
                                 get_metadata=_get_template_data)

    def __init__(self, *args, **kwargs):
        template = kwargs.pop('template', None)
        if template is None:
            inject_validators(self, 'template', [DataRequired()])
        super(PaperTemplateForm, self).__init__(*args, **kwargs)


class DeadlineForm(IndicoForm):
    deadline = IndicoDateTimeField(_("Deadline"), [Optional()], default_time=time(23, 59))
    enforce = BooleanField(_("Enforce deadline"), [HiddenUnless('deadline')], widget=SwitchWidget())

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(DeadlineForm, self).__init__(*args, **kwargs)
