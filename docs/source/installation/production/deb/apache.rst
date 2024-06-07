Apache
======

1. Install Packages
-------------------

PostgreSQL is installed from its upstream repos to get a more recent version.

.. code-block:: shell

    apt install -y lsb-release wget curl gnupg
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor > /usr/share/keyrings/pgdg-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/pgdg-archive-keyring.gpg] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
    apt update
    apt install -y --install-recommends postgresql-16 libpq-dev apache2 libapache2-mod-proxy-uwsgi libapache2-mod-xsendfile libxslt1-dev libxml2-dev libffi-dev libpcre3-dev libyaml-dev libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libncurses5-dev libncursesw5-dev xz-utils liblzma-dev uuid-dev build-essential redis-server git libpango1.0-dev


If you use Debian, run this command:

.. code-block:: shell

    apt install -y libjpeg62-turbo-dev


If you use Ubuntu, run this instead:

.. code-block:: shell

    apt install -y libjpeg-turbo8-dev

Afterwards, make sure the services you just installed are running:

.. code-block:: shell

    systemctl start postgresql.service redis-server.service


2. Create a Database
--------------------

Let's create a user and database for indico and enable the necessary Postgres
extensions (which can only be done by the Postgres superuser).

.. code-block:: shell

    su - postgres -c 'createuser indico'
    su - postgres -c 'createdb -O indico indico'
    su - postgres -c 'psql indico -c "CREATE EXTENSION unaccent; CREATE EXTENSION pg_trgm;"'

.. important::

    Do not forget to setup a cronjob that creates regular database
    backups once you start using Indico in production!


3. Configure uWSGI & Apache
---------------------------

The default uWSGI and Apache configuration files should work fine in
most cases.

.. code-block:: shell

    cat > /etc/uwsgi-indico.ini <<'EOF'
    [uwsgi]
    uid = indico
    gid = www-data
    umask = 027

    processes = 4
    enable-threads = true
    chmod-socket = 770
    chown-socket = indico:www-data
    socket = /opt/indico/web/uwsgi.sock
    stats = /opt/indico/web/uwsgi-stats.sock
    protocol = uwsgi

    master = true
    auto-procname = true
    procname-prefix-spaced = indico
    disable-logging = true

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

We also need a systemd unit to start uWSGI.

.. code-block:: shell

    cat > /etc/systemd/system/indico-uwsgi.service <<'EOF'
    [Unit]
    Description=Indico uWSGI
    After=network.target

    [Service]
    ExecStart=/opt/indico/.venv/bin/uwsgi --ini /etc/uwsgi-indico.ini
    ExecReload=/bin/kill -HUP $MAINPID
    Restart=always
    SyslogIdentifier=indico-uwsgi
    User=indico
    Group=www-data
    UMask=0027
    Type=notify
    NotifyAccess=all
    KillMode=mixed
    KillSignal=SIGQUIT
    TimeoutStopSec=300

    [Install]
    WantedBy=multi-user.target
    EOF


.. note::

    Replace ``YOURHOSTNAME`` in the next files with the hostname on which
    your Indico instance should be available, e.g. ``indico.yourdomain.com``


.. code-block:: shell

    cat > /etc/apache2/sites-available/indico-sslredir.conf <<'EOF'
    <VirtualHost *:80>
        ServerName YOURHOSTNAME
        RewriteEngine On
        RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]
    </VirtualHost>
    EOF

    cat > /etc/apache2/sites-available/indico.conf <<'EOF'
    <VirtualHost *:443>
        ServerName YOURHOSTNAME
        DocumentRoot "/var/empty/apache"
        Protocols h2 http/1.1

        SSLEngine             on
        SSLCertificateFile    /etc/ssl/indico/indico.crt
        SSLCertificateKeyFile /etc/ssl/indico/indico.key

        SSLProtocol           all -SSLv3 -TLSv1 -TLSv1.1
        SSLCipherSuite        ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
        SSLHonorCipherOrder   off
        SSLSessionTickets     off

        XSendFile on
        XSendFilePath /opt/indico
        CustomLog /opt/indico/log/apache/access.log combined
        ErrorLog /opt/indico/log/apache/error.log
        LogLevel error
        ServerSignature Off

        <If "%{HTTP_HOST} != 'YOURHOSTNAME'">
            Redirect 301 / https://YOURHOSTNAME/
        </If>

        AliasMatch "^/(images|fonts)(.*)/(.+?)(__v[0-9a-f]+)?\.([^.]+)$" "/opt/indico/web/static/$1$2/$3.$5"
        AliasMatch "^/(css|dist|images|fonts)/(.*)$" "/opt/indico/web/static/$1/$2"
        Alias /robots.txt /opt/indico/web/static/robots.txt

        SetEnv UWSGI_SCHEME https
        ProxyPass / unix:/opt/indico/web/uwsgi.sock|uwsgi://localhost/

        <Directory /opt/indico>
            AllowOverride None
            Require all granted
        </Directory>
    </VirtualHost>
    EOF


Now enable the necessary modules and the indico site in apache:

.. code-block:: shell

    a2enmod proxy_uwsgi rewrite ssl xsendfile
    a2dissite 000-default
    a2ensite indico indico-sslredir


4. Create a TLS Certificate
---------------------------

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
`Let's Encrypt`_.


.. note::

    There's an optional step later in this guide to get a certificate
    from Let's Encrypt. We can't do it right now since the Apache
    config references a directory yet to be created, which prevents
    Apache from starting.


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
    UMask=0027
    Type=simple
    KillMode=mixed
    TimeoutStopSec=300

    [Install]
    WantedBy=multi-user.target
    EOF

    systemctl daemon-reload


Now create a user that will be used to run Indico and switch to it:

.. code-block:: shell

    useradd -rm -g www-data -d /opt/indico -s /bin/bash indico
    su - indico

The first thing to do is installing pyenv - we use it to install the latest Python version
as not all Linux distributions include it and like this Indico can benefit from the latest
Python features.

.. code-block:: shell

    curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash

    cat >> ~/.bashrc <<'EOF'
    export PATH="/opt/indico/.pyenv/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    EOF

    source ~/.bashrc

You are now ready to install Python 3.12:

.. code-block:: shell

    pyenv install 3.12
    pyenv global 3.12

This may take a while since pyenv needs to compile the specified Python version. Once done, you
may want to use ``python -V`` to confirm that you are indeed using the version you just installed.

You are now ready to install Indico:

.. code-block:: shell

    python -m venv --upgrade-deps --prompt indico ~/.venv
    source ~/.venv/bin/activate
    echo 'source ~/.venv/bin/activate' >> ~/.bashrc
    pip install setuptools wheel
    pip install uwsgi
    pip install indico


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
    chmod 710 ~/ ~/archive ~/cache ~/log ~/tmp
    chmod 750 ~/web ~/.venv
    chmod g+w ~/log/apache
    echo -e "\nSTATIC_FILE_METHOD = 'xsendfile'" >> ~/etc/indico.conf


7. Create database schema
-------------------------

Finally, you can create the database schema and switch back to *root*:

.. code-block:: shell

    indico db prepare
    exit


8. Launch Indico
----------------

You can now start Indico and set it up to start automatically when the
server is rebooted:

.. code-block:: shell

    systemctl restart apache2.service indico-celery.service indico-uwsgi.service
    systemctl enable apache2.service postgresql.service redis-server.service indico-celery.service indico-uwsgi.service


9. Optional: Get a Certificate from Let's Encrypt
-------------------------------------------------

To avoid ugly TLS warnings in your browsers, the easiest option is to
get a free certificate from Let's Encrypt. We also enable the cronjob
to renew it automatically:


.. code-block:: shell

    apt install -y certbot python3-certbot-apache
    certbot --apache --no-redirect --staple-ocsp -d YOURHOSTNAME
    rm -f /etc/ssl/indico/indico.*
    systemctl start certbot.timer
    systemctl enable certbot.timer


10. Create an Indico user
-------------------------

Access ``https://YOURHOSTNAME`` in your browser and follow the steps
displayed there to create your initial user.


11. Set up PDF Document Generation
----------------------------------

Follow the :ref:`PDF generation guide <pdf_generation>` to setup PDF document
generation in Indico.


.. _deb-apache-shib:

Optional: Shibboleth
--------------------

If your organization uses Shibboleth/SAML-based SSO, follow these steps to use
it in Indico:

1. Install Shibboleth
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    apt install -y libapache2-mod-shib
    a2enmod shib

2. Configure Shibboleth
^^^^^^^^^^^^^^^^^^^^^^^

This is outside the scope of this documentation and depends on your
environment (Shibboleth, SAML, ADFS, etc).  Please contact whoever
runs your SSO infrastructure if you need assistance.

3. Enable Shibboleth in Apache
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Add the following code to your ``/etc/apache2/sites-available/indico.conf``
right before the ``AliasMatch`` lines:

.. code-block:: apache

    <LocationMatch "^(/Shibboleth\.sso|/login/shib-sso/shibboleth)">
        AuthType shibboleth
        ShibRequestSetting requireSession 1
        ShibExportAssertion Off
        Require valid-user
    </LocationMatch>


4. Enable Shibboleth in Indico
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. include:: ../_sso_indico.rst


.. _PostgreSQL wiki: https://wiki.postgresql.org/wiki/YUM_Installation#Configure_your_YUM_repository
.. _Let's Encrypt: https://letsencrypt.org/
