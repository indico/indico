.. _pdf_generation:

PDF Generation
==============

WeasyPrint
----------

Indico uses `WeasyPrint <weasyprint_>`_ to generate PDF files from `Document
templates <DT_>`_. WeasyPrint generally works out of the box and does not
require any setup.

.. note::

    WeasyPrint uses fonts installed on the system to render the PDFs. If you are
    generating documents containing character sets like CJK (Chinese, Japanese,
    Korean), make sure to install the necessary fonts. Note that, the exact
    procedure to install new fonts depends on the distribution.

.. _weasyprint: https://github.com/Kozea/WeasyPrint
.. _DT: https://learn.getindico.io/document_templates/about/

.. _latex:

LaTeX
-----

Indico uses LaTeX (xelatex to be exact) to generate some PDF files such
as the *Book of Abstracts* and the PDF versions of contributions. If
you do not need these features, you can skip this part of the documentation
and avoid installing LaTeX altogether.

.. warning::

    LaTeX is extremely powerful, and while Indico tries its best to sanitize LaTeX
    input to disarm any harmful statements, we cannot make any guarantees that all
    these usecases are covered. We **strongly** recommend not installing LaTeX on
    your system anymore, but instead running it inside a container.

    If you absolutely insist on installing TeXLive system-wide, you probably need
    a "full" version of TeXLive, often called ``texlive-full``, ``texlive-scheme-full``
    or similar.

For the reasons mentioned in the warning above, we only support the containerized
setup using Podman. Installing it is quite easy:

If you are on an RPM-based distribution (AlmaLinux, RockyLinux, RHEL), run this:

.. code-block:: shell

    dnf install podman

If you are on a DEB-based distribution (Debian, Ubuntu), use this instead:

.. code-block:: shell

    apt install podman

You then need to configure the Indico user to be able to run unprivileged containers.
It is recommended that you check ``/etc/subuid`` and ``/etc/subgid`` to avoid any
conflicts, but on a system that doesn't run anything besides Indico it is extremely
unlikely to encounter conflicts. You can also edit that file directly and add a range
manually instead of using the ``usermod`` command below:

.. code-block:: shell

    usermod indico --add-subuids 1000000-1065535 --add-subgids 1000000-1065535
    loginctl enable-linger indico

.. important::

    If (and only if) you are on Debian 12 (Bookworm), you need to run this command to
    avoid excessive disk space usage and performance issues as well (however, you should
    not be installing Indico on Debian 12 anymore, considering that it reaches end of life
    in June 2026):

    .. code-block:: shell

        cat >> /etc/containers/storage.conf <<'EOF'
        [storage]
        driver = "overlay"
        EOF

After setting everything up it, add this line to your ``indico.conf`` file to enable
containerized LaTeX functionality:

.. code-block:: python

    XELATEX_PATH = 'podman'

You may then want to proactively pull the texlive container image; otherwise it is
done on the fly the first time it's needed which can make this request quite slow.

.. code-block:: shell

    indico maint pull-latex-image

If you are in a production setup, restart uWSGI and Celery so the updatd config
is actually used:

.. code-block:: shell

    systemctl restart indico-celery.service indico-uwsgi.service

.. tip::

    :data:`XELATEX_PATH` also has some advanced options that allow specifying custom
    container images etc. Most likely you do not need them, but check the linked
    documentation page if you are interested.
