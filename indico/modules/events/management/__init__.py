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
    yield 'organization', SideMenuSection(_("Organization"), 50, icon='list', active=True)
    yield 'services', SideMenuSection(_("Services"), 40, icon='broadcast')
    yield 'reports', SideMenuSection(_("Reports"), 30, icon='stack')
    yield 'customization', SideMenuSection(_("Customization"), 20, icon='image')
    yield 'advanced', SideMenuSection(_("Advanced options"), 10, icon='lamp')


@signals.menu.items.connect_via('event-management-sidemenu')
def _sidemenu_items(sender, event, **kwargs):

    # Some legacy handling of menu items
    # Once those parts are modularized, we will be able to include them
    # conditionally from their respective modules.

    can_modify = event.canModify(session.user)
    rb_active = Config.getInstance().getIsRoomBookingActive()
    cfa_enabled = event.hasEnabledSection('cfa')
    can_manage_registration = can_modify or event.canManageRegistration(session.user)
    reg_form_enabled = event.hasEnabledSection('regForm')

    event_type = event.getType()
    is_lecture = event_type == 'simple_event'
    is_conference = event_type == 'conference'
    paper_review = event.getConfPaperReview()
    is_review_staff = paper_review.isInReviewingTeam(session.avatar)
    is_review_manager = paper_review.isPaperReviewManager(session.avatar)

    yield 'general', SideMenuItem(_('General settings'),
                                  url_for('event_mgmt.conferenceModification', event),
                                  90,
                                  visible=can_modify,
                                  icon='settings')
    yield 'timetable', SideMenuItem(_('Timetable'),
                                    url_for('event_mgmt.confModifSchedule', event),
                                    80,
                                    icon='calendar',
                                    visible=(can_modify and not is_lecture))
    yield 'room_booking', SideMenuItem(_('Room Booking'),
                                       url_for('event_mgmt.rooms_booking_list', event),
                                       50,
                                       icon='location',
                                       visible=(rb_active and can_modify))
    if is_conference:
        yield 'program', SideMenuItem(_('Programme'),
                                      url_for('event_mgmt.confModifProgram', event),
                                      section='organization',
                                      visible=can_modify)
        yield 'registration', SideMenuItem(_('Registration'),
                                           url_for('event_mgmt.confModifRegistrationForm', event),
                                           section='organization',
                                           visible=(reg_form_enabled and can_manage_registration))
        yield 'abstracts', SideMenuItem(_('Abstracts'),
                                        url_for('event_mgmt.confModifCFA', event),
                                        section='organization',
                                        visible=(cfa_enabled and can_modify))
        yield 'contributions', SideMenuItem(_('Contributions'),
                                            url_for('event_mgmt.confModifContribList', event),
                                            section='organization',
                                            visible=(can_modify or is_review_manager))
        yield 'paper_reviewing', SideMenuItem(_('Paper Reviewing'),
                                              url_for('event_mgmt.confModifReviewing-access', event),
                                              section='organization',
                                              visible=(can_modify or is_review_staff))
    else:
        yield 'participants', SideMenuItem(_('Participants'),
                                           url_for('event_mgmt.confModifParticipants', event),
                                           section='organization',
                                           visible=can_modify)

    yield 'lists', SideMenuItem(_('Lists'),
                                url_for('event_mgmt.confModifListings-allSpeakers', event),
                                section='reports',
                                visible=(can_modify and not is_lecture))
    yield 'utilities', SideMenuItem(_('Utilities'),
                                    url_for('event_mgmt.confModifTools', event),
                                    section='advanced',
                                    visible=can_modify)
    yield 'protection', SideMenuItem(_('Protection'),
                                     url_for('event_mgmt.confModifAC', event),
                                     60,
                                     icon='shield',
                                     visible=can_modify)
