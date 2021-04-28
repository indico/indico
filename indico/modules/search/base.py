# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core import signals
from indico.modules.search.controllers import InternalSearch
from indico.util.enum import IndicoEnum
from indico.util.signals import values_from_signal


def get_search_provider():
    providers = signals.get_search_providers.send()
    return values_from_signal(providers, as_list=True)[0] if len(providers) else InternalSearch


class SearchTarget(int, IndicoEnum):
    category = 1
    event = 2
    contribution = 3
    subcontribution = 4
    event_note = 5
    attachment = 6


class IndicoSearchProvider:
    RESULTS_PER_PAGE = 10

    def search(self, query, access, page=1, object_types=(), **params):
        """Search using a custom service across multiple targets.

        :param query: Keyword based query string
        :param access: The requester access control list
        :param page: The target page
        :param object_types: A filter for a specific `SearchTarget`
        :param params: Any additional search params such as filters
        """
        raise NotImplementedError()
