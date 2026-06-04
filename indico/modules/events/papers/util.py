# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.orm import load_only, noload

from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.papers.models.reviews import PaperReviewType
from indico.modules.events.papers.models.revisions import PaperRevision, PaperRevisionState
from indico.modules.users import User
from indico.util.date_time import now_utc


def _query_contributions_with_user_as_reviewer(event, user):
    query = Contribution.query.with_parent(event)
    return query.filter(db.or_(Contribution.paper_content_reviewers.any(User.id == user.id),
                               Contribution.paper_layout_reviewers.any(User.id == user.id)),
                        Contribution._paper_revisions.any())


def get_user_reviewed_contributions(event, user):
    """Get the list of contributions where user already reviewed paper."""
    contribs = _query_contributions_with_user_as_reviewer(event, user).all()
    return [contrib for contrib in contribs if contrib.paper.last_revision.has_user_reviewed(user)]


def get_user_contributions_to_review(event, user):
    """Get the list of contributions where user has paper to review."""
    contribs = _query_contributions_with_user_as_reviewer(event, user).all()
    return [contrib for contrib in contribs if not contrib.paper.last_revision.has_user_reviewed(user)]


def get_events_with_paper_roles(user, dt=None):
    """
    Get the IDs and PR roles of events where the user has any kind
    of paper reviewing privileges.

    :param user: A `User`
    :param dt: Only include events taking place on/after that date
    :return: A dict mapping event IDs to a set of roles
    """
    paper_permissions = {'paper_manager', 'paper_judge', 'paper_content_reviewer', 'paper_layout_reviewer'}
    role_criteria = [EventPrincipal.has_management_permission(permission, explicit=True)
                     for permission in paper_permissions]
    query = (user.in_event_acls
             .join(Event)
             .options(noload('user'), noload('local_group'), load_only('event_id', 'permissions'))
             .filter(~Event.is_deleted, Event.ends_after(dt))
             .filter(db.or_(*role_criteria)))
    return {principal.event_id: set(principal.permissions) & paper_permissions for principal in query}


def get_contributions_with_paper_submitted_by_user(event, user):
    return (Contribution.query.with_parent(event)
            .filter(Contribution._paper_revisions.any(PaperRevision.submitter == user))
            .all())


def _query_contributions_with_user_paper_submission_rights(event, user):
    criteria = [
        Contribution.abstract.has(Abstract.submitter_id == user.id),
        Contribution.acl_entries.any(db.and_(ContributionPrincipal.user == user,
                                             ContributionPrincipal.has_management_permission('submit')))]
    return Contribution.query.with_parent(event).filter(db.or_(*criteria))


def has_contributions_with_user_paper_submission_rights(event, user):
    return _query_contributions_with_user_paper_submission_rights(event, user).has_rows()


def generate_spreadsheet_from_paper_assignments(contributions, event):
    """Generate spreadsheet data for paper assignment exports."""
    id_header = 'ID'
    title_header = 'Title'
    state_header = 'State'
    track_header = 'Track'
    session_header = 'Session'
    type_header = 'Type'
    revision_header = 'Revision'
    judges_header = 'Judges'
    content_reviewers_header = 'Content reviewers'
    layout_reviewers_header = 'Layout reviewers'

    headers = [
        id_header,
        title_header,
        state_header,
        track_header,
        session_header,
        type_header,
        revision_header,
        judges_header,
    ]
    if event.cfp.content_reviewing_enabled:
        headers.append(content_reviewers_header)
    if event.cfp.layout_reviewing_enabled:
        headers.append(layout_reviewers_header)

    def _user_names(users):
        return [user.display_full_name for user in sorted(users, key=lambda user: user.display_full_name.lower())]

    rows = []
    for contrib in contributions:
        paper = contrib.paper
        row = {
            id_header: contrib.friendly_id,
            title_header: contrib.title,
            state_header: paper.last_revision.state.title if paper else 'Not submitted',
            track_header: contrib.track.title_with_group if contrib.track else 'No track',
            session_header: contrib.session.title if contrib.session else 'No session',
            type_header: contrib.type.name if contrib.type else '',
            revision_header: paper.revision_count if paper else '',
            judges_header: _user_names(contrib.paper_judges),
        }
        if event.cfp.content_reviewing_enabled:
            row[content_reviewers_header] = _user_names(contrib.paper_content_reviewers)
        if event.cfp.layout_reviewing_enabled:
            row[layout_reviewers_header] = _user_names(contrib.paper_layout_reviewers)
        rows.append(row)
    return headers, rows


def get_user_submittable_contributions(event, user):
    criteria = [Contribution._paper_last_revision == None,  # noqa: E711
                Contribution._paper_last_revision.has(PaperRevision.state == PaperRevisionState.to_be_corrected)]
    return (_query_contributions_with_user_paper_submission_rights(event, user)
            .filter(db.or_(*criteria))
            .all())


def is_type_reviewing_possible(cfp, review_type):
    if review_type == PaperReviewType.content:
        return (cfp.content_reviewing_enabled
                and (not cfp.content_reviewer_deadline_enforced or cfp.content_reviewer_deadline > now_utc()))
    elif review_type == PaperReviewType.layout:
        return (cfp.layout_reviewing_enabled
                and (not cfp.layout_reviewer_deadline_enforced or cfp.layout_reviewer_deadline > now_utc()))
    else:
        raise ValueError('invalid review type')
