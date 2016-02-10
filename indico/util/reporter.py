# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from copy import deepcopy

from flask import session, request


class ReporterBase(object):
    """Serves as a base class for classes performing actions on reports."""

    #: A unique ID for the report
    REPORT_ID = ''
    #: Dict containing the default visible columns and filtering options
    DEFAULT_REPORT_CONFIG = {}
    #: OrderedDict containing the filterable columns of the report
    FILTERABLE_ITEMS = None
    cache = None

    @classmethod
    def get_config_session_key(cls, entry_parent_id):
        """Compose the unique configuration ID.

        This ID will be used as a key to set the report's configuration to the
        session.

        :param entry_parent_id: The ID of the parent of the report's entries
        """
        return '{}_config_{}'.format(cls.REPORT_ID, entry_parent_id)

    @classmethod
    def get_config(cls, entry_parent_id):
        """Get the report's configuration from the session and return it.

        :param entry_parent_id: The ID of the parent of the report's entries
        """
        session_key = cls.get_config_session_key(entry_parent_id)
        report_config_uuid = request.args.get('config')
        if report_config_uuid:
            configuration = cls.cache.get(report_config_uuid)
            if configuration and configuration['entry_parent_id'] == entry_parent_id:
                session[session_key] = configuration['data']
        return session.get(session_key, cls.DEFAULT_REPORT_CONFIG)

    @classmethod
    def build_query(cls):
        """Return the query of the report's entries.

        The query should not take into account the user's filtering
        configuration, for example:
            return event.contributions.filter_by(is_deleted=False)
        """
        raise NotImplementedError

    @classmethod
    def filter_report_entries(cls):
        """Apply user's filters to query and return it."""
        raise NotImplementedError

    @classmethod
    def get_filters_from_request(cls):
        """Get the new filters after the filter form is submitted."""
        filters = deepcopy(cls.DEFAULT_REPORT_CONFIG['filters'])
        for item_id, item in cls.FILTERABLE_ITEMS.iteritems():
            if item.get('filter_choices'):
                options = request.form.getlist('field_{}'.format(item_id))
                if options:
                    filters['items'][item_id] = options
        return filters
