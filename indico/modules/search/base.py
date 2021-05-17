# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import dataclasses

from indico.core import signals
from indico.util.enum import IndicoEnum
from indico.util.signals import values_from_signal


def get_search_provider():
    from indico.modules.search.controllers import InternalSearch
    providers = values_from_signal(signals.get_search_providers.send(), as_list=True)

    if not providers:
        return InternalSearch
    elif len(providers) == 1:
        return providers[0]
    else:
        providers_str = ', '.join(f'{x.__module__}.{x.__name__}' for x in providers)
        raise RuntimeError(f'Only one search provider can be defined (found: {providers_str})')


class SearchTarget(int, IndicoEnum):
    category = 1
    event = 2
    contribution = 3
    subcontribution = 4
    event_note = 5
    attachment = 6


@dataclasses.dataclass
class SearchOption:
    key: str
    label: str


@dataclasses.dataclass
class SearchOptions:
    placeholders: list[SearchOption]
    sort_options: list[SearchOption]

    def dump(self):
        return dataclasses.asdict(self)


class IndicoSearchProvider:
    RESULTS_PER_PAGE = 10

    def search(self, query, access, page=None, object_types=(), **params):
        """Search using a custom service across multiple targets.

        :param query: Keyword based query string
        :param access: The requester access control list
        :param page: The target page
        :param object_types: A filter for a specific `SearchTarget`
        :param params: Any additional search params such as filters

        :return: a dict with the `ResultSchema` structure
        """
        raise NotImplementedError()

    def get_placeholders(self):
        """
        Retrieve the list of search shortcuts that will be shown to users
        when typing a search query.

        :return: a list of `SearchFilter` instances
        """
        return []

    def get_filters(self):
        """
        Retrieve the list of search filters available as aggregations to
        each query result.

        :return: a list of `SearchFilter` instances
        """
        return []

    def get_sort_options(self):
        """
        Retrieve the list of search sortable options.

        :return: a list of `SearchFilter` instances
        """
        return []
