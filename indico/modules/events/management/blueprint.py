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

from indico.modules.events import event_management_object_url_prefixes
from indico.modules.events.management.controllers import (RHEventSettings, RHEditEventData, RHEditEventDates,
                                                          RHEditEventLocation, RHEditEventPersons,
                                                          RHEditEventContactInfo, RHEditEventClassification,
                                                          RHDeleteEvent, RHChangeEventType, RHLockEvent, RHUnlockEvent,
                                                          RHShowNonInheriting, RHEventProtection,
                                                          RHMoveEvent, RHEventACL, RHEventACLMessage,
                                                          RHManageReferences, RHManageEventLocation,
                                                          RHManageEventPersonLinks, RHManageEventKeywords,
                                                          RHPrintEventPoster, RHPosterPrintSettings)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_management', __name__, template_folder='templates',
                      virtual_template_folder='events/management',
                      url_prefix='/event/<confId>/manage')

_bp.add_url_rule('/', 'settings', RHEventSettings)
_bp.add_url_rule('/settings/data', 'edit_data', RHEditEventData, methods=('GET', 'POST'))
_bp.add_url_rule('/settings/dates', 'edit_dates', RHEditEventDates, methods=('GET', 'POST'))
_bp.add_url_rule('/settings/location', 'edit_location', RHEditEventLocation, methods=('GET', 'POST'))
_bp.add_url_rule('/settings/persons', 'edit_persons', RHEditEventPersons, methods=('GET', 'POST'))
_bp.add_url_rule('/settings/contact-info', 'edit_contact_info', RHEditEventContactInfo, methods=('GET', 'POST'))
_bp.add_url_rule('/settings/classification', 'edit_classification', RHEditEventClassification, methods=('GET', 'POST'))
_bp.add_url_rule('/delete', 'delete', RHDeleteEvent, methods=('GET', 'POST'))
_bp.add_url_rule('/change-type', 'change_type', RHChangeEventType, methods=('POST',))
_bp.add_url_rule('/lock', 'lock', RHLockEvent, methods=('GET', 'POST'))
_bp.add_url_rule('/unlock', 'unlock', RHUnlockEvent, methods=('POST',))
_bp.add_url_rule('/protection', 'protection', RHEventProtection, methods=('GET', 'POST'))
_bp.add_url_rule('/protection/acl', 'acl', RHEventACL)
_bp.add_url_rule('/protection/acl-message', 'acl_message', RHEventACLMessage)
_bp.add_url_rule('/move', 'move', RHMoveEvent, methods=('POST',))
_bp.add_url_rule('/external-ids', 'manage_event_references', RHManageReferences, methods=('GET', 'POST'))
_bp.add_url_rule('/event-location', 'manage_event_location', RHManageEventLocation, methods=('GET', 'POST'))
_bp.add_url_rule('/event-keywords', 'manage_event_keywords', RHManageEventKeywords, methods=('GET', 'POST'))
_bp.add_url_rule('/event-persons', 'manage_event_person_links', RHManageEventPersonLinks, methods=('GET', 'POST'))
_bp.add_url_rule('/print-poster/settings', 'poster_settings', RHPosterPrintSettings, methods=('GET', 'POST'))
_bp.add_url_rule('/print-poster/<int:template_id>/<uuid>', 'print_poster', RHPrintEventPoster)

for object_type, prefixes in event_management_object_url_prefixes.iteritems():
    if object_type == 'subcontribution':
        continue
    for prefix in prefixes:
        prefix = '!/event/<confId>' + prefix
        _bp.add_url_rule(prefix + '/show-non-inheriting', 'show_non_inheriting', RHShowNonInheriting,
                         defaults={'object_type': object_type})
