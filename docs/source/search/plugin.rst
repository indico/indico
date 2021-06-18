API Reference
*************

The ``IndicoSearchProvider`` interface allows an abstract service to integrate with Indico's search module.

.. automodule:: indico.modules.search.base
    :members:
    :undoc-members:

Models
++++++

.. automodule:: indico.modules.search.result_schemas

    .. autoclass:: ResultSchemaBase()
        :members:

    .. autoclass:: EventResultSchema()
        :members:
        :show-inheritance:

    .. autoclass:: ContributionResultSchema()
        :members:
        :show-inheritance:

    .. autoclass:: SubContributionResultSchema()
        :members:
        :show-inheritance:

    .. autoclass:: AttachmentResultSchema()
        :members:
        :show-inheritance:

    .. autoclass:: EventNoteResultSchema()
        :members:
        :show-inheritance:

    .. autoclass:: PersonSchema()
        :members:
        :show-inheritance:

    .. autoclass:: LocationResultSchema()
        :members:
        :show-inheritance:

    .. autoclass:: HighlightSchema()
        :members:
        :show-inheritance:
