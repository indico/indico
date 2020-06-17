Authentication
==============

Indico uses `Flask-Multipass`_ to handle authentication, searching for
users in an external database, and externally managed groups.  This
means any Flask-Multipass authentication/identity provider can be used
in Indico without any modifications to Indico itself.

For a description of the basic settings regarding local accounts
(managed within Indico itself), see the
:ref:`general indico config documentation <settings-auth>`.
This guide focuses solely on advanced authentication methods and how to
configure them in Indico.

Configuration
-------------

Authentication providers
^^^^^^^^^^^^^^^^^^^^^^^^

Authentication providers handle the login process, i.e. asking for user
credentials or redirecting to an external site in case of SSO.

The :data:`AUTH_PROVIDERS` setting is Indico's equivalent to the
``MULTIPASS_AUTH_PROVIDERS`` setting of `Flask-Multipass`_.

It must be set to a dict mapping a unique (internal) name of the auth
provider (e.g. ``mycompany-ldap``) to a dict of whatever data is
needed for the given provider.

The following keys are available in the provider data:

- ``type`` -- **Required.** The type of the provider. Valid values
  are e.g. ``ldap``, ``oauth``, ``shibboleth``, and whatever custom
  providers you have installed.
- ``title`` -- The title of the provider (shown on the login page).
  If omitted, the provider name is used.
- ``default`` -- Must be set to ``True`` for exactly one form-based
  provider in case more than one such provider is used.  The login
  form of the default provider is displayed when opening the login
  page so it should be the provider that most people use.
- Any provider-specific settings.


Identity providers
^^^^^^^^^^^^^^^^^^

Identity providers get data about a user who logged in (based on the
information passed on by the authentication provider) and also handle
searching of external users and groups.

The :data:`IDENTITY_PROVIDERS` setting is Indico's equivalent to the
``MULTIPASS_IDENTITY_PROVIDERS`` setting of `Flask-Multipass`_.

It must be set to a dict mapping a unique (internal) name of the
identity provider (e.g. ``mycompany-ldap``) to a dict of whatever
data is needed for the given provider.  Note that once an identity
provider has been used, its name must not be changed.

The following keys are available in the provider data:

- ``type`` -- **Required.** The type of the provider. Valid values
  are e.g. ``ldap``, ``oauth``, ``shibboleth``, and whatever custom
  providers you have installed.
- ``title`` -- The title of the provider (shown in the account list
  of the user profile).  If omitted, the provider name is used.
- ``trusted_email`` -- Set this to ``True`` if all email addresses
  received from the provider are trustworthy, i.e. if it is guaranteed
  that an email address actually belongs to the user (either because
  it's coming from a trusted employee database or the provider is known
  to send verification emails).  If an email is trusted, Indico will
  use it immediately to start the signup process or associate an
  existing account with a matching email address.  Otherwise a
  verification email is sent to prove that the user has access to the
  email address, which is less user-friendly but extremely important
  to prevent malicious takeovers of Indico accounts.
- ``moderated`` -- Set this to ``True`` if you want to require manual
  approval of the registration by an Indico admin.  This results in
  the same workflow as :data:`LOCAL_MODERATION` in case of local
  accounts.
- ``synced_fields`` -- This may be set in no more than once identity
  provider and enables user data synchronization.  Its value should
  be a set of user attributes that can be synchronized during login.
  Indico does not support synchronizing email addresses; only the
  following attributes can be synchronized:
  ``first_name``, ``last_name``, ``affiliation``, ``phone``, ``address``
- ``mapping`` -- A dictionary that maps between keys given by the
  identity provider and keys expected by Indico for user information.
  The key of each entry is the Indico-side attribute name; the value
  is the key under which the data is exposed by the provider.
  Indico can take user information from the following keys: ``first_name``,
  ``last_name``, ``email``, ``affiliation``, ``phone``, ``address``.
  For example, this mapping would use the ``givenName`` provided by
  the identity provider to populate the user's ``first_name`` in Indico:

  .. code-block:: python

      'mapping': {'first_name': 'givenName'}
- ``identity_info_keys`` -- By default, all six attributes listed above
  will be used if the provider has them (either directly or in some
  other field specified in the ``mapping``).  If you want to restrict
  the data from a provider (e.g. because the value it provides is known
  to be useless/incorrect), you can set this to a set containing only
  the attributes you want to use.  Note that external user search requires
  email addresses, so if you exclude email addresses here, users from
  this provider will never appear in search results.
- Any provider-specific settings.


Links between providers
^^^^^^^^^^^^^^^^^^^^^^^

By default, authentication and identity providers with the same name
are linked together. If this is not what you want, you can use the
:data:`PROVIDER_MAP` setting to manually link providers.  This is useful
for advanced cases where you have e.g. both a login form to enter LDAP
credentials and a SSO provider, but want to have a single LDAP identity
provider that can use the username from either SSO or the LDAP login.
In this case you would link both authentication providers to the same
identity provider.

Specific providers
------------------

LDAP
^^^^

The ``ldap`` authentication/identity providers are available by default,
but to use them you need to install the ``python-ldap`` library using
``pip install python-ldap``.

.. note::

    ``python-ldap`` has some extra system dependencies (openldap and
    libsasl). How to install them (apt, yum, etc.) depends on your linux
    distribution.  The package names are usually ``libsasl2-dev`` or
    ``libsasl-dev`` and ``openldap-dev`` (or ``-devel`` on some distros).
    If one of these libraries is missing, ``pip`` will fail when
    installing ``python-ldap``. Simply re-run the command after
    installing the missing library.

Once everything is installed, you can add the LDAP-related settings to
your ``indico.conf``. Below is an example based on the LDAP config we
use at CERN with Active Directory; you can copy this as a starting point
for your own config and then adapt it to your own environment:

.. code-block:: python

    _ldap_config = {
        'uri': 'ldaps://...',
        'bind_dn': 'cn=***,OU=Users,OU=Organic Units,DC=cern,DC=ch',
        'bind_password': '***',
        'timeout': 30,
        'verify_cert': True,
        'page_size': 1500,

        'uid': 'cn',
        'user_base': 'DC=cern,DC=ch',
        'user_filter': '(objectCategory=user)',

        'gid': 'cn',
        'group_base': 'OU=Workgroups, DC=cern, DC=ch',
        'group_filter': '(objectCategory=group)',
        'member_of_attr': 'memberOf',
        'ad_group_style': True
    }


    AUTH_PROVIDERS = {
        'ldap': {
            'type': 'ldap',
            'title': 'LDAP',
            'ldap': _ldap_config,
            'default': True
        }
    }

    IDENTITY_PROVIDERS = {
        'ldap': {
            'type': 'ldap',
            'title': 'LDAP',
            'ldap': _ldap_config,
            'mapping': {
                'first_name': 'givenName',
                'last_name': 'sn',
                'email': 'mail',
                'affiliation': 'company',
                'phone': 'telephoneNumber'
            },
            'trusted_email': True,
            'synced_fields': {'first_name', 'last_name', 'affiliation', 'phone', 'address'}
        }
    }

The LDAP-specific config uses the following keys:

- ``uri`` -- **Required.**
  The URI referring to the LDAP server including the protocol and the
  port.  Use ``ldaps://`` for LDAP over SSL/TLS and ``ldap://`` with
  the ``starttls`` option for a plain LDAP connection with TLS negotiation.
  The port can be omitted if the LDAP server listens on the default port
  (636 for LDAP over SSL and 389 for a plain LDAP connection with TLS
  negotiation).
- ``bind_dn`` -- **Required.**
  The distinguished name to bind to the LDAP directory.
- ``bind_password`` -- **Required**.
  The password to use together with the ``bind_dn`` to login to the
  LDAP server.
- ``timeout`` --
  The delay in seconds to wait for a reply from the LDAP server (set
  to ``-1`` to disable).
  Default: ``30``
- ``verify_cert`` --
  Whether to verify the TLS certificate of the LDAP server.
  Default: ``True``
- ``starttls`` --
  Whether to use STARTTLS to switch to an encrypted connection.
  Ignored with an ``ldaps://`` URI.
  Default: ``False``
- ``page_size`` --
  The limit of entries to retrieve at once for a search.
  ``0`` means no size limit.  It is recommended to have at most the
  size limit imposed by the server.
  Default: ``1000``
- ``uid`` --
  The attribute whose value is used as an identifier for the user
  (typically the username).  This attribute must be a single-valued
  attribute whose value is unique for each user. If the attribute is
  multi-valued, only the first one retrieved will be returned.
  Default: ``'uid'``
- ``user_base`` -- **Required.**
  The base node for all the nodes which might contain a user.
- ``user_filter`` --
  A valid LDAP filter which will select exclusively all users in the
  subtree from the ``user_base``.  The combination of the ``user_base``
  and the ``user_filter`` must match exclusively all the users.
  Default: ``'(objectClass=person)'``
- ``gid`` --
  The attribute whose value is used as an identifier for the group
  (typically the group's name).  This attribute must be a single-valued
  attribute whose value is unique for each group. If the attribute is
  multi-valued, only the first one retrieved will be returned.
  Default: ``'cn'``
- ``group_base`` -- **Required.**
  The base node for all the nodes which might contain a group.
- ``group_filter`` --
  A valid LDAP filter which will select exclusively all groups in the
  subtree from the ``group_base``.  The combination of the ``group_base``
  and the ``group_filter`` must match exclusively all the groups.
  Default: ``'(objectClass=groupOfNames)'``
- ``member_of_attr`` --
  The multi-valued attribute of a user containing the list of groups
  the user is a member of.
  Default: ``'memberOf'``

  .. note::

      In case of SLAPD/OpenLDAP, the *member of* attribute must be enabled.
      While it is not enabled by default, the majority of servers will
      have it enabled.  A simple ``ldapsearch`` for a user member of any
      group should show if that is the case.  If not, you can check
      `this article`_ on information how to enable it on your LDAP server.
      Note that unless you manage the LDAP server, you need to ask the
      administrator of that server to do that.
- ``ad_group_style`` --
  Whether the server uses Active-Directory-style groups or not.
  This is only used when checking if a user is a member of a group.
  If enabled, the code will take advantage of the ``tokenGroups``
  attribute of a user to check for nested group membership.
  Otherwise, it will only look through the values of the ``member_of_attr``,
  which should also work for Active Directory, but only for direct
  membership.
  Default: ``False``


SAML / Shibboleth
^^^^^^^^^^^^^^^^^

The ``shibboleth`` authentication/identity providers are available by
default, but due to how the protocol works you need to use the Apache
webserver to use SAML atuhentication provider.

You can find guides on how to set it up for :ref:`CentOS <centos-apache-shib>`
and :ref:`Debian <deb-apache-shib>`.

If you also have an LDAP server, it may be a good idea to use the
``shibboleth`` authentication provider and connect it to an ``ldap``
identity provider. This way the user information is retrieved from LDAP
based on a unique identifier of the user that comes from SAML, and you
can still use the search and group functionality provided by LDAP.


.. _Flask-Multipass: https://flask-multipass.readthedocs.io
.. _this article: https://www.adimian.com/blog/2014/10/how-to-enable-memberof-using-openldap/
