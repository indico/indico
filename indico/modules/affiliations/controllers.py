# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from uuid import UUID

from flask import jsonify, session
from marshmallow import fields

from indico.core import signals
from indico.core.celery import AsyncResult
from indico.core.db import db
from indico.modules.admin.controllers.base import RHAdminBase
from indico.modules.affiliations.matching import (get_affiliation_mappings, get_affiliation_mappings_date,
                                                  get_affiliation_matches_from_mapping, get_class_from_entity_type)
from indico.modules.affiliations.schemas import AffiliationArgs
from indico.modules.affiliations.tasks import generate_affiliation_matches
from indico.modules.affiliations.util import SearchAffiliationsMixin, search_affiliations
from indico.modules.affiliations.views import WPAffiliations
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
        return WPAffiliations.render_template('affiliations_dashboard.html', 'affiliations')


class RHAffiliationsMapping(RHAdminBase):
    """Entry point for the Affiliations Mapping admin panel."""

    def _process(self):
        return WPAffiliations.render_template('affiliations_mapping.html', 'affiliations')


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


class RHAffiliationsMappingAPI(RHAdminBase):
    def _process_GET(self):
        mapping = get_affiliation_mappings()
        if mapping is None:
            task = generate_affiliation_matches.delay()
            return jsonify(task=task.id)

        matches = get_affiliation_matches_from_mapping(mapping)

        return jsonify({
            'date': get_affiliation_mappings_date(),
            'mapping': [{
                'original_text': match_result.original_text,
                'match_text': match_result.match_text,
                'score': match_result.score,
                'original_id': match_result.original_id,
                'original_entity_type': match_result.original_entity_type,
                'affiliation_id': match_result.affiliation_id,
                'display': match_result.display,
            } for match_result in matches],
        })

    def _process_POST(self):
        task = generate_affiliation_matches.delay()
        return jsonify(task=task.id)


class RHAffiliationsMappingStatusAPI(RHAdminBase):
    @use_kwargs({'task_id': fields.UUID(required=True)}, location='view_args')
    def _process(self, task_id: UUID):
        task = AsyncResult(str(task_id))
        if task.state == 'FAILURE':
            exception = task.get()
            task.forget()
            assert isinstance(exception, Exception)
            raise exception
        return {'status': task.state}


class RHAffiliationsMappingApplyAPI(RHAdminBase):
    @use_kwargs({'original_ids': fields.List(fields.Integer(), required=True)})
    def _process(self, original_ids: list[int]):
        mapping = get_affiliation_mappings()
        if mapping is None:
            # Maybe return error instead of exception?
            raise Exception('No mapping exists')

        approved_matches = [
            match for match in get_affiliation_matches_from_mapping(mapping)
            if match.original_id in original_ids
        ]

        # FIXME: bulk update?
        for match in approved_matches:
            entry_class = get_class_from_entity_type(match.original_entity_type)
            db.session.query(entry_class).filter_by(id=match.original_id).update(
                {'affiliation_id': match.affiliation_id}
            )

        return 'success'


class RHCountries(RHAdminBase):
    """Return the available countries for affiliation forms."""

    def _process(self):
        return jsonify(list(get_countries().items()))


class RHSearchAffiliations(SearchAffiliationsMixin, RH):
    @property
    def context(self):
        return {}
