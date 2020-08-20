Except for minor differences, this guide applies to both Debian and Ubuntu.
It has been tested with Debian 8 (Jessie), Debian 9 (Stretch) and Ubuntu 16.04 (Xenial).

.. warning::
    Ubuntu 20+ (*Focal*) is currently not supported as it lacks a Python 2 uWSGI plugin.
    Please use an older Ubuntu version for now; modern Ubuntu versions will be supported again
    in Indico 3.0.

    If you are an advanced user and need to use Ubuntu 20, you can also ``pip install uwsgi``
    in the Indico virtualenv and manually create a systemd unit file to start it on boot.
    This is not covered by the documentation though, but should work in principle (we did
    not test it).
