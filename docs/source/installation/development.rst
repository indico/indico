.. _install-dev:

Installation guide (development)
================================

Installing System Packages
--------------------------

Web assets such as JavaScript and SCSS files are compiled using `Webpack <https://webpack.js.org>`_, which
requires NodeJS to be present. You can find information on how to install NodeJS
`here <https://nodejs.org/en/download/package-manager/>`_.

Do not use the default NodeJS packages from your Linux distribution as they are usually outdated or come with
an outdated npm version.

Since only the latest Linux distributions include Python 3.12 in their package managers, we recommend installing
`pyenv <https://github.com/pyenv/pyenv-installer>`_ and then install the latest Python 3.12 version using
``pyenv install 3.12``.

.. tip::

    You can run ``pyenv doctor`` once you installed and enabled pyenv in order to see whether all dependencies are
    met. There's a good chance that you need to install some additional system packages beyond those listed below, and using
    this tool will tell you what exactly you need.

RPM-based distributions (Alma, Rocky, Fedora)
+++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: shell

    dnf install -y gcc redis libjpeg-turbo-devel libxslt-devel libxml2-devel \
        libffi-devel pcre-devel libyaml-devel redhat-rpm-config \
        postgresql postgresql-server postgresql-contrib libpq-devel pango
    systemctl start redis.service postgresql.service


Debian/Ubuntu
+++++++++++++

.. code-block:: shell

    apt install -y --install-recommends libxslt1-dev libxml2-dev libffi-dev libpcre3-dev \
        libyaml-dev build-essential redis-server postgresql libpq-dev libpango1.0-dev

Then on Debian::

    apt install -y libjpeg62-turbo-dev

And on Ubuntu::

    apt install -y libjpeg-turbo8-dev zlib1g-dev


macOS
+++++

We recommend that you use `Homebrew <https://brew.sh/>`_::

    brew install redis libjpeg libffi pcre libyaml postgresql pango
    brew services start postgresql
    brew services start redis


Creating the directory structure
--------------------------------

You will need a directory in your file system to store Indico as well as its data files (archives, etc...). Some
developers keep all their code inside a ``dev`` or ``code`` dir. We will assume ``dev`` here.

.. code-block:: shell

    mkdir -p ~/dev/indico/data

We will need a virtualenv where to run Indico::

    cd ~/dev/indico
    pyenv local 3.12
    python -m venv env

.. note::

    After setting the version with pyenv, it's a good idea to use ``python -V`` to ensure you are really running that
    particular Python version; depending on the shell you may need to restart your shell first.


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

    python -m venv maildump
    ./maildump/bin/pip install -U pip setuptools wheel
    ./maildump/bin/pip install maildump
    ./maildump/bin/maildump -p /tmp/maildump.pid

You'll then be able to access the message log at `<http://localhost:1080>`_.


Creating the DB
---------------

Linux
+++++

.. code-block:: shell

    sudo -u postgres createuser $USER --createdb
    sudo -u postgres createdb indico_template -O $USER
    sudo -u postgres psql indico_template -c "CREATE EXTENSION unaccent; CREATE EXTENSION pg_trgm;"
    createdb indico -T indico_template

macOS
+++++

If you are on macOS with PostgreSQL installed via Homebrew, you should not use ``sudo`` as that only works on Linux
systems where a system user named ``postgres`` exists. Use the following instead:

.. code-block:: shell

    createdb indico_template -O $USER
    psql indico_template -c "CREATE EXTENSION unaccent; CREATE EXTENSION pg_trgm;"
    createdb indico -T indico_template


.. _configuring-dev:

Configuring
-----------

Let's get into the Indico virtualenv::

    source ./env/bin/activate
    pip install -U pip setuptools wheel

    cd src
    pip install -e '.[dev]'
    npm ci

Then, follow the instructions given by the wizard::

    indico setup wizard --dev

You can then initialize the DB::

    indico db prepare

To build the locales, use:

.. code-block:: shell

    indico i18n compile indico

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
If you went with the default settings provided by the wizard it might be something like
``indico run -h 127.0.0.1 -p 8000 -q --enable-evalex``

It is also worth mentioning that when working on a plugin, it is necessary to run another webpack watcher
to build the plugin assets. That can be accomplished using the same command as above with an argument specifying
which plugin you want to build the assets for:

.. code-block:: shell

    ./bin/maintenance/build-assets.py plugin <plugin-directory> --dev --watch

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

    sudo dnf install nginx  # alma/rocky/fedora
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


Running the Unit Tests
----------------------

Indico comes with a comprehensive suite of unit tests. To run them, you will need to have PostgreSQL available. By default,
the tests expect a local server, but you can also use the a Docker-backed setup for a more standalone and isolated environment.

**Running tests with the default setup**

To run all tests, simply execute:

.. code-block:: shell

    pytest

You can also run a subset of tests by specifying the path or test name:

.. code-block:: shell

    pytest path/to/test_file.py
    pytest -k test_some_function

**Using the Docker-backed PostgreSQL for tests**

Indico provides a Docker-based PostgreSQL fixture for running tests without requiring a local PostgreSQL installation. To enable this,
set the ``INDICO_TEST_USE_DOCKER`` environment variable (to `yes`, `true` or `1`) before running the tests:

.. code-block:: shell

    INDICO_TEST_USE_DOCKER=1 pytest

This will automatically start a temporary PostgreSQL server in a Docker container for the duration of the test run. The container and
its data will be cleaned up automatically afterwards.

If you want to use a custom Docker daemon (for example, if Docker is not running on the default socket), you can set
``INDICO_TEST_USE_DOCKER`` to the Docker API URL, such as ``unix:///var/run/docker.sock`` or ``tcp://127.0.0.1:2375``.

**Notes:**

- Make sure Docker is installed and running on your system, and that your user has permission to access the Docker socket (you may need to be in the `docker` group);
- The first time you run the tests with Docker, the required PostgreSQL image will be pulled, which may take a few minutes.


**Using Podman instead of Docker**

If you prefer to use Podman as a drop-in replacement for Docker, you can do so with Indico's Docker-backed PostgreSQL fixture. Podman is
compatible with the Docker API, but you need to ensure that the Podman socket is available and that your user has permission to access it.

To use Podman for running the tests, set the ``INDICO_TEST_USE_DOCKER`` environment variable to the Podman socket URL. For example:

.. code-block:: shell

    INDICO_TEST_USE_DOCKER=unix:///run/user/$(id -u)/podman/podman.sock pytest

Make sure the Podman socket is running. You can start it with:

.. code-block:: shell

    systemctl --user start podman.socket

Or, if you are not using systemd user services, you can run:

.. code-block:: shell

    podman system service --time=0 unix:///run/user/$(id -u)/podman/podman.sock

**Notes:**

- The first test run may take longer as Podman will pull the required PostgreSQL image;
- Ensure your user has permission to access the Podman socket;
- The rest of the test setup and cleanup works the same as with Docker.
