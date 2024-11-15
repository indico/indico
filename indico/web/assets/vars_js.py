# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
from urllib.parse import urlsplit

from flask import current_app, json, render_template, session

from indico.core.auth import multipass
from indico.core.config import config
from indico.core.plugins import plugin_engine
from indico.modules.auth.util import url_for_login
from indico.modules.users.schemas import AffiliationSchema
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
    all_locales = get_all_locales()
    if locale_name not in all_locales:
        locale_name = config.DEFAULT_LOCALE if config.DEFAULT_LOCALE in all_locales else 'en_GB'

    root_path = os.path.join(current_app.root_path, 'translations')
    i18n_data = get_locale_data(root_path, locale_name, 'indico', react=react)
    if not i18n_data:
        # Dummy data, not having the indico domain would cause lots of failures
        i18n_data = {'indico': {'': {'domain': 'indico',
                                     'lang': locale_name}}}

    for pid, plugin in plugin_engine.get_active_plugins().items():
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
            'title': user._title.name,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'fullName': user.full_name,
            'email': user.email,
            'favoriteUsers': {u.id: serialize_user(u) for u in user.favorite_users},
            'language': session.lang,
            'avatarURL': user.avatar_url,
            'isAdmin': user.is_admin,
            'affiliation': user.affiliation,
            'affiliationId': user.affiliation_id,
            'affiliationMeta': AffiliationSchema().dump(user.affiliation_link) if user.affiliation_link else None,
            'address': user.address,
            'phone': user.phone,
            'type': user.principal_type.name,  # always 'user'
            'mastodonServerURL': user.settings.get('mastodon_server_url') or '',
            'mastodonServerName': user.settings.get('mastodon_server_name') or '',
        }
    return render_template('assets/vars_user.js', user_vars=user_vars, user=user)


def generate_global_file():
    ext_auths = [{
        'name': auth.name,
        'title': auth.title,
        'supports_groups': auth.supports_groups
    } for auth in multipass.identity_providers.values() if auth.supports_search]

    indico_vars = {
        'ExperimentalEditingService': config.EXPERIMENTAL_EDITING_SERVICE,
        'Urls': {
            'Base': config.BASE_URL,
            'BasePath': urlsplit(config.BASE_URL).path.rstrip('/'),
            'ExportAPIBase': url_for('api.httpapi', prefix='export'),
            'APIBase': url_for('api.httpapi', prefix='api'),

            'ImagesBase': config.IMAGES_BASE_URL,

            'Login': url_for_login(),

            'AttachmentManager': url_rule_to_js('attachments.management'),
            'ManagementAttachmentInfoColumn': url_rule_to_js('attachments.management_info_column'),

            'FontSassBundle': current_app.manifest['fonts.css']._paths,

            'EventCreation': url_rule_to_js('events.create'),
            'PermissionsDialog': url_rule_to_js('event_management.permissions_dialog'),

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
