Translations
************

Indico comes with a number of languages by default. In release 2.3, those are:
English (default), French, Portuguese, Spanish and Chinese (in the order of integration).
Additional languages are being prepared on the Transifex platform.

In order to use (partially) existing translations from Transifex or to contribute
translations, you need to register with the
`Indico project on the Transifex platform <https://www.transifex.com/indico/>`_.

Additional Translations
=======================

This is a guide to set up an Indico instance with a new language.
It is useful for translators to verify how the translation looks in production
or for administrators who just want to lurk at the incubated translation embryos.

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
Afterwards, you should run the command ``tx init --skipsetup``.
It will request the token you just copied from the previous settings and save it locally so you can start
using transifex locally.
If you do not know how to run this command, please refer to the
`transifex client guide <https://docs.transifex.com/client/init>`_.

4. Install the translations
---------------------------

Navigate to ``~/dev/indico/src`` (assuming you used the standard locations from the dev setup guide).

Run ``tx pull -f -l <language_code>``.
Languages codes can be obtained `here <https://www.transifex.com/indico/>`_.

For example, Chinese (China) is ``zh_CN.GB2312``.

5. Compile translations and run Indico
--------------------------------------

Run the commands ``indico i18n compile-catalog``
and ``indico i18n compile-catalog-react``
and:

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


Contributing
============

As a **translator**, you should have a good knowledge of the Indico functions
(from the user side at least). Then you can subscribe to the abovementioned
`Transifex site for Indico <https://www.transifex.com/indico/>`_
and request membership of one of the translation teams. You should also contact
the coordinators; some languages have specific coordinators assigned.
They may point you to places, where work is needed and which rules have
been agreed for the translations.

The glossary is usually of big help to obtain a uniform translation of all
technical terms. Use it!

As a **programmer** or **developer**, you will have to be aware of the needs and
difficulties of translation work.
A `Wiki page for Internationalisation <https://github.com/indico/indico/wiki/Internationalisation>`_
is available from github (slightly outdated and we should eventually move it to this documentation).
It describes the interface between translating and programming and some conventions to be followed.
Everyone involved in translating or programming Indico should have read it before starting the work.

Whenever translaters spot difficult code (forgotten pluralization, typos), they
should do their best to avoid double (or rather: multiple) work to their fellow translators.
What is a problem for their translation, usually will be a problem for all translations.
Don't hesitate to open an issue or pull request on `GitHub <https://github.com/indico/indico>`_.
Repair first, then translate (and be aware that after repair, the translation has to be made
again for all languages).

.. note::

    The codebase also contains legacy code, which may not follow all rules.

File Organisation
=================

The relationship between

- transifex resources names (core.js, core.py, core.react.js)
- PO file names (messages-js.po, messages.po, messages-react.po) and
- the actual place, where the strings are found

is not always obvious. Starting with the resource names, the files ending in

- ``.py`` refer to translations used with python and jinja templates,
- ``.js`` refer to translations used with generic or legacy javascript,
- ``react.js`` refer to translations used with the new react-based javascript.

These contain a relationship to PO files, as defined in the following example extracted
from ``src/.tx/config``.

.. code-block:: none

    [indico.<transifex resource slug>]
    file_filter = indico/translations/<lang>/LC_MESSAGES/<PO file name>.po
    source_file = indico/translations/<source file name>.pot
    source_lang = en
    type = PO

.. note::

    The transifex resource slug is a name-like alias that identifies a particular file.

For more information regarding this subject a `thread has started here <https://talk.getindico.io/t/relationship-between-resources-and-po-files-in-transifex/1890>`_.
