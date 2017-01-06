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

from datetime import time

from flask import request
from wtforms.fields import TextAreaField, BooleanField, HiddenField
from wtforms.validators import Optional

from indico.modules.events.fields import ReviewQuestionsField
from indico.modules.events.papers.models.reviews import PaperAction, PaperReviewType
from indico.modules.events.papers.models.review_questions import PaperReviewQuestion
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (PrincipalListField, IndicoDateTimeField, IndicoTagListField, HiddenEnumField,
                                     HiddenFieldList)
from indico.web.forms.validators import LinkedDateTime


def make_competences_form(event):
    form_class = type(b'PaperCompetencesForm', (IndicoForm,), {})
    for entry in event.cfp.assignees:
        name = 'competences_{}'.format(entry.id)
        field = IndicoTagListField('Competences')
        setattr(form_class, name, field)
    return form_class


class PaperTeamsForm(IndicoForm):
    managers = PrincipalListField(_('Paper managers'), groups=True,
                                  description=_('List of users allowed to manage the call for papers'))
    judges = PrincipalListField(_('Judges'),
                                description=_('List of users allowed to judge a paper reviewing process'))
    content_reviewers = PrincipalListField(_('Content reviewers'),
                                           description=_('List of users allowed to review the content of the assigned '
                                                         'papers'))
    layout_reviewers = PrincipalListField(_('Layout reviewers'),
                                          description=_('List of users allowed to review the layout of the assigned '
                                                        'papers'))

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
    judgment_comment = TextAreaField(_("Comment"), render_kw={'placeholder': _("Leave a comment for the submitter...")})
    send_notifications = BooleanField(_("Send notifications to submitter"), default=True)

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(BulkPaperJudgmentForm, self).__init__(*args, **kwargs)

    def is_submitted(self):
        return super(BulkPaperJudgmentForm, self).is_submitted() and 'submitted' in request.form

    @property
    def split_data(self):
        contrib_data = self.data
        judgment_data = {
            'judgment': contrib_data.pop('judgment'),
            'send_notifications': contrib_data.pop('send_notifications'),
        }
        return judgment_data, contrib_data


class PaperReviewingSettingsForm(IndicoForm):
    content_review_questions = ReviewQuestionsField(
        _("Content review questions"),
        question_model=lambda: PaperReviewQuestion(type=PaperReviewType.content)
    )
    layout_review_questions = ReviewQuestionsField(
        _("Layout review questions"),
        question_model=lambda: PaperReviewQuestion(type=PaperReviewType.layout)
    )

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(PaperReviewingSettingsForm, self).__init__(*args, **kwargs)
        if not self.event.cfp.content_reviewing_enabled:
            del self.content_review_questions
        if not self.event.cfp.layout_reviewing_enabled:
            del self.layout_review_questions
