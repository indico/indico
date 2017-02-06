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

from flask import request, session
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import BooleanField, IntegerField, RadioField, SelectField, StringField, TextAreaField, HiddenField
from wtforms.validators import NumberRange, Optional, DataRequired, ValidationError, InputRequired
from wtforms.widgets import Select

from indico.core.db import db
from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.modules.events.abstracts.fields import (EmailRuleListField, AbstractPersonLinkListField, AbstractField,
                                                    TrackRoleField)
from indico.modules.events.abstracts.models.abstracts import EditTrackMode
from indico.modules.events.abstracts.models.reviews import AbstractAction, AbstractCommentVisibility
from indico.modules.events.abstracts.models.review_questions import AbstractReviewQuestion
from indico.modules.events.abstracts.settings import BOASortField, BOACorrespondingAuthorType, abstracts_settings
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.fields import ReviewQuestionsField
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.tracks.models.tracks import Track
from indico.util.i18n import _
from indico.util.placeholders import render_placeholder_info
from indico.web.forms.base import IndicoForm, FormDefaults, generated_data
from indico.web.forms.fields import (PrincipalListField, IndicoEnumSelectField, IndicoMarkdownField,
                                     IndicoQuerySelectMultipleCheckboxField, EmailListField, EditableFileField,
                                     IndicoDateTimeField, HiddenFieldList, HiddenEnumField,
                                     IndicoQuerySelectMultipleField)
from indico.web.forms.util import inject_validators
from indico.web.forms.validators import HiddenUnless, UsedIf, LinkedDateTime, WordCount, SoftLength
from indico.web.forms.widgets import JinjaWidget, SwitchWidget


def make_review_form(event):
    """Extends the abstract WTForm to add the extra fields.

    Each extra field will use a field named ``custom_ID``.

    :param event: The `Event` for which to create the abstract form.
    :return: An `AbstractForm` subclass.
    """
    form_class = type(b'_AbstractReviewForm', (AbstractReviewForm,), {})
    for idx, question in enumerate(event.abstract_review_questions, start=1):
        name = 'question_{}'.format(question.id)
        range_ = event.cfa.rating_range
        field = RadioField(question.text, validators=[DataRequired()],
                           choices=[(unicode(n), unicode(n)) for n in range(range_[0], range_[1] + 1)],
                           widget=JinjaWidget('events/reviews/rating_widget.html',
                                              question=question, rating_range=event.cfa.rating_range, inline_js=True,
                                              question_idx=idx))
        setattr(form_class, name, field)
    return form_class


def build_review_form(abstract=None, track=None, review=None):
    if review:
        abstract = review.abstract
        track = review.track
    review_form_class = make_review_form(abstract.event_new)
    reviews_for_track = abstract.get_reviews(user=session.user, group=track)
    review_for_track = reviews_for_track[0] if reviews_for_track else None

    if review_for_track:
        answers = {'question_{}'.format(rating.question.id): rating.value
                   for rating in review_for_track.ratings}
        defaults = FormDefaults(obj=review_for_track, **answers)
    else:
        defaults = FormDefaults()

    return review_form_class(prefix='track-{}'.format(track.id), obj=defaults, abstract=abstract,
                             edit=review is not None)


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
    submission_instructions = IndicoMarkdownField(_('Instructions'), editor=True,
                                                  description=_("These instructions will be displayed right before the "
                                                                "submission form."))

    @generated_data
    def announcement_render_mode(self):
        return RenderMode.markdown

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(AbstractSubmissionSettingsForm, self).__init__(*args, **kwargs)

    def validate_contrib_type_required(self, field):
        if field.data and not self.event.contribution_types.count():
            raise ValidationError(_('The event has no contribution types defined.'))


class AbstractReviewingSettingsForm(IndicoForm):
    """Settings form for abstract reviewing"""

    RATING_FIELDS = ('scale_lower', 'scale_upper')

    scale_lower = IntegerField(_("Scale (from)"), [UsedIf(lambda form, field: not form.has_ratings), InputRequired()])
    scale_upper = IntegerField(_("Scale (to)"), [UsedIf(lambda form, field: not form.has_ratings), InputRequired()])
    allow_convener_judgment = BooleanField(_("Allow track conveners to judge"), widget=SwitchWidget(),
                                           description=_("Enabling this allows track conveners to make a judgment "
                                                         "such as accepting or rejecting an abstract."))
    allow_comments = BooleanField(_("Allow comments"), widget=SwitchWidget(),
                                  description=_("Enabling this allows judges, conveners and reviewers to leave "
                                                "comments on abstracts."))
    allow_contributors_in_comments = BooleanField(_("Allow contributors in comments"),
                                                  [HiddenUnless('allow_comments', preserve_data=True)],
                                                  widget=SwitchWidget(),
                                                  description=_("Enabling this allows submitters, authors, and "
                                                                "speakers to also participate in the comments."))
    abstract_review_questions = ReviewQuestionsField(_("Review questions"), question_model=AbstractReviewQuestion,
                                                     extra_fields=[{'id': 'no_score',
                                                                    'caption': _("Exclude from score"),
                                                                    'type': 'checkbox'}])
    reviewing_instructions = IndicoMarkdownField(_('Reviewing Instructions'), editor=True,
                                                 description=_("These instructions will be displayed right before the "
                                                               "reviewing form."))
    judgment_instructions = IndicoMarkdownField(_('Judgment Instructions'), editor=True,
                                                description=_("These instructions will be displayed right before the "
                                                              "decision box."))

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


class AbstractJudgmentFormBase(IndicoForm):
    """Form base class for abstract judgment operations"""

    _order = ('judgment', 'accepted_track', 'accepted_contrib_type', 'session', 'duplicate_of', 'merged_into',
              'merge_persons', 'judgment_comment', 'send_notifications')

    accepted_track = QuerySelectField(_("Track"), [HiddenUnless('judgment', AbstractAction.accept)],
                                      get_label='title', allow_blank=True, blank_text=_("Choose a track..."),
                                      description=_("The abstract will be accepted in this track"))
    accepted_contrib_type = QuerySelectField(_("Contribution type"), [HiddenUnless('judgment', AbstractAction.accept)],
                                             get_label=lambda x: x.name.title(), allow_blank=True,
                                             blank_text=_("You may choose a contribution type..."),
                                             description=_("The abstract will be converted "
                                                           "into a contribution of this type"))
    session = QuerySelectField(_("Session"), [HiddenUnless('judgment', AbstractAction.accept)],
                               get_label='title', allow_blank=True, blank_text=_("You may choose a session..."),
                               description=_("The generated contribution will be allocated in this session"))
    duplicate_of = AbstractField(_("Duplicate of"),
                                 [HiddenUnless('judgment', AbstractAction.mark_as_duplicate), DataRequired()],
                                 description=_("The current abstract will be marked as duplicate of the selected one"),
                                 ajax_endpoint='abstracts.other_abstracts')
    merged_into = AbstractField(_("Merge into"), [HiddenUnless('judgment', AbstractAction.merge), DataRequired()],
                                description=_("The current abstract will be merged into the selected one"),
                                ajax_endpoint='abstracts.other_abstracts')
    merge_persons = BooleanField(_("Merge persons"), [HiddenUnless('judgment', AbstractAction.merge)],
                                 description=_("Authors and speakers of the current abstract will be added to the "
                                               "selected one"))
    judgment_comment = TextAreaField(_("Comment"), render_kw={'placeholder': _("Leave a comment for the submitter...")})
    # TODO: show only if notifications apply?
    send_notifications = BooleanField(_("Send notifications to submitter"), default=True)

    def __init__(self, *args, **kwargs):
        super(AbstractJudgmentFormBase, self).__init__(*args, **kwargs)
        self.session.query = Session.query.with_parent(self.event).order_by(Session.title)
        if not self.session.query.count():
            del self.session
        self.accepted_track.query = Track.query.with_parent(self.event).order_by(Track.position)
        if not self.accepted_track.query.count():
            del self.accepted_track
        self.accepted_contrib_type.query = (ContributionType.query
                                            .with_parent(self.event)
                                            .order_by(ContributionType.name))
        if not self.accepted_contrib_type.query.count():
            del self.accepted_contrib_type

    @property
    def split_data(self):
        abstract_data = self.data
        judgment_data = {
            'judgment': abstract_data.pop('judgment'),
            'send_notifications': abstract_data.pop('send_notifications'),
            'contrib_session': abstract_data.pop('session', None),
            'merge_persons': abstract_data.pop('merge_persons', None)
        }
        return judgment_data, abstract_data


class AbstractJudgmentForm(AbstractJudgmentFormBase):
    """Form for judging an abstract"""

    judgment = IndicoEnumSelectField(_("Judgment"), [DataRequired()], enum=AbstractAction,
                                     skip={AbstractAction.change_tracks})

    def __init__(self, *args, **kwargs):
        abstract = kwargs.pop('abstract')
        self.event = abstract.event_new
        candidate_tracks = list(abstract.candidate_tracks)
        candidate_contrib_types = list(abstract.candidate_contrib_types)
        if len(candidate_tracks) == 1:
            kwargs.setdefault('accepted_track', candidate_tracks[0])
        if len(candidate_contrib_types) == 1:
            kwargs.setdefault('accepted_contrib_type', candidate_contrib_types[0])
        elif not abstract.reviews:
            kwargs.setdefault('accepted_contrib_type', abstract.submitted_contrib_type)
        super(AbstractJudgmentForm, self).__init__(*args, **kwargs)
        self.duplicate_of.excluded_abstract_ids = {abstract.id}
        self.merged_into.excluded_abstract_ids = {abstract.id}


class AbstractReviewForm(IndicoForm):
    """Form for reviewing an abstract"""

    _order = ('proposed_action', 'proposed_contribution_type', 'proposed_related_abstract', 'proposed_tracks',
              'comment')

    comment = TextAreaField(_("Comment"), render_kw={'placeholder': _("You may leave a comment (only visible to "
                                                                      "conveners and judges)...")})
    proposed_action = IndicoEnumSelectField(_("Proposed Action"), [DataRequired()], enum=AbstractAction)
    proposed_related_abstract = AbstractField(
        _("Target Abstract"),
        [HiddenUnless('proposed_action', {AbstractAction.mark_as_duplicate, AbstractAction.merge}), DataRequired()],
        description=_("The current abstract should be marked as duplicate of the selected one"),
        ajax_endpoint='abstracts.other_abstracts')
    proposed_contribution_type = QuerySelectField(
        _("Contribution type"),
        [HiddenUnless('proposed_action', AbstractAction.accept)],
        get_label=lambda x: x.name.title(), allow_blank=True, blank_text=_("You may propose a contribution type..."))
    proposed_tracks = IndicoQuerySelectMultipleCheckboxField(
        _("Propose for tracks"),
        [HiddenUnless('proposed_action', AbstractAction.change_tracks), DataRequired()],
        collection_class=set, get_label='title')

    def __init__(self, edit=False, *args, **kwargs):
        abstract = kwargs.pop('abstract')
        super(AbstractReviewForm, self).__init__(*args, **kwargs)
        self.event = abstract.event_new
        if not edit:
            self.proposed_action.none = _("Propose an action...")
        self.proposed_related_abstract.excluded_abstract_ids = {abstract.id}
        self.proposed_contribution_type.query = (ContributionType.query
                                                 .with_parent(self.event)
                                                 .order_by(ContributionType.name))
        if not self.proposed_contribution_type.query.count():
            del self.proposed_contribution_type
        reviewed_for_track_ids = {t.id for t in abstract.reviewed_for_tracks}
        existing_prop_track_cond = (Track.id.in_(t.id for t in self.proposed_tracks.object_data)
                                    if self.proposed_tracks.object_data else False)
        self.proposed_tracks.query = (Track.query
                                      .with_parent(self.event)
                                      .filter(db.or_(Track.id.notin_(reviewed_for_track_ids),
                                                     existing_prop_track_cond))
                                      .order_by(Track.position))
        if not self.proposed_tracks.query.count():
            del self.proposed_tracks
            self.proposed_action.skip.add(AbstractAction.change_tracks)

    @property
    def split_data(self):
        data = self.data
        return {'questions_data': {k: v for k, v in data.iteritems() if k.startswith('question_')},
                'review_data': {k: v for k, v in data.iteritems() if not k.startswith('question_')}}


class BulkAbstractJudgmentForm(AbstractJudgmentFormBase):
    _order = ('judgment', 'accepted_track', 'override_contrib_type', 'accepted_contrib_type', 'session', 'duplicate_of',
              'merged_into', 'merge_persons', 'judgment_comment', 'send_notifications')

    judgment = HiddenEnumField(enum=AbstractAction, skip={AbstractAction.change_tracks})
    abstract_id = HiddenFieldList()
    submitted = HiddenField()
    override_contrib_type = BooleanField(_("Override contribution type"),
                                         [HiddenUnless('judgment', AbstractAction.accept)], widget=SwitchWidget(),
                                         description=_("Override the contribution type for all selected abstracts"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super(BulkAbstractJudgmentForm, self).__init__(*args, **kwargs)
        if self.accepted_track:
            self.accepted_track.description = _("The abstracts will be accepted in this track")
        if self.accepted_contrib_type:
            self.accepted_contrib_type.description = _("The abstracts will be converted into a contribution of this "
                                                       "type")
        else:
            del self.override_contrib_type
        if self.session:
            self.session.description = _("The generated contributions will be allocated in this session")
        self.duplicate_of.description = _("The selected abstracts will be marked as duplicate of the specified "
                                          "abstract")
        self.merged_into.description = _("The selected abstracts will be merged into the specified abstract")
        self.merge_persons.description = _("Authors and speakers of the selected abstracts will be added to the "
                                           "specified abstract")
        self.duplicate_of.excluded_abstract_ids = set(kwargs['abstract_id'])
        self.merged_into.excluded_abstract_ids = set(kwargs['abstract_id'])
        if kwargs['judgment']:
            self._remove_unused_fields(kwargs['judgment'])

    def _remove_unused_fields(self, judgment):
        for field in list(self):
            validator = next((v for v in field.validators if isinstance(v, HiddenUnless) and v.field == 'judgment'),
                             None)
            if validator is None:
                continue
            if not any(v.name == judgment for v in validator.value):
                delattr(self, field.name)

    def is_submitted(self):
        return super(BulkAbstractJudgmentForm, self).is_submitted() and 'submitted' in request.form

    @classmethod
    def _add_contrib_type_hidden_unless(cls):
        # In the bulk form we need to hide/disable the contrib type selector unless we want to
        # override the type specified in the abstract.  However, multiple HiddenUnless validators
        # are not supported in the client-side JS so we only add it to this form - it removes
        # inactive fields on the server side so it still works (the JavaScript picks up the last
        # HiddenUnless validator)
        inject_validators(BulkAbstractJudgmentForm, 'accepted_contrib_type', [HiddenUnless('override_contrib_type')])


BulkAbstractJudgmentForm._add_contrib_type_hidden_unless()


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
    extra_cc_emails = EmailListField(_("CC"), description=_("Additional CC e-mail addresses (one per line)"))
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

    default_tpl = SelectField(_('Email template'), [DataRequired()], choices=[
        ('submit', _('Submit')),
        ('accept', _('Accept')),
        ('reject', _('Reject')),
        ('merge', _('Merge'))
    ], description=_("The default template that will be used as a basis for this notification. "
                     "You can customize it later."))


class AbstractForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired()])
    description = IndicoMarkdownField(_('Content'), editor=True, mathjax=True)
    submitted_contrib_type = QuerySelectField(_("Contribution type"), get_label='name', allow_blank=True,
                                              blank_text=_("No type selected"))
    person_links = AbstractPersonLinkListField(_("Authors"), [DataRequired()], default_author_type=AuthorType.primary)
    submission_comment = TextAreaField(_("Comments"))
    attachments = EditableFileField(_('Attachments'), multiple_files=True, lightweight=True)

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.abstract = kwargs.pop('abstract', None)
        description_settings = abstracts_settings.get(self.event, 'description_settings')
        description_validators = self._get_description_validators(description_settings)
        if description_validators:
            inject_validators(self, 'description', description_validators)
        if abstracts_settings.get(self.event, 'contrib_type_required'):
            inject_validators(self, 'submitted_contrib_type', [DataRequired()])
        super(AbstractForm, self).__init__(*args, **kwargs)
        self.submitted_contrib_type.query = self.event.contribution_types
        if not self.submitted_contrib_type.query.count():
            del self.submitted_contrib_type
        if not self.event.cfa.allow_attachments:
            del self.attachments
        if not description_settings['is_active']:
            del self.description
        self.person_links.require_speaker_author = abstracts_settings.get(self.event, 'speakers_required')
        self.person_links.allow_speakers = abstracts_settings.get(self.event, 'allow_speakers')

    def _get_description_validators(self, description_settings):
        validators = []
        if description_settings['is_required']:
            validators.append(DataRequired())
        if description_settings['max_length']:
            validators.append(SoftLength(max=description_settings['max_length']))
        if description_settings['max_words']:
            validators.append(WordCount(max=description_settings['max_words']))
        return validators


class NoTrackMixin(object):
    def __init__(self, *args, **kwargs):
        self.track_field_disabled = True
        super(NoTrackMixin, self).__init__(*args, **kwargs)


class _SingleChoiceQuerySelectMultipleField(IndicoQuerySelectMultipleField):
    # single-choice version of the multi select field that uses
    # a collection instead of a single value for `data`
    widget = Select()

    def iter_choices(self):
        yield ('__None', self.blank_text, self.data is None)
        for choice in super(_SingleChoiceQuerySelectMultipleField, self).iter_choices():
            yield choice

    def process_formdata(self, valuelist):
        # remove "no value" indicator. QuerySelectMultipleField validation
        # is broken in WTForms so it never causes a validation error to have
        # invalid data in valuelist but maybe it gets fixed at some point...
        valuelist = list(set(valuelist) - {'__None'})
        if len(valuelist) > 1:
            raise ValueError('Received more than one value')
        super(_SingleChoiceQuerySelectMultipleField, self).process_formdata(valuelist)


class SingleTrackMixin(object):
    submitted_for_tracks = _SingleChoiceQuerySelectMultipleField(_("Track"), get_label='title', collection_class=set)

    def __init__(self, *args, **kwargs):
        event = kwargs['event']
        self.track_field_disabled = (kwargs.get('abstract') and
                                     kwargs['abstract'].edit_track_mode != EditTrackMode.both)
        if abstracts_settings.get(event, 'tracks_required') and not self.track_field_disabled:
            inject_validators(self, 'submitted_for_tracks', [DataRequired()])
        super(SingleTrackMixin, self).__init__(*args, **kwargs)
        if not abstracts_settings.get(event, 'tracks_required'):
            self.submitted_for_tracks.blank_text = _('No track selected')
        self.submitted_for_tracks.query = Track.query.with_parent(event).order_by(Track.position)


class MultiTrackMixin(object):
    submitted_for_tracks = IndicoQuerySelectMultipleCheckboxField(_("Tracks"), get_label='title', collection_class=set)

    def __init__(self, *args, **kwargs):
        event = kwargs['event']
        self.track_field_disabled = (kwargs.get('abstract') and
                                     kwargs['abstract'].edit_track_mode != EditTrackMode.both)
        if abstracts_settings.get(event, 'tracks_required') and not self.track_field_disabled:
            inject_validators(self, 'submitted_for_tracks', [DataRequired()])
        super(MultiTrackMixin, self).__init__(*args, **kwargs)
        self.submitted_for_tracks.query = Track.query.with_parent(event).order_by(Track.position)


class SendNotificationsMixin(object):
    send_notifications = BooleanField(_("Send email notifications"), default=True)


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


class AbstractCommentForm(IndicoForm):
    text = TextAreaField(_("Comment"), [DataRequired()], render_kw={'placeholder': _("Leave a comment...")})
    visibility = IndicoEnumSelectField(_("Visibility"), [DataRequired()], enum=AbstractCommentVisibility,
                                       skip={AbstractCommentVisibility.users})

    def __init__(self, *args, **kwargs):
        comment = kwargs.get('obj')
        user = comment.user if comment else kwargs.pop('user')
        abstract = kwargs.pop('abstract')
        super(IndicoForm, self).__init__(*args, **kwargs)
        if not abstract.event_new.cfa.allow_contributors_in_comments:
            self.visibility.skip.add(AbstractCommentVisibility.contributors)
        if not abstract.can_judge(user) and not abstract.can_convene(user):
            self.visibility.skip.add(AbstractCommentVisibility.judges)
            if not abstract.can_review(user):
                del self.visibility


class AbstractReviewedForTracksForm(IndicoForm):
    reviewed_for_tracks = IndicoQuerySelectMultipleCheckboxField(_("Tracks"), get_label='title', collection_class=set)

    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event')
        super(AbstractReviewedForTracksForm, self).__init__(*args, **kwargs)
        self.reviewed_for_tracks.query = Track.query.with_parent(event).order_by(Track.position)
