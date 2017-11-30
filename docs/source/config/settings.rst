Settings
========

``indico.conf`` is Indico's main configuration file. Its initial version
is usually generated when running ``indico setup wizard`` as described in
the Installation Guide, but depending on the setup it should be modified
later.

The config file is loaded from the path specified in the ``INDICO_CONFIG``
environment variable; if no such path is set, the config file (or a symlink
to it) is searched in the following places, in order:

- ``<indico_package_path>/indico.conf`` (development setups only)
- ``~/.indico.conf``
- ``/etc/indico.conf``

The file is executed as a Python module, so anything that is valid Python
2.7 code can be used in it. When defining temporary variables that are not
config options, their name should be prefixed with an underscore; otherwise
you will get a warning about unknowing config options being defined.


.. _settings-auth:

Authentication
--------------

.. data:: LOCAL_IDENTITIES

    This setting controls whether local Indico accounts are available.
    If no centralized authentication infrastructure (e.g. LDAP, OAuth,
    or another kind of SSO) is used, local accounts are the only way
    of logging in to Indico.

    Default: ``True``

.. data:: LOCAL_REGISTRATION

    This setting controls whether people accessing Indico can create a
    new account.  Admins can always create new local accounts, regardless
    of this setting.

    This setting is only taken into account if :data:`LOCAL_IDENTITIES`
    are enabled.

    Default: ``True``

.. data:: LOCAL_MODERATION

    This setting controls whether a new registration needs to be approved
    by an admin before the account is actually created.

    This setting is only taken into account if :data:`LOCAL_IDENTITIES`
    and :data:`LOCAL_REGISTRATION` are enabled.

    Default: ``False``

.. data:: EXTERNAL_REGISTRATION_URL

    The URL to an external page where people can register an account that
    can then be used to login to Indico (usually via LDAP/SSO).

    This setting is only taken into account if :data:`LOCAL_IDENTITIES`
    are disabled.

    Default: ``None``

.. data:: AUTH_PROVIDERS

    A dict defining `Flask-Multipass`_ authentication providers used
    by Indico.  The dict specified here is passed to the
    ``MULTIPASS_AUTH_PROVIDERS`` setting of Flask-Multipass.

    Default: ``{}``

.. data:: IDENTITY_PROVIDERS

    A dict defining `Flask-Multipass`_ identity providers used by Indico
    to look up user information based on the data provided by an
    authentication provider.  The dict specified here is passed to the
    ``MULTIPASS_IDENTITY_PROVIDERS`` setting of Flask-Multipass.

    Default: ``{}``

.. data:: PROVIDER_MAP

    If not specified, authentication and identity providers with the
    same name are linked automatically.  The dict specified here is
    passed to the ``MULTIPASS_PROVIDER_MAP`` setting of Flask-Multipass.

    Default: ``{}``


Cache
-----

.. data:: CACHE_BACKEND

    The backend used for caching. Valid backends are ``redis``,
    ``files``, and ``memcached``.

    To use the ``redis`` backend (recommended), you need to set
    :data:`REDIS_CACHE_URL` to the URL of your Redis instance.

    With the ``files`` backend, cache data is stored in :data:`CACHE_DIR`,
    which always needs to be set, even when using a different cache
    backend since Indico needs to cache some data on disk.

    To use the ``memcached`` backend, you need to install the
    ``python-memcached`` package from PyPI and set :data:`MEMCACHED_SERVERS`
    to a list containing at least one memcached server.

    .. note::

        We only test Indico with the ``redis`` cache backend. While
        the other backends should work, we make no guarantees as
        they are not actively being used or tested.

    Default: ``'files'``

.. data:: REDIS_CACHE_URL

    The URL of the redis server to use with the ``redis`` cache backend.

    If the Redis server requires authentication, use a URL like this:
    ``redis://unused:password@127.0.0.1:6379/1``

    If no authentication is used (usually the case with a local Redis
    server), you can omit the user/password part:
    ``redis://127.0.0.1:6379/1``

    Default: ``None``

.. data:: MEMCACHED_SERVERS

    The list of memcached servers (each entry is an ``ip:port`` string)
    to use with the ``memcached`` cache backend.

    Default: ``[]``


Celery
------

.. data:: CELERY_BROKER

    The URL of the Celery broker (usually Redis of AMQP) used for
    communication between Indico and the Celery background workers.

    We recommend using Redis as it is the easiest option, but you can
    check the `Celery documentation on brokers`_ for more information
    on the other possible brokers.

    Default: ``None``

.. data:: CELERY_RESULT_BACKEND

    The URL of the Celery result backend. If not set, the same backend
    as the broker is used.  Indico currently does not use task results,
    and we recommend leaving this setting at its default.

    Default: ``None``

.. data:: CELERY_CONFIG

    A dict containing additional Celery settings.

    .. warning::

        This is an advanced setting that is rarely needed and we do not
        recommend using it unless you know exactly what you are doing!
        Changing Celery settings may break things or result in tasks not
        being executed without other changes (such as running additional
        celery workers on different queues).

    One use case for this setting is routing certain tasks to a different
    queue, and then running multiple Celery workers for these queues.

    .. code-block:: python

        CELERY_CONFIG = {
            'task_routes': {
                'indico_livesync.task.scheduled_update': {'queue': 'livesync'},
            }
        }

    Default: ``{}``

.. data:: SCHEDULED_TASK_OVERRIDE

    A dict overriding the task schedule for specific tasks.

    By default, all periodic tasks are enabled and use a schedule which
    we consider useful for most cases.  Using this setting, you can
    override the default schedule.

    The dict key is the name of the task and the value can be one of
    the following:

    - ``None`` or ``False`` -- disables the task completely
    - A dictionary, as described in the `Celery documentation on periodic tasks`_.
      The ``task`` should not be specified, as it is set automatically.
    - A :class:`~datetime.timedelta` or :class:`~celery.schedules.crontab`
      object which will just override the schedule without changing any
      other options of the task.  Both classes are available in the config
      file by default.

    .. note::

        Use ``indico celery inspect registered`` to get a list of task
        names.  Celery must be running for this command to work.

    Default: ``{}``


Customization
-------------

.. data:: CUSTOMIZATION_DIR

    The base path to the directory containing customizations for your
    Indico instance.

    It is possible to override specific templates and add CSS and
    JavaScript for advanced customizations.  When using this, be
    advised that depending on the modifications you perform things
    may break after an Indico update.  Make sure to test all your
    modifications whenever you update Indico!

    To include custom CSS and JavaScript, simply put ``*.scss`` and
    ``*.js`` files into ``<CUSTOMIZATION_DIR>/scss`` / ``<CUSTOMIZATION_DIR>/js``.
    If there are multiple files, they will be included in alphabetical
    order, so prefixing them with a number (e.g. ``00-base.scss``, ``10-events.scss``)
    is a good idea.

    Static files may be added in ``<CUSTOMIZATION_DIR>/static``.  They can be
    referenced in templates through the ``assets.custom`` endpoint.

    For template customizations, see the description of :data:`CUSTOMIZATION_DEBUG`
    as this setting is highly recommended to figure out where exactly to
    put customized templates.

    Here is an example for a template customization that includes a
    custom asset and uses inheritance to avoid having to replace the
    whole template:

    .. code-block:: jinja

        {% extends '~footer.html' %}

        {% block footer_logo %}
            {%- set filename = 'cern_small_light.png' if dark else 'cern_small.png' -%}
            <a href="https://home.cern/" class="footer-logo">
                <img src="{{ url_for('assets.custom', filename=filename) }}" alt="CERN">
            </a>
        {% endblock %}

    Default: ``None``

.. data:: CUSTOMIZATION_DEBUG

    Whether to log details for all customizable templates the first time
    they are accessed.  The log message contains the path where you need
    to store the template; this path is relative to
    ``<CUSTOMIZATION_DIR>/templates/``.

    The log message also contains the full path of the original template
    in case you decide to copy it.
    However, instead of copying templates it is better to use Jinja
    inheritance where possible.  To make this easier the log entry contains
    a "reference" path that can be used to reference the original template
    from the customized one.

    Default: ``False``

.. data:: HELP_URL

    The URL used for the "Help" link in the footer.

    Default: ``'https://learn.getindico.io'``

.. data:: LOGO_URL

    The URL to a custom logo.  If unset, the default Indico logo is used.

    Default: ``None``

.. data:: CUSTOM_COUNTRIES

    A dict with country name overrides.  This can be useful if the official
    ISO name of a country does not match what your Indico instance's target
    audience expects for a country, e.g. due to political situations.

    .. code-block:: python

        CUSTOM_COUNTRIES = {'KP': 'North Korea'}

    Default: ``{}``


Database
--------

.. data:: SQLALCHEMY_DATABASE_URI

    The URI used to connect to the PostgreSQL database.  For a local database,
    you can usually omit everything besides the database name:
    ``postgresql:///indico``

    If the database requires authentication and/or runs on a separate host,
    this form should be used: ``postgresql://user:password@hostname/dbname``

.. data:: SQLALCHEMY_POOL_SIZE

    This setting configures SQLAlchemy's connection pool.
    For details, check the `Flask-SQLAlchemy documentation`_.

    Default: ``5``

.. data:: SQLALCHEMY_POOL_RECYCLE

    This setting configures SQLAlchemy's connection pool.
    For details, check the `Flask-SQLAlchemy documentation`_.

    Default: ``120``

.. data:: SQLALCHEMY_POOL_TIMEOUT

    This setting configures SQLAlchemy's connection pool.
    For details, check the `Flask-SQLAlchemy documentation`_.

    Default: ``10``


Development
-----------

.. warning::

    Do not turn on development settings in production.  While we are not
    aware of serious security issues caused by these settings, they may
    slow down Indico or remove redundancies and thus make Indico not as
    stable as one would expect it to be in a production environment.

.. data:: DEBUG

    Enables debugging mode.  If enabled, assets are not minified, error
    messages are more verbose and various other features are configured
    in a developer-friendly way.

    **Do not enable debug mode in production.**

    Default: ``False``

.. data:: DB_LOG

    Enables real-time database query logging.  When enabled, all database
    queries are sent to a socket where they can be read by the ``db_log.py``
    script.  To use the database logger, run ``bin/utils/db_log.py`` (only
    available when running Indico from a Git clone) in a separate terminal
    and all requests and verbose queries will be displayed there.

    Default: ``False``

.. data:: PROFILE

    Enables the Python profiler.  The profiler output is stored in
    ``<TEMP_DIR>/*.prof``.

    Default: ``False``

.. data:: SMTP_USE_CELERY

    If disabled, emails will be sent immediately instead of being
    handed to a Celery background worker.  This is often more convenient
    during development as you do not need to run a Celery worker while still
    receiving emails sent from Indico.
    Disabling it may result in emails not being sent if the mail server is
    unavailable or some other failure happens during email sending.  Because
    of this, the setting should never be disabled in a production environment.

    Default: ``True``

.. data:: COMMUNITY_HUB_URL

    The URL of the community hub. This should only be changed when using a local
    instance of Mereswine to debug the interface between Indico and Mereswine.

    Default: ``'https://hub.getindico.io'``


Directories
-----------

.. data:: ASSETS_DIR

    The directory in which built assets are stored. Must be accessible
    by the web server.

    Default: ``'/opt/indico/assets'``

.. data:: CACHE_DIR

    The directory in which various data is cached temporarily. Must be
    accessible by the web server.

    Default: ``'/opt/indico/cache'``

.. data:: LOG_DIR

    The directory in which log files are stored. Can be overridden by
    using absolute paths in ``logging.yaml``.

    Default: ``'/opt/indico/log'``

.. data:: TEMP_DIR

    The directory in which various temporary files are stored. Must be
    accessible by the web server.

    Default: ``'/opt/indico/cache'``


Emails
------

.. data:: SMTP_SERVER

    The hostname and port of the SMTP server used for sending emails.

    Default: ``('localhost', 25)``

.. data:: SMTP_LOGIN

    The username to send if the SMTP server requires authentication.

    Default: ``None``

.. data:: SMTP_PASSWORD

    The password to send if the SMTP server requires authentication.

    Default: ``None``

.. data:: SMTP_USE_TLS

    If enabled, STARTTLS will be used to use an encrypted SMTP connection.

    Default: ``False``

.. data:: SMTP_TIMEOUT

    The timeout in seconds after which a connection attempt to the SMTP
    server is aborted.

    Default: ``30``

.. data:: NO_REPLY_EMAIL

    The email address used when sending emails to users to which they
    should not reply.

    Default: ``None``

.. data:: PUBLIC_SUPPORT_EMAIL

    The email address that is shown to users on the "Contact" page.

    Default: ``None``

.. data:: SUPPORT_EMAIL

    The email address of the technical manager of the Indico instance.
    Emails about unhandled errors/exceptions are sent to this address.

    Default: ``None``


LaTeX
-----

.. data:: XELATEX_PATH

    The full path to the ``xelatex`` program of `TeXLive`_.

    If it is installed in a directory in your ``$PATH``, specifying its
    name without a path is sufficient.

    Default: ``xelatex``

.. data:: STRICT_LATEX

    Enables strict mode for LaTeX rendering, in which case a non-zero
    status code is considered failure.

    LaTeX is rather generous when it comes to using a non-zero exit code.
    For example, having an oversized image in an abstract is enough to
    cause one.  It is generally not a good idea to enable strict mode as
    this will result in PDF generation to fail instead of creating a PDF
    that looks slightly uglier (e.g. a truncated image) than one that would
    succeed without a non-zero status code.

    Default: ``False``


Logging
-------

.. data:: LOGGING_CONFIG_FILE

    The path to the logging config file.  Unless an absolute path is specified,
    the path is relative to the location of the Indico config file after
    resolving symlinks.

    Default: ``'logging.yaml'``

.. data:: SENTRY_DSN

    If you use `Sentry`_ for logging warnings/errors, you can specify the
    connection string here.

    Default: ``None``

.. data:: SENTRY_LOGGING_LEVEL

    The minimum level a log record needs to have to be sent to Sentry.
    If you do not care about warnings, set this to ``'ERROR'``.

    Default: ``'WARNING'``


Security
--------

.. data:: SECRET_KEY

    The secret key used to sign tokens in URLs.  It must be kept secret
    under all circumstances.

    When using Indico on a cluster of more than one worker, all machines
    need to have the same secret key.

    The initial key is generated by the setup wizard, but if you have to
    regenerate it, the best way of doing so is running this snippet on a
    shell:  ``python -c 'import os; print repr(os.urandom(32))'``

    Default: ``None``

.. data:: SESSION_LIFETIME

    The duration of inactivity after which a session and its session cookie
    expires.  If set to ``0``, the session cookie will be cleared when the
    browser is closed.

    Default: ``86400 * 31``


Storage
-------

.. data:: STORAGE_BACKENDS

    The list of backends that can be used to store/retrieve files.

    Indico needs to store various files such as event attachments somewhere.
    By default only a filesystem based storage backend is available, but
    plugins could add additional backends.  You can define multiple backends,
    but once a backend has been used, you **MUST NOT** remove it or all
    files stored in that backend will become unavailable.

    To define a filesystem-based backend, use the string ``fs:/base/path``.
    If you stopped using a backend, you can switch it to read-only mode by
    using ``fs-readonly:`` instead of ``fs:``

    Other backends may accept different options - see the documentation of these
    backends for details.

    Default: ``{'default': 'fs:/opt/indico/archive'}``

.. data:: ATTACHMENT_STORAGE

    The name of the storage backend used to store all kinds of attachments.
    Anything in this backend is write-once, i.e. once stored, files in it
    are never modified or deleted.

    Changing this only affects new uploads; existing files are taken from
    the backend that was active when they were uploaded -- which is also
    why you must not remove a backend from :data:`STORAGE_BACKENDS` once
    it has been used.

    Default: ``'default'``

.. data:: STATIC_SITE_STORAGE

    The name of the storage backend used to store "offline copies" of
    events.  Files are written to this backend when generating an offline
    copy and deleted after a certain amount of time.

    If not set, the :data:`ATTACHMENT_STORAGE` backend is used.

    Default: ``None``


System
------

.. data:: BASE_URL

    This is the URL through which Indico is accessed by users.  For
    production systems this should be an ``https://`` URL and your
    web server should redirect all plain HTTP requests to HTTPs.

    Default: ``None``

.. data:: USE_PROXY

    This setting controls whether Indico runs behind a proxy or load
    balancer and should honor headers such as ``X-Forwarded-For`` to
    get the real IP address of the users accessing it.

    The headers taken into account are:

    - ``X-Forwarded-For`` -- the IP address of the user
    - ``X-Forwarded-Proto`` -- the protocol used by the user
    - ``X-Forwarded-Host`` -- the hostname as specified in :data:`BASE_URL` (can
      be omitted if the ``Host`` header is correct)

    .. warning::

        This setting **MUST NOT** be enabled if the server is
        accessible directly by untrusted clients without going through
        the proxy or users will be able to spoof their IP address by
        sending a custom ``X-Forwarded-For`` header.  You need to
        configure your firewall so only requests coming from your proxy
        or load balancer are allowed.

    Default: ``False``

.. data:: ROUTE_OLD_URLS

    If you migrated from an older Indico version (v1.x), enable this
    option to redirect from the legacy URLs so external links keep
    working.

    Default: ``False``

.. data:: STATIC_FILE_METHOD

    This setting controls how static files (like attachments) are
    sent to clients.

    Web servers are very good at doing this; much better and more efficient
    than Indico or the WSGI container, so this should be offloaded to your
    web server using this setting.

    When using Apache with ``mod_xsendfile`` or lighttpd, set this to
    ``'xsendfile'`` and of course enable xsendfile in your Apache config.

    When using nginx, set this to ``('xaccelredirect', {'/opt/indico': '/.xsf/indico'})``
    and add an internal location handler to your nginx config to serve
    ``/opt/indico`` via ``/.xsf/indico``:

    .. code-block:: nginx

        location /.xsf/indico/ {
          internal;
          alias /opt/indico/;
        }

    The :ref:`production installation instructions <install-prod>` already
    configure this properly, so if you installed Indico using our guide,
    you only need to change this setting if you add e.g. a new storage
    backend in :data:`STORAGE_BACKENDS` that stores the files outside
    ``/opt/indico``.

    Default: ``None``

.. data:: MAX_UPLOAD_FILE_SIZE

    The maximum size of an uploaded file (in MB).
    A value of ``0`` disables the limit.

    This limit is only enforced on the client side.  For a hard limit that
    is enforced on the server, see :data:`MAX_UPLOAD_FILES_TOTAL_SIZE`

    Default: ``0``

.. data:: MAX_UPLOAD_FILES_TOTAL_SIZE

    The maximum size (in MB) of all files uploaded in a single request
    (or to be more exact, any data contained in the body of a single
    request).

    A value of ``0`` disables the limit, but most web servers also have
    limits which need to be configured as well (``client_max_body_size``
    in nginx) to allow very large uploads.

    Default: ``0``

.. data:: DEFAULT_LOCALE

    The locale that is used by default for i18n. Valid values are
    ``en_GB``, ``fr_FR``, and ``es_ES``.

    Default: ``'en_GB'``

.. data:: DEFAULT_TIMEZONE

    The timezone that is used by default. Any timezone identifier
    such as ``Europe/Zurich`` or ``US/Central`` can be used.

    Default: ``'UTC'``

.. data:: ENABLE_ROOMBOOKING

    Whether to enable the room booking system.

    Default: ``False``

.. data:: PLUGINS

    The list of :doc:`Indico plugins <plugins>` to enable.

    A list of all installed plugins can be displayed by the
    ``indico setup list_plugins`` command; see the guide linked above
    for details on how to enable plugins.

    Default: ``set()``

.. data:: CATEGORY_CLEANUP

    This setting specifies categories where events are automatically
    deleted a certain amount of days after they have been created.

    For each entry, the key is the category id and the value the days
    after which an event is deleted.

    .. warning::

        This feature is mostly intended for "Sandbox" categories where
        users test Indico features.  Since it is common for such categories
        to be used for real events nonetheless, we recommend enabling the
        "Event Header" in the category settings and clearly mention that
        the event will be deleted after a while.

    Default: ``{}``

.. data:: WORKER_NAME

    The name of the machine running Indico.  The default value is
    usually fine unless your servers have ugly (e.g. auto-generated)
    hostnames and you prefer nicer names to show up in error emails.

    Default: ``socket.getfqdn()``

.. data:: FLOWER_URL

    The URL of the `Flower`_ instance monitoring your Celery workers.
    If set, a link to it will be displayed in the admin area.

    To use flower, install it using ``pip install flower``, then start
    it using ``indico celery flower``. By default it will listen on the
    same host as specified in :data:`BASE_URL` (plain HTTP) on port 5555.
    Authentication is done using OAuth so only Indico administrators
    can access flower.  You need to configure the allowed auth callback
    URLs in the admin area; otherwise authentication will fail with an
    OAuth error.

    .. note::

        The information displayed by Flower is usually not very useful.
        Unless you are very curious it is usually not worth using it.

    Default: ``None``


.. _Flask-SQLAlchemy documentation: https://flask-sqlalchemy.readthedocs.io/en/stable/config/#configuration-keys
.. _Sentry: https://sentry.io
.. _Celery documentation on brokers: https://celery.readthedocs.io/en/stable/getting-started/brokers/index.html
.. _Celery documentation on periodic tasks: https://celery.readthedocs.io/en/stable/userguide/periodic-tasks.html#available-fields
.. _Flower: https://flower.readthedocs.io/en/latest/
.. _TeXLive: https://www.tug.org/texlive/
.. _Flask-Multipass: https://flask-multipass.readthedocs.io
