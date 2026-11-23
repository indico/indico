# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import fields

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.custom.unaccent import unaccent_match
from indico.core.db.sqlalchemy.searchable import fts_matches
from indico.modules.users.models.affiliations import Affiliation
from indico.util.caching import memoize_redis
from indico.util.countries import get_countries_regex, get_country_reverse
from indico.util.signals import values_from_signal
from indico.web.args import use_kwargs


def _match_search(q, exact=False, prefix=False):
    if exact:
        match_str = f'|||{q}|||'
    elif prefix:
        match_str = f'|||{q}'
    else:
        match_str = q
    return unaccent_match(Affiliation.searchable_names, match_str, exact=False)


def _weighted_score(*params):
    return sum(db.cast(param, db.Integer) * weight for param, weight in params)


def _search_affiliations(q, *, filters=()):
    exact_match = _match_search(q, exact=True)
    score = _weighted_score((exact_match, 150), (_match_search(q, prefix=True), 60), (_match_search(q), 20))
    countries = set(get_countries_regex().findall(q))
    for country in countries:
        q = q.replace(country, '')
        if (country_code := get_country_reverse(country, case_sensitive=False)):
            score += _weighted_score((Affiliation.country_code.ilike(country_code), 50))
    for word in q.split():
        score += _weighted_score((unaccent_match(Affiliation.city, word, exact=False), 20),
                                    (_match_search(word, exact=True), 40),
                                    (_match_search(word, prefix=True), 30),
                                    (_match_search(word), 10),
                                    (Affiliation.popularity, 1))
    q_filter = fts_matches(Affiliation.searchable_names, q)
    return (
        Affiliation.query
        .filter(~Affiliation.is_deleted, q_filter, *filters)
        .order_by(
            score.desc(),
            db.func.indico.indico_unaccent(db.func.lower(Affiliation.name)),
        )
        .limit(20)
        .all()
    )


@memoize_redis(3600, versioned=True)
def _cached_search_affiliations(q):
    return _search_affiliations(q)


def search_affiliations(q, *, filters=()):
    if filters:
        return _search_affiliations(q, filters=filters)
    return _cached_search_affiliations(q)


search_affiliations.clear_cached = _cached_search_affiliations.clear_cached
search_affiliations.is_cached = _cached_search_affiliations.is_cached
search_affiliations.bump_version = _cached_search_affiliations.bump_version


class SearchAffiliationsMixin:
    @use_kwargs({'q': fields.String(load_default='')}, location='query')
    def _process(self, q):
        from indico.modules.users.schemas import AffiliationSchema
        filters = values_from_signal(signals.affiliations.get_affiliation_filters.send(self, context=self.context),
                                     as_list=True, multi_value_types=list)
        res = search_affiliations(q, filters=filters)
        basic_fields = ('id', 'name', 'code', 'street', 'postcode', 'city', 'country_code', 'meta')
        return AffiliationSchema(many=True, only=basic_fields).jsonify(res)

    @property
    def context(self):
        """The context dict passed to affiliation filter signal receivers.

        The dict should contain any objects relevant to the current search,
        keyed by descriptive names.
        """
        raise NotImplementedError
