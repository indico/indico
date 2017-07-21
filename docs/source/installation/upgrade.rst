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

    pip install -U --pre indico

Some versions may include database schema upgrades.  Make sure to
perform them immediately after upgrading.  If there are no schema
changes, the command will simply do nothing.

.. code-block:: shell

    indico db upgrade

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

To upgrade to 2.0, follow the upgrade instructions above.
After successfully running the upgrade, use ``indico db reset_alembic`` to clear
pre-2.0 database migration information, since all the old migration steps from
the 1.9.x version line have been removed in 2.0.
