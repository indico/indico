Upgrade Indico from 1.2
=======================

The migration tool (`indico-migrate <https://github.com/indico/indico-migrate>`_)
requires Python 2.7 and Indico 2.0. It is not supported by Indico v3 nor will it
work on Python 3.

If you still need to migrate a legacy instance from the 1.x (or older), please
consult the documentation from Indico v2. You may also want to consider running
the migration on a separate virtual machine in order to not clutter the server
that will run Indico v3 with legacy tools and software.
