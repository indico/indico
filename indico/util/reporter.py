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

from indico.modules.events.models.report_links import ReportLink


class ReporterBase(object):
    """Serves as a base class for classes performing actions on reports."""

    def __init__(self, event, entry_parent):
        self.report_event = event
        self.entry_parent = entry_parent
        self.report_link_type = ''
        self.default_report_config = {}
        self.filterable_items = None

    def get_config_session_key(self):
        """Compose the unique configuration ID.

        This ID will be used as a key to set the report's configuration to the
        session.
        """
        return '{}_config_{}'.format(self.report_link_type, self.entry_parent.id)

    def get_config(self):
        """Load the report's configuration from the DB and return it."""
        session_key = self.get_config_session_key()
        report_config_uuid = request.args.get('config')
        if report_config_uuid:
            configuration = ReportLink.load(self.report_event, self.report_link_type, report_config_uuid)
            if configuration and configuration['entry_parent_id'] == self.entry_parent.id:
                session[session_key] = configuration['data']
        return session.get(session_key, self.default_report_config)

    def build_query(self):
        """Return the query of the report's entries.

        The query should not take into account the user's filtering
        configuration, for example:
            return event.contributions.filter_by(is_deleted=False)
        """
        raise NotImplementedError

    def filter_report_entries(self):
        """Apply user's filters to query and return it."""
        raise NotImplementedError

    def get_filters_from_request(self):
        """Get the new filters after the filter form is submitted."""
        filters = deepcopy(self.default_report_config['filters'])
        for item_id, item in self.filterable_items.iteritems():
            if item.get('filter_choices'):
                options = request.form.getlist('field_{}'.format(item_id))
                if options:
                    filters['items'][item_id] = options
        return filters

    def get_report_url(*args, **kwargs):
        """Return the URL of the report management page."""
        raise NotImplementedError

    def has_config(self):
        return 'config' in request.args
