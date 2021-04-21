Apache
======

.. warning::

    CentOS 8 with Apache is **not supported**, as some important packages
    (mod_xsendfile and mod_proxy_uwsgi) are not (yet?) available for
    CentOS 8 in first-party repos. Once they are in EPEL, there is a
    good chance this guide will work as expected.


.. _centos-apache-epel:

1. Enable EPEL
--------------

.. code-block:: shell

    yum install -y epel-release

.. note::

    If you use CC7, EPEL is already enabled and this step is not necessary


.. _centos-apache-pkg:

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

.. code-block:: shell

    yum install -y postgresql13 postgresql13-server postgresql13-libs postgresql13-devel postgresql13-contrib
    yum install -y git gcc make redis httpd mod_proxy_uwsgi mod_ssl mod_xsendfile
    yum install -y libjpeg-turbo-devel libxslt-devel libxml2-devel libffi-devel pcre-devel libyaml-devel zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel xz xz-devel libffi-devel findutils libuuid-devel
    /usr/pgsql-13/bin/postgresql-13-setup initdb
    systemctl start postgresql-13.service redis.service


.. _centos-apache-db:

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


.. _centos-apache-web:

4. Configure uWSGI & Apache
---------------------------

The default uWSGI and Apache configuration files should work fine in
most cases.

.. code-block:: shell

    cat > /etc/uwsgi-indico.ini <<'EOF'
    [uwsgi]
    uid = indico
    gid = apache
    umask = 027

    processes = 4
    enable-threads = true
    socket = 127.0.0.1:8008
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
    Group=apache
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

    cat > /etc/httpd/conf.d/indico-sslredir.conf <<'EOF'
    <VirtualHost *:80>
        ServerName YOURHOSTNAME
        RewriteEngine On
        RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]
    </VirtualHost>
    EOF

    cat > /etc/httpd/conf.d/indico.conf <<'EOF'
    <VirtualHost *:443>
        ServerName YOURHOSTNAME
        DocumentRoot "/var/empty/apache"

        SSLEngine               on
        SSLCertificateFile      /etc/ssl/indico/indico.crt
        SSLCertificateChainFile /etc/ssl/indico/indico.crt
        SSLCertificateKeyFile   /etc/ssl/indico/indico.key

        SSLProtocol             all -SSLv3 -TLSv1 -TLSv1.1
        SSLCipherSuite          ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
        SSLHonorCipherOrder     off
        SSLSessionTickets       off

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
        ProxyPass / uwsgi://127.0.0.1:8008/

        <Directory /opt/indico>
            AllowOverride None
            Require all granted
        </Directory>
    </VirtualHost>
    EOF


Now enable the uwsgi proxy module in apache:

.. code-block:: shell

    echo 'LoadModule proxy_uwsgi_module modules/mod_proxy_uwsgi.so' > /etc/httpd/conf.modules.d/proxy_uwsgi.conf


.. _centos-apache-ssl:

5. Create a TLS Certificate
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


.. _centos-apache-selinux:

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
    (filecon "/opt/indico/log/apache(/.*)?" any (system_u object_r httpd_log_t ((s0)(s0))))
    EOF
    semodule -i /tmp/indico.cil


.. _centos-apache-install:

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
    Group=apache
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

    useradd -rm -g apache -d /opt/indico -s /bin/bash indico
    su - indico

The first thing to do is installing pyenv - we use it to install the latest Python version
as not all Linux distributions include it and like this Indico can benefit from the latest
Python features.

.. code-block:: shell

    curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash

    cat >> ~/.bashrc <<'EOF'
    export PATH="/opt/indico/.pyenv/bin:$PATH"
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


.. _centos-apache-config:

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

    mkdir ~/log/apache
    chmod go-rwx ~/* ~/.[^.]*
    chmod 710 ~/ ~/archive ~/cache ~/log ~/tmp
    chmod 750 ~/web ~/.venv
    chmod g+w ~/log/apache
    restorecon -R ~/
    echo -e "\nSTATIC_FILE_METHOD = 'xsendfile'" >> ~/etc/indico.conf


9. Create database schema
-------------------------

Finally you can create the database schema and switch back to *root*:

.. code-block:: shell

    indico db prepare
    exit


.. _centos-apache-launch:

10. Launch Indico
-----------------

You can now start Indico and set it up to start automatically when the
server is rebooted:

.. code-block:: shell

    systemctl restart httpd.service indico-celery.service indico-uwsgi.service
    systemctl enable httpd.service postgresql-13.service redis.service indico-celery.service indico-uwsgi.service


.. _centos-apache-firewall:

11. Open the Firewall
---------------------

.. code-block:: shell

    firewall-cmd --permanent --add-port 443/tcp --add-port 80/tcp
    firewall-cmd --reload

.. note::

    This is only needed if you use CC7 as CentOS 7/8 have no firewall enabled
    by default


.. _centos-apache-letsencrypt:

12. Optional: Get a Certificate from Let's Encrypt
--------------------------------------------------

To avoid ugly TLS warnings in your browsers, the easiest option is to
get a free certificate from Let's Encrypt. We also enable the cronjob
to renew it automatically:


.. code-block:: shell

    yum install -y python-certbot-apache
    certbot --apache --rsa-key-size 4096 --no-redirect --staple-ocsp -d YOURHOSTNAME
    rm -rf /etc/ssl/indico
    systemctl start certbot-renew.timer
    systemctl enable certbot-renew.timer


.. _centos-apache-user:

13. Create an Indico user
-------------------------

Access ``https://YOURHOSTNAME`` in your browser and follow the steps
displayed there to create your initial user.


.. _centos-apache-latex:

14. Install TeXLive
-------------------

Follow the :ref:`LaTeX install guide <latex>` to install TeXLive so
Indico can generate PDF files in various places.


.. _centos-apache-shib:

Optional: Shibboleth
--------------------

If your organization uses Shibboleth/SAML-based SSO, follow these steps to use
it in Indico:

1. Install Shibboleth
^^^^^^^^^^^^^^^^^^^^^

Add the Shibboleth yum repository:

.. note::

    If you use CC7, Shibboleth is already available and there is no
    need to add the repo manually.

If you use CentOS 7:

.. code-block:: shell

    curl -fsSL -o /etc/yum.repos.d/shibboleth.repo 'https://shibboleth.net/cgi-bin/sp_repo.cgi?platform=CentOS_7'

If you use CentOS 8:

.. code-block:: shell

    curl -fsSL -o /etc/yum.repos.d/shibboleth.repo 'https://shibboleth.net/cgi-bin/sp_repo.cgi?platform=CentOS_8'

Now install Shibboleth itself.  When prompted to accept the GPG key
of the Shibboleth yum repo, confirm the prompt.

.. code-block:: shell

    setsebool httpd_can_network_connect 1
    yum install -y shibboleth xmltooling-schemas opensaml-schemas

2. Configure Shibboleth
^^^^^^^^^^^^^^^^^^^^^^^

This is outside the scope of this documentation and depends on your
environment (Shibboleth, SAML, ADFS, etc).  Please contact whoever
runs your SSO infrastructure if you need assistance.

3. Enable Shibboleth in Apache
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Add the following code to your ``/etc/httpd/conf.d/indico.conf`` right
before the ``AliasMatch`` lines:

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
