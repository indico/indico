# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import render_template, session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.permissions import ManagementPermission
from indico.modules.events import Event
from indico.modules.events.features.base import EventFeature
from indico.modules.events.layout.util import MenuEntryData
from indico.modules.events.surveys.util import query_active_surveys
from indico.util.i18n import _
from indico.web.flask.templating import template_hook
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.survey')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.surveys.models.submissions import SurveySubmission
    SurveySubmission.find(user_id=source.id).update({SurveySubmission.user_id: target.id})


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.has_feature('surveys') or not event.can_manage(session.user, 'surveys'):
        return
    return SideMenuItem('surveys', _('Surveys'), url_for('surveys.manage_survey_list', event), section='organization')


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    def _visible(event):
        return event.has_feature('surveys') and query_active_surveys(event).has_rows()

    return MenuEntryData(_('Surveys'), 'surveys', 'surveys.display_survey_list', position=12, visible=_visible)


def _get_active_surveys(event):
    if not event.has_feature('surveys'):
        return []
    return query_active_surveys(event).all()


@template_hook('event-header')
def _inject_event_header(event, **kwargs):
    from indico.modules.events.surveys.util import was_survey_submitted
    surveys = _get_active_surveys(event)
    if surveys:
        return render_template('events/surveys/display/event_header.html', surveys=surveys,
                               was_survey_submitted=was_survey_submitted)


@template_hook('conference-home-info')
def _inject_survey_announcement(event, **kwargs):
    from indico.modules.events.surveys.util import was_survey_submitted
    surveys = _get_active_surveys(event)
    if surveys:
        return render_template('events/surveys/display/conference_home.html', surveys=surveys, event=event,
                               was_survey_submitted=was_survey_submitted)


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return SurveysFeature


@signals.acl.get_management_permissions.connect_via(Event)
def _get_management_permissions(sender, **kwargs):
    return SurveysPermission


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.events.surveys.tasks  # noqa: F401


class SurveysFeature(EventFeature):
    name = 'surveys'
    friendly_name = _('Surveys')
    description = _('Gives event managers the opportunity to create surveys.')

    @classmethod
    def is_default_for_event(cls, event):
        return True


class SurveysPermission(ManagementPermission):
    name = 'surveys'
    friendly_name = _('Surveys')
    description = _('Grants management access to surveys.')
    user_selectable = True


@signals.get_placeholders.connect_via('survey-link-email')
def _get_placeholders(sender, event, survey, **kwargs):
    from indico.modules.events.surveys import placeholders
    yield placeholders.EventTitlePlaceholder
    yield placeholders.SurveyTitlePlaceholder
    yield placeholders.SurveyLinkPlaceholder
