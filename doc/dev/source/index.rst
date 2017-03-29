Welcome to Indico's documentation!
==================================


.. raw:: html
    :file: _static/github_star.html

.. image:: images/indico.png
    :width: 300 px
    :align: center

.. epigraph:: *Your swiss army knife event management system.*

|build-status| |license| |pypi-ver|

Welcome to Indico's documentation. This documentation is split into several parts, from `installing Indico <installation/>`_ to developing `Indico plugins <plugins>`_.
To dive into the internals of Indico, check out the `API documentation <api>`_.


Installation / Configuration
++++++++++++++++++++++++++++

.. include:: installation/_intro.rst

.. toctree::
    :maxdepth: 2

    installation/index.rst


Server administration
+++++++++++++++++++++

.. include:: admin/_intro.rst

.. toctree::
    :maxdepth: 2

    admin/index.rst


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


Indices and tables
++++++++++++++++++

* :ref:`genindex`
* :ref:`modindex`

.. |build-status| image:: https://travis-ci.org/indico/indico.png?branch=master
                   :alt: Travis Build Status
                   :target: https://travis-ci.org/indico/indico
.. |pypi-ver| image:: https://img.shields.io/pypi/v/indico.png
                   :alt: Available on PyPI
                   :target: https://pypi.python.org/pypi/indico/
.. |license| image:: https://img.shields.io/github/license/indico/indico.png
                   :alt: License
                   :target: https://github.com/indico/indico/blob/master/COPYING
