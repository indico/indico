nginx
=====

.. include:: ../_sso_note.rst

.. _deb-pkg:

1. Install Packages
-------------------

PostgreSQL and nginx are installed from their upstream repos to get
much more recent versions.

.. code-block:: shell

    apt install -y lsb-release wget
    echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
    echo "deb http://nginx.org/packages/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/ $(lsb_release -cs) nginx" > /etc/apt/sources.list.d/nginx.list
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
    wget --quiet -O - https://nginx.org/keys/nginx_signing.key | apt-key add -
    apt update
    apt install -y --install-recommends postgresql-9.6 libpq-dev nginx python-dev python-virtualenv libxslt1-dev libxml2-dev libffi-dev libpcre3-dev libyaml-dev build-essential redis-server uwsgi uwsgi-plugin-python


If you use Debian, run this command:

.. code-block:: shell

    apt install -y libjpeg62-turbo-dev


If you use Ubuntu, run this instead:

.. code-block:: shell

    apt install -y libjpeg-turbo8-dev zlib1g-dev

Afterwards, make sure the services you just installed are running:

.. code-block:: shell

    systemctl start postgresql.service redis-server.service


.. _deb-db:

2. Create a Database
--------------------

Let's create a user and database for indico and enable the necessary Postgres
extensions (which can only be done by the Postgres superuser).

.. code-block:: shell

    su - postgres -c 'createuser indico'
    su - postgres -c 'createdb -O indico indico'
    su - postgres -c 'psql indico -c "CREATE EXTENSION unaccent; CREATE EXTENSION pg_trgm;"'

.. warning::

    Do not forget to setup a cronjob that creates regular database
    backups once you start using Indico in production!


.. _deb-web:

3. Configure uWSGI & nginx
--------------------------

The default uWSGI and nginx configuration files should work fine in
most cases.

.. code-block:: shell

    ln -s /etc/uwsgi/apps-available/indico.ini /etc/uwsgi/apps-enabled/indico.ini
    cat > /etc/uwsgi/apps-available/indico.ini <<'EOF'
    [uwsgi]
    uid = indico
    gid = nginx
    umask = 027

    processes = 4
    enable-threads = true
    chmod-socket = 770
    socket = /opt/indico/web/uwsgi.sock
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

    cat > /etc/nginx/conf.d/indico.conf <<'EOF'
    server {
      listen 80;
      listen [::]:80;
      server_name YOURHOSTNAME;
      return 301 https://$server_name$request_uri;
    }

    server {
      listen       *:443 ssl http2;
      listen       [::]:443 ssl http2 default ipv6only=on;
      server_name  YOURHOSTNAME;

      ssl on;

      ssl_certificate           /etc/ssl/indico/indico.crt;
      ssl_certificate_key       /etc/ssl/indico/indico.key;
      ssl_session_cache         shared:SSL:10m;
      ssl_session_timeout       5m;
      ssl_protocols             TLSv1 TLSv1.1 TLSv1.2;
      ssl_ciphers               ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES256-SHA:ECDHE-ECDSA-DES-CBC3-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:!DSS;
      ssl_prefer_server_ciphers on;

      access_log            /opt/indico/log/nginx/access.log combined;
      error_log             /opt/indico/log/nginx/error.log;

      location /.xsf/indico/ {
        internal;
        alias /opt/indico/;
      }

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

      location / {
        root  /var/empty/nginx;
        include /etc/nginx/uwsgi_params;
        uwsgi_pass unix:/opt/indico/web/uwsgi.sock;
        uwsgi_param UWSGI_SCHEME $scheme;
        uwsgi_read_timeout 15m;
        uwsgi_buffers 32 32k;
        uwsgi_busy_buffers_size 128k;
        uwsgi_hide_header X-Sendfile;
        client_max_body_size 1G;
      }
    }
    EOF


.. _deb-ssl:

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
`Let's Encrypt`_.


.. note::

    There's an optional step later in this guide to get a certificate
    from Let's Encrypt. We can't do it right now since the nginx
    config references a directory yet to be created, which prevents
    nginx from starting.


.. _deb-install:

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
    Group=nginx
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

    useradd -rm -g nginx -d /opt/indico -s /bin/bash indico
    su - indico


You are now ready to install Indico:

.. code-block:: shell

    virtualenv ~/.venv
    source ~/.venv/bin/activate
    pip install -U pip setuptools
    pip install indico


.. _deb-config:

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

    mkdir ~/log/nginx
    chmod go-rwx ~/* ~/.[^.]*
    chmod 710 ~/ ~/archive ~/assets ~/cache ~/log ~/tmp
    chmod 750 ~/web ~/.venv
    chmod g+w ~/log/nginx
    echo -e "\nSTATIC_FILE_METHOD = ('xaccelredirect', {'/opt/indico': '/.xsf/indico'})" >> ~/etc/indico.conf


7. Create database schema
-------------------------

Finally, you can create the database schema and switch back to *root*:

.. code-block:: shell

    indico db prepare
    exit


.. _deb-launch:

8. Launch Indico
----------------

You can now start Indico and set it up to start automatically when the
server is rebooted:

.. code-block:: shell

    systemctl restart uwsgi.service nginx.service indico-celery.service
    systemctl enable uwsgi.service nginx.service postgresql.service redis-server.service indico-celery.service


.. _deb-letsencrypt:

9. Optional: Get a Certificate from Let's Encrypt
-------------------------------------------------

.. note::

    You need to use at least Debian 9 (Stretch) to use certbot.
    If you are still using Debian 8 (Jessie), consider updating
    or install certbot from backports.


If you use Ubuntu, install the certbot PPA:

.. code-block:: shell

    apt install -y software-properties-common
    add-apt-repository -y ppa:certbot/certbot
    apt update


To avoid ugly SSL warnings in your browsers, the easiest option is to
get a free certificate from Let's Encrypt. We also enable the cronjob
to renew it automatically:


.. code-block:: shell

    apt install -y python-certbot-nginx
    certbot --nginx --rsa-key-size 4096 --no-redirect --staple-ocsp -d YOURHOSTNAME
    rm -rf /etc/ssl/indico
    systemctl start certbot.timer
    systemctl enable certbot.timer


.. _deb-user:

10. Create an Indico user
-------------------------

Access ``https://YOURHOSTNAME`` in your browser and follow the steps
displayed there to create your initial user.


.. _deb-latex:

11. Install TeXLive
-------------------

Follow the :ref:`LaTeX install guide <latex>` to install TeXLive so
Indico can generate PDF files in various places.


.. _PostgreSQL wiki: https://wiki.postgresql.org/wiki/YUM_Installation#Configure_your_YUM_repository
.. _Let's Encrypt: https://letsencrypt.org/
