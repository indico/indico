# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin, RenderMode
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii, text_to_repr


def get_next_position(context):
    from indico.modules.events.tracks.models.groups import TrackGroup

    event_id = context.current_parameters['event_id']
    track_max_position = db.session.query(db.func.max(Track.position)).filter_by(event_id=event_id).scalar()
    track_group_max_position = db.session.query(db.func.max(TrackGroup.position)).filter_by(event_id=event_id).scalar()
    pos = max(track_max_position, track_group_max_position)
    return (pos or 0) + 1


class Track(DescriptionMixin, ProtectionManagersMixin, db.Model):
    __tablename__ = 'tracks'
    __table_args__ = {'schema': 'events'}

    disable_protection_mode = True
    is_track_group = False

    possible_render_modes = {RenderMode.markdown}
    default_render_mode = RenderMode.markdown

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    code = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    position = db.Column(
        db.Integer,
        nullable=False,
        default=get_next_position
    )
    default_session_id = db.Column(
        db.Integer,
        db.ForeignKey('events.sessions.id'),
        index=True,
        nullable=True
    )
    track_group_id = db.Column(
        db.Integer,
        db.ForeignKey('events.track_groups.id', ondelete='SET NULL'),
        index=True,
        nullable=True
    )
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'tracks',
            cascade='all, delete-orphan',
            lazy=True,
            order_by=position
        )
    )
    acl_entries = db.relationship(
        'TrackPrincipal',
        lazy=True,
        cascade='all, delete-orphan',
        collection_class=set,
        backref='track'
    )
    default_session = db.relationship(
        'Session',
        lazy=True,
        backref='default_for_tracks'
    )
    track_group = db.relationship(
        'TrackGroup',
        lazy=True,
        backref=db.backref(
            'tracks',
            order_by=position,
            lazy=True,
            passive_deletes=True
        )
    )

    # relationship backrefs:
    # - abstract_reviews (AbstractReview.track)
    # - abstracts_accepted (Abstract.accepted_track)
    # - abstracts_reviewed (Abstract.reviewed_for_tracks)
    # - abstracts_submitted (Abstract.submitted_for_tracks)
    # - contributions (Contribution.track)
    # - proposed_abstract_reviews (AbstractReview.proposed_tracks)

    @property
    def short_title(self):
        return self.code if self.code else self.title

    @property
    def full_title(self):
        return '{} - {}'.format(self.code, self.title) if self.code else self.title

    @property
    def title_with_group(self):
        return '{}: {}'.format(self.track_group.title, self.title) if self.track_group else self.title

    @property
    def short_title_with_group(self):
        return '{}: {}'.format(self.track_group.title, self.short_title) if self.track_group else self.short_title

    @property
    def full_title_with_group(self):
        return '{}: {}'.format(self.track_group.title, self.full_title) if self.track_group else self.full_title

    @locator_property
    def locator(self):
        return dict(self.event.locator, track_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=text_to_repr(self.title))

    def can_delete(self, user):
        return self.event.can_manage(user) and not self.abstracts_accepted

    def can_review_abstracts(self, user):
        if not user:
            return False
        elif not self.event.can_manage(user, permission='abstract_reviewer', explicit_permission=True):
            return False
        elif self.event.can_manage(user, permission='review_all_abstracts', explicit_permission=True):
            return True
        return self.can_manage(user, permission='review', explicit_permission=True)

    def can_convene(self, user):
        if not user:
            return False
        elif not self.event.can_manage(user, permission='track_convener', explicit_permission=True):
            return False
        elif self.event.can_manage(user, permission='convene_all_abstracts', explicit_permission=True):
            return True
        return self.can_manage(user, permission='convene', explicit_permission=True)
