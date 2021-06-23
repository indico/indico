Internal Search
===============

The Internal Search is a default SQL based engine implementation, created to support the most basic queries.
While not as fast and less feature rich (no filters or aggregations) compared to specialized search engines,
this search engine provides a decent option for smaller Indico instances which may not want to spend
additional time on deploying a separate service just for search.

It supports the two types of records from a total of six targets:

- Events
- Categories
- Contributions
- Attachments
- Notes

.. note::
    The Internal Search only supports text-based search on titles, description and notes content.

External Search Service
=======================

Indico provides several powerful features for aggregation and filtering when combined with an external
search service supporting them, such as `Citadel`_.

Aggregations
------------

Aggregations, as seen in `Elastic Search <https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations.html>`_,
provide a way to combine information in groups according to a certain metric, such as a field value, sum or average.

.. image:: ../images/search_features_aggregation.png

Indico supports any bucket or metric group, composed of a key, count and filter key:

.. autoclass:: indico.modules.search.result_schemas.AggregationSchema()
    :members:

.. autoclass:: indico.modules.search.result_schemas.BucketSchema()
    :members:

Filters
-------

Filters act combined upon a certain aggregation on structured data. Consider the following bucket group
composed of a single affiliation:

.. code-block:: json

    {
        "affiliation": {
            "label": "Affiliation",
            "buckets": {
                "key": "CERN",
                "count": 5,
                "filter": "cern"
            }
        }
    }

The combination of `key` and `filter` from :class:`AggregationSchema` can be used as a way to define a
human-readable label to an attribute. A corresponding filter acting upon the same key in the example above
would be ``affiliation=cern``.

.. todo::
    Remove unused get_filters method

Placeholders
------------

Placeholders are a special type of filters specifically designed to be part of the user-facing text based search query.
Examples of valid placeholders would be: `affiliation:CERN` or `person:"John Doe"`.

.. image:: ../images/search_features_placeholders.png

Indico expects to receive a list of valid placeholders through ``get_placeholders()`` where each one will be
merely hinted to the user while doing a text based search.

.. autoclass:: indico.modules.search.base.IndicoSearchProvider
    :members: get_placeholders

.. _Citadel: https://gitlab.cern.ch/webservices/cern-search/cern-search-rest-api
