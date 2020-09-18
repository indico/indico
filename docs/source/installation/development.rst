.. _install-dev:

Installation guide (development)
================================

Installing System Packages
--------------------------

Web assets such as JavaScript and SCSS files are compiled using `Webpack <https://webpack.js.org>`_, which
requires NodeJS to be present. You can find information on how to install NodeJS
`here <https://nodejs.org/en/download/package-manager/>`_.

Do not use the default NodeJS packages from your Linux distribution as they are usually outdated or come wit
an outdated npm version.

CentOS/Fedora
+++++++++++++

.. code-block:: shell

    yum install -y gcc redis python-devel python-virtualenv libjpeg-turbo-devel libxslt-devel libxml2-devel \
        libffi-devel pcre-devel libyaml-devel redhat-rpm-config \
        postgresql postgresql-server postgresql-contrib libpq-devel
    systemctl start redis.service postgresql.service


Debian/Ubuntu
+++++++++++++

.. code-block:: shell

    apt install -y --install-recommends python-dev python-virtualenv libxslt1-dev libxml2-dev libffi-dev libpcre3-dev \
        libyaml-dev build-essential redis-server postgresql libpq-dev

Then on Debian::

    apt install -y libjpeg62-turbo-dev

And on Ubuntu::

    apt install -y libjpeg-turbo8-dev zlib1g-dev


macOS
+++++

We recommend that you use `Homebrew <https://brew.sh/>`_::

    brew install python2 redis libjpeg libffi pcre libyaml postgresql
    brew services start postgresql
    pip install virtualenv

Note: Homebrew dropped support for the python2 formula at the end of 2019.
As an alternative you can install it directly using the latest commit::

    brew install https://raw.githubusercontent.com/Homebrew/homebrew-core/86a44a0a552c673a05f11018459c9f5faae3becc/Formula/python@2.rb


Creating the directory structure
--------------------------------

You will need a directory in your file system to store Indico as well as its data files (archives, etc...). Some
developers keep all their code inside a ``dev`` or ``code`` dir. We will assume ``dev`` here.

.. code-block:: shell

    mkdir -p ~/dev/indico/data

We will need a virtualenv where to run Indico::

    cd ~/dev/indico
    virtualenv env -p /usr/bin/python2.7


.. _cloning:

Cloning Indico
--------------

First, let's clone Indico's code base. If you're going to contribute back to the project, it's probably best if you
clone your own `GitHub fork of the project <https://help.github.com/articles/fork-a-repo/>`_ and set it as the origin::

    git clone git@github.com:<your-github-username>/indico.git src
    cd src
    git remote add upstream https://github.com/indico/indico.git
    cd ..

Otherwise, cloning the upstream repository as the origin should be enough::

    git clone https://github.com/indico/indico.git src

If you're going to be changing the standard Indico plugins and/or the documentation, you can also clone those::

    mkdir plugins
    git clone https://github.com/indico/indico-plugins.git plugins/base
    git clone https://github.com/indico/indico-user-docs.git user-docs


Setting up Maildump (recommended)
---------------------------------

Some actions in Indico trigger automatic e-mails. Those will normally have to be routed through an SMTP server.
This can become a problem if you're using production data and/or real e-mails, as users may end up being spammed
unnecessarily. This is why we advise that you include a fake SMTP server in your development setup.
`Maildump <https://github.com/ThiefMaster/maildump>`_ does exactly this and runs on Python. It should be quite simple
to set up::

    virtualenv maildump -p /usr/bin/python2.7
    ./maildump/bin/pip install -U pip setuptools
    ./maildump/bin/pip install maildump
    ./maildump/bin/maildump -p /tmp/maildump.pid

You'll then be able to access the message log at `<http://localhost:1080>`_.


Creating the DB
---------------

.. code-block:: shell

    sudo -u postgres createuser $USER --createdb
    sudo -u postgres createdb indico_template -O $USER
    sudo -u postgres psql indico_template -c "CREATE EXTENSION unaccent; CREATE EXTENSION pg_trgm;"
    createdb indico -T indico_template


.. _configuring-dev:

Configuring
-----------

Let's get into the Indico virtualenv::

    source ./env/bin/activate
    pip install -U pip setuptools

    cd src
    pip install -r requirements.dev.txt
    pip install -e .
    npm ci

Then, follow the instructions given by the wizard::

    indico setup wizard --dev

You can then initialize the DB::

    indico db prepare

To build the locales, use:

.. code-block:: shell

    indico i18n compile-catalog
    indico i18n compile-catalog-react

.. _run-dev:

Running Indico
--------------

You will need two shells running in parallel. The first one will run the webpack watcher, which compiles
the JavaScript and style assets every time you change them:

.. code-block:: shell

    ./bin/maintenance/build-assets.py indico --dev --watch

On the second one we'll run the Indico Development server:

.. code-block:: shell

    indico run -h <your-hostname> -q --enable-evalex

Double-check that your hostname matches that which has been set in the config file (by the wizard).

It is also worth mentioning that when working on a plugin, it is necessary to run another webpack watcher
to build the plugin assets. That can be accomplished using the same command as above with an argument specifying
which plugin you want to build the assets for:

.. code-block:: shell

    ./bin/maintenance/build-assets.py <plugin-name> --dev --watch

You can also build the assets for all the plugins:

.. code-block:: shell

    ./bin/maintenance/build-assets.py all-plugins --dev <plugins-directory>


Installing TeXLive (optional)
-----------------------------

If you need PDF generation in certain parts of Indico to work (e.g.
for contributions and the Book of Abstracts), you need LaTeX.  To
install it, follow the :ref:`LaTeX install guide <latex>`.


Using HTTPS through nginx (optional)
------------------------------------

If you wish to open your development server to others, then we highly recommend that you properly set HTTPS. While
you could do so directly at the development server, it's normally easier to proxy it through nginx and have it serve
static files as well.

You should obviously install nginx first::

    sudo yum install nginx  # centos/fedora
    sudo apt install nginx  # debian/ubuntu
    brew install nginx      # macOS

Here is an example of a ``nginx.conf`` you can use. It assumes your username is ``jdoe`` and the hostname is
``acme.example.org``::

    user jdoe users;
    worker_processes 4;
    error_log /var/log/nginx/error.log info;
    pid /run/nginx.pid;

    events {
        worker_connections 1024;
        use epoll;
    }

    http {
        access_log off;

        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;

        keepalive_timeout   75 20;
        types_hash_max_size 2048;
        ignore_invalid_headers on;

        connection_pool_size 256;
        client_header_buffer_size 10k;
        large_client_header_buffers 4 20k;
        request_pool_size 4k;
        client_max_body_size 2048m;

        proxy_buffers 32 32k;
        proxy_buffer_size 32k;
        proxy_busy_buffers_size 128k;

        gzip on;
        gzip_min_length 1100;
        gzip_buffers 4 8k;
        gzip_types text/plain text/css application/x-javascript;

        include             /etc/nginx/mime.types;
        default_type        application/octet-stream;

        server {
            listen [::]:80 ipv6only=off;
            server_name acme.example.org;

            access_log /var/log/nginx/acme.access_log combined;
            error_log /var/log/nginx/acme.error_log info;

            root /var/empty;

            return 302 https://$server_name$request_uri;
        }

        server {
            listen [::]:443 ipv6only=off http2;
            server_name acme.example.org;

            ssl on;
            ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
            ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA;
            ssl_prefer_server_ciphers on;
            ssl_certificate /home/jdoe/acme.crt;
            ssl_certificate_key /home/jdoe/acme.key;

            access_log /var/log/nginx/acme.ssl_access_log combined;
            error_log /var/log/nginx/acme.ssl_error_log info;

            root /var/empty;


            location ~ ^/(images|fonts)(.*)/(.+?)(__v[0-9a-f]+)?\.([^.]+)$ {
                alias /home/jdoe/dev/indico/src/indico/web/static/$1$2/$3.$5;
            }

            location ~ ^/(css|dist|images|fonts)/(.*)$ {
                alias /home/jdoe/dev/indico/src/indico/web/static/$1/$2;
            }

            location / {
                proxy_pass http://127.0.0.1:8000;
                proxy_set_header Host $server_name;
                proxy_set_header X-Forwarded-For $remote_addr;
                proxy_set_header X-Forwarded-Proto $scheme;
            }
        }
    }

This configuration also assumes you've already got a secret key and certificate stored in ``~/acme.key`` and
``acme.crt`` respectively. In most cases you will probably use a self-signed certificate. There are many guides on-line
on `how to generate a self-signed certificate <https://devcenter.heroku.com/articles/ssl-certificate-self>`_, so we will
not cover it here.

If you're using SELinux, you will need to set the following configuration options::

    sudo setsebool -P httpd_can_network_connect 1
    sudo setsebool -P httpd_read_user_content 1

Uploading large files will probably fail unless you do::

    sudo chown -R jdoe:nginx /var/lib/nginx/tmp/

The Indico dev server should be run with the ``--proxy`` option::

    indico run -h 127.0.0.1 -p 8000 -q --enable-evalex --url https://acme.example.org --proxy

You can then start nginx and access ``https://acme.example.org`` directly.
