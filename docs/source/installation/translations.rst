Translations
************

Indico comes with a number of languages by default. In release 3.3, those are:
English (default), French, Portuguese, Spanish, Chinese, Ukrainian, Polish,
Mongolian, Turkish, German, Czech, Italian, Hungarian, Swedish, Japanese and Finnish (in the order of integration).
Additional languages are being prepared on the
`Transifex platform <https://www.transifex.com/indico/>`_.

In order to use (partially) existing translations from Transifex or to contribute
translations, you need to register with the
`Indico project on the Transifex platform <https://www.transifex.com/indico/>`_.

If, instead, you are interested in contributing translations, we have a
:ref:`separate guide <translations>` just for that.

Additional Translations
=======================

This is a guide to set up an Indico instance with a new language.
It is useful for translators to verify how the translation looks in production
or for administrators who just want to lurk at the incubated translation embryos.

You may also use the translation `demo instance
<https://localization-demo.getindico.io>`_ to check out both official and
unofficial translations.

Alternatively, you may use this guide to expose a translation we do not officially support,
in your production version.

1. Setup an Indico dev environment
----------------------------------

This should usually be done on your own computer or a virtual machine.

For creating your own Indico instance, we provide two different guides:
The first one is for a :ref:`production system <install-prod>`,
it will prepare Indico to be served to users and used in all the different purposes you may have besides translations.
The second is :ref:`development <install-dev>` a light-weight,
easier to set up, version oriented to testing purposes, that should not be exposed to the public.

For the purpose of translation **development** or **testing** we recommend using the development version.

2. Install the transifex client
-------------------------------

Follow the instructions on the `transifex site <https://docs.transifex.com/client/installing-the-client>`_.

3. Get an API token
-------------------

Go `to your transifex settings <https://www.transifex.com/user/settings/api/>`_ and generate an API token.
Next, create a ``~/.transifexrc`` configuration file::

    [https://www.transifex.com]
    rest_hostname = https://rest.api.transifex.com
    token = API_TOKEN_HERE

You can either save your API token in the configuration file as shown above or pass it
as an environment variable every time you invoke a command using ``TX_TOKEN=myapitoken``.

You can also consult the official
`transifex client guide <https://developers.transifex.com/docs/using-the-client>`_.

4. Install the translations
---------------------------

Navigate to ``~/dev/indico/src`` (assuming you used the standard locations from the dev setup guide).

Run ``indico i18n pull indico <language_code>``.
Languages codes can be obtained `here <https://www.transifex.com/indico/>`_.

For example, Chinese (China) is ``zh_CN.GB2312``.

5. Check the translations
-------------------------

Run ``indico i18n check-format-strings`` to make sure that all placeholders in the
translated strings match.

If this command finds any issues, we recommend fixing the translations in Transifex and
reinstalling the updated translations before proceeding to the next step. Otherwise,
this could to lead to errors when Indico tries to use the translated string.

6. Compile translations and run Indico
--------------------------------------

Run the command ``indico i18n compile indico`` and:

- :ref:`launch Indico <run-dev>`, or
- :ref:`build <building>` and :ref:`deploy your own version of Indico <install-prod>`,
  if you wish to deploy the translation in a production version.

The language should now show up as an option in the top right corner.

In case you modified the ``.js`` resources, you also need to delete the cached
files in ``~/dev/indico/data/cache/assets_i18n_*.js``.

FAQ
---

Why isn't Indico loading my language?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some languages in transifex use codes that Indico is not able to recognize.
One example is the Chinese's ``zh_CN.GB2312``.
The easy fix for this is to rename the folder ``zh_CN.GB2312`` (inside
``indico/translations/``) to the extended locale code |zh_Hant_TW|_.
Unfortunately, there is no list with mappings for all the languages.
So if by any reason it doesn't work for you, feel free to :ref:`ask us <contact>`.

.. |zh_Hant_TW| replace:: ``zh_Hant_TW``
.. _zh_Hant_TW: https://www.localeplanet.com/icu/zh-Hant-TW/index.html
