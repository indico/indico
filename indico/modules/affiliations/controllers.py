# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, session

from indico.core import signals
from indico.core.db import db
from indico.modules.admin.controllers.base import RHAdminBase
from indico.modules.affiliations.schemas import AffiliationArgs
from indico.modules.affiliations.util import SearchAffiliationsMixin, search_affiliations
from indico.modules.affiliations.views import WPAffiliationsDashboard
from indico.modules.logs.models.entries import AppLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.schemas import AffiliationSchema
from indico.util.countries import get_countries
from indico.util.marshmallow import ModelField
from indico.web.args import use_args, use_kwargs
from indico.web.rh import RH


class RHAffiliationsDashboard(RHAdminBase):
    """Entry point for the Affiliations admin dashboard."""

    def _process(self):
        return WPAffiliationsDashboard.render_template('affiliations_dashboard.html', 'affiliations')


class RHAffiliationsAPI(RHAdminBase):
    """List/create affiliations via the admin API."""

    def _process_GET(self):
        affiliations = (Affiliation.query
                        .filter(~Affiliation.is_deleted)
                        .order_by(db.func.indico.indico_unaccent(db.func.lower(Affiliation.name)))
                        .all())
        return AffiliationSchema(many=True).jsonify(affiliations)

    @use_args(AffiliationArgs)
    def _process_POST(self, data):
        affiliation = Affiliation()
        affiliation.populate_from_dict(data)
        db.session.add(affiliation)
        db.session.flush()
        signals.affiliations.affiliation_created.send(affiliation)
        affiliation.log(AppLogRealm.admin, LogKind.positive, 'Affiliation',
                         f'Affiliation "{affiliation.name}" created', session.user)
        search_affiliations.bump_version()
        return AffiliationSchema().jsonify(affiliation), 201


class RHAffiliationAPI(RHAdminBase):
    """CRUD operations on a single affiliation."""

    @use_kwargs({
        'affiliation': ModelField(Affiliation, filter_deleted=True, required=True, data_key='affiliation_id')
    }, location='view_args')
    def _process_args(self, affiliation):
        RHAdminBase._process_args(self)
        self.affiliation = affiliation

    def _process_GET(self):
        return AffiliationSchema().jsonify(self.affiliation)

    @use_args(AffiliationArgs, partial=True)
    def _process_PATCH(self, data):
        signals.affiliations.affiliation_updated.send(self.affiliation, payload=data)
        if not data:
            return '', 204
        changes = self.affiliation.populate_from_dict(data)
        db.session.flush()
        log_fields = {
            'name': 'Name',
            'alt_names': 'Alternative names',
            'street': 'Street',
            'postcode': 'Postcode',
            'city': 'City',
            'country_code': 'Country',
            'meta': 'Metadata',
        }
        self.affiliation.log(AppLogRealm.admin, LogKind.change, 'Affiliation',
                                f'Affiliation "{self.affiliation.name}" modified', session.user,
                                data={'Changes': make_diff_log(changes, log_fields)})
        search_affiliations.bump_version()
        return '', 204

    def _process_DELETE(self):
        self.affiliation.is_deleted = True
        db.session.flush()
        self.affiliation.log(AppLogRealm.admin, LogKind.negative, 'Affiliation',
                             f'Affiliation "{self.affiliation.name}" deleted', session.user)
        search_affiliations.bump_version()
        return '', 204


class RHCountries(RHAdminBase):
    """Return the available countries for affiliation forms."""

    def _process(self):
        return jsonify(list(get_countries().items()))


class RHSearchAffiliations(SearchAffiliationsMixin, RH):
    @property
    def context(self):
        return {}
