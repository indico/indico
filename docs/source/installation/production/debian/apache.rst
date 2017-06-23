Apache
======

.. _deb-apache-pkg:

1. Install Packages
-------------------

PostgreSQL is installed from its upstream repos to get a much more recent version.

.. code-block:: shell

    echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
    apt update
    apt install -y postgresql-9.6 libpq-dev apache2 libapache2-mod-proxy-uwsgi libapache2-mod-xsendfile python-dev python-virtualenv libxslt1-dev libxml2-dev libffi-dev libpcre3-dev libyaml-dev build-essential redis-server uwsgi uwsgi-plugin-python


If you use Debian, run this command:

.. code-block:: shell

    apt install -y libjpeg62-turbo-dev


If you use Ubuntu, run this instead:

.. code-block:: shell

    apt install -y libjpeg-turbo8-dev zlib1g-dev


.. _deb-apache-db:

2. Create a Database
--------------------

We create a user and database for indico and enable the necessary
Postgres extensions (which can only be done by the Postgres superuser)

.. code-block:: shell

    su - postgres -c 'createuser indico'
    su - postgres -c 'createdb -O indico indico'
    su - postgres -c 'psql indico -c "CREATE EXTENSION unaccent; CREATE EXTENSION pg_trgm;"'

.. warning::

    Do not forget to setup a cronjob that creates regular database
    backups once you start using Indico in production!


.. _deb-apache-web:

3. Configure uWSGI & Apache
---------------------------

The default uWSGI and Apache configuration files should work fine in
most cases.

.. code-block:: shell

    ln -s /etc/uwsgi/apps-available/indico.ini /etc/uwsgi/apps-enabled/indico.ini
    cat > /etc/uwsgi/apps-available/indico.ini <<'EOF'
    [uwsgi]
    uid = indico
    gid = www-data

    processes = 4
    enable-threads = false
    socket = 127.0.0.1:8008
    stats = /opt/indico/web/uwsgi-stats.sock
    protocol = uwsgi

    master = true
    auto-procname = true
    procname-prefix-spaced = indico
    disable-logging = true

    plugin = python
    single-interpreter = true

    touch-reload = /opt/indico/web/indico.wsgi
    wsgi-file = /opt/indico/web/indico.wsgi
    virtualenv = /opt/indico/.venv

    vacuum = true
    buffer-size = 20480
    memory-report = true
    max-requests = 2500
    harakiri = 900
    harakiri-verbose = true
    reload-on-rss = 2048
    evil-reload-on-rss = 8192
    EOF


.. note::

    Replace ``YOURHOSTNAME`` in the next file with the hostname on which
    your Indico instance should be available, e.g. ``indico.yourdomain.com``


.. code-block:: shell

    cat > /etc/apache2/sites-available/indico.conf <<'EOF'
    <VirtualHost *:80>
        ServerName YOURHOSTNAME
        RewriteEngine On
        RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]
    </VirtualHost>


    <VirtualHost *:443>
        ServerName YOURHOSTNAME
        DocumentRoot "/var/empty/apache"

        SSLEngine             on
        SSLCertificateFile    /etc/ssl/indico/indico.crt
        SSLCertificateKeyFile /etc/ssl/indico/indico.key
        SSLProtocol           all -SSLv2 -SSLv3
        SSLCipherSuite        ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES256-SHA:ECDHE-ECDSA-DES-CBC3-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:!DSS
        SSLHonorCipherOrder   on

        XSendFile on
        XSendFilePath /opt/indico
        CustomLog /opt/indico/log/apache/access.log combined
        ErrorLog /opt/indico/log/apache/error.log
        LogLevel error
        ServerSignature Off

        AliasMatch "^/static/assets/(core|(?:plugin|theme)-[^/]+)/(.*)$" "/opt/indico/assets/$1/$2"
        AliasMatch "^/(ihelp|css|images|js|static(?!/plugins|/assets|/themes|/custom))(/.*)$" "/opt/indico/web/htdocs/$1$2"
        Alias /robots.txt /opt/indico/web/htdocs/robots.txt

        SetEnv UWSGI_SCHEME https
        ProxyPass / uwsgi://127.0.0.1:8008/

        <Directory /opt/indico>
            AllowOverride None
            Require all granted
        </Directory>
    </VirtualHost>
    EOF


Now enable the necessary modules and the indico site in apache:

.. code-block:: shell

    a2enmod proxy_uwsgi rewrite ssl xsendfile
    a2ensite indico


.. _deb-apache-ssl:

4. Create an SSL Certificate
----------------------------

First, create the folders for the certificate/key and set restrictive
permissions on them:

.. code-block:: shell

    mkdir /etc/ssl/indico
    chown root:root /etc/ssl/indico/
    chmod 700 /etc/ssl/indico

If you are just trying out Indico you can simply use a self-signed
certificate (your browser will show a warning which you will have
to confirm when accessing your Indico instance for the first time).


.. note::

    Do not forget to replace ``YOURHOSTNAME`` with the same value
    you used above

.. code-block:: shell

    openssl req -x509 -nodes -newkey rsa:4096 -subj /CN=YOURHOSTNAME -keyout /etc/ssl/indico/indico.key -out /etc/ssl/indico/indico.crt


While a self-signed certificate works for testing, it is not suitable
for a production system.  You can either buy a certificate from any
commercial certification authority or get a free one from
`Let's Encrypt`_. Once you have a proper key/certificate, save them
as ``/etc/ssl/indico/indico.key`` and ``/etc/ssl/indico/indico.crt``.


.. _deb-apache-install:

5. Install Indico
-----------------

Celery runs as a background daemon. Add a systemd unit file for it:

.. code-block:: shell

    cat > /etc/systemd/system/indico-celery.service <<'EOF'
    [Unit]
    Description=Indico Celery
    After=network.target

    [Service]
    ExecStart=/opt/indico/.venv/bin/indico celery worker -B
    Restart=always
    SyslogIdentifier=indico-celery
    User=indico
    Group=www-data
    Type=simple

    [Install]
    WantedBy=multi-user.target
    EOF
    systemctl daemon-reload


Now create a user that will be used to run Indico and switch to it:

.. code-block:: shell

    useradd -rm -g www-data -d /opt/indico -s /bin/bash indico
    su - indico


You are now ready to install Indico:

.. code-block:: shell

    virtualenv ~/.venv
    source ~/.venv/bin/activate
    pip install -U pip setuptools
    pip install indico

.. note::

    If you use a custom-built indico wheel, use ``pip install /path/to/indico-*.whl``
    instead of ``pip install indico``


.. _deb-apache-config:

6. Configure Indico
-------------------

Once Indico is installed, you can run the configuration wizard.  You can
keep the defaults for most options, but make sure to use ``https://YOURHOSTNAME``
when prompted for the Indico URL. Also specify valid email addresses when asked
and enter a valid SMTP server Indico can use to send emails.  When asked for the
default timezone make sure this is the main time zone used in your Indico instance.

.. code-block:: shell

    indico setup wizard


Now finish setting up the directory structure and permissions:

.. code-block:: shell

    mkdir ~/log/apache
    chmod go-rwx ~/* ~/.[^.]*
    chmod 710 ~/ ~/archive ~/assets ~/cache ~/log ~/tmp
    chmod 750 ~/web ~/.venv
    chmod g+w ~/log/apache
    echo -e "\nStaticFileMethod = 'xsendfile'" >> ~/etc/indico.conf


7. Create database schema
-------------------------

Finally, you can create the database schema and switch back to *root*:

.. code-block:: shell

    indico db prepare
    exit


.. _deb-apache-launch:

8. Launch Indico
----------------

You can now start Indico and set it up to start automatically when the
server is rebooted:

.. code-block:: shell

    systemctl restart uwsgi.service apache2.service indico-celery.service
    systemctl enable uwsgi.service apache2.service postgresql.service redis-server.service indico-celery.service


.. _deb-apache-user:

9. Create an Indico user
------------------------

Access ``https://YOURHOSTNAME`` in your browser and follow the steps
displayed there to create your initial user.


.. _PostgreSQL wiki: https://wiki.postgresql.org/wiki/YUM_Installation#Configure_your_YUM_repository
.. _Let's Encrypt: https://letsencrypt.org/
