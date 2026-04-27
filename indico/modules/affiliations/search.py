# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import abc
import dataclasses

from indico.core.db import db
from indico.core.db.sqlalchemy.custom.unaccent import unaccent_match
from indico.core.db.sqlalchemy.searchable import fts_matches
from indico.core.logger import Logger
from indico.modules.users.models.affiliations import Affiliation


logger = Logger.get('affiliations')


def match_search(q, exact=False, prefix=False):
    if exact:
        match_str = f'|||{q}|||'
    elif prefix:
        match_str = f'|||{q}'
    else:
        match_str = q
    return unaccent_match(Affiliation.searchable_names, match_str, exact=False)


def weighted_score(*params):
    return sum(db.cast(param, db.Integer) * weight for param, weight in params)


@dataclasses.dataclass(frozen=True)
class AffiliationSearchMatch:
    score: float
    text: str
    affiliation_id: int


class AffiliationSearch(abc.ABC):
    @abc.abstractmethod
    def match_many(self, texts: list[str], k: int = 1) -> list[list[AffiliationSearchMatch]]:
        raise NotImplementedError

    @abc.abstractmethod
    def match(self, text: str, k: int = 1) -> list[AffiliationSearchMatch]:
        raise NotImplementedError


class StringMatchAffiliationSearch(AffiliationSearch):
    def match(self, text: str, k: int = 1) -> list[AffiliationSearchMatch]:
        score = weighted_score((match_search(text, exact=True), 4), (match_search(text, prefix=True), 2),
                               (match_search(text), 1))
        text_filter = fts_matches(Affiliation.searchable_names, text)
        results = (
            Affiliation.query
            .filter(~Affiliation.is_deleted, text_filter)
            .add_columns(score.label('score'))
            .order_by(
                score.desc(),
                db.func.indico.indico_unaccent(db.func.lower(Affiliation.name)),
            )
            .limit(k)
            .all()
        )
        return [
            AffiliationSearchMatch(
                score=row.score / 14 + 0.5, text=row.Affiliation.name, affiliation_id=row.Affiliation.id
            ) for row in results
        ]

    def match_many(self, texts: list[str], k: int = 1) -> list[list[AffiliationSearchMatch]]:
        return [self.match(text, k) for text in texts]
