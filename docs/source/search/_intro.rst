Indico’s version 3.0 introduced a brand new reusable and agnostic search module
backed up by your SQL storage by default. This module can however be decomposed
into multiple providers, supporting any external service through a plugin.

Indico provides multiple options for a search service, such as:

- The default SQL based search.
- A performant and feature-rich elastic search based search service, `Citadel`_
  which can be integrated with Indico out-of-the-box thanks
  to its corresponding plugin developed in-house.
- Any external search service, as long as you implement a plugin interface
  according to the specification below.

.. _Citadel: https://gitlab.cern.ch/webservices/cern-search/cern-search-rest-api
