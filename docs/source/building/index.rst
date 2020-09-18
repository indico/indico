.. _building:

Building
========

Before starting Indico compilation, this guide assumes you've previously
:ref:`setup the development base <install-dev>` up until the :ref:`configuring step <configuring-dev>`.

.. warning::
    We do not recommend doing these steps in the same instance you deploy your production version, as you run
    into the risk of mixing the latter with development resources.

The first step is to generate a local distribution archive. Navigate to the Indico source folder
(by default, it is ``~/dev/indico/src``) and run the following commands::

    ./bin/maintenance/build-wheel.py indico --add-version-suffix


.. note::
    The build script refuses to run on a git dirty working directory, so any changes you decide to include must be
    committed temporarily. Make sure you're also not running any similar script, such as the ``build_assets.py``
    in watch mode, as it may interfere with the creation of a production build.

Finally, the ``dist`` folder will contain the wheel distribution, the file you should to copy to your production
machine::

    dist/
      indico-2.3.dev0+20200917.1612.81538f4da8-py2-none-any.whl


To deploy this distribution, you should follow the :ref:`production installation guide <install-prod>`,
but replacing the indexed package in Indico installation (``pip install indico``) with your local wheel from the
previous step::

    pip install ~/dev/indico/src/dist/indico-2.3.dev0+20200917.1612.81538f4da8-py2-none-any.whl


Including a new translation
---------------------------

If you are including a new translation, you should also append the moment resource as the exact first locale,
before building, in ``indico/web/client/js/jquery/index.js``::

    // moment.js locales
    import 'moment/locale/your-locale';

    import 'moment/locale/zh-cn';
    import 'moment/locale/es';
    import 'moment/locale/fr';
    import 'moment/locale/en-gb';
