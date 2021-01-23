# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os

from flask import current_app, json, render_template, session
from werkzeug.urls import url_parse

from indico.core.auth import multipass
from indico.core.config import config
from indico.core.plugins import plugin_engine
from indico.modules.auth.util import url_for_login
from indico.modules.events.registration.util import url_rule_to_angular
from indico.modules.users.util import serialize_user
from indico.util.i18n import get_all_locales, po_to_json
from indico.web.flask.util import url_for, url_rule_to_js


def get_locale_data(path, name, domain, react=False):
    if react:
        json_file = os.path.join(path, name, 'LC_MESSAGES', 'messages-react.json')
        if not os.access(json_file, os.R_OK):
            return {}
        with open(json_file) as f:
            rv = json.load(f)
        rv['messages'][''] = {
            'domain': domain,
            'lang': name,
            'plural_forms': rv['messages']['']['plural_forms'],
        }
        return {domain: rv['messages']}
    else:
        po_file = os.path.join(path, name, 'LC_MESSAGES', 'messages-js.po')
        return po_to_json(po_file, domain=domain, locale=name) if os.access(po_file, os.R_OK) else {}


def generate_i18n_file(locale_name, react=False):
    if locale_name not in get_all_locales():
        return None
    root_path = os.path.join(current_app.root_path, 'translations')
    i18n_data = get_locale_data(root_path, locale_name, 'indico', react=react)
    if not i18n_data:
        # Dummy data, not having the indico domain would cause lots of failures
        i18n_data = {'indico': {'': {'domain': 'indico',
                                     'lang': locale_name}}}

    for pid, plugin in plugin_engine.get_active_plugins().iteritems():
        data = {}
        if plugin.translation_path:
            data = get_locale_data(plugin.translation_path, locale_name, pid, react=react)
        if not data:
            # Dummy entry so we can still load the domain
            data = {pid: {'': {'domain': pid,
                               'lang': locale_name}}}
        i18n_data.update(data)
    return json.dumps(i18n_data)


def generate_user_file(user=None):
    user = user or session.user
    if user is None:
        user_vars = {}
    else:
        user_vars = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'favorite_users': {u.id: serialize_user(u) for u in user.favorite_users},
            'language': session.lang,
            'avatar_bg_color': user.avatar_bg_color,
            'is_admin': user.is_admin,
            'full_name': user.full_name
        }
    return render_template('assets/vars_user.js', user_vars=user_vars, user=user)


def generate_global_file():
    ext_auths = [{
        'name': auth.name,
        'title': auth.title,
        'supports_groups': auth.supports_groups
    } for auth in multipass.identity_providers.itervalues() if auth.supports_search]

    indico_vars = {
        'ExperimentalEditingService': config.EXPERIMENTAL_EDITING_SERVICE,
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

            'APIKeyCreate': url_for('api.key_create'),
            'APIKeyTogglePersistent': url_for('api.key_toggle_persistent'),
            'FontSassBundle': current_app.manifest['fonts.css']._paths,

            'EventCreation': url_rule_to_js('events.create'),
            'PermissionsDialog': url_rule_to_js('event_management.permissions_dialog'),

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
                    'protection': url_rule_to_js('contributions.manage_contrib_protection'),
                    'clone': url_rule_to_js('timetable.clone_contribution')
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
                'display': url_rule_to_js('categories.display'),
                'info': url_rule_to_js('categories.info'),
                'infoFrom': url_rule_to_js('categories.info_from'),
                'search': url_rule_to_js('categories.search')
            }
        },

        'Data': {
            'WeekDays': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        },

        'Settings': {
            'ExtAuthenticators': ext_auths,
        },

        'FileRestrictions': {
            'MaxUploadFilesTotalSize': config.MAX_UPLOAD_FILES_TOTAL_SIZE,
            'MaxUploadFileSize': config.MAX_UPLOAD_FILE_SIZE
        }
    }

    return render_template('assets/vars_globals.js', indico_vars=indico_vars, config=config)
