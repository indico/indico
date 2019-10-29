Paper
=====

.. todo::
    Docstrings (module, models, operations, utilities, settings)

.. automodule:: indico.modules.events.papers


Models
++++++

.. indico_uml::

    User "1" --* PaperRevision : submitter
    User "1" --* PaperRevision : judge
    PaperRevision *-- "1" Contribution
    PaperRevision "1" --* PaperFile
    PaperReview *-- "1" PaperRevision
    PaperReviewComment *-- "1" PaperRevision
    PaperReviewComment *-- "1" User : creator
    User "1" --* PaperReview : reviewer
    PaperReview "1" --* PaperReviewRating
    PaperReviewRating  *-- "1" PaperReviewQuestion
    Contribution *--* User : judge
    Contribution *--* User : content_reviewer
    Contribution *--* User : layout_reviewer

.. automodule:: indico.modules.events.papers.models.call_for_papers
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.papers.models.comments
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.papers.models.competences
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.papers.models.files
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.papers.models.papers
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.papers.models.review_questions
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.papers.models.review_ratings
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.papers.models.reviews
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.papers.models.revisions
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.papers.models.templates
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.papers.models.user_contributions
    :members:
    :undoc-members:


Operations
++++++++++

.. automodule:: indico.modules.events.papers.operations
    :members:
    :undoc-members:


Utilities
+++++++++

.. automodule:: indico.modules.events.papers.util
    :members:
    :undoc-members:


Settings
++++++++

.. automodule:: indico.modules.events.settings
    :members:
    :undoc-members:
