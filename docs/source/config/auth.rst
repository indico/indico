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
- ``default_group_provider`` -- If you have any providers which have
  group support (usually the case for LDAP), you should enable this
  for exactly one provider.  This is used by legacy parts of Indico
  such as the room booking module which support groups but only take
  a group name and no information from which provider to get them.
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


.. _Flask-Multipass: https://flask-multipass.readthedocs.io
