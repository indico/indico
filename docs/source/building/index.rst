.. _building:

Building
========

Before starting Indico compilation, this guide assumes you've previously
:ref:`setup the development base <install-dev>` up until the :ref:`configuring step <configuring-dev>`.

.. warning::
    We do not recommend doing these steps on the same system where you are running your production
    version, as you run into the risk of mixing the latter with development resources.

.. note::
    The ``master`` branch on Git is usually the next version under (heavy) development. Check if there
    is a ``2.x-maintenance`` branch for your version and if yes, use that branch instead of ``master``.

The first step is to generate a local distribution archive. Navigate to the Indico source folder
(by default, it is ``~/dev/indico/src``) and run the following command::

    ./bin/maintenance/build-wheel.py indico --add-version-suffix


.. note::
    The build script refuses to run on a dirty git working directory, so any changes you decide to
    include must be committed temporarily. You can use ``git checkout --detach`` to avoid committing
    to your local master branch; if you plan to actually use the translation the better option would
    be of course to create a real Git branch.

.. warning::
    Make sure you're also not running any other build tool such as ``build-assets.py``, as it
    may interfere with the creation of a production build when running in ``--watch`` mode.

Finally, the ``dist`` folder will contain the wheel distribution, the file you should to copy to your production
machine::

    dist/
      indico-2.3.1.dev0+202009231923.a14a24f564-py2-none-any.whl


To deploy this distribution, you should follow the :ref:`production installation guide <install-prod>`,
but instead of installing Indico from PyPI (``pip install indico``), install your custom-built wheel from
the previous step::

    pip install /tmp/indico-2.3.1.dev0+202009231923.a14a24f564-py2-none-any.whl

If you already have Indico installed, then simply installing the version from the wheel and restarting
uwsgi and indico-celery is all you need to do.

Including a new translation
---------------------------

If you are including a new translation, you should also include the moment-js locale in
``indico/web/client/js/jquery/index.js`` before building::

    // moment.js locales
    import 'moment/locale/your-locale';

    import 'moment/locale/zh-cn';
    import 'moment/locale/es';
    import 'moment/locale/fr';
    import 'moment/locale/en-gb';

.. note::
    Put your custom locale first, since ``en-gb`` needs to be the last one as a fallback.
