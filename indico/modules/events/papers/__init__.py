# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

"""
The ``papers`` module handles the Indico's Paper Peer Reviewing workflow.
The "inputs" of this module are the conference papers, which will be uploaded
by the corresponding authors/submitters.
"""

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.permissions import ManagementPermission
from indico.modules.events.features.base import EventFeature
from indico.modules.events.models.events import Event, EventType
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.papers')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.cfp.is_manager(session.user) or not PapersFeature.is_allowed_for_event(event):
        return
    return SideMenuItem('papers', _('Peer Reviewing'), url_for('papers.management', event),
                        section='workflows', weight=20)


@signals.menu.items.connect_via('event-editing-sidemenu')
def _extend_editing_menu(sender, event, **kwargs):
    from indico.modules.events.papers.util import has_contributions_with_user_paper_submission_rights
    if not session.user or not event.has_feature('papers'):
        return None
    if (has_contributions_with_user_paper_submission_rights(event, session.user) or
            event.cfp.is_staff(session.user)):
        return SideMenuItem('papers', _('Peer Reviewing'), url_for('papers.call_for_papers', event))


@signals.event_management.management_url.connect
def _get_event_management_url(event, **kwargs):
    if event.cfp.is_manager(session.user):
        return url_for('papers.management', event)


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return PapersFeature


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.papers.models.comments import PaperReviewComment
    from indico.modules.events.papers.models.competences import PaperCompetence
    from indico.modules.events.papers.models.reviews import PaperReview
    from indico.modules.events.papers.models.revisions import PaperRevision
    PaperReviewComment.query.filter_by(user_id=source.id).update({PaperReviewComment.user_id: target.id})
    PaperReviewComment.query.filter_by(modified_by_id=source.id).update({PaperReviewComment.modified_by_id: target.id})
    PaperReview.query.filter_by(user_id=source.id).update({PaperReview.user_id: target.id})
    PaperRevision.query.filter_by(submitter_id=source.id).update({PaperRevision.submitter_id: target.id})
    PaperRevision.query.filter_by(judge_id=source.id).update({PaperRevision.judge_id: target.id})
    PaperCompetence.merge_users(target, source)
    target.judge_for_contributions |= source.judge_for_contributions
    source.judge_for_contributions.clear()
    target.content_reviewer_for_contributions |= source.content_reviewer_for_contributions
    source.content_reviewer_for_contributions.clear()
    target.layout_reviewer_for_contributions |= source.layout_reviewer_for_contributions
    source.layout_reviewer_for_contributions.clear()


@signals.acl.get_management_permissions.connect_via(Event)
def _get_management_permissions(sender, **kwargs):
    yield PaperManagerPermission
    yield PaperJudgePermission
    yield PaperContentReviewerPermission
    yield PaperLayoutReviewerPermission


class PapersFeature(EventFeature):
    name = 'papers'
    friendly_name = _('Paper Peer Reviewing')
    description = _('Gives event managers the opportunity to let contribution authors '
                    'submit papers and use the paper peer reviewing workflow.')

    @classmethod
    def is_allowed_for_event(cls, event):
        return event.type_ == EventType.conference


class PaperManagerPermission(ManagementPermission):
    name = 'paper_manager'
    friendly_name = _('Paper Manager')
    description = _('Grants management rights for paper peer reviewing on an event.')
    user_selectable = True


class PaperJudgePermission(ManagementPermission):
    name = 'paper_judge'
    friendly_name = _('Judge')
    description = _('Grants paper judgment rights for assigned papers.')


class PaperContentReviewerPermission(ManagementPermission):
    name = 'paper_content_reviewer'
    friendly_name = _('Content reviewer')
    description = _('Grants content reviewing rights for assigned papers.')


class PaperLayoutReviewerPermission(ManagementPermission):
    name = 'paper_layout_reviewer'
    friendly_name = _('Layout reviewer')
    description = _('Grants layout reviewing rights for assigned papers.')


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    from indico.modules.events.layout.util import MenuEntryData

    def _judging_area_visible(event):
        if not session.user or not event.has_feature('papers'):
            return False
        return event.cfp.can_access_judging_area(session.user)

    def _reviewing_area_visible(event):
        if not session.user or not event.has_feature('papers'):
            return False
        return event.cfp.can_access_reviewing_area(session.user)

    def _call_for_papers_visible(event):
        from indico.modules.events.papers.util import has_contributions_with_user_paper_submission_rights
        if not session.user or not event.has_feature('papers'):
            return False
        return (has_contributions_with_user_paper_submission_rights(event, session.user) or
                event.cfp.is_staff(session.user))

    yield MenuEntryData(title=_("Paper Peer Reviewing"), name='call_for_papers',
                        endpoint='papers.call_for_papers', position=8,
                        visible=_call_for_papers_visible)

    yield MenuEntryData(title=_("Reviewing Area"), name='paper_reviewing_area', parent='call_for_papers',
                        endpoint='papers.reviewing_area', position=0, visible=_reviewing_area_visible)

    yield MenuEntryData(title=_("Judging Area"), name='paper_judging_area', parent='call_for_papers',
                        endpoint='papers.papers_list', position=1, visible=_judging_area_visible)
