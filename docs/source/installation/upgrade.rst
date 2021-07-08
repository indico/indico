Upgrade
=======

It is important to keep your Indico instance up to date to have the
latest bug fixes and features.  Upgrading can be done with almost no
user-facing downtime.

.. warning::

    When upgrading a production system it is highly recommended to
    create a database backup before starting.

Upgrading between 3.x versions
------------------------------

First of all, stop the Celery worker.  To do so, run this as *root*:

.. code-block:: shell

    systemctl stop indico-celery.service

Now switch to the *indico* user and activate the virtualenv:

.. code-block:: shell

    su - indico
    source ~/.venv/bin/activate

If you are on CentOS, update your PATH to avoid errors in case the new
Indico version needs to install an updated version of the PostgreSQL client
library (psycopg2):

.. code-block:: shell

    export PATH="$PATH:/usr/pgsql-13/bin"

You are now ready to install the latest version of Indico:

.. code-block:: shell

    pip install -U indico

If you installed the official plugins, update them too:

.. code-block:: shell

    pip install -U indico-plugins

It is a good idea to ensure you are using the latest recommended Python version:

.. code-block:: shell

    indico setup upgrade-python

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



Upgrading from 2.x to 3.x
-------------------------

The upgrade from 2.x to 3.x is a major change since Indico now requires
Python 3. We also strongly recommend upgrading your database to PostgreSQL 13.

.. note::

    There are no changes that require the newer Postgres version immediately,
    but we no longer test on versions older than Postgres 12, and thus can
    give you no guarantees that things will keep working on older versions such
    as 9.6.

.. warning::

    If you are using any custom plugins they will most likely no longer work and
    need to be updated. Contact the developers of these plugins to see whether they
    already have a version compatible with Python 3 and Indico 3.

Due to the significant changes in the environment, we recommend using a **freshly
installed server/VM** with the latest long-term-supported version of your preferred
Linux distribution.

.. note::

    If you are using CentOS, staying with CentOS 7 is recommended as CentOS 8
    actually has a much earlier end-of-life date (end of 2021) than CentOS 7
    (mid 2024), and running Indico with Apache on CentOS 8 is currently not
    supported.

When following the :ref:`production installation guide <install-prod>`, there
are a few places where you need to do something differently:

- Instead of running ``indico db prepare``, restore a dump of your old Postgres
  database
- You still need to run ``indico setup wizard`` to create some of the directories,
  but compare the generated config file with your old one and update any settings
  you may have changed manually (e.g. for LDAP or SSO authentication)
- Copy the contents of the ``/opt/indico/archive`` folder from your old instance and
  ensure owner, group and permissions are correct. This step is critical as this folder
  contains all the files uploaded to Indico

If you need any help with the upgrade or encounter any issues, please open a thread
in `our forum`_.

Upgrading from 2.x to 3.x in-place
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::

    If you are not experienced with Linux system administration, we highly recommend
    you to either ask someone from your IT department for assistance and/or follow our
    recommendation of using a new server/VM to install Indico v3.

In case you prefer to perform the upgrade in place on your existing server, you will
need to compare the installation guides of 2.3 and 3.x and apply the differences
manually.  This should be fairly easy for someone with Linux system administration
experience, but here are some important points:

- Create a backup of both your Postgres database and ``/opt/indico/archive``
- Stop, disable and and uninstall uWSGI and delete the old config file. To support
  the latest Python version uWSGI is now installed into the Indico virtual environment
  using ``pip``
- Delete the ``~/.venv`` folder of the Indico user and recreate it using the commands
  from the setup guide
- Make sure to update your webserver config to use the more modern TLS defaults


.. _our forum: https://talk.getindico.io/
