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
from indico.web.flask.util import url_for


class ReporterBase(object):
    """Base class for classes performing actions on reports.

    :param event: The associated `Event`
    :param entry_parent: The parent of the entries of the report. If it's None,
                         the parent is assumed to be the event itself.
    """

    #: The endpoint to the report management page
    endpoint = ''

    def __init__(self, event, entry_parent=None):
        self.report_event = event
        self.entry_parent = entry_parent if entry_parent else event
        self.report_link_type = ''
        self.default_report_config = {}
        self.filterable_items = None
        self.must_renew_config = 'config' in request.args

    def _get_config_session_key(self):
        """Compose the unique configuration ID.

        This ID will be used as a key to set the report's configuration to the
        session.
        """
        return '{}_config_{}'.format(self.report_link_type, self.entry_parent.id)

    def get_config(self):
        """Load the report's configuration from the DB and return it."""
        session_key = self._get_config_session_key()
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

    def get_report_url(self, uuid=None):
        """Return the URL of the report management page."""
        kwargs = {'config': uuid, '_external': True} if uuid else {}
        return url_for(self.endpoint, self.entry_parent, **kwargs)

    def generate_static_url(self):
        """Return a URL with a uuid referring to the report's configuration."""
        session_key = self._get_config_session_key()
        configuration = {
            'entry_parent_id': self.entry_parent.id,
            'data': session.get(session_key)
        }
        if configuration['data']:
            link = ReportLink.create(self.report_event, self.report_link_type, configuration)
            return self.get_report_url(uuid=link.uuid)
        return self.get_report_url()

    def store_filters(self):
        """Load the filters from the request and store them in the session."""
        filters = self.get_filters_from_request()
        session_key = self._get_config_session_key()
        self.report_config = session.setdefault(session_key, {})
        self.report_config['filters'] = filters
        session.modified = True
