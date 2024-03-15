# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import defaultdict

from flask import jsonify, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.contributions.models.persons import (AuthorType, ContributionPersonLink,
                                                                SubContributionPersonLink)
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.controllers.base import RHEventBase
from indico.modules.events.registration.util import get_registered_event_persons
from indico.modules.events.util import check_event_locked
from indico.util.i18n import _


class ManageEventMixin:
    ALLOW_LOCKED = False
    PERMISSION = None

    def _require_user(self):
        if session.user is None:
            raise Forbidden

    def _check_access(self):
        self._require_user()
        if not self.event.can_manage(session.user, permission=self.PERMISSION):
            raise Forbidden(_('You are not authorized to manage this event.'))
        check_event_locked(self, self.event)


class RHManageEventBase(RHEventBase, ManageEventMixin):
    """Base class for event management RHs."""

    DENY_FRAMES = True

    def _check_access(self):
        ManageEventMixin._check_access(self)


class RHContributionPersonListMixin:
    """List of persons somehow related to contributions (co-authors, speakers...)."""

    @property
    def _membership_filter(self):
        raise NotImplementedError

    def _process(self):
        contribution_persons = (ContributionPersonLink.query
                                .filter(ContributionPersonLink.contribution.has(self._membership_filter))
                                .all())
        contribution_persons.extend(SubContributionPersonLink.query
                                    .filter(SubContributionPersonLink.subcontribution
                                            .has(SubContribution.contribution.has(self._membership_filter)))
                                    .all())

        registered_persons = get_registered_event_persons(self.event)

        contribution_persons_dict = defaultdict(lambda: {'speaker': False, 'primary_author': False,
                                                         'secondary_author': False, 'not_registered': True})
        for contrib_person in contribution_persons:
            person_dict = contribution_persons_dict[contrib_person.person.identifier]
            person_dict['identifier'] = contrib_person.person.identifier
            person_dict['full_name'] = contrib_person.display_full_name
            person_dict['email'] = contrib_person.email
            person_dict['affiliation'] = contrib_person.affiliation
            person_dict['speaker'] |= contrib_person.is_speaker
            person_dict['primary_author'] |= contrib_person.author_type == AuthorType.primary
            person_dict['secondary_author'] |= contrib_person.author_type == AuthorType.secondary
            person_dict['registered'] = contrib_person.person in registered_persons

        return jsonify(event_persons=contribution_persons_dict)
