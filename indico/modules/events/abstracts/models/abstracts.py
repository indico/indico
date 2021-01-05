# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import division, unicode_literals

from collections import defaultdict
from itertools import chain
from operator import attrgetter

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin, RenderMode
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.modules.events.abstracts.models.review_questions import AbstractReviewQuestion
from indico.modules.events.abstracts.models.review_ratings import AbstractReviewRating
from indico.modules.events.abstracts.models.reviews import AbstractAction, AbstractReview
from indico.modules.events.abstracts.settings import AllowEditingType
from indico.modules.events.contributions.models.contributions import CustomFieldsMixin, _get_next_friendly_id
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.models.persons import AuthorsSpeakersMixin
from indico.modules.events.models.reviews import ProposalMixin, ProposalRevisionMixin
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import MarkdownText, format_repr, return_ascii, text_to_repr
from indico.util.struct.enum import IndicoEnum, RichIntEnum


class AbstractState(RichIntEnum):
    __titles__ = [None, _("Submitted"), _("Withdrawn"), _("Accepted"), _("Rejected"), _("Merged"), _("Duplicate"),
                  _("Invited")]
    __css_classes__ = [None, '', 'outline dashed', 'success', 'error', 'visited', 'strong', 'warning']
    submitted = 1
    withdrawn = 2
    accepted = 3
    rejected = 4
    merged = 5
    duplicate = 6
    invited = 7


class AbstractPublicState(RichIntEnum):
    __titles__ = {i: title for i, title in enumerate(AbstractState.__titles__[2:], 2)}
    __titles__.update({-1: _("Awaiting Review"), -2: _("Under Review")})
    __css_classes__ = {i: css_class for i, css_class in enumerate(AbstractState.__css_classes__[2:], 2)}
    __css_classes__.update({-1: '', -2: 'highlight'})
    # regular states (must match AbstractState!)
    withdrawn = 2
    accepted = 3
    rejected = 4
    merged = 5
    duplicate = 6
    invited = 7
    # special states
    awaiting = -1
    under_review = -2


class AbstractReviewingState(RichIntEnum):
    __titles__ = [_("Not Started"), _("In progress"), _("Positive"), _("Conflicting"), _("Negative"), _("Mixed")]
    __css_classes__ = ['', '', 'success', '', 'error', 'warning']
    not_started = 0
    in_progress = 1
    positive = 2
    conflicting = 3
    negative = 4
    mixed = 5


class EditTrackMode(int, IndicoEnum):
    none = 0
    both = 1
    reviewed_for = 2


class Abstract(ProposalMixin, ProposalRevisionMixin, DescriptionMixin, CustomFieldsMixin, AuthorsSpeakersMixin,
               db.Model):
    """An abstract that can be associated to a Contribution."""

    __tablename__ = 'abstracts'
    __auto_table_args = (db.Index(None, 'friendly_id', 'event_id', unique=True,
                                  postgresql_where=db.text('NOT is_deleted')),
                         db.CheckConstraint('(state = {}) OR (accepted_track_id IS NULL)'
                                            .format(AbstractState.accepted),
                                            name='accepted_track_id_only_accepted'),
                         db.CheckConstraint('(state = {}) OR (accepted_contrib_type_id IS NULL)'
                                            .format(AbstractState.accepted),
                                            name='accepted_contrib_type_id_only_accepted'),
                         db.CheckConstraint('(state = {}) = (merged_into_id IS NOT NULL)'
                                            .format(AbstractState.merged),
                                            name='merged_into_id_only_merged'),
                         db.CheckConstraint('(state = {}) = (duplicate_of_id IS NOT NULL)'
                                            .format(AbstractState.duplicate),
                                            name='duplicate_of_id_only_duplicate'),
                         db.CheckConstraint('(state IN ({}, {}, {}, {})) = (judge_id IS NOT NULL)'
                                            .format(AbstractState.accepted, AbstractState.rejected,
                                                    AbstractState.merged, AbstractState.duplicate),
                                            name='judge_if_judged'),
                         db.CheckConstraint('(state IN ({}, {}, {}, {})) = (judgment_dt IS NOT NULL)'
                                            .format(AbstractState.accepted, AbstractState.rejected,
                                                    AbstractState.merged, AbstractState.duplicate),
                                            name='judgment_dt_if_judged'),
                         db.CheckConstraint('(state != {}) OR (uuid IS NOT NULL)'.format(AbstractState.invited),
                                            name='uuid_if_invited'),
                         {'schema': 'event_abstracts'})

    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown
    marshmallow_aliases = {'_description': 'content'}

    # Proposal mixin properties
    proposal_type = 'abstract'
    call_for_proposals_attr = 'cfa'
    delete_comment_endpoint = 'abstracts.delete_abstract_comment'
    create_comment_endpoint = 'abstracts.comment_abstract'
    edit_comment_endpoint = 'abstracts.edit_abstract_comment'
    create_review_endpoint = 'abstracts.review_abstract'
    edit_review_endpoint = 'abstracts.edit_review'
    create_judgment_endpoint = 'abstracts.judge_abstract'
    revisions_enabled = False

    AUTHORS_SPEAKERS_DISPLAY_ORDER_ATTR = 'display_order_key_lastname'

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    uuid = db.Column(
        UUID,
        index=True,
        unique=True,
        nullable=True
    )
    friendly_id = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_friendly_id
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    #: ID of the user who submitted the abstract
    submitter_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    submitted_contrib_type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contribution_types.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    submitted_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    modified_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=True,
        index=True
    )
    modified_dt = db.Column(
        UTCDateTime,
        nullable=True,
    )
    state = db.Column(
        PyIntEnum(AbstractState),
        nullable=False,
        default=AbstractState.submitted
    )
    submission_comment = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: ID of the user who judged the abstract
    judge_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    _judgment_comment = db.Column(
        'judgment_comment',
        db.Text,
        nullable=False,
        default=''
    )
    judgment_dt = db.Column(
        UTCDateTime,
        nullable=True,
    )
    accepted_track_id = db.Column(
        db.Integer,
        db.ForeignKey('events.tracks.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    accepted_contrib_type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contribution_types.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    merged_into_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        index=True,
        nullable=True
    )
    duplicate_of_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        index=True,
        nullable=True
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'abstracts',
            primaryjoin='(Abstract.event_id == Event.id) & ~Abstract.is_deleted',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    #: User who submitted the abstract
    submitter = db.relationship(
        'User',
        lazy=True,
        foreign_keys=submitter_id,
        backref=db.backref(
            'abstracts',
            primaryjoin='(Abstract.submitter_id == User.id) & ~Abstract.is_deleted',
            lazy='dynamic'
        )
    )
    modified_by = db.relationship(
        'User',
        lazy=True,
        foreign_keys=modified_by_id,
        backref=db.backref(
            'modified_abstracts',
            primaryjoin='(Abstract.modified_by_id == User.id) & ~Abstract.is_deleted',
            lazy='dynamic'
        )
    )
    submitted_contrib_type = db.relationship(
        'ContributionType',
        lazy=True,
        foreign_keys=submitted_contrib_type_id,
        backref=db.backref(
            'proposed_abstracts',
            primaryjoin='(Abstract.submitted_contrib_type_id == ContributionType.id) & ~Abstract.is_deleted',
            lazy=True,
            passive_deletes=True
        )
    )
    submitted_for_tracks = db.relationship(
        'Track',
        secondary='event_abstracts.submitted_for_tracks',
        collection_class=set,
        backref=db.backref(
            'abstracts_submitted',
            primaryjoin='event_abstracts.submitted_for_tracks.c.track_id == Track.id',
            secondaryjoin='(event_abstracts.submitted_for_tracks.c.abstract_id == Abstract.id) & ~Abstract.is_deleted',
            collection_class=set,
            lazy=True,
            passive_deletes=True
        )
    )
    reviewed_for_tracks = db.relationship(
        'Track',
        secondary='event_abstracts.reviewed_for_tracks',
        collection_class=set,
        backref=db.backref(
            'abstracts_reviewed',
            primaryjoin='event_abstracts.reviewed_for_tracks.c.track_id == Track.id',
            secondaryjoin='(event_abstracts.reviewed_for_tracks.c.abstract_id == Abstract.id) & ~Abstract.is_deleted',
            collection_class=set,
            lazy=True,
            passive_deletes=True
        )
    )
    #: User who judged the abstract
    judge = db.relationship(
        'User',
        lazy=True,
        foreign_keys=judge_id,
        backref=db.backref(
            'judged_abstracts',
            primaryjoin='(Abstract.judge_id == User.id) & ~Abstract.is_deleted',
            lazy='dynamic'
        )
    )
    accepted_track = db.relationship(
        'Track',
        lazy=True,
        backref=db.backref(
            'abstracts_accepted',
            primaryjoin='(Abstract.accepted_track_id == Track.id) & ~Abstract.is_deleted',
            lazy=True,
            passive_deletes=True
        )
    )
    accepted_contrib_type = db.relationship(
        'ContributionType',
        lazy=True,
        foreign_keys=accepted_contrib_type_id,
        backref=db.backref(
            'abstracts_accepted',
            primaryjoin='(Abstract.accepted_contrib_type_id == ContributionType.id) & ~Abstract.is_deleted',
            lazy=True,
            passive_deletes=True
        )
    )
    merged_into = db.relationship(
        'Abstract',
        lazy=True,
        remote_side=id,
        foreign_keys=merged_into_id,
        backref=db.backref(
            'merged_abstracts',
            primaryjoin=(db.remote(merged_into_id) == id) & ~db.remote(is_deleted),
            lazy=True
        )
    )
    duplicate_of = db.relationship(
        'Abstract',
        lazy=True,
        remote_side=id,
        foreign_keys=duplicate_of_id,
        backref=db.backref(
            'duplicate_abstracts',
            primaryjoin=(db.remote(duplicate_of_id) == id) & ~db.remote(is_deleted),
            lazy=True
        )
    )
    #: Data stored in abstract/contribution fields
    field_values = db.relationship(
        'AbstractFieldValue',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'abstract',
            lazy=True
        )
    )
    #: Persons associated with this abstract
    person_links = db.relationship(
        'AbstractPersonLink',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='AbstractPersonLink.display_order',
        backref=db.backref(
            'abstract',
            lazy=True
        )
    )

    # relationship backrefs:
    # - comments (AbstractComment.abstract)
    # - contribution (Contribution.abstract)
    # - duplicate_abstracts (Abstract.duplicate_of)
    # - email_logs (AbstractEmailLogEntry.abstract)
    # - files (AbstractFile.abstract)
    # - merged_abstracts (Abstract.merged_into)
    # - proposed_related_abstract_reviews (AbstractReview.proposed_related_abstract)
    # - reviews (AbstractReview.abstract)

    @property
    def candidate_contrib_types(self):
        contrib_types = set()
        for track in self.reviewed_for_tracks:
            if self.get_track_reviewing_state(track) == AbstractReviewingState.positive:
                review = next((x for x in self.reviews if x.track == track), None)
                contrib_types.add(review.proposed_contribution_type)
        return contrib_types

    @property
    def candidate_tracks(self):
        states = {AbstractReviewingState.positive, AbstractReviewingState.conflicting}
        return {t for t in self.reviewed_for_tracks if self.get_track_reviewing_state(t) in states}

    @property
    def edit_track_mode(self):
        if not inspect(self).persistent:
            return EditTrackMode.both
        elif self.state not in {AbstractState.submitted, AbstractState.withdrawn}:
            return EditTrackMode.none
        elif (self.public_state in (AbstractPublicState.awaiting, AbstractPublicState.withdrawn) and
                self.reviewed_for_tracks == self.submitted_for_tracks):
            return EditTrackMode.both
        else:
            return EditTrackMode.reviewed_for

    @property
    def public_state(self):
        if self.state != AbstractState.submitted:
            return getattr(AbstractPublicState, self.state.name)
        elif self.reviews:
            return AbstractPublicState.under_review
        else:
            return AbstractPublicState.awaiting

    @property
    def reviewing_state(self):
        if not self.reviews:
            return AbstractReviewingState.not_started
        track_states = {x: self.get_track_reviewing_state(x) for x in self.reviewed_for_tracks}
        positiveish_states = {AbstractReviewingState.positive, AbstractReviewingState.conflicting}
        if any(x == AbstractReviewingState.not_started for x in track_states.itervalues()):
            return AbstractReviewingState.in_progress
        elif all(x == AbstractReviewingState.negative for x in track_states.itervalues()):
            return AbstractReviewingState.negative
        elif all(x in positiveish_states for x in track_states.itervalues()):
            if len(self.reviewed_for_tracks) > 1:
                # Accepted for more than one track
                return AbstractReviewingState.conflicting
            elif any(x == AbstractReviewingState.conflicting for x in track_states.itervalues()):
                # The only accepted track is in conflicting state
                return AbstractReviewingState.conflicting
            else:
                return AbstractReviewingState.positive
        else:
            return AbstractReviewingState.mixed

    @property
    def score(self):
        scores = [x.score for x in self.reviews if x.score is not None]
        if not scores:
            return None
        return sum(scores) / len(scores)

    @property
    def data_by_field(self):
        return {value.contribution_field_id: value for value in self.field_values}

    @locator_property
    def locator(self):
        return dict(self.event.locator, abstract_id=self.id)

    @locator.token
    def locator(self):
        return dict(self.event.locator, uuid=self.uuid)

    @hybrid_property
    def judgment_comment(self):
        return MarkdownText(self._judgment_comment)

    @judgment_comment.setter
    def judgment_comment(self, value):
        self._judgment_comment = value

    @judgment_comment.expression
    def judgment_comment(cls):
        return cls._judgment_comment

    @property
    def verbose_title(self):
        return '#{} ({})'.format(self.friendly_id, self.title)

    @property
    def is_in_final_state(self):
        return self.state != AbstractState.submitted

    @property
    def modification_ended(self):
        return self.event.cfa.modification_ended

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', is_deleted=False, _text=text_to_repr(self.title))

    def can_access(self, user):
        if not user:
            return False
        if self.submitter == user:
            return True
        if self.event.can_manage(user):
            return True
        if any(x.person.user == user for x in self.person_links):
            return True
        return self.can_judge(user) or self.can_convene(user) or self.can_review(user)

    def can_comment(self, user, check_state=False):
        if not user:
            return False
        if check_state and self.is_in_final_state:
            return False
        if not self.event.cfa.allow_comments:
            return False
        if self.user_owns(user) and self.event.cfa.allow_contributors_in_comments:
            return True
        return self.can_judge(user) or self.can_convene(user) or self.can_review(user)

    def can_convene(self, user):
        if not user:
            return False
        elif not self.event.can_manage(user, permission='track_convener', explicit_permission=True):
            return False
        elif self.event.can_manage(user, permission='convene_all_abstracts', explicit_permission=True):
            return True
        elif any(track.can_manage(user, permission='convene', explicit_permission=True)
                 for track in self.reviewed_for_tracks):
            return True
        else:
            return False

    def can_review(self, user, check_state=False):
        # The total number of tracks/events a user is a reviewer for (indico-wide)
        # is usually reasonably low so we just access the relationships instead of
        # sending a more specific query which would need to be cached to avoid
        # repeating it when performing this check on many abstracts.
        if not user:
            return False
        elif check_state and self.public_state not in (AbstractPublicState.under_review, AbstractPublicState.awaiting):
            return False
        elif not self.event.can_manage(user, permission='abstract_reviewer', explicit_permission=True):
            return False
        elif self.event.can_manage(user, permission='review_all_abstracts', explicit_permission=True):
            return True
        elif any(track.can_manage(user, permission='review', explicit_permission=True)
                 for track in self.reviewed_for_tracks):
            return True
        else:
            return False

    def can_judge(self, user, check_state=False):
        if not user:
            return False
        elif check_state and self.state != AbstractState.submitted:
            return False
        elif self.event.can_manage(user):
            return True
        elif self.event.cfa.allow_convener_judgment and self.can_convene(user):
            return True
        else:
            return False

    def can_edit(self, user):
        if not user:
            return False

        manager_edit_states = (
            AbstractPublicState.under_review,
            AbstractPublicState.withdrawn,
            AbstractPublicState.awaiting,
            AbstractPublicState.invited,
        )
        if self.public_state in manager_edit_states and self.event.can_manage(user):
            return True
        elif self.public_state not in (AbstractPublicState.awaiting, AbstractPublicState.invited):
            return False
        elif not self.user_owns(user) or not self.event.cfa.can_edit_abstracts(user):
            return False

        editing_allowed = self.event.cfa.allow_editing
        author_type = next((x.author_type for x in self.person_links if x.person.user == user), None)
        is_primary = author_type == AuthorType.primary
        is_secondary = author_type == AuthorType.secondary
        if user == self.submitter:
            return True
        elif editing_allowed == AllowEditingType.submitter_all:
            return True
        elif editing_allowed == AllowEditingType.submitter_primary and is_primary:
            return True
        elif editing_allowed == AllowEditingType.submitter_authors and (is_primary or is_secondary):
            return True
        return False

    def can_withdraw(self, user, check_state=False):
        if not user:
            return False
        elif self.event.can_manage(user) and (not check_state or self.state != AbstractState.withdrawn):
            return True
        elif user == self.submitter and (not check_state or self.state == AbstractState.submitted):
            return True
        else:
            return False

    def can_see_reviews(self, user):
        return self.can_judge(user) or self.can_convene(user)

    def get_timeline(self, user=None):
        comments = [x for x in self.comments if x.can_view(user)] if user else self.comments
        reviews = [x for x in self.reviews if x.can_view(user)] if user else self.reviews
        return sorted(chain(comments, reviews), key=attrgetter('created_dt'))

    def get_track_reviewing_state(self, track):
        if track not in self.reviewed_for_tracks:
            raise ValueError("Abstract not in review for given track")
        reviews = self.get_reviews(group=track)
        if not reviews:
            return AbstractReviewingState.not_started
        rejections = any(x.proposed_action == AbstractAction.reject for x in reviews)
        acceptances = {x for x in reviews if x.proposed_action == AbstractAction.accept}
        if rejections and not acceptances:
            return AbstractReviewingState.negative
        elif acceptances and not rejections:
            proposed_contrib_types = {x.proposed_contribution_type for x in acceptances
                                      if x.proposed_contribution_type is not None}
            if len(proposed_contrib_types) <= 1:
                return AbstractReviewingState.positive
            else:
                return AbstractReviewingState.conflicting
        else:
            return AbstractReviewingState.mixed

    def get_track_question_scores(self):
        query = (db.session.query(AbstractReview.track_id,
                                  AbstractReviewQuestion,
                                  db.func.avg(AbstractReviewRating.value.op('#>>')('{}').cast(db.Integer)))
                 .join(AbstractReviewRating.review)
                 .join(AbstractReviewRating.question)
                 .filter(AbstractReview.abstract == self,
                         AbstractReviewQuestion.field_type == 'rating',
                         db.func.jsonb_typeof(AbstractReviewRating.value) == 'null',
                         ~AbstractReviewQuestion.is_deleted,
                         ~AbstractReviewQuestion.no_score)
                 .group_by(AbstractReview.track_id, AbstractReviewQuestion.id))
        scores = defaultdict(lambda: defaultdict(lambda: None))
        for track_id, question, score in query:
            scores[track_id][question] = score
        return scores

    def get_reviewed_for_groups(self, user, include_reviewed=False):
        already_reviewed = {each.track for each in self.get_reviews(user=user)} if include_reviewed else set()
        if self.event.can_manage(user, permission='review_all_abstracts', explicit_permission=True):
            return self.reviewed_for_tracks | already_reviewed
        reviewer_tracks = {track for track in self.reviewed_for_tracks
                           if track.can_manage(user, permission='review', explicit_permission=True)}
        return reviewer_tracks | already_reviewed

    def get_track_score(self, track):
        if track not in self.reviewed_for_tracks:
            raise ValueError("Abstract not in review for given track")
        reviews = [x for x in self.reviews if x.track == track]
        scores = [x.score for x in reviews if x.score is not None]
        if not scores:
            return None
        return sum(scores) / len(scores)

    def reset_state(self):
        self.state = AbstractState.submitted
        self.judgment_comment = ''
        self.judge = None
        self.judgment_dt = None
        self.accepted_track = None
        self.accepted_contrib_type = None
        self.merged_into = None
        self.duplicate_of = None

    def user_owns(self, user):
        if not user:
            return None
        return user == self.submitter or any(x.person.user == user for x in self.person_links)

    def log(self, *args, **kwargs):
        """Log with prefilled metadata for the abstract."""
        self.event.log(*args, meta={'abstract_id': self.id}, **kwargs)
