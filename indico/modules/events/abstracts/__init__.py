# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from flask import render_template, session

from indico.core import signals
from indico.core.logger import Logger
from indico.core.roles import ManagementRole
from indico.modules.events.abstracts.clone import AbstractSettingsCloner
from indico.modules.events.abstracts.notifications import StateCondition, TrackCondition, ContributionTypeCondition
from indico.modules.events.features.base import EventFeature
from indico.modules.events.models.events import EventType, Event
from indico.modules.events.timetable.models.breaks import Break
from indico.util.i18n import _
from indico.util.placeholders import Placeholder
from indico.web.flask.templating import template_hook
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('events.abstracts')


@signals.event.updated.connect
@signals.event.contribution_created.connect
@signals.event.contribution_updated.connect
@signals.event.contribution_deleted.connect
@signals.event.session_deleted.connect
@signals.event.session_updated.connect
@signals.event.person_updated.connect
@signals.event.times_changed.connect
def _clear_boa_cache(sender, obj=None, **kwargs):
    from indico.modules.events.abstracts.util import clear_boa_cache
    if isinstance(obj, Break):
        # breaks do not show up in the BoA
        return
    event = (obj or sender).event_new
    clear_boa_cache(event)


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.can_manage(session.user) or not AbstractsFeature.is_allowed_for_event(event):
        return
    return SideMenuItem('abstracts', _('Call for Abstracts'), url_for('abstracts.management', event),
                        section='organization')


@signals.event.get_feature_definitions.connect
def _get_feature_definitions(sender, **kwargs):
    return AbstractsFeature


@signals.event_management.get_cloners.connect
def _get_cloners(sender, **kwargs):
    yield AbstractSettingsCloner


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.abstracts.models.abstracts import Abstract
    from indico.modules.events.abstracts.models.comments import AbstractComment
    from indico.modules.events.abstracts.models.reviews import AbstractReview
    from indico.modules.events.abstracts.settings import abstracts_settings
    Abstract.query.filter_by(submitter_id=source.id).update({Abstract.submitter_id: target.id})
    Abstract.query.filter_by(modified_by_id=source.id).update({Abstract.modified_by_id: target.id})
    Abstract.query.filter_by(judge_id=source.id).update({Abstract.judge_id: target.id})
    AbstractComment.query.filter_by(user_id=source.id).update({AbstractComment.user_id: target.id})
    AbstractComment.query.filter_by(modified_by_id=source.id).update({AbstractComment.modified_by_id: target.id})
    AbstractReview.query.filter_by(user_id=source.id).update({AbstractReview.user_id: target.id})
    abstracts_settings.acls.merge_users(target, source)


@signals.get_conditions.connect_via('abstract-notifications')
def _get_abstract_notification_rules(sender, **kwargs):
    yield StateCondition
    yield TrackCondition
    yield ContributionTypeCondition


class AbstractsFeature(EventFeature):
    name = 'abstracts'
    friendly_name = _('Call for Abstracts')
    description = _('Gives event managers the opportunity to open a "Call for Abstracts" and use the abstract '
                    'reviewing workflow.')

    @classmethod
    def is_allowed_for_event(cls, event):
        return event.type_ == EventType.conference


@signals.acl.get_management_roles.connect_via(Event)
def _get_management_roles(sender, **kwargs):
    return AbstractReviewerRole


class AbstractReviewerRole(ManagementRole):
    name = 'abstract_reviewer'
    friendly_name = _('Reviewer')
    description = _('Grants abstract reviewing rights on an event.')


@signals.get_placeholders.connect_via('abstract-notification-email')
def _get_notification_placeholders(sender, **kwargs):
    from indico.modules.events.abstracts import placeholders
    for name in placeholders.__all__:
        obj = getattr(placeholders, name)
        if issubclass(obj, Placeholder):
            yield obj


@signals.event.sidemenu.connect
def _extend_event_menu(sender, **kwargs):
    from indico.modules.events.abstracts.util import has_user_tracks
    from indico.modules.events.layout.util import MenuEntryData

    def _reviewing_area_visible(event):
        if not session.user or not event.has_feature('abstracts'):
            return False
        return has_user_tracks(event, session.user)

    yield MenuEntryData(title=_("Book of Abstracts"), name='abstracts_book', endpoint='abstracts.export_boa',
                        position=9, visible=lambda event: event.has_feature('abstracts'), static_site=True)
    yield MenuEntryData(title=_("Call for Abstracts"), name='call_for_abstracts',
                        endpoint='abstracts.call_for_abstracts', position=2,
                        visible=lambda event: event.has_feature('abstracts'))
    yield MenuEntryData(title=_("Reviewing Area"), name='abstract_reviewing_area',
                        endpoint='abstracts.display_reviewable_tracks', position=0, parent='call_for_abstracts',
                        visible=_reviewing_area_visible)


@template_hook('conference-home-info')
def _inject_cfa_announcement(event, **kwargs):
    if (event.has_feature('abstracts') and
            (event.cfa.is_open or (session.user and event.cfa.can_submit_abstracts(session.user)))):
        return render_template('events/abstracts/display/conference_home.html', event=event)
