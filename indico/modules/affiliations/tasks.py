# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import datetime
import typing

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.logger import Logger
from indico.modules.affiliations.matching import AFFILIATION_BACKREF_CLASSES, affiliation_mappings_cache
from indico.modules.affiliations.search import StringMatchAffiliationSearch


if typing.TYPE_CHECKING:
    from indico.modules.affiliations.search import AffiliationSearch, AffiliationSearchMatch


logger = Logger.get('affiliations')


@celery.periodic_task(name='generate_affiliation_matches', run_every=crontab(minute='0', hour='3'), ignore_result=False)
def generate_affiliation_matches(
    search_engine: 'AffiliationSearch | None' = None, batch_size: int = 100, cache: bool = True,
) -> dict[str, 'AffiliationSearchMatch']:
    """
    This task goes through each database object that includes a "free-text" affiliation, gathers each unique string,
    and tries to find a matching affiliation for it, storing the results in the affiliation mappings cache.
    """
    logger.info('starting matching')
    search_engine: AffiliationSearch = (
        StringMatchAffiliationSearch() if search_engine is None else search_engine
    )
    affiliations: set[str] = set()
    for cls in AFFILIATION_BACKREF_CLASSES:
        filters = [
            cls.affiliation.is_not(None), cls.affiliation != ''  # noqa: PLC1901
        ]
        if hasattr(cls, 'is_deleted'):
            filters.append(cls.is_deleted.is_(False))

        affiliations = affiliations.union(
            str(cwa.affiliation)
            for cwa in cls.query.filter(*filters).all()
        )
    affiliations_list = list(affiliations)

    matches: dict[str, AffiliationSearchMatch] = {}
    for i in range(0, len(affiliations_list), batch_size):
        segment = affiliations_list[i:i+batch_size]
        for original, results in zip(segment, search_engine.match_many(segment), strict=True):
            if len(results) == 0:
                continue
            matches[original] = results[0]

    if cache:
        affiliation_mappings_cache.set_many({
            'date': datetime.datetime.now(),
            'mapping': matches
        })

    return matches
