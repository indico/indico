# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import dataclasses

from indico.core import signals
from indico.util.decorators import classproperty
from indico.util.enum import IndicoIntEnum
from indico.util.signals import values_from_signal


def get_search_provider(only_active=True):
    """Get the search provider to use for a search.

    :param only_active: Whether to check that the provider is active;
                        in case it isn't, the default InternalSearch
                        provider will be used.
    """
    from indico.modules.search.controllers import InternalSearch
    providers = values_from_signal(signals.core.get_search_providers.send(), as_list=True)

    if not providers:
        return InternalSearch
    elif len(providers) == 1:
        provider = providers[0]
        return provider if not only_active or provider.active else InternalSearch
    else:
        providers_str = ', '.join(f'{x.__module__}.{x.__name__}' for x in providers)
        raise RuntimeError(f'Only one search provider can be defined (found: {providers_str})')


class SearchTarget(IndicoIntEnum):
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
    #: The number of results to show per page.
    RESULTS_PER_PAGE = 10

    @classproperty
    @classmethod
    def active(cls):
        """Whether this provider can be used for searching.

        Providers that require any particular config should return
        ``False`` here so users get the internal search until the
        provider is fully configured.
        """
        return True

    def search(self, query, user=None, page=None, object_types=(), *, admin_override_enabled=False,
               **params):
        """Search using a custom service across multiple targets.

        :param query: Keyword based query string
        :param user: The user performing the search (for access checks)
        :param page: The result page to show
        :param object_types: A filter for a specific `SearchTarget`
        :param admin_override_enabled: Whether to ignore access restrictions
        :param params: Any additional search params such as filters

        :return: a dict with the `ResultSchema` structure
        """
        raise NotImplementedError

    def get_placeholders(self):
        """
        Retrieve the list of search shortcuts that will be shown to users
        when typing a search query.

        :return: a list of :class:`SearchOption` instances
        """
        return []

    def get_sort_options(self):
        """
        Retrieve the list of search sortable options.

        :return: a list of :class:`SearchOption` instances
        """
        return []
