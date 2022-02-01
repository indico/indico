nginx
=====

.. include:: ../_sso_note.rst

1. Enable EPEL
--------------

.. code-block:: shell

    yum install -y epel-release

.. note::

    If you use CC7, EPEL is already enabled and this step is not necessary


2. Install Packages
-------------------

If you are on CentOS 7, edit ``/etc/yum.repos.d/CentOS-Base.repo`` and add
``exclude=postgresql*`` to the ``[base]`` and ``[updates]`` sections, as
described in the `PostgreSQL wiki`_ and then run these commands:

.. code-block:: shell

    yum install -y centos-release-scl
    yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm

If you are on CentOS 8, run this instead:

.. code-block:: shell

    dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm
    dnf -qy module disable postgresql
    yum config-manager --set-enabled powertools

Now install all the required packages:

.. code-block:: shell

    yum install -y postgresql13 postgresql13-server postgresql13-libs postgresql13-devel postgresql13-contrib
    yum install -y git gcc make redis nginx
    yum install -y libjpeg-turbo-devel libxslt-devel libxml2-devel libffi-devel pcre-devel libyaml-devel zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel xz xz-devel findutils libuuid-devel
    /usr/pgsql-13/bin/postgresql-13-setup initdb
    systemctl start postgresql-13.service redis.service


3. Create a Database
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


4. Configure uWSGI & nginx
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


5. Create a TLS Certificate
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


6. Configure SELinux
--------------------

Indico works fine with SELinux enabled, but you need to load a custom
SELinux module to tell SELinux about Indico's files and how they
should be handled.

.. code-block:: shell

    cat > /tmp/indico.cil <<'EOF'
    ; define custom type that logrotate can access
    (type indico_log_t)
    (typeattributeset file_type (indico_log_t))
    (typeattributeset logfile (indico_log_t))
    (roletype object_r indico_log_t)

    ; allow logrotate to reload systemd services
    (allow logrotate_t init_t (service (start)))
    (allow logrotate_t policykit_t (dbus (send_msg)))
    (allow policykit_t logrotate_t (dbus (send_msg)))

    ; make sure the uwsgi socket is writable by the webserver
    (typetransition unconfined_service_t usr_t sock_file "uwsgi.sock" httpd_sys_rw_content_t)
    (filecon "/opt/indico/web/uwsgi\.sock" socket (system_u object_r httpd_sys_rw_content_t ((s0)(s0))))

    ; set proper types for our log dirs
    (filecon "/opt/indico/log(/.*)?" any (system_u object_r indico_log_t ((s0)(s0))))
    (filecon "/opt/indico/log/nginx(/.*)?" any (system_u object_r httpd_log_t ((s0)(s0))))
    EOF
    semodule -i /tmp/indico.cil


7. Install Indico
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
    export PATH="$PATH:/usr/pgsql-13/bin"
    echo 'source ~/.venv/bin/activate' >> ~/.bashrc
    pip install wheel
    pip install uwsgi
    pip install indico


8. Configure Indico
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
    restorecon -R ~/
    echo -e "\nSTATIC_FILE_METHOD = ('xaccelredirect', {'/opt/indico': '/.xsf/indico'})" >> ~/etc/indico.conf


9. Create database schema
-------------------------

Finally you can create the database schema and switch back to *root*:

.. code-block:: shell

    indico db prepare
    exit


10. Launch Indico
-----------------

You can now start Indico and set it up to start automatically when the
server is rebooted:

.. code-block:: shell

    systemctl restart nginx.service indico-celery.service indico-uwsgi.service
    systemctl enable nginx.service postgresql-13.service redis.service indico-celery.service indico-uwsgi.service


11. Open the Firewall
---------------------

.. code-block:: shell

    firewall-cmd --permanent --add-port 443/tcp --add-port 80/tcp
    firewall-cmd --reload

.. note::

    This is only needed if you use CC7 as CentOS 7/8 have no firewall enabled
    by default


12. Optional: Get a Certificate from Let's Encrypt
--------------------------------------------------

To avoid ugly TLS warnings in your browsers, the easiest option is to
get a free certificate from Let's Encrypt. We also enable the cronjob
to renew it automatically:


.. code-block:: shell

    yum install -y python-certbot-nginx
    certbot --nginx --rsa-key-size 4096 --no-redirect --staple-ocsp -d YOURHOSTNAME
    rm -rf /etc/ssl/indico
    systemctl start certbot-renew.timer
    systemctl enable certbot-renew.timer


13. Create an Indico user
-------------------------

Access ``https://YOURHOSTNAME`` in your browser and follow the steps
displayed there to create your initial user.


14. Install TeXLive
-------------------

Follow the :ref:`LaTeX install guide <latex>` to install TeXLive so
Indico can generate PDF files in various places.


.. _PostgreSQL wiki: https://wiki.postgresql.org/wiki/YUM_Installation#Configure_your_YUM_repository
.. _Let's Encrypt: https://letsencrypt.org/
