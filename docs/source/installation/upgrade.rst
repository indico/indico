Upgrade
=======

It is important to keep your Indico instance up to date to have the
latest bug fixes and features.  Upgrading can be done with almost no
user-facing downtime.

.. warning::

    When upgrading a production system it is highly recommended to
    create a database backup before starting.


First of all, stop the Celery worker.  To do so, run this as *root*:

.. code-block:: shell

    systemctl stop indico-celery.service

Now switch to the *indico* user and activate the virtualenv:

.. code-block:: shell

    su - indico
    source ~/.venv/bin/activate

You are now ready to install the latest version of Indico:

.. code-block:: shell

    pip install -U indico

If you installed the official plugins, update them too:

.. code-block:: shell

    pip install -U indico-plugins

Some versions may include database schema upgrades.  Make sure to
perform them immediately after upgrading.  If there are no schema
changes, the command will simply do nothing.

.. code-block:: shell

    indico db upgrade
    indico db --all-plugins upgrade

.. note::

    Some database structure changes require an *exclusive lock* on
    some tables in the database.  Unless you have very high activity
    on your instance, this lock can be acquired quickly, but if the
    upgrade command seems to hang for more than a few seconds, you can
    restart uWSGI by running ``systemctl restart uwsgi.service`` as
    *root* (in a separate shell, i.e. don't abort the upgrade command!)
    which will ensure nothing is accessing Indico for a moment.

Unless you just restarted uWSGI, it is now time to reload it so the new
version is actually used:

.. code-block:: shell

    touch ~/web/indico.wsgi


Also start the Celery worker again (once again, as *root*):

.. code-block:: shell

    systemctl start indico-celery.service



Upgrading from 1.9.11 to 2.0
----------------------------

Make sure that you have the latest 1.9.11 version installed and that you used
``indico db upgrade`` to have the most recent database structure.

First of all, if you had installed any plugins manually, you need to uninstall
them first as we changed some of the Python distribution names so if you do
not uninstall them, you will get errors about duplicate plugins.

.. code-block:: shell

    pip freeze | grep -Po 'indico(?!-fonts).+(?===)' | pip uninstall -y


.. note::

    If you used ``pip install -e`` to install the plugins, the command
    above will not work and you need to manually uninstall them.  All
    the plugin packages have names like ``indico_chat`` or ``indico_payment_manual``.
    If you are unsure about what to uninstall here, please contact us.


To upgrade to 2.0, follow the upgrade instructions above, but skip the DB
upgrade commands.  After successfully running the upgrade, use
``indico db reset_alembic`` to clear pre-2.0 database migration information,
since all the old migration steps from the 1.9.x version line have been
removed in 2.0.

The names of all settings changed in 2.0; instead of using ``CamelCased`` names
they now use ``UPPER_SNAKE_CASE``. The old names still work, but we recommend
updating the config file anyway. You can find a list of all the new option names
`in the code`_.  Most renames are pretty straightforward; only the following
options have been changed in more than just capitalization:

===================  ==================
**Old**              **New**
-------------------  ------------------
PDFLatexProgram      XELATEX_PATH
IsRoomBookingActive  ENABLE_ROOMBOOKING
SanitizationLevel    *removed*
===================  ==================

The format of the logging config changed. The old file ``/opt/indico/etc/logging.conf``
is not used anymore and can be deleted.
Run ``indico setup create_logging_config /opt/indico/etc/``  to create the new
``logging.yaml`` which can then be customized if needed.

.. _in the code: https://github.com/indico/indico/blob/master/indico/core/config.py#L40
