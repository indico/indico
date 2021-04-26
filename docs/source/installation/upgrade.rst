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



Upgrading from 2.x to 2.2
-------------------------

.. warning::

    Keep in mind that running Indico from a subdirectory such as ``https://example.com/indico`` is
    **no longer supported** by the packages we provide on PyPI. Please use a subdomain instead.

When updating to version 2.2 you need to perform some extra steps due to the changes in Indico's
static asset pipeline.

After installing 2.2, run ``indico setup create-symlinks ~/web`` (still as the *indico* user) to
create the new symlink.

You can also perform some clean-up:

.. code-block:: shell

    rm /opt/indico/web/htdocs
    rm -rf /opt/indico/assets
    sed -i -e '/ASSETS_DIR/d' ~/etc/indico.conf

Now switch back to *root* and update the webserver config as explained below.


Apache
^^^^^^

Open ``/etc/httpd/conf.d/indico.conf`` (CentOS) or ``/etc/apache2/sites-available/indico.conf`` (Debian)
with an editor and replace this snippet:

.. code-block:: apache

    AliasMatch "^/static/assets/(core|(?:plugin|theme)-[^/]+)/(.*)$" "/opt/indico/assets/$1/$2"
    AliasMatch "^/(css|images|js|static(?!/plugins|/assets|/themes|/custom))(/.*)$" "/opt/indico/web/htdocs/$1$2"
    Alias /robots.txt /opt/indico/web/htdocs/robots.txt

with this one:

.. code-block:: apache

    AliasMatch "^/(images|fonts)(.*)/(.+?)(__v[0-9a-f]+)?\.([^.]+)$" "/opt/indico/web/static/$1$2/$3.$5"
    AliasMatch "^/(css|dist|images|fonts)/(.*)$" "/opt/indico/web/static/$1/$2"
    Alias /robots.txt /opt/indico/web/static/robots.txt

Reload apache using ``systemctl reload apache2.service``.


nginx
^^^^^

Open ``/etc/nginx/conf.d/indico.conf`` with an editor and replace this snippet:

.. code-block:: nginx

    location ~ ^/static/assets/(core|(?:plugin|theme)-[^/]+)/(.*)$ {
      alias /opt/indico/assets/$1/$2;
      access_log off;
    }

    location ~ ^/(css|images|js|static(?!/plugins|/assets|/themes|/custom))(/.*)$ {
      alias /opt/indico/web/htdocs/$1$2;
      access_log off;
    }

    location /robots.txt {
      alias /opt/indico/web/htdocs/robots.txt;
      access_log off;
    }

with this one:

.. code-block:: nginx

    location ~ ^/(images|fonts)(.*)/(.+?)(__v[0-9a-f]+)?\.([^.]+)$ {
      alias /opt/indico/web/static/$1$2/$3.$5;
      access_log off;
    }

    location ~ ^/(css|dist|images|fonts)/(.*)$ {
      alias /opt/indico/web/static/$1/$2;
      access_log off;
    }

    location /robots.txt {
      alias /opt/indico/web/static/robots.txt;
      access_log off;
    }

Reload nginx using ``systemctl reload nginx.service``.

If you are using customizations using the :data:`CUSTOMIZATION_DIR` setting, see its
updated documentation as you will have to update those customizations.



Upgrading from 2.2 to 2.3
-------------------------

Logging config
^^^^^^^^^^^^^^

We changed the way the user id is logged in ``indico.log`` (it's now logged in a more
structured way and included in every log message instead of just the one indicating
the start of a request).

If you have not modified the logging config the easiest option is deleting
``/opt/indico/etc/logging.yaml`` and running ``indico setup create-logging-config /opt/indico/etc/``
to recreate it.

If you do have custom changes or don't remember whether you do, you can apply the change
from the diff below manually.

.. code-block:: diff

     formatters:
       default:
    -    format: '%(asctime)s  %(levelname)-7s  %(request_id)s  %(name)-25s %(message)s'
    +    format: '%(asctime)s  %(levelname)-7s  %(request_id)s  %(user_id)-6s  %(name)-25s %(message)s'
       simple:
         format: '%(asctime)s  %(levelname)-7s  %(name)-25s %(message)s'
       email:
         append_request_info: true
    -    format: "%(asctime)s  %(request_id)s  %(name)s - %(levelname)s %(filename)s:%(lineno)d -- %(message)s\n\n"
    +    format: "%(asctime)s  %(request_id)s  %(user_id)-6s  %(name)s - %(levelname)s %(filename)s:%(lineno)d -- %(message)s\n\n"


OAuth SSO
^^^^^^^^^

If you are using OAuth-based SSO you need to update ``indico.conf`` as the ``oauth``
auth provider type has been replaced by the more modern and flexible ``authlib`` one.
Please see the `Flask-Multipass documentation`_ on how to configure it.  You
can also ask in `our forum`_ if you need any help with updating your SSO config.



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
Run ``indico setup create-logging-config /opt/indico/etc/``  to create the new
``logging.yaml`` which can then be customized if needed.

.. _in the code: https://github.com/indico/indico/blob/master/indico/core/config.py#L31
.. _Flask-Multipass documentation: https://flask-multipass.readthedocs.io/en/latest/
.. _our forum: https://talk.getindico.io/
