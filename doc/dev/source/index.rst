Indico
======

Welcome to Indico's documentation. This documentation is split into several parts, from `installing Indico <installation.html>`_ to developing `Indico plugins <plugins>`_.
To dive into the internals of Indico, check out the `API documentation <api>`_.

Installation / Configuration
++++++++++++++++++++++++++++

To simply install and use Indico, follow the `production installation instructions <installation_prod.rst>`_. For those who are interested in developing new features and plugins for Indico, check out the `development installation instructions <installation_dev.rst>`_.

.. toctree::
    :maxdepth: 2

    installation/index.rst


Plugins
+++++++

Indico can be extended through plugins, standalone packages of code that do not require any modifications to the Indico core itself. A plugin can perform something very simple such as adding a new command to the Indico CLI to more complex functionalities like introducing new payment methods, chat integration, etc.
We suggest that you first have a look at `Getting started <plugins/getting_started.rst>`_ and then head over to the more advance topics in the table of contents.

.. toctree::
    :maxdepth: 2

    Indico plugins <plugins/index.rst>


HTTP API
++++++++

Indico allows you to programmatically access the content of its database by exposing various information like category contents, events, rooms and room bookings through a web service, the HTTP Export API.

.. toctree::
    :maxdepth: 2

    HTTP API <http_api/index.rst>


API reference
+++++++++++++

This part of the documentation focuses on the core modules of Indico and includes information about the **models** and **utility functions and classes** that are useful for understanding the internals of the application.

.. toctree::
    :maxdepth: 2

    api/index.rst


Indices and tables
++++++++++++++++++

* :ref:`genindex`
* :ref:`modindex`
