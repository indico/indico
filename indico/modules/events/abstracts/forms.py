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

from wtforms.fields import BooleanField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import NumberRange, Optional, DataRequired, ValidationError

from indico.modules.events.abstracts.fields import EmailRuleListField
from indico.modules.events.abstracts.settings import BOASortField, BOACorrespondingAuthorType
from indico.util.i18n import _
from indico.util.placeholders import render_placeholder_info
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import PrincipalListField, IndicoEnumSelectField, IndicoMarkdownField, EmailListField
from indico.web.forms.validators import HiddenUnless
from indico.web.forms.widgets import SwitchWidget


class AbstractContentSettingsForm(IndicoForm):
    """Configure the content field of abstracts"""

    is_active = BooleanField(_('Active'), widget=SwitchWidget(),
                             description=_("Whether the content field is available."))
    is_required = BooleanField(_('Required'), widget=SwitchWidget(),
                               description=_("Whether the user has to fill the content field."))
    max_length = IntegerField(_('Max length'), [Optional(), NumberRange(min=1)])
    max_words = IntegerField(_('Max words'), [Optional(), NumberRange(min=1)])


class BOASettingsForm(IndicoForm):
    """Settings form for the 'Book of Abstracts'"""

    extra_text = IndicoMarkdownField(_('Additional text'), editor=True, mathjax=True)
    sort_by = IndicoEnumSelectField(_('Sort by'), [DataRequired()], enum=BOASortField, sorted=True)
    corresponding_author = IndicoEnumSelectField(_('Corresponding author'), [DataRequired()],
                                                 enum=BOACorrespondingAuthorType, sorted=True)
    show_abstract_ids = BooleanField(_('Show abstract IDs'), widget=SwitchWidget(),
                                     description=_("Show abstract IDs in the table of contents."))


class AbstractSubmissionSettingsForm(IndicoForm):
    """Settings form for abstract submission"""

    announcement = IndicoMarkdownField(_('Announcement'), editor=True)
    allow_multiple_tracks = BooleanField(_('Multiple tracks'), widget=SwitchWidget())
    tracks_required = BooleanField(_('Require tracks'), widget=SwitchWidget())
    allow_attachments = BooleanField(_('Allow attachments'), widget=SwitchWidget())
    allow_speakers = BooleanField(_('Allow speakers'), widget=SwitchWidget())
    speakers_required = BooleanField(_('Require a speaker'), [HiddenUnless('allow_speakers')], widget=SwitchWidget())
    authorized_submitters = PrincipalListField(_("Authorized submitters"),
                                               description=_("These users may always submit abstracts, even outside "
                                                             "the regular submission period."))


class EditEmailTemplateRuleForm(IndicoForm):
    """Form for editing a new e-mail template."""

    title = StringField(_("Title"), [DataRequired()])
    rules = EmailRuleListField(_("Rules"), [DataRequired()])
    stop_on_match = BooleanField(_("Stop on match"), [DataRequired()], widget=SwitchWidget(), default=True,
                                 description=_("Do not evaluate any other rules once this one matches."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(EditEmailTemplateRuleForm, self).__init__(*args, **kwargs)
        self.rules.event = self.event

    def validate_rules(self, field):
        dedup_data = {tuple((k, tuple(v)) for k, v in r.viewitems()) for r in field.data}
        if len(field.data) != len(dedup_data):
            raise ValidationError(_("There is a duplicate rule"))


class EditEmailTemplateTextForm(IndicoForm):
    """Form for editing the text of a new e-mail template."""

    reply_to_address = SelectField(_('"Reply to" address'), [DataRequired()])
    include_submitter = BooleanField(_('Send to submitter'), widget=SwitchWidget())
    include_authors = BooleanField(_('Send to primary authors'), widget=SwitchWidget())
    include_coauthors = BooleanField(_('Send to co-authors'), widget=SwitchWidget())
    cc_addresses = EmailListField(_("CC"), description=_("Additional CC e-mail addresses (one per line)"))
    subject = StringField(_("Subject"), [DataRequired()])
    body = TextAreaField(_("Body"), [DataRequired()])

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(EditEmailTemplateTextForm, self).__init__(*args, **kwargs)
        self.reply_to_address.choices = (self.event
                                         .get_allowed_sender_emails(extra=self.reply_to_address.object_data)
                                         .items())
        self.body.description = render_placeholder_info('abstract-notification-email', event=self.event)


class CreateEmailTemplateForm(EditEmailTemplateRuleForm):
    """Form for adding a new e-mail template."""

    default_tpl = SelectField(_('Default template'), [DataRequired()], choices=[
        ('submit', _('Submit')),
        ('accept', _('Accept')),
        ('reject', _('Reject')),
        ('merge', _('Merge'))
    ], description=_("The template that will be used as a basis for this notification. You can customize it later."))
