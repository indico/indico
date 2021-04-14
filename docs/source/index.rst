Welcome to Indico's documentation!
==================================


.. raw:: html
    :file: _static/github_star.html

.. image:: images/indico.png
    :width: 300 px
    :align: center

.. epigraph:: *The effortless open source tool for event organization, archival and collaboration.*

|build-status| |license| |pypi-ver| |cern-foss|

Welcome to Indico's documentation. This documentation is split into several parts, from `installing Indico <installation/>`_ to developing `Indico plugins <plugins>`_.
To dive into the internals of Indico, check out the `API documentation <api>`_. Read more about Indico in our `official website <https://getindico.io>`_.


Installation
++++++++++++

.. include:: installation/_intro.rst

.. toctree::
    :maxdepth: 2

    installation/index.rst


Configuration
+++++++++++++

.. include:: config/_intro.rst

.. toctree::
    :maxdepth: 2

    config/index.rst


Building
++++++++

.. toctree::
    :maxdepth: 2

    building/index.rst


Plugins
+++++++

.. include:: plugins/_intro.rst

.. toctree::
    :maxdepth: 2

    Indico plugins <plugins/index.rst>


HTTP API
++++++++

.. include:: http_api/_intro.rst

.. toctree::
    :maxdepth: 2

    HTTP API <http_api/index.rst>


API reference
+++++++++++++

.. include:: api/_intro.rst

.. toctree::
    :maxdepth: 2

    api/index.rst


What's New
++++++++++

.. toctree::
    :maxdepth: 2

    changelog.rst


Indices and tables
++++++++++++++++++

* :ref:`genindex`
* :ref:`modindex`


Contact
+++++++

.. toctree::
    :maxdepth: 2

    contact/index.rst


.. |build-status| image:: https://github.com/indico/indico/workflows/CI/badge.svg
                   :alt: CI Build Status
                   :target: https://github.com/indico/indico/actions
.. |pypi-ver| image:: https://img.shields.io/pypi/v/indico.png
                   :alt: Available on PyPI
                   :target: https://pypi.python.org/pypi/indico/
.. |license| image:: https://img.shields.io/github/license/indico/indico.png
                   :alt: License
                   :target: https://github.com/indico/indico/blob/master/LICENSE
.. |cern-foss| image:: https://img.shields.io/badge/CERN-Open%20Source-%232980b9.svg
                   :alt: Made at CERN!
                   :target: https://home.cern
