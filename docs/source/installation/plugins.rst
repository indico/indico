Plugins
=======

We provide a meta-package that contains all official plugins. Before
installing it, make sure you are logged in as the *indico* user and
inside the Indico environment:

.. code-block:: shell

    su - indico
    source ~/.venv/bin/activate


Now install the package which will automatically install our plugins:

.. code-block:: shell

    pip install indico-plugins


.. note::

    Having all plugins installed has no disadvantages; only plugins enabled
    in ``indico.conf`` are actually loaded and executed.
    If you do not use the ``indico-plugins`` package, we won't be able to
    display a notification when updates are available and you would have to
    update all the plugins separately.


You can use the ``indico setup list_plugins`` command to see which plugins
are installed and which name to use in the config file to load them.

To enable plugins, add a ``PLUGINS`` entry to ``/opt/indico/etc/indico.conf``.
For example, the following line would enable the "Bank Transfer" and "PayPal"
payment plugins:

.. code-block:: python

    PLUGINS = {'payment_manual', 'payment_paypal'}


Some plugins contain additional database tables. Run the plugin database
migrations to create them (if you do not have any plugins with custom
tables, the command will simply do nothing):

.. code-block:: shell

    indico db --all-plugins upgrade


After any change to the config file, you need to reload uWSGI:

.. code-block:: shell

    touch ~/web/indico.wsgi


It is also a good idea to restart the Celery worker (as *root*) since
some plugins may come with background tasks:

.. code-block:: shell

    systemctl restart indico-celery.service
