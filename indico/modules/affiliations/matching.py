# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import dataclasses
import typing

from indico.core.cache import make_scoped_cache
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.models.persons import EventPerson, EventPersonLink
from indico.modules.events.sessions.models.persons import SessionBlockPersonLink
from indico.modules.users.models.users import User


if typing.TYPE_CHECKING:
    from datetime import datetime

    from indico.modules.affiliations.search import AffiliationSearchMatch


affiliation_mappings_cache = make_scoped_cache('affiliation-mapping')

AFFILIATION_BACKREF_CLASSES = [
    AbstractPersonLink,
    ContributionPersonLink,
    EventPersonLink,
    EventPerson,
    SessionBlockPersonLink,
    SubContributionPersonLink,
    User,
]

type AffiliationEntityType = typing.Literal[
    'AbstractPersonLink',
    'ContributionPersonLink',
    'EventPersonLink',
    'EventPerson',
    'SessionBlockPersonLink',
    'SubContributionPersonLink',
    'User',
]


@dataclasses.dataclass
class AffiliationMatch:
    original_text: str
    match_text: str
    score: float
    original_id: int
    original_entity_type: AffiliationEntityType
    affiliation_id: int


def get_affiliation_entity_type(entity: object) -> AffiliationEntityType:
    match entity:
        case AbstractPersonLink():
            return 'AbstractPersonLink'
        case ContributionPersonLink():
            return 'ContributionPersonLink'
        case EventPersonLink():
            return 'EventPersonLink'
        case EventPerson():
            return 'EventPerson'
        case SessionBlockPersonLink():
            return 'SessionBlockPersonLink'
        case SubContributionPersonLink():
            return 'SubContributionPersonLink'
        case User():
            return 'User'
    raise ValueError(f'type {type(entity)} is not a valid affiliation entity type')


def get_affiliation_mappings() -> dict[str, 'AffiliationSearchMatch'] | None:
    return affiliation_mappings_cache.get('mapping')


def get_affiliation_mappings_date() -> 'datetime':
    return affiliation_mappings_cache.get('date')


def get_affiliation_matches_from_mapping(
    mapping: dict[str, 'AffiliationSearchMatch']
) -> list[AffiliationMatch]:
    matched_affiliation_texts = [search_match.text for search_match in mapping.values()]

    affiliations = []
    for cls in AFFILIATION_BACKREF_CLASSES:
        affiliations.extend(
            cwa for cwa in cls.query.filter(
                cls.affiliation.is_not(None), cls.affiliation.in_(matched_affiliation_texts)
            ).all()
        )

    return [
        AffiliationMatch(
            score=mapping[affiliation.affiliation].score,
            match_text=mapping[affiliation.affiliation].text,
            affiliation_id=mapping[affiliation.affiliation].affiliation_id,
            original_text=affiliation.affiliation,
            original_id=affiliation.id,
            original_entity_type=get_affiliation_entity_type(affiliation),
        )
        for affiliation in affiliations
    ]
