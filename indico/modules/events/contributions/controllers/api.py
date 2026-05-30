# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict

from flask import jsonify, session
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import StaleDataError
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.events.contributions.controllers.display import RHDisplayProtectionBase
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.contributions.schemas import UserContributionSchema
from indico.modules.events.contributions.util import get_contributions_for_user
from indico.modules.events.controllers.base import RHAuthenticatedEventBase
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.util.marshmallow import ModelField
from indico.util.string import natural_sort_key
from indico.web.args import use_rh_kwargs


class RHAPIMyContributions(RHDisplayProtectionBase):
    """API endpoint to get a user's contributions."""

    MENU_ENTRY_NAME = 'my_timetable'

    def _process(self):
        contribs = get_contributions_for_user(self.event, session.user)
        categorized = defaultdict(set)
        for contrib in contribs:
            added = False
            links = [link for link in contrib.person_links if link.person.user == session.user]
            for link in links:
                if link.is_speaker:
                    categorized['speaker'].add(contrib)
                    added = True
                if link.author_type == AuthorType.primary:
                    categorized['primary'].add(contrib)
                    added = True
                if link.author_type == AuthorType.secondary:
                    categorized['secondary'].add(contrib)
                    added = True
            # Only add contributions to the submitter category if they are not in any other category
            if not added and contrib.can_manage(session.user, 'submit', allow_admin=False, check_parent=False):
                categorized['submitter'].add(contrib)

        schema = UserContributionSchema(context={'user': session.user}, many=True)
        return jsonify({
            category: sorted(schema.dump(contributions), key=lambda x: (natural_sort_key(x['title']), x['friendly_id']))
            for category, contributions in categorized.items()
        })


class RHFavoriteContributionsAPI(RHAuthenticatedEventBase):
    @use_rh_kwargs({
        'contribution': ModelField(Contribution, with_parent='event', data_key='contrib_id')
    }, location='view_args', rh_context=('event',))
    def _process(self, contribution=None):
        self.contribution = contribution
        return super()._process()

    def _process_GET(self):
        if self.contribution is None:
            favorites = (
                Contribution.query
                .with_parent(session.user)
                .with_parent(self.event)
                .outerjoin(Contribution.timetable_entry)
                .options(contains_eager(Contribution.timetable_entry).lazyload('*'))
                .order_by(TimetableEntry.start_dt.is_(None), TimetableEntry.start_dt, Contribution.friendly_id)
                .all()
            )
            return UserContributionSchema(exclude=('edit_url',), many=True).jsonify(favorites)
        return jsonify(self.contribution in session.user.favorite_contributions)

    def _process_PUT(self):
        if self.contribution not in session.user.favorite_contributions:
            if not self.contribution.can_access(session.user):
                raise Forbidden
            session.user.favorite_contributions.add(self.contribution)
        return jsonify(success=True)

    def _process_DELETE(self):
        if self.contribution in session.user.favorite_contributions:
            session.user.favorite_contributions.discard(self.contribution)
            try:
                db.session.flush()
            except StaleDataError:
                # Deleted in another transaction
                db.session.rollback()
        return jsonify(success=True)
