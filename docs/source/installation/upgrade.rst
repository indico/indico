Upgrade Indico from an older version
====================================

Upgrading from versions < 2.0
-----------------------------

If you're running a version that is lower than 2.0, you will have to run a special migration command provided by the
``indico-migrate`` package. This document will guide you over the steps needed to perform the upgrade.


Prerequisites
+++++++++++++

In order to migrate to version 2.0 of Indico you will first of all need to make sure you have **at least version 1.2**
of Indico installed. Migration of databases using earlier versions will either **fail** or very likely result in
**data loss**. So, please make sure that you are **on 1.2.x** before migrating.

.. warning::

    If you are running a version of the experimental (thus unsupported) **1.9.x branch**, you will have to perform a
    **step-by-step migration**. We hope that, as advised, no-one upgraded to intermediate 1.9.x releases. If you did and
    need help with it, please **ping us on IRC**.


Backing up ZODB
+++++++++++++++

The migration script doesn't write to the ZODB, but we still recommend that you **make a backup** just in case:

.. code-block:: shell

    repozo -B -F -r <some-place-safe> -f <indico-db-dir>/Data.fs --verbose


You should replace ``<some-place-safe>`` with the directory in your filesystem where you want to keep the backup.
As for ``<indico-db-dir>``, that's the directory where the database file is kept. That should be ``/opt/indico/db`` in
most Indico installations.

Make sure that backup files have been created (you should have an ``*.index`` and an ``*.fs`` file).

Now, let's shut down the ZEO daemon:

.. code-block:: shell

    zdaemon -C /opt/indico/etc/zdctl.conf stop

Double check that the daemon is not running:

.. code-block:: shell

    zdaemon -C /opt/indico/etc/zdctl.conf status


Moving legacy data
++++++++++++++++++

Indico 2.0 will use a directory structure that is similar to Indico 1.x, so first of all you will need to rename the old
tree:

.. code-block:: shell

    mv /opt/indico /opt/indico-legacy


.. warning::

    After the migration is done, **do not** delete the ``/opt/indico-legacy`` directory without first moving the
    ``archive`` dir elsewhere. Please read the full guide until the end.



Installing Indico 2.0
+++++++++++++++++++++

The first step should be to have a working Indico 2.0 setup. In order to do that, you should follow the regular Indico
2.x installation instructions up to the "Configure Indico" step.  We provide below direct links to the relevant sections
of the installation guides.

On a **Debian/Ubuntu** system:

 * :ref:`deb-pkg`
 * :ref:`deb-db`
 * :ref:`deb-web`
 * :ref:`deb-ssl`
 * :ref:`deb-install`
 * :ref:`deb-config`

On a **CentOS7-based system**:

 * :ref:`centos-epel`
 * :ref:`centos-pkg`
 * :ref:`centos-db`
 * :ref:`centos-web`
 * :ref:`centos-ssl`
 * :ref:`centos-selinux`
 * :ref:`centos-install`
 * :ref:`centos-config`


Configuration Wizard
++++++++++++++++++++

You will then need to run the Configuration Wizard, following the normal installation guide (Debian/Ubuntu or CentOS).
When the wizard asks you about the **"Old archvive dir"**, make sure to set it to the archive dir in the
``indico-legacy`` directory.


.. code-block:: none

    ...
    If you are upgrading from Indico 1.2, please specify the path to the
    ArchiveDir of the old indico version.  Leave this empty if you are not
    upgrading.
    Old archive dir: /opt/indico-legacy/archive
    ...


Running ``indico-migrate``
++++++++++++++++++++++++++

First of all, make sure that you are using the **user** and **virtualenv** created using the step **"Install Indico"**:

.. code-block:: shell

    su - indico
    source ~/.venv/bin/activate


You should then install the package using:

.. code-block:: shell

   pip install indico-migrate


``indico-migrate`` requires a series of parameters that have to be tuned according to your current setup. We now provide
a list of values that should work in most standard Indico installations. However, please **carefully read** the
`documentation of the indico-migrate command <https://github.com/indico/indico-migrate#migration-settings>`_, to make
sure there are no option conflicts with your setup.

Most frequenty, ``indico-migrate postgresql:///indico fs:///opt/indico-legacy/db/Data.fs`` will work, followed by the following
parameters:

 * ``--archive-dir /opt/indico-legacy/archive``
 * ``--storage-backend legacy``
 * ``--default-email default@<organization-hostname>``
 * ``--default-currency EUR``
 * ``--symlink-target ~/archive/legacy_symlinks/``
 * ``--symlink-backend legacy-symlinks``

(don't forget to replace ``<organization-hostname>`` with the e-mail hostname of your organization)

An example:

.. code-block:: shell

    indico-migrate postgresql:///indico zeo://localhost:9675/indico --archive-dir /opt/indico/archive --storage-backend legacy --default-email default@acme.example.com --default-currency EUR --symlink-target ~/archive/legacy_symlinks/ --symlink-backend legacy-symlinks


.. note::

    If for some reason the migration fails, ``indico-migrate`` will ask you whether you would like to post an error report
    on a public pastebin (Gist). The link will not be advertised and only the log information that was shown on screen
    (plus the exception traceback that was printed) will be included. If you are not comfortable with letting
    ``indico-migrate`` post this on a public pastebin, you can always send us your ``migration.log`` file (which gets
    generated automatically).


Post-migration work
+++++++++++++++++++

After the migration is done you may need to apply some adjustments in your ``indico.conf``. You may want to read our
guide on how to configure an Identity/Authentication provider.

We really recommend as well that you move your old Indico archive (``/opt/indico-legacy/archive``) inside your new
Indico directory:

.. code-block:: shell

    mv /opt/indico-legacy/archive /opt/indico/legacy-archive

The legacy archive will remain **read-only**. You should update your ``indico.conf`` (``StorageBackends`` option) to
reflect the new path:

.. code-block:: python

    StorageBackends = {
        # ...
        'legacy': 'fs-readonly:/opt/indico/legacy-archive'
        # ...
    }


Finishing up
++++++++++++

You can now proceed with the remaining migration steps:

On a **Debian/Ubuntu** system:

 * :ref:`deb-launch`
 * :ref:`deb-user`


On a **CentOS7-based system**:

 * :ref:`centos-launch`
 * :ref:`centos-firewall`
 * :ref:`centos-user`


Removing old data
+++++++++++++++++

Even if you're sure the migration succeeded and all data was kept, please keep around the backup of your ZODB you
made at the beginning of this guide. **After** and **only after** having **moved the legacy archive** to the new Indico
dir and stored a **backup of your ZODB** in a safe place, you can proceed to delete the old ``/opt/indico`` directory:

.. code-block:: shell

    rm -rf /opt/indico-legacy
