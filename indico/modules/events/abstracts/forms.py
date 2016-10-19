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

from datetime import time

from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import BooleanField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import NumberRange, Optional, DataRequired, ValidationError, InputRequired

from indico.modules.events.abstracts.fields import (EmailRuleListField, AbstractReviewQuestionsField,
                                                    AbstractPersonLinkListField, AbstractField, TrackRoleField)
from indico.modules.events.abstracts.models.reviews import AbstractAction
from indico.modules.events.abstracts.settings import BOASortField, BOACorrespondingAuthorType, abstracts_settings
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.tracks.models.tracks import Track
from indico.util.i18n import _
from indico.util.placeholders import render_placeholder_info
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (PrincipalListField, IndicoEnumSelectField, IndicoMarkdownField,
                                     IndicoQuerySelectMultipleCheckboxField, EmailListField, FileField,
                                     IndicoDateTimeField)
from indico.web.forms.util import inject_validators
from indico.web.forms.validators import HiddenUnless, UsedIf, LinkedDateTime
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
    allow_multiple_tracks = BooleanField(_('Multiple tracks'), widget=SwitchWidget(),
                                         description=_("Allow the selection of multiple tracks"))
    tracks_required = BooleanField(_('Require tracks'), widget=SwitchWidget(),
                                   description=_("Make the track selection mandatory"))
    contrib_type_required = BooleanField(_('Require contrib. type'), widget=SwitchWidget(),
                                         description=_("Make the selection of a contribution type mandatory"))
    allow_attachments = BooleanField(_('Allow attachments'), widget=SwitchWidget(),
                                     description=_("Allow files to be attached to the abstract"))
    allow_speakers = BooleanField(_('Allow speakers'), widget=SwitchWidget(),
                                  description=_("Allow the selection of the abstract speakers"))
    speakers_required = BooleanField(_('Require a speaker'), [HiddenUnless('allow_speakers')], widget=SwitchWidget(),
                                     description=_("Make the selection of at least one author as speaker mandatory"))
    authorized_submitters = PrincipalListField(_("Authorized submitters"),
                                               description=_("These users may always submit abstracts, even outside "
                                                             "the regular submission period."))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(AbstractSubmissionSettingsForm, self).__init__(*args, **kwargs)

    def validate_contrib_type_required(self, field):
        if field.data and not self.event.contribution_types.count():
            raise ValidationError(_('The event has no contribution types defined.'))


class AbstractReviewingSettingsForm(IndicoForm):
    """Settings form for abstract reviewing"""

    RATING_FIELDS = ('scale_lower', 'scale_upper')

    scale_lower = IntegerField(_('Scale (from)'), [UsedIf(lambda form, field: not form.has_ratings), InputRequired()])
    scale_upper = IntegerField(_('Scale (to)'), [UsedIf(lambda form, field: not form.has_ratings), InputRequired()])
    allow_convener_judgment = BooleanField(_('Allow track conveners to judge'), widget=SwitchWidget(),
                                           description=_('Enabling this allows track conveners to make a judgment '
                                                         'such as accepting or rejecting an abstract.'))
    abstract_review_questions = AbstractReviewQuestionsField(_('Review questions'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.has_ratings = kwargs.pop('has_ratings', False)
        super(AbstractReviewingSettingsForm, self).__init__(*args, **kwargs)
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
        data = super(AbstractReviewingSettingsForm, self).data
        if self.has_ratings:
            for key in self.RATING_FIELDS:
                del data[key]
        return data


class AbstractJudgmentForm(IndicoForm):
    """Form for judging an abstract"""

    judgment = IndicoEnumSelectField(_("Judgment"), [DataRequired()], enum=AbstractAction,
                                     skip={AbstractAction.change_tracks})
    accepted_track = QuerySelectField(_("Track"), [HiddenUnless('judgment', AbstractAction.accept)],
                                      get_label='title', allow_blank=True, blank_text=_("Choose a track..."),
                                      description=_("The abstract will be accepted in this track"))
    accepted_contrib_type = QuerySelectField(_("Contribution type"), [HiddenUnless('judgment', AbstractAction.accept)],
                                             get_label=lambda x: x.name.title(), allow_blank=True,
                                             blank_text=_("Choose the contribution type..."),
                                             description=_("The abstract will be converted "
                                                           "into a contribution of this type"))
    session = QuerySelectField(_("Session"), [HiddenUnless('judgment', AbstractAction.accept)],
                               get_label='title', allow_blank=True, blank_text=_("Choose a session..."),
                               description=_("The generated contribution will be allocated in this session"))
    merged_into = AbstractField(_("Merge into"), [HiddenUnless('judgment', AbstractAction.merge), DataRequired()],
                                description=_("The current abstract will be merged onto the selected one"))
    merge_persons = BooleanField(_("Merge persons"), [HiddenUnless('judgment', AbstractAction.merge), DataRequired()],
                                 description=_("Authors and speakers of the current abstract will be added to the "
                                               "selected one"))
    duplicate_of = AbstractField(_("Duplicate of"),
                                 [HiddenUnless('judgment', AbstractAction.mark_as_duplicate), DataRequired()],
                                 description=_("The current abstract will be marked as duplicate of the selected one"))
    judgment_comment = TextAreaField(_("Comment"), render_kw={'placeholder': _("Leave a comment for the submitter...")})
    # TODO: show only if notifications apply?
    send_notifications = BooleanField(_("Send notifications to submitter"), default=True)

    def __init__(self, *args, **kwargs):
        abstract = kwargs.pop('abstract')
        self.event = abstract.event_new
        candidate_tracks = list(abstract.candidate_tracks)
        candidate_contrib_types = list(abstract.candidate_contrib_types)
        if len(candidate_tracks) == 1:
            kwargs.setdefault('accepted_track', candidate_tracks[0])
        if len(candidate_contrib_types) == 1:
            kwargs.setdefault('accepted_contrib_type', candidate_contrib_types[0])
        super(AbstractJudgmentForm, self).__init__(*args, **kwargs)
        self.session.query = Session.query.with_parent(self.event).order_by(Session.title)
        self.accepted_track.query = Track.query.with_parent(self.event).order_by(Track.title)
        self.accepted_contrib_type.query = (ContributionType.query
                                                            .with_parent(self.event)
                                                            .order_by(ContributionType.name))


class AbstractReviewingRolesForm(IndicoForm):
    """Settings form for abstract reviewing roles"""
    roles = TrackRoleField()

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(AbstractReviewingRolesForm, self).__init__(*args, **kwargs)
        self.roles.event = self.event
        self.roles.tracks = self.event.tracks


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
    include_authors = BooleanField(_('Send to primary authorized_submittershors'), widget=SwitchWidget())
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


class AbstractForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired()])
    description = IndicoMarkdownField(_('Content'), [DataRequired()], editor=True, mathjax=True)
    submitted_contrib_type = QuerySelectField(_("Type"), get_label='name', allow_blank=True,
                                              blank_text=_("No type selected"))
    person_links = AbstractPersonLinkListField(_("People"), [DataRequired()])
    submission_comment = TextAreaField(_("Comments"))
    attachments = FileField(_('Attachments'), param_name='attachments', multiple_files=True, lightweight=True)

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.abstract = kwargs.pop('abstract', None)
        if abstracts_settings.get(self.event, 'contrib_type_required'):
            inject_validators(self, 'submitted_contrib_type', [DataRequired()])
        super(AbstractForm, self).__init__(*args, **kwargs)
        self.submitted_contrib_type.query = self.event.contribution_types
        if not self.submitted_contrib_type.query.count():
            del self.submitted_contrib_type
        if not abstracts_settings.get(self.event, 'allow_attachments'):
            del self.attachments
        self.person_links.require_speaker_author = abstracts_settings.get(self.event, 'speakers_required')
        self.person_links.allow_speakers = abstracts_settings.get(self.event, 'allow_speakers')


class SingleTrackMixin(object):
    submitted_for_tracks = QuerySelectField(_("Track"), get_label=lambda x: x.title, allow_blank=True)

    def __init__(self, *args, **kwargs):
        event = kwargs['event']
        if abstracts_settings.get(event, 'tracks_required'):
            inject_validators(self, 'submitted_for_tracks', [DataRequired()])
        super(SingleTrackMixin, self).__init__(*args, **kwargs)
        if not abstracts_settings.get(event, 'tracks_required'):
            self.submitted_for_tracks.blank_text = _('No track selected')
        self.submitted_for_tracks.query = Track.query.with_parent(event).order_by(Track.title)


class MultiTrackMixin(object):
    submitted_for_tracks = IndicoQuerySelectMultipleCheckboxField(_("Tracks"), get_label=lambda x: x.title,
                                                                  collection_class=set)

    def __init__(self, *args, **kwargs):
        event = kwargs['event']
        if abstracts_settings.get(event, 'tracks_required'):
            inject_validators(self, 'submitted_for_tracks', [DataRequired()])
        super(MultiTrackMixin, self).__init__(*args, **kwargs)
        self.submitted_for_tracks.query = Track.query.with_parent(event).order_by(Track.title)


class AbstractsScheduleForm(IndicoForm):
    start_dt = IndicoDateTimeField(_("Start"), [Optional()], default_time=time(0, 0),
                                   description=_("The moment users can start submitting abstracts"))
    end_dt = IndicoDateTimeField(_("End"), [Optional(), LinkedDateTime('start_dt')], default_time=time(23, 59),
                                 description=_("The moment the submission process will end"))
    modification_end_dt = IndicoDateTimeField(_("Modification deadline"), [Optional(), LinkedDateTime('end_dt')],
                                              default_time=time(23, 59),
                                              description=_("Deadline until which the submitted abstracts can be "
                                                            "modified"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(AbstractsScheduleForm, self).__init__(*args, **kwargs)
