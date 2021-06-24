Indico's version 3.0 introduced a brand new reusable and backend-agnostic search module backed up by the
SQL storage by default. This module can however be decomposed into a single provider,
supporting any external service through a plugin.

Indico provides multiple options for a search service, such as:

- The default SQL based search.
- A performant and feature-rich ElasticSearch-based search service, `Citadel`_ which can be integrated with
  Indico easily using the official `Citadel plugin`_.
- Any external search service, as long as you implement a plugin interface according to the specification below.

.. _Citadel: https://gitlab.cern.ch/webservices/cern-search/cern-search-rest-api
.. _Citadel plugin: https://pypi.org/project/indico-plugin-citadel/
