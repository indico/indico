# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import uuid4

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.session import object_session

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.errors import IndicoError
from indico.core.notifications import make_email, send_email
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.surveys import logger
from indico.util.date_time import now_utc
from indico.util.enum import IndicoEnum
from indico.util.locators import locator_property
from indico.web.flask.templating import get_template_module


class SurveyState(IndicoEnum):
    not_ready = 1
    ready_to_open = 2
    active_and_clean = 3
    active_and_answered = 4
    finished = 5
    limit_reached = 6


class Survey(db.Model):
    __tablename__ = 'surveys'
    __table_args__ = (db.CheckConstraint('anonymous OR require_user', 'valid_anonymous_user'),
                      {'schema': 'event_surveys'})

    #: The ID of the survey
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: The title of the survey
    title = db.Column(
        db.String,
        nullable=False
    )
    uuid = db.Column(
        UUID,
        unique=True,
        nullable=False,
        default=lambda: str(uuid4())
    )
    # An introduction text for users of the survey
    introduction = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: Whether submissions will not be linked to a user
    anonymous = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether submissions must be done by logged users
    require_user = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    # #: Whether the survey is only for selected users
    private = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Maximum number of submissions allowed
    submission_limit = db.Column(
        db.Integer,
        nullable=True
    )
    #: Datetime when the survey is open
    start_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    #: Datetime when the survey is closed
    end_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    #: Whether the survey has been marked as deleted
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether start notification has been already sent
    start_notification_sent = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether to send survey related notifications to users
    notifications_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether include Participants / Registrants when sending start notifications
    notify_participants = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Email addresses to notify about the start of a survey
    start_notification_emails = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    #: Email addresses to notify about new submissions
    new_submission_emails = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    #: Whether answers can be saved without submitting the survey
    partial_completion = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The last user-friendly submission ID
    _last_friendly_submission_id = db.deferred(db.Column(
        'last_friendly_submission_id',
        db.Integer,
        nullable=False,
        default=0
    ))

    #: The list of submissions
    submissions = db.relationship(
        'SurveySubmission',
        cascade='all, delete-orphan',
        lazy=True,
        backref=db.backref(
            'survey',
            lazy=True
        )
    )

    #: The list of items
    items = db.relationship(
        'SurveyItem',
        cascade='all, delete-orphan',
        lazy=True,
        backref=db.backref(
            'survey',
            lazy=True
        )
    )
    #: The list of sections
    sections = db.relationship(
        'SurveySection',
        lazy=True,
        viewonly=True,
        order_by='SurveySection.position'
    )
    #: The list of questions
    questions = db.relationship(
        'SurveyQuestion',
        lazy=True,
        viewonly=True
    )
    #: The Event containing this survey
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'surveys',
            lazy=True
        )
    )

    # relationship backrefs:
    # - anonymous_submissions (AnonymousSurveySubmission.survey)

    @hybrid_property
    def has_ended(self):
        return self.end_dt is not None and self.end_dt <= now_utc()

    @has_ended.expression
    def has_ended(cls):
        return cls.end_dt.isnot(None) & (cls.end_dt <= now_utc())

    @hybrid_property
    def has_started(self):
        return self.start_dt is not None and self.start_dt <= now_utc()

    @has_started.expression
    def has_started(cls):
        return cls.start_dt.isnot(None) & (cls.start_dt <= now_utc())

    @locator_property
    def locator(self):
        return {'event_id': self.event_id,
                'survey_id': self.id}

    @locator.token
    def locator(self):
        """A locator that adds the UUID if the survey is private."""
        token = self.uuid if self.private else None
        return dict(self.locator, token=token)

    @property
    def state(self):
        if not self.questions:
            return SurveyState.not_ready
        if not self.has_started:
            return SurveyState.ready_to_open
        if self.limit_reached:
            return SurveyState.limit_reached
        if not self.has_ended:
            return SurveyState.active_and_answered if self.submissions else SurveyState.active_and_clean
        return SurveyState.finished

    @property
    def limit_reached(self):
        return self.submission_limit is not None and len(self.submissions) >= self.submission_limit

    @property
    def start_notification_recipients(self):
        """Return all recipients of the notifications.

        This includes both explicit recipients and, if enabled,
        participants of the event.
        """
        recipients = set(self.start_notification_emails)
        if self.notify_participants:
            recipients.update(reg.email for reg in Registration.get_all_for_event(self.event))
        recipients.discard('')  # just in case there was an empty email address somewhere
        return recipients

    @hybrid_property
    def is_active(self):
        return not self.is_deleted and self.state in {SurveyState.active_and_answered, SurveyState.active_and_clean}

    @is_active.expression
    def is_active(cls):
        submissions = (db.session.query(db.func.count(db.m.SurveySubmission.id))
                       .filter(db.m.SurveySubmission.survey_id == cls.id)
                       .correlate(Survey)
                       .scalar_subquery())
        limit_criterion = db.case([(cls.submission_limit.is_(None), True)],
                                  else_=(submissions < cls.submission_limit))
        return ~cls.is_deleted & cls.questions.any() & cls.has_started & ~cls.has_ended & limit_criterion

    @hybrid_property
    def is_visible(self):
        return (not self.is_deleted and
                self.state in {SurveyState.active_and_answered, SurveyState.active_and_clean, SurveyState.finished,
                               SurveyState.limit_reached})

    @is_visible.expression
    def is_visible(cls):
        return ~cls.is_deleted & cls.questions.any() & cls.has_started

    def __repr__(self):
        return f'<Survey({self.id}, {self.event_id}): {self.title}>'

    def can_submit(self, user):
        return self.is_active and (not self.require_user or user)

    def open(self):
        if self.state != SurveyState.ready_to_open:
            raise IndicoError("Survey can't be opened")
        self.start_dt = now_utc()

    def close(self):
        if self.state not in (SurveyState.active_and_clean, SurveyState.active_and_answered, SurveyState.limit_reached):
            raise IndicoError("Survey can't be closed")
        self.end_dt = now_utc()

    def send_start_notification(self):
        if not self.notifications_enabled or self.start_notification_sent or not self.event.has_feature('surveys'):
            return
        with self.event.force_event_locale():
            template_module = get_template_module('events/surveys/emails/start_notification_email.txt', survey=self)
            email = make_email(bcc_list=self.start_notification_recipients, template=template_module)
        send_email(email, event=self.event, module='Surveys')
        logger.info('Sending start notification for survey %s', self)
        self.start_notification_sent = True

    def send_submission_notification(self, submission):
        if not self.notifications_enabled:
            return
        with self.event.force_event_locale():
            template_module = get_template_module('events/surveys/emails/new_submission_email.txt',
                                                  submission=submission)
            email = make_email(bcc_list=self.new_submission_emails, template=template_module)
        send_email(email, event=self.event, module='Surveys')
        logger.info('Sending submission notification for survey %s', self)


@listens_for(Survey.questions, 'append')
@listens_for(Survey.questions, 'remove')
@listens_for(Survey.sections, 'append')
@listens_for(Survey.sections, 'remove')
def _wrong_collection_modified(target, value, *unused):
    raise Exception('This collection is view-only. Use `items` for write operations!')


@listens_for(Survey.items, 'append')
@listens_for(Survey.items, 'remove')
def _items_modified(target, value, *unused):
    sess = object_session(target)
    if sess is not None and inspect(target).persistent:
        sess.expire(target, ['questions', 'sections'])
