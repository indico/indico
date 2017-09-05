Add the following code to your ``/opt/indico/etc/indico.conf``:

.. code-block:: python

    # SSO
    AUTH_PROVIDERS = {
        'shib-sso': {
            'type': 'shibboleth',
            'title': 'SSO',
            'attrs_prefix': 'ADFS_',
            'callback_uri': '/login/shib-sso/shibboleth',
            # 'logout_uri': 'https://login.yourcompany.tld/logout'
        }
    }
    IDENTITY_PROVIDERS = {
        'shib-sso': {
            'type': 'shibboleth',
            'title': 'SSO',
            'identifier_field': 'ADFS_LOGIN',
            'mapping': {
                'affiliation': 'ADFS_HOMEINSTITUTE',
                'first_name': 'ADFS_FIRSTNAME',
                'last_name': 'ADFS_LASTNAME',
                'email': 'ADFS_EMAIL',
                'phone': 'ADFS_PHONENUMBER'
            },
            'trusted_email': True
        }
    }


The values for ``attrs_prefix``, ``mapping`` and ``identifier_field``
may be different in your environment.  Uncomment and set ``logout_uri``
if your SSO infrastructure provides a logout URL (usually used to log
you out from all applications).

If you only want to use SSO, without allowing people to login locally
using username/password, disable it by setting ``LOCAL_IDENTITIES = False``
in ``indico.conf``.


.. warning::
    We assume that emails received from SSO are already validated.
    If this is not the case, make sure to disable ``trusted_email``
    which will require email validation in Indico when logging in
    for the first time. Otherwise people could take over the account
    of someone else by using their email address!


.. note::
    The example config is rather simple and only accesses data from
    SSO during login.  This is not sufficient for advanced features
    such as automatic synchronization of names, affiliations and phone
    numbers or using centrally managed groups.  To use these features,
    you need to use e.g. the LDAP identity provider and use the
    information received via SSO to retrieve the user details from LDAP.
    If you need assistance with this, feel free to ask us on IRC
    (#indico @ Freenode) or via e-mail (indico-team@cern.ch).
