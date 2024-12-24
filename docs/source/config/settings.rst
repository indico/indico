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

.. data:: LOCAL_GROUPS

    This setting controls whether local Indico groups are available.
    If no centralized authentication infrastructure that supports groups
    (e.g. LDAP) is used, local groups are the only way to define groups in
    Indico, but if you do have central groups it may be useful to disable
    local ones to have all groups in one central place.

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

.. data:: FAILED_LOGIN_RATE_LIMIT

    Applies a rate limit to failed login attempts due to an invalid username
    or password. When specifying multiple rate limits separated with a semicolon,
    they are checked in that specific order, which can allow for a short burst of
    attempts (e.g. a legitimate user trying multiple passwords they commonly use)
    and then slowing down more strongly (in case someone tries to brute-force more
    than just a few passwords).

    Rate limiting is applied by IP address and only failed logins count against the
    rate limit. It also does not apply to login attempts using external login systems
    (SSO) as failures there are rarely related to invalid credentials coming from the
    user (these would be rejected on the SSO side, which should implement its own rate
    limiting).

    The default allows a burst of 10 attempts, and then only 5 attempts every 15
    minutes for the next 24 hours.  Setting the rate limit to ``None`` disables it.

    Default: ``'5 per 15 minutes; 10 per day'``

.. data:: SIGNUP_RATE_LIMIT

    Applies a rate limit to sending verification emails in signup attempts.
    When specifying multiple rate limits separated with a semicolon, they are checked
    in that specific order, which can allow for a short burst of attempts.

    Rate limiting is applied by IP address and each verification email sent counts
    against the rate limit.

    The default allows a burst of 5 attempts, and then only 2 attempts every hour for
    the next 24 hours.  Setting the rate limit to ``None`` disables it.

    Default: ``'2 per hour; 5 per day'``

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

.. data:: SIGNUP_CAPTCHA

    If enabled, a CAPTCHA is required when creating an Indico account to prevent
    spam bots from registering accounts automatically.  Signups through external
    authentication systems (LDAP, SSO etc.) are not affected by this; they are
    expected to have their own protection in place to prevent spam signups.

    Default: ``True``


Cache
-----

.. data:: REDIS_CACHE_URL

    The URL of the redis server to use for caching.

    If the Redis server requires authentication, use a URL like this:
    ``redis://unused:password@127.0.0.1:6379/1``

    If no authentication is used (usually the case with a local Redis
    server), you can omit the user/password part:
    ``redis://127.0.0.1:6379/1``

    Default: ``None``


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

    To include custom CSS and JavaScript, simply put ``*.css`` and
    ``*.js`` files into ``<CUSTOMIZATION_DIR>/css`` / ``<CUSTOMIZATION_DIR>/js``.
    If there are multiple files, they will be included in alphabetical
    order, so prefixing them with a number (e.g. ``00-base.css``, ``10-events.css``)
    is a good idea.

    Static files may be added in ``<CUSTOMIZATION_DIR>/files``.  They can be
    referenced in templates through the ``assets.custom`` endpoint.  In CSS/JS,
    the URL for them needs to be built manually (``/static/custom/files/...``).

    For template customizations, see the description of :data:`CUSTOMIZATION_DEBUG`
    as this setting is highly recommended to figure out where exactly to
    put customized templates.

    Here is an example for a template customization that includes a
    custom asset and uses inheritance to avoid having to replace the
    whole template:

    .. code-block:: jinja

        {% extends '~footer.html' %}

        {% block footer_logo %}
            {%- set filename = 'cern_small_light.png' if dark|default(false) else 'cern_small.png' -%}
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

.. data:: FAVICON_URL

    The URL to a custom favicon.  If unset, the default monochrome Indico favicon is
    used.

    Default: ``None``

.. data:: LOGO_URL

    The URL to a custom logo.  If unset, the default monochrome Indico logo is
    used.

    Default: ``None``

.. data:: LOGIN_LOGO_URL

    The URL to a custom logo used on the login page.  If unset, the default
    Indico logo is used.

    Default: ``None``

.. data:: WALLET_LOGO_URL

    The URL to a custom logo used in Google Wallet and Apple Wallet tickets.
    If unset, a compact version of the default Indico logo is used.
    The URL must publicly accessible from the Internet and changes typically
    do not affect existing tickets.

    Default: ``None``

.. data:: CUSTOM_COUNTRIES

    A dict with country name overrides.  This can be useful if the official
    ISO name of a country does not match what your Indico instance's target
    audience expects for a country, e.g. due to political situations.

    .. code-block:: python

        CUSTOM_COUNTRIES = {'KP': 'North Korea'}

    Default: ``{}``

.. data:: CUSTOM_LANGUAGES

    A dict with language/territory name overrides.  This can be useful if the
    official territory name that goes along with a language does not match what
    your Indico instance's target audience expects for a country, e.g. due to
    political situations.

    For example, to replace "Chinese (Simplified)" with "Chinese (China)",
    you would use:

    .. code-block:: python

        CUSTOM_LANGUAGES = {'zh_Hans_CN': ('Chinese', 'Simplified')}

    Note that the language and territory name should be written in that
    particular language to be consistent with the defaults. So in the example
    above, you would write "Chinese" and "Simplified" in Simplified Chinese.

    Setting the territory (second element in the tuple) to ``None`` will hide
    it and only show the language name itself.  Setting the dict value to ``None``
    will effectively hide the language altogether.

    Default: ``{}``

.. data:: CHECKIN_APP_URL

    The URL of the mobile checkin app. The app is purely client-side and only
    communicates with your Indico instance, so even when using the default app
    (which is hosted in CERN's datacenter in Switzerland) no data about your
    events or participants is sent to CERN, the Indico dev team or anyone else.
    If you wish to use a custom app nonetheless, you can find its
    `source code on GitHub <https://github.com/indico/indico-checkin-pwa/>`_ and
    deploy it wherever you want. Note that you need to add the URL of the app
    to the *"Allowed authorization callback URLs"* of the OAuth app named
    "Checkin App" in the Indico admin area.

    Default: ``'https://checkin.getindico.io'``


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
    For details, check the `SQLAlchemy connection pool documentation`_.

    Default: ``5``

.. data:: SQLALCHEMY_POOL_RECYCLE

    This setting configures SQLAlchemy's connection pool.
    For details, check the `SQLAlchemy connection pool documentation`_.

    Default: ``120``

.. data:: SQLALCHEMY_POOL_TIMEOUT

    This setting configures SQLAlchemy's connection pool.
    For details, check the `SQLAlchemy connection pool documentation`_.

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

.. data:: SYSTEM_NOTICES_URL

    The URL of a YAML file with system notices. This should only be changed during
    development (to test custom notices) or set to ``None`` to opt-out from ever
    fetching or displaying system notices.

    Default: ``'https://getindico.io/notices.yml'``

.. data:: DISABLE_CELERY_CHECK

    Disables the warning about Celery not running or being outdated. When set to
    ``None``, the warning is disabled when :data:`DEBUG` is enabled; otherwise
    this setting enables/disables the warning regardless of debug mode.

    Default: ``None``


Directories
-----------

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

.. data:: EMAIL_BACKEND

    Qualified import name for the email sending backend. It can be set to any email
    backend compatible with Django Mail.

    Default: ``'indico.vendor.django_mail.backends.smtp.EmailBackend'``

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

.. data:: SMTP_CERTFILE

    If provided, this certificate file will be used for certificate-based
    SMTP authentication.

    Default: ``None``

.. data:: SMTP_KEYFILE

    If provided, this private key file will be used for certificate-based
    SMTP authentication.

    Default: ``None``

.. data:: SMTP_TIMEOUT

    The timeout in seconds after which a connection attempt to the SMTP
    server is aborted.

    Default: ``30``

.. data:: SMTP_ALLOWED_SENDERS

    A list of allowed email senders for this Indico instance. Each entry must be an
    email address, but using the ``*`` wildcard is allowed.
    For any address not matching an entry in this list, the ``From`` address will be
    rewritten to the :data:`SMTP_SENDER_FALLBACK` address, and the name (or email if
    no name is available) of the original sender will be used in the human-friendly
    part, e.g. ``John Doe (via Indico) <noreply@example.com>``, while their email
    address will go into the ``Reply-to`` header.

    For example, if your mail server only allowed sending emails from your domain
    ``example.com``, you would set this setting to ``{'*@example.com'}``. If only
    a specific sender address was allowed, you'd use e.g. ``{'indico@example.com'}``.

    .. important::

        You most likely want to configure this setting to ensure emails sent from your
        Indico instance are not classified as junk, since email spoofing is nowadays
        being more and more frowned upon by large email providers, as it is commonly
        abused by spammers and threat actors.

    Default: ``set()``

.. data:: SMTP_SENDER_FALLBACK

    The envelope sender address to be used for any senders that are not whitelisted
    in :data:`SMTP_ALLOWED_SENDERS`. This setting is required if the sender whitelist
    is used. Typically setting it to a no-reply address is a good choice.

    Default: ``None``

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


Experimental Features
----------------------

.. data:: EXPERIMENTAL_EDITING_SERVICE

    If enabled, event managers can connect the Editing module of their
    events to an external microservice extending the normal Editing workflow.
    As long as this is considered experimental, there are no guarantees
    on backwards compatibility even in minor Indico version bumps. Please
    check the `reference implementation`_ for details/changes.

    Default: ``False``


LaTeX
-----

.. data:: XELATEX_PATH

    The full path to the ``xelatex`` program of `TeXLive`_.

    If it is installed in a directory in your ``$PATH``, specifying its
    name without a path is sufficient.

    If the path is not configured, any functionality that requires LaTeX
    on the server (such as generating the Book of Abstracts or exporting
    contributions to PDF) will be disabled.

    Default: ``None``

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

.. data:: LATEX_RATE_LIMIT

    Applies a rate limit to public endpoints that generate PDFs using LaTeX
    when accessed by people who are not logged in (such as crawlers).

    Rate limiting is applied by IP address.

    The default allows 2 PDF generations every 3 seconds. Setting the rate limit
    to ``None`` disables it.

    Default: ``'2 per 3 seconds'``


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
    shell:  ``python -c 'import os; print(repr(os.urandom(32)))'``

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

.. data:: MAX_DATA_EXPORT_SIZE

    The maximum file size (in MB) for files added to the user data export archive.
    Note that this limit does not apply to the YAML metadata files which are
    always generated and typically do not exceed a few megabytes. However,
    any additional files such as attachments, papers, etc., that the user might
    have and that do not fit within the limit are not included in the exported
    archive. The default size is 10 GB.

    Default: ``10 * 1024``


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

.. data:: ENABLE_GOOGLE_WALLET

    Whether to enable the Google Wallet integration for event tickets.

    Default: ``False``

.. data:: ENABLE_APPLE_WALLET

    Whether to enable the Apple Wallet integration for event tickets.

    Default: ``False``

.. data:: ENABLE_DELETE_USER_FROM_UI

    Whether to enable administrators to delete users from the UI.

    Enable Indico administrators to delete a user from the UI along with
    all their associated data. If it is not possible to delete the user
    (e.g. because they are listed as a speaker at an event), the user
    will be anonymized instead.

    Default: ``False``

.. data:: PLUGINS

    The list of :ref:`Indico plugins <installation-plugins>` to enable.

    A list of all installed plugins can be displayed by the
    ``indico setup list-plugins`` command; see the guide linked above
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


.. _SQLAlchemy connection pool documentation: https://docs.sqlalchemy.org/en/14/core/pooling.html
.. _Sentry: https://sentry.io
.. _Celery documentation on brokers: https://celery.readthedocs.io/en/stable/getting-started/brokers/index.html
.. _Celery documentation on periodic tasks: https://celery.readthedocs.io/en/stable/userguide/periodic-tasks.html#available-fields
.. _TeXLive: https://www.tug.org/texlive/
.. _Flask-Multipass: https://flask-multipass.readthedocs.io
.. _reference implementation: https://github.com/indico/openreferee
