# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.core import signals
from indico.core.config import Config
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem, SideMenuSection


@signals.menu.sections.connect_via('event-management-sidemenu')
def _sidemenu_sections(sender, **kwargs):
    yield SideMenuSection('organization', _("Organization"), 50, icon='list', active=True)
    yield SideMenuSection('services', _("Services"), 40, icon='broadcast')
    yield SideMenuSection('reports', _("Reports"), 30, icon='stack')
    yield SideMenuSection('customization', _("Customization"), 20, icon='image')
    yield SideMenuSection('advanced', _("Advanced options"), 10, icon='lamp')


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):

    # Some legacy handling of menu items
    # Once those parts are modularized, we will be able to include them
    # conditionally from their respective modules.

    can_modify = event.can_manage(session.user, allow_key=True)
    rb_active = Config.getInstance().getIsRoomBookingActive()
    cfa_enabled = event.as_legacy.hasEnabledSection('cfa')
    can_manage_registration = can_modify or event.can_manage(session.user, 'registration')
    reg_form_enabled = event.as_legacy.hasEnabledSection('regForm')

    event_type = event.as_legacy.getType()
    is_lecture = event_type == 'simple_event'
    is_conference = event_type == 'conference'
    paper_review = event.as_legacy.getConfPaperReview()
    is_review_staff = paper_review.isInReviewingTeam(session.avatar)
    is_review_manager = paper_review.isPaperReviewManager(session.avatar)

    if can_modify:
        yield SideMenuItem('general', _('General settings'),
                           url_for('event_mgmt.conferenceModification', event),
                           90,
                           icon='settings')
        if not is_lecture:
            yield SideMenuItem('timetable', _('Timetable'),
                               url_for('event_mgmt.confModifSchedule', event),
                               80,
                               icon='calendar')
        if rb_active:
            yield SideMenuItem('room_booking', _('Room Booking'),
                               url_for('event_mgmt.rooms_booking_list', event),
                               50,
                               icon='location')
    if is_conference:
        if can_modify:
            yield SideMenuItem('program', _('Programme'),
                               url_for('event_mgmt.confModifProgram', event),
                               section='organization')
        if reg_form_enabled and can_manage_registration:
            yield SideMenuItem('registration', _('Registration'),
                               url_for('event_mgmt.confModifRegistrationForm', event),
                               section='organization')
        if can_modify and cfa_enabled:
            yield SideMenuItem('abstracts', _('Abstracts'),
                               url_for('event_mgmt.confModifCFA', event),
                               section='organization')
        if can_modify or is_review_manager:
            yield SideMenuItem('contributions', _('Contributions'),
                               url_for('event_mgmt.confModifContribList', event),
                               section='organization')
        if can_modify or is_review_staff:
            yield SideMenuItem('paper_reviewing', _('Paper Reviewing'),
                               url_for('event_mgmt.confModifReviewing-access', event),
                               section='organization')
    else:
        if can_modify:
            yield SideMenuItem('participants', _('Participants'),
                               url_for('event_mgmt.confModifParticipants', event),
                               section='organization')

    if can_modify:
        if not is_lecture:
            yield SideMenuItem('lists', _('Lists'),
                               url_for('event_mgmt.confModifListings-allSpeakers', event),
                               section='reports')
        yield SideMenuItem('utilities', _('Utilities'),
                           url_for('event_mgmt.confModifTools', event),
                           section='advanced')
        yield SideMenuItem('protection', _('Protection'),
                           url_for('event_mgmt.confModifAC', event),
                           60,
                           icon='shield')
