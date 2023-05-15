nginx
=====

.. include:: ../_sso_note.rst

1. Install Packages
-------------------

PostgreSQL and nginx are installed from their upstream repos to get
much more recent versions.

.. code-block:: shell

    apt install -y lsb-release wget curl gnupg
    echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
    echo "deb http://nginx.org/packages/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/ $(lsb_release -cs) nginx" > /etc/apt/sources.list.d/nginx.list
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
    wget --quiet -O - https://nginx.org/keys/nginx_signing.key | apt-key add -
    apt update
    apt install -y --install-recommends postgresql-13 libpq-dev nginx libxslt1-dev libxml2-dev libffi-dev libpcre3-dev libyaml-dev libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libncurses5-dev libncursesw5-dev xz-utils liblzma-dev uuid-dev build-essential redis-server


If you use Debian, run this command:

.. code-block:: shell

    apt install -y libjpeg62-turbo-dev


If you use Ubuntu, run this instead:

.. code-block:: shell

    apt install -y libjpeg-turbo8-dev zlib1g-dev

Afterwards, make sure the services you just installed are running:

.. code-block:: shell

    systemctl start postgresql.service redis-server.service
    pg_ctlcluster 13 main start


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


3. Configure uWSGI & nginx
--------------------------

The default uWSGI and nginx configuration files should work fine in
most cases.

.. code-block:: shell

    cat > /etc/uwsgi-indico.ini <<'EOF'
    [uwsgi]
    uid = indico
    gid = nginx
    umask = 027

    processes = 4
    enable-threads = true
    chmod-socket = 770
    chown-socket = indico:nginx
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
    Group=nginx
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

      ssl_certificate           /etc/ssl/indico/indico.crt;
      ssl_certificate_key       /etc/ssl/indico/indico.key;
      ssl_dhparam               /etc/ssl/indico/ffdhe2048;

      ssl_session_timeout       1d;
      ssl_session_cache         shared:SSL:10m;
      ssl_session_tickets       off;
      ssl_protocols             TLSv1.2 TLSv1.3;
      ssl_ciphers               ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
      ssl_prefer_server_ciphers off;

      access_log            /opt/indico/log/nginx/access.log combined;
      error_log             /opt/indico/log/nginx/error.log;

      if ($host != $server_name) {
        rewrite ^/(.*) https://$server_name/$1 permanent;
      }

      location /.xsf/indico/ {
        internal;
        alias /opt/indico/;
      }

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

      location / {
        root /var/empty/nginx;
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


4. Create a TLS Certificate
---------------------------

First, create the folders for the certificate/key and set restrictive
permissions on them:

.. code-block:: shell

    mkdir /etc/ssl/indico
    chown root:root /etc/ssl/indico/
    chmod 700 /etc/ssl/indico

We also use a strong set of pre-generated DH params (ffdhe2048 from RFC7919)
as suggested in Mozilla's TLS config recommendations:

.. code-block:: shell

    cat > /etc/ssl/indico/ffdhe2048 <<'EOF'
    -----BEGIN DH PARAMETERS-----
    MIIBCAKCAQEA//////////+t+FRYortKmq/cViAnPTzx2LnFg84tNpWp4TZBFGQz
    +8yTnc4kmz75fS/jY2MMddj2gbICrsRhetPfHtXV/WVhJDP1H18GbtCFY2VVPe0a
    87VXE15/V8k1mE8McODmi3fipona8+/och3xWKE2rec1MKzKT0g6eXq8CrGCsyT7
    YdEIqUuyyOP7uWrat2DX9GgdT0Kj3jlN9K5W7edjcrsZCwenyO4KbXCeAvzhzffi
    7MA0BM0oNC9hkXL+nOmFg/+OTxIy7vKBg8P+OxtMb61zO7X8vC7CIAXFjvGDfRaD
    ssbzSibBsu/6iGtCOGEoXJf//////////wIBAg==
    -----END DH PARAMETERS-----
    EOF

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

You are now ready to install Python 3.9:

Run ``pyenv install --list | egrep '^\s*3\.9\.'`` to check for the latest available version and
then install it and set it as the active Python version (replace ``x`` in both lines).

.. code-block:: shell

    pyenv install 3.9.x
    pyenv global 3.9.x

This may take a while since pyenv needs to compile the specified Python version. Once done, you
may want to use ``python -V`` to confirm that you are indeed using the version you just installed.

You are now ready to install Indico:

.. code-block:: shell

    python -m venv --upgrade-deps --prompt indico ~/.venv
    source ~/.venv/bin/activate
    echo 'source ~/.venv/bin/activate' >> ~/.bashrc
    pip install wheel
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

    mkdir ~/log/nginx
    chmod go-rwx ~/* ~/.[^.]*
    chmod 710 ~/ ~/archive ~/cache ~/log ~/tmp
    chmod 750 ~/web ~/.venv
    chmod g+w ~/log/nginx
    echo -e "\nSTATIC_FILE_METHOD = ('xaccelredirect', {'/opt/indico': '/.xsf/indico'})" >> ~/etc/indico.conf


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

    systemctl restart nginx.service indico-celery.service indico-uwsgi.service
    systemctl enable nginx.service postgresql.service redis-server.service indico-celery.service indico-uwsgi.service


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


To avoid ugly TLS warnings in your browsers, the easiest option is to
get a free certificate from Let's Encrypt. We also enable the cronjob
to renew it automatically:


.. code-block:: shell

    apt install -y python-certbot-nginx
    certbot --nginx --rsa-key-size 4096 --no-redirect --staple-ocsp -d YOURHOSTNAME
    rm -rf /etc/ssl/indico
    systemctl start certbot.timer
    systemctl enable certbot.timer


10. Create an Indico user
-------------------------

Access ``https://YOURHOSTNAME`` in your browser and follow the steps
displayed there to create your initial user.


11. Install TeXLive
-------------------

Follow the :ref:`LaTeX install guide <latex>` to install TeXLive so
Indico can generate PDF files in various places.


.. _PostgreSQL wiki: https://wiki.postgresql.org/wiki/YUM_Installation#Configure_your_YUM_repository
.. _Let's Encrypt: https://letsencrypt.org/
