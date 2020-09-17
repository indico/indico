.. _compilation:

Compilation
=============

Before starting Indico compilation, this guide assumes you've previously
:ref:`cloned the development version <cloning>`.
The first step is to generate a local distribution archive. Navigate to the Indico source folder
(by default, it is ``~/dev/indico/src``) and run the following commands::

    ./bin/maintenance/build-wheel.py --target-dir dist indico --add-version-suffix


This will generate a wheel distribution in the ``dist`` folder::

    dist/
      indico-2.3.dev0-py2-none-any.whl


To deploy this distribution, you should follow the `production installation guide <compilation/index.rst>`_,
but replacing the indexed package in Indico installation with your local wheel from the previous step::

    pip install ~/dev/indico/src/dist/indico-2.3.dev0-py2-none-any.whl
