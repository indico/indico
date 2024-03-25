Except for minor differences, these guides apply to vanilla CentOS 7/8
and also the CERN flavor of CentOS 7, CC7 (CentOS CERN 7).

We have **not** tested the installation guides with CentOS Stream 8,
as there are no up to date official Postgres packages available yet.

.. warning::

    CentOS 8 is **only** supported with nginx, as some important packages
    (mod_xsendfile and mod_proxy_uwsgi) are not (yet?) available for
    CentOS 8 in first-party repos. Once they are in EPEL, there is a
    good chance the guide will work as expected.
