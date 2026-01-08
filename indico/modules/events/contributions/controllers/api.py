# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict

from flask import jsonify, session

from indico.modules.events.contributions.controllers.management import RHManageContributionsBase
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.contributions.util import get_contributions_for_user
from indico.modules.users.schemas import FavoriteContributionSchema


# FIXME: Use another base class
class RHAPIMyContributions(RHManageContributionsBase):
    """API endpoint to get a user's contributions."""

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

        return jsonify({
            category: [
                FavoriteContributionSchema(context={'user': session.user, 'event': self.event}).dump(c)
                for c in contributions
            ] for category, contributions in categorized.items()
        })
