# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import render_template
from werkzeug.urls import url_parse

from indico.core.auth import multipass
from indico.core.config import config
from indico.modules.auth.util import url_for_login
from indico.modules.events.registration.util import url_rule_to_angular
from indico.modules.rb.models.locations import Location
from indico.web.assets import core_env
from indico.web.flask.util import url_for, url_rule_to_js


def generate_global_file():
    locations = Location.find_all() if config.ENABLE_ROOMBOOKING else []
    location_names = {loc.name: loc.name for loc in locations}
    default_location = next((loc.name for loc in locations if loc.is_default), None)
    ext_auths = [{
        'name': auth.name,
        'title': auth.title,
        'supports_groups': auth.supports_groups
    } for auth in multipass.identity_providers.itervalues() if auth.supports_search]

    indico_vars = {
        'Urls': {
            'Base': config.BASE_URL,
            'BasePath': url_parse(config.BASE_URL).path.rstrip('/'),
            'JsonRpcService': url_for('api.jsonrpc'),
            'ExportAPIBase': url_for('api.httpapi', prefix='export'),
            'APIBase': url_for('api.httpapi', prefix='api'),

            'ImagesBase': config.IMAGES_BASE_URL,

            'Login': url_for_login(),
            'Favorites': url_for('users.user_favorites'),
            'FavoriteUserAdd': url_for('users.user_favorites_users_add'),
            'FavoriteUserRemove': url_rule_to_js('users.user_favorites_user_remove'),

            'AttachmentManager': url_rule_to_js('attachments.management'),
            'ManagementAttachmentInfoColumn': url_rule_to_js('attachments.management_info_column'),

            'RoomBookingBookRoom': url_rule_to_js('rooms.room_book'),
            'RoomBookingBook': url_rule_to_js('rooms.book'),
            'RoomBookingDetails': url_rule_to_js('rooms.roomBooking-roomDetails'),
            'RoomBookingCloneBooking': url_rule_to_js('rooms.roomBooking-cloneBooking'),

            'APIKeyCreate': url_for('api.key_create'),
            'APIKeyTogglePersistent': url_for('api.key_toggle_persistent'),
            'FontSassBundle': core_env['fonts_sass'].urls(),

            'EventCreation': url_rule_to_js('events.create'),

            'RegistrationForm': {
                'section': {
                    'add': url_rule_to_angular('event_registration.add_section'),
                    'modify': url_rule_to_angular('event_registration.modify_section'),
                    'toggle': url_rule_to_angular('event_registration.toggle_section'),
                    'move': url_rule_to_angular('event_registration.move_section')
                },
                'field': {
                    'add': url_rule_to_angular('event_registration.add_field'),
                    'modify': url_rule_to_angular('event_registration.modify_field'),
                    'toggle': url_rule_to_angular('event_registration.toggle_field'),
                    'move': url_rule_to_angular('event_registration.move_field')
                },
                'text': {
                    'add': url_rule_to_angular('event_registration.add_text'),
                    'modify': url_rule_to_angular('event_registration.modify_text'),
                    'toggle': url_rule_to_angular('event_registration.toggle_text'),
                    'move': url_rule_to_angular('event_registration.move_text')
                }
            },

            'Timetable': {
                'management': url_rule_to_js('timetable.management'),
                'default_pdf': url_rule_to_js('timetable.export_default_pdf'),
                'pdf': url_rule_to_js('timetable.export_pdf'),
                'reschedule': url_rule_to_js('timetable.reschedule'),
                'breaks': {
                    'add': url_rule_to_js('timetable.add_break')
                },
                'contributions': {
                    'add': url_rule_to_js('timetable.add_contribution'),
                    'notScheduled': url_rule_to_js('timetable.not_scheduled'),
                    'schedule': url_rule_to_js('timetable.schedule'),
                    'protection': url_rule_to_js('contributions.manage_contrib_protection')
                },
                'sessionBlocks': {
                    'add': url_rule_to_js('timetable.add_session_block'),
                    'fit': url_rule_to_js('timetable.fit_session_block')
                },
                'sessions': {
                    'add': url_rule_to_js('timetable.add_session')
                },
                'entries': {
                    'delete': url_rule_to_js('timetable.delete_entry'),
                    'edit': url_rule_to_js('timetable.edit_entry'),
                    'editDatetime': url_rule_to_js('timetable.edit_entry_datetime'),
                    'editTime': url_rule_to_js('timetable.edit_entry_time'),
                    'move': url_rule_to_js('timetable.move_entry'),
                    'shift': url_rule_to_js('timetable.shift_entries'),
                    'swap': url_rule_to_js('timetable.swap_entries'),
                    'info': {
                        'display': url_rule_to_js('timetable.entry_info'),
                        'manage': url_rule_to_js('timetable.entry_info_manage'),
                    },
                }
            },

            'Contributions': {
                'display_contribution': url_rule_to_js('contributions.display_contribution')
            },

            'Sessions': {
                'display_session': url_rule_to_js('sessions.display_session')
            },

            'Categories': {
                'info': url_rule_to_js('categories.info'),
                'infoFrom': url_rule_to_js('categories.info_from'),
                'search': url_rule_to_js('categories.search')
            }
        },

        'Data': {
            'WeekDays': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
            'DefaultLocation': default_location,
            'Locations': location_names
        },

        'Settings': {
            'ExtAuthenticators': ext_auths,
            'RoomBookingModuleActive': config.ENABLE_ROOMBOOKING
        },

        'FileRestrictions': {
            'MaxUploadFilesTotalSize': config.MAX_UPLOAD_FILES_TOTAL_SIZE,
            'MaxUploadFileSize': config.MAX_UPLOAD_FILE_SIZE
        }
    }

    return render_template('assets/vars_globals.js', indico_vars=indico_vars, config=config)
