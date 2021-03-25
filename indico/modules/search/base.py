from indico.core import signals
from indico.util.enum import IndicoEnum
from indico.util.signals import values_from_signal


def get_search_provider():
    providers = signals.get_search_providers.send()
    return values_from_signal(providers, as_list=True)[0] if len(providers) else None


class SearchTarget(int, IndicoEnum):
    category = 1
    event = 2
    contribution = 3
    attachment = 4


class IndicoSearchProvider:
    RESULTS_PER_PAGE = 10

    def search(self, query, access, object_type=SearchTarget.event, page=1):
        raise NotImplementedError()
