Welcome to Indico's documentation!
==================================


.. raw:: html
    :file: _static/github_star.html

.. image:: images/indico.png
    :width: 300 px
    :align: center

.. epigraph:: *The effortless open source tool for event organization, archival and collaboration.*

|build-status| |license| |pypi-ver|

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


.. |build-status| image:: https://travis-ci.org/indico/indico.png?branch=master
                   :alt: Travis Build Status
                   :target: https://travis-ci.org/indico/indico
.. |pypi-ver| image:: https://img.shields.io/pypi/v/indico.png
                   :alt: Available on PyPI
                   :target: https://pypi.python.org/pypi/indico/
.. |license| image:: https://img.shields.io/github/license/indico/indico.png
                   :alt: License
                   :target: https://github.com/indico/indico/blob/master/COPYING
