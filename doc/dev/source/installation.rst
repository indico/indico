Installation guide
=================================================

===============
Before starting
===============

Indico runs on WSGI. There are WSGI modules for all major web servers. We normally run `mod_wsgi <http://code.google.com/p/modwsgi/>`_, using the `Apache httpd <http://httpd.apache.org/>`_ server. Here is the recommended setup:

* Python 2.7+
* Apache httpd 2.2+
* mod_wsgi 3.3+ (by installing libapache2-mod-wsgi)

You will need some system libraries:

* *python-devel* (or *python-dev* depending on your OS)
* *libxslt-devel*
* *libxml2-devel*
* *libffi-devel*
* *openldap-devel* (if you wish to use LDAP authentication)

You will also need to ``easy_install python-ldap`` if you want LDAP to work.

=============
Installing it
=============

First of all, make sure your ``setuptools`` is up-to-date. You may want to execute:

.. code-block:: console

    # pip install -U setuptools

You can then either install Indico's latest release or retrieve it from Git.

-----------------------------------------
Fetching the latest release (recommended)
-----------------------------------------

You can do it from command line executing:

.. code-block:: console

    # easy_install indico

Or, you can also do it fetching a tarball or egg file from our `releases on Github <https://github.com/indico/indico/releases/>`_.

-----------------------
From our Git repository
-----------------------

You can find the source code in our `Github repository <https://github.com/indico/indico/>`_. Cloning it is as easy as:

.. code-block:: console

    $ git clone https://github.com/indico/indico/

You should now have an ``indico`` directory. ``cd`` into it:

.. code-block:: console

    $ cd indico

Since you are building from source, you will need to install our development dependencies:

.. code-block:: console

    $ pip install -r requirements.dev.txt

And then fetch any non-Python external modules.

.. code-block:: console

    $ fab setup_deps

Finally, you can install Indico:

.. code-block:: console

    # python setup.py install

Or, alternatively, if you are just trying to set up an Indico development environment:

.. code-block:: console

    # python setup.py develop_config


The setup script will fetch all the dependencies for you and install Indico in your Python library path.

===================
Post-Install script
===================

The next step is to run ``indico_initial_setup``:

.. code-block:: console

    # indico_initial_setup
    No previous installation of Indico was found.
    Please specify a directory prefix:
    [/opt/indico]:

and follow the instructions that the script will provide. By default, Indico will be installed under ``/opt/indico``, but the setup script allows you to specify other paths.

By the end of the process, you should have obtained some information on how to start the database::

    If you are running ZODB on this host:
     - Review etc/zodb.conf and etc/zdctl.conf to make sure everything is ok.
     - To start the database run: zdaemon -C etc/zdctl.conf start

As well as some information on the paths::

    indico.conf:      /opt/indico/etc/indico.conf

    BinDir:           /opt/indico/bin
    DocumentationDir: /opt/indico/doc
    ConfigurationDir: /opt/indico/etc
    HtdocsDir:        /opt/indico/htdocs

==========================
Configuring the Web Server
==========================

Indico needs to run behind a WSGI-compliant web server. This guide describes two options:

* Apache HTTPD
* Nginx/uWSGI

--------------------------------
Configuring Apache (recommended)
--------------------------------

Create a new file in Apache HTTPD's config folder. Depending on the OS, it can be something like ``/etc/httpd/conf.d/``:

.. code-block:: console

    $ sudo vim /etc/httpd/conf.d/indico.conf

This is an example configuration that should be able to get you started:

.. code-block:: apacheconf

    AddDefaultCharset UTF-8

    <VirtualHost *:80>
        ErrorLog /var/log/apache2/error.log
        LogLevel warn

        Alias /indico/images "/opt/indico/htdocs/images"
        Alias /indico/css "/opt/indico/htdocs/css"
        Alias /indico/js "/opt/indico/htdocs/js"
        Alias /indico/ihelp "/opt/indico/htdocs/ihelp"

        WSGIDaemonProcess WSGIDAEMON processes=8 threads=1 inactivity-timeout=3600 maximum-requests=10000 \
                python-eggs=/opt/indico/tmp/egg-cache

        WSGIScriptAlias /indico "/opt/indico/htdocs/indico.wsgi"

        <Directory "/opt/indico">
            WSGIProcessGroup WSGIDAEMON
            WSGIApplicationGroup %{GLOBAL}
            AllowOverride None
            Options None
            Order deny,allow
            Allow from all
        </Directory>
    </VirtualHost>

    <VirtualHost *:443>
        ErrorLog /var/log/apache2/error.log
        LogLevel warn

        Alias /indico/images "/opt/indico/htdocs/images"
        Alias /indico/css "/opt/indico/htdocs/css"
        Alias /indico/js "/opt/indico/htdocs/js"
        Alias /indico/ihelp "/opt/indico/htdocs/ihelp"

        WSGIScriptAlias /indico "/opt/indico/htdocs/indico.wsgi"

        SSLEngine on
        SSLCertificateFile    /etc/ssl/certs/ssl-cert-snakeoil.pem
        SSLCertificateKeyFile /etc/ssl/private/ssl-cert-snakeoil.key
    </VirtualHost>

Here's the explanation of the above lines:

* ``Alias``: Redirects some static locations to the containing folders, reducing load times
* ``WSGIDaemonProcess``: Create 8 daemon processes of 1 thread each with name WSGIDAEMON. Set ``python-path`` and ``python-eggs`` paths. (The other two parameters are for robustness). Please note that the maximum number of processes will depend on how much load your server can handle (it's normal to have > 30 processes)
* ``WSGIScriptAlias``: Redirect all petitions starting with ``/indico`` to the specified file
* ``WSGIProcessGroup``: Configure the execution with the settings of ``WSGIDAEMON``
* ``WSGIApplicationGroup``: Set the execution to run under the same Python interpreter (the first created)

Accessing ``http://localhost/indico/`` should give you the main Indico page.

----------------------------------
Configuring uWSGI/nginx (option 2)
----------------------------------

Indico might be installed as a uWSGI application, in order to run on Nginx (and possibly on Varnish as well). Create a uWSGI application configuration file for indico on ``/etc/uwsgi/apps-available/indico.ini``::

    [uwsgi]
    pythonpath = /opt/indico
    processes = 4
    threads = 2
    wsgi-file = /opt/indico/htdocs/indico.wsgi
    post-buffering = 1
    autoload = true
    master = true
    workers = 2
    no-orphans = true
    pidfile = /run/uwsgi/%(deb-confnamespace)/%(deb-confname)/pid
    socket = /run/uwsgi/%(deb-confnamespace)/%(deb-confname)/socket
    chmod-socket = 660
    log-date = true
    uid = www-data
    gid = www-data

Then symlink this configuration file at ``/etc/uwsgi/apps-enabled/indico.ini``:

.. code-block:: console

    # ln -s ../apps-available/indico.ini /etc/uwsgi/apps-enabled/indico.ini

The uWSGI daemon should be started after ZODB is running, and if you commit any changes to indico configuration, the daemon should also be restarted:

.. code-block:: console

    # service uwsgi start

This will create the uwsgi daemon socket at ``/run/uwsgi/app/indico/socket``.

+++++++++++++++++++
Nginx configuration
+++++++++++++++++++

By default all you need to do on Nginx is to redirect all Indico requests to the uwsgi socket. However, static files should be delivered directly. Here's a sample configuration that works for both HTTP and HTTPS::

    ## Here's the upstream socket
    upstream indico {
        server unix:/run/uwsgi/app/indico/socket;
    }

    ## Uncomment the following lines in case you want to enable HTTPS
    #ssl_certificate        /etc/ssl/certs/ssl-cert-snakeoil.pem;
    #ssl_certificate_key    /etc/ssl/private/ssl-cert-snakeoil.key;

    ## uWSGI cache params:
    uwsgi_cache_key     $scheme$host$request_uri;
    uwsgi_cache_valid   200 302  1h;
    uwsgi_cache_valid   301      1d;
    uwsgi_cache_valid   any      1m;
    uwsgi_cache_min_uses  1;
    uwsgi_cache_use_stale error  timeout invalid_header http_500;

    server {
        listen 80;
        ## uncomment the following line to enable HTTPS access
        #listen 443 ssl;

        server_name _;
        root                   /opt/indico/htdocs;
        index                  index.py;

        ## try to get static files directly, if not, send request to Indico upstream
        location ~* ^.+.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt|pdf|swf|woff|ttf|otf|svg|ico)$ {
            access_log        off;
            expires           max;
            try_files $uri @indico;
        }

        ## This is should be the same path as the BaseURL configuration at indico.conf
        location / {
            include         uwsgi_params;
            uwsgi_pass      indico;
        }

        location @indico {
            include         uwsgi_params;
            uwsgi_pass      indico;
        }
    }

If the file ``/etc/nginx/uwsgi_params`` does not exist, create it with the following content::

    uwsgi_param     QUERY_STRING            $query_string;
    uwsgi_param     REQUEST_METHOD          $request_method;
    uwsgi_param     CONTENT_TYPE            $content_type;
    uwsgi_param     CONTENT_LENGTH          $content_length;

    uwsgi_param     REQUEST_URI             $request_uri;
    uwsgi_param     PATH_INFO               $document_uri;
    uwsgi_param     DOCUMENT_ROOT           $document_root;
    uwsgi_param     SERVER_PROTOCOL         $server_protocol;
    uwsgi_param     UWSGI_SCHEME            $scheme;

    uwsgi_param     REMOTE_ADDR             $remote_addr;
    uwsgi_param     REMOTE_PORT             $remote_port;
    uwsgi_param     SERVER_PORT             $server_port;
    uwsgi_param     SERVER_NAME             $server_name;

Please note that the uwsgi_param ``UWSGI_SCHEME`` is not available by default, and it's required in case you configure a server with both HTTP and HTTPS.

After setup, restart nginx:

.. code-block:: console

    # service nginx restart

==================
Indico config file
==================

The next step should be inspecting ``indico.conf`` and configuring it to fit your server configuration. ``indico.conf`` replaces the old ``config.xml``, so you will have to update it with the paramaters that you already have in your ``config.xml``.

From v1.2 on, the URLs will be shorter, alike ``http://my.indico.srv/event/2413/`` instead of the historical ``http://my.indico.srv/conferenceDisplay.py?confId=2413``. If you want to stay compatible with the old way, i.e. redirect from the old URLs to new URLs, then you need to set ``RouteOldUrls = True`` in your (new) ``indico.conf`` file.

==================
Post-install tasks
==================

For background tasks you need to run the Celery scheduler daemon:

.. code-block:: console

    # indico celery worker -B

If you have changed your server host name for some reason  you may need to delete ``/opt/indico/tmp/vars.js.tpl.tmp``.

=========
Migration
=========

In order to upgrade Indico you can do the following:

.. code-block:: console

    # easy_install -U indico
    # indico_initial_setup --existing-config=/opt/indico/etc/indico.conf  # replace with the path to your indico.conf
    # python /opt/indico/bin/migration/migrate.py --prev-version=<previous-version>
    # service httpd restart
