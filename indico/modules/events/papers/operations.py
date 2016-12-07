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

from flask import session

from indico.modules.events.logs.models.entries import EventLogRealm, EventLogKind
from indico.modules.events.util import update_object_principals
from indico.modules.events.papers import logger
from indico.modules.events.papers.models.competences import PaperCompetence


def set_reviewing_state(event, reviewing_type, enable):
    event.cfp.set_reviewing_state(reviewing_type, enable)
    action = 'enabled' if enable else 'disabled'
    logger.info("Reviewing type '%s' for event %r %s by %r", reviewing_type, event, action, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
              "{} reviewing type '{}'".format("Enabled" if enable else "Disabled", reviewing_type), session.user)


def update_team_members(event, managers, judges, content_reviewers, layout_reviewers):
    update_object_principals(event, managers, role='paper_manager')
    update_object_principals(event, judges, role='paper_judge')
    if content_reviewers:
        update_object_principals(event, content_reviewers, role='paper_content_reviewer')
    if layout_reviewers:
        update_object_principals(event, layout_reviewers, role='paper_layout_reviewer')
    logger.info("Paper teams of %r updated by %r", event, session.user)


def create_competences(event, user, competences):
    PaperCompetence(event_new=event, user=user, competences=competences)
    logger.info("Competences for user %r for event %r created by %r", user, event, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
              "Added competences of {}".format(user.full_name), session.user,
              data={'Competences': ', '.join(competences)})


def update_competences(user_competences, competences):
    event = user_competences.event_new
    user_competences.competences = competences
    logger.info("Competences for user %r in event %r updated by %r", user_competences.user, event, session.user)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Papers',
              "Updated competences for user {}".format(user_competences.user.full_name), session.user,
              data={'Competences': ', '.join(competences)})
