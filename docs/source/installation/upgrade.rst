Upgrade
=======

It is important to keep your Indico instance up to date to have the
latest bug fixes and features.  Upgrading can be done with almost no
user-facing downtime.

.. warning::

    When upgrading a production system it is highly recommended to
    create a database backup before starting.

.. important::

    If you are upgrading from Indico v3.2.x or older to v3.3 or newer, make sure to
    fully read and understand the :ref:`Upgrading from 3.x to 3.3 <upgrade-3-to-33>`
    guide before starting with any of the upgrade steps below.

.. _upgrade-3-to-3:

Upgrading between 3.x versions
------------------------------

First of all, stop the Celery worker.  To do so, run this as *root*:

.. code-block:: shell

    systemctl stop indico-celery.service

Now switch to the *indico* user and activate the virtualenv:

.. code-block:: shell

    su - indico
    source ~/.venv/bin/activate

If you use Alma/Rocky, update your PATH to avoid errors in case the new
Indico version needs to install an updated version of the PostgreSQL client
library (psycopg2). If you use a different Postgres version, you need to
adapt the command accordingly:

.. code-block:: shell

    export PATH="$PATH:/usr/pgsql-16/bin"

.. _upgrade-3-to-3-indico:

You are now ready to install the latest version of Indico:

.. hint::

    Are you upgrading from Indico v3.2.x or older to v3.3 or newer? Then you have
    to jump to the :ref:`Upgrading from 3.x to 3.3 <upgrade-3-to-33>` guide now!

.. code-block:: shell

    pip install -U indico

.. _upgrade-3-to-3-plugins:

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


.. _upgrade-3-to-33:

Upgrading from 3.x to 3.3
-------------------------

When updating to Indico v3.3 you need to perform some extra steps since the required Python
version has been raised from Python 3.9 to Python 3.12.

.. attention::

    If you are still using **CentOS 7** (or 8), you are required to **update your operating
    system** to version **9** - your system is not only too old, but also going end-of-life
    in the middle of 2024. Since CentOS no longer exists in its original form, we recommend
    using **AlmaLinux 9** or **Rocky Linux 9**. You can find guides on the internet on how
    to do such an upgrade in-place (we never tried this!), but it is almost certainly easier
    to just use a new VM and migrate your Indico installations to that one.

    If you are using an older **Debian** (Buster or Bullseye) or **Ubuntu** (Focal) release,
    switching to the latest one is also highly recommended - we no longer test on older releases,
    and things may be broken. Upgrading in-place is possible, but our same advice applies here:
    We never tried this and cannot help you with it; migrating to a new VM is almost certainly
    the easier and safer option.

    Please also read the :ref:`2.x to 3.x <upgrade-2-to-3>` guide below which explains how to
    migrate your Indico data to a new system.

The general :ref:`upgrade guide between 3.x versions <upgrade-3-to-3>` above still applies,
you just need to perform some additional steps. Anything below assumes you are on a supported
Linux distribution (or know exactly what you're doing).

Before the :ref:`Indico upgrade step <upgrade-3-to-3-indico>` (``pip install -U indico``),
you need to install the required Python version:

.. code-block:: shell

    indico setup upgrade-python --force-version 3.12

Confirm both the warning about the requested version not being within the spec (which is based
on the previous Indico version) and the warning about having to re-install packages with :kbd:`Y`.

Now you just need to install the *setuptools* package and then continue with installing the
new Indico version and updating the symlink for the static assets:

.. code-block:: shell

    pip install setuptools
    pip install -U indico
    indico setup create-symlinks ~/web/

You can now resume the regular upgrade guide :ref:`right after the <upgrade-3-to-3-plugins>`
``pip install -U indico`` step.

.. _upgrade-2-to-3:

Upgrading from 2.x to 3.x
-------------------------

The upgrade from 2.x to 3.x is a major change since Indico now requires
Python 3. We also strongly recommend upgrading your database to PostgreSQL 16
or newer (PostgreSQL 13 is the minimum required version we still test with).

.. note::

    As of Indico 3.2, the upgrade **will fail** on Postgres 10 and older.

.. warning::

    If you are using any custom plugins they will most likely no longer work and
    need to be updated. Contact the developers of these plugins to see whether they
    already have a version compatible with Python 3 and Indico 3.

Due to the significant changes in the environment, we recommend using a **freshly
installed server/VM** with the latest long-term-supported version of your preferred
Linux distribution.

.. note::

    In case you are using CentOS 7, please note that CentOS 7 is soon reaching its
    end-of-life date (mid 2024), and Indico v3.3 is no longer compatible with this
    very old distribution. Please use Alma/Rocky 9, or the latest Debian/Ubuntu LTS
    release instead.

When following the :ref:`production installation guide <install-prod>`, there
are a few places where you need to do something differently:

- Instead of running ``indico db prepare``, restore a dump of your old Postgres
  database
- You still need to run ``indico setup wizard`` to create some of the directories,
  but compare the generated config file with your old one and update any settings
  you may have changed manually (e.g. for LDAP or SSO authentication)
- You need to perform the database structure upgrades just like during any other
  Indico upgrade: ``indico db upgrade`` and ``indico db --all-plugins upgrade``
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
