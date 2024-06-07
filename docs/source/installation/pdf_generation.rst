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

LaTeX
-----
.. _latex:

Indico uses LaTeX (xelatex to be exact) to generate some PDF files such
as the *Book of Abstracts* and the PDF versions of contributions.  If
you do not need these features, you can skip this part of the documentation
and avoid installing LaTeX altogether.

Since Indico requires quite a few LaTeX packages which are not always
installed by default when using the texlive packages of the various
linux distributions, we recommend installing it manually.

.. note::

    If you know what you're doing, feel free to try using your distribution's "full"
    texlive package (often named ``texlive-full``, ``texlive-scheme-full``, or similar)
    instead of using the texlive installer.

    However, e.g. on Alma9 there are some LaTeX packages missing which Indico needs.
    A possible workaround for this (which works fine) is using the packages from
    Fedora 34, but this is not straightforward at all.

First of all, you will need to install some dependencies so that all TeX
formats are generated successfully upon TeXLive installation.

.. code-block:: shell

    # If you use Alma or Rocky:
    dnf install perl ghostscript fontconfig wget
    # If you use Debian or Ubuntu:
    apt install perl ghostscript libfontconfig1

You are now ready to install TeXLive. The following commands should work
fine to install everything you need.
You need to run the installation as root or create ``/opt/texlive`` as
root and grant your user write access to it.

Download the installer and cd to its location (the directory name contains
the date when the package was built, so use the wildcard or type the name
manually based on the output when unpacking the archive):

.. code-block:: shell

    cd /tmp
    wget http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
    tar xvzf install-tl-unx.tar.gz
    cd install-tl-*/

Create the setup config file to install all the packages you need:

.. code-block:: shell

    cat > texlive.profile <<'EOF'
    selected_scheme scheme-full
    TEXDIR /opt/texlive
    TEXMFCONFIG ~/.texlive/texmf-config
    TEXMFHOME ~/texmf
    TEXMFLOCAL /opt/texlive/texmf-local
    TEXMFSYSCONFIG /opt/texlive/texmf-config
    TEXMFSYSVAR /opt/texlive/texmf-var
    TEXMFVAR ~/.texlive/texmf-var
    binary_x86_64-linux 1
    instopt_adjustpath 0
    instopt_adjustrepo 0
    instopt_letter 0
    instopt_portable 0
    instopt_write18_restricted 1
    tlpdbopt_autobackup 1
    tlpdbopt_backupdir tlpkg/backups
    tlpdbopt_create_formats 1
    tlpdbopt_generate_updmap 0
    tlpdbopt_install_docfiles 0
    tlpdbopt_install_srcfiles 0
    tlpdbopt_post_code 1
    tlpdbopt_sys_bin /usr/local/bin
    tlpdbopt_sys_info /usr/local/share/info
    tlpdbopt_sys_man /usr/local/share/man
    EOF

Start the installer and wait for it to complete. This may take between
a few minutes and a few hours depending on the speed of the (randomly
chosen) mirror.

.. code-block:: shell

    ./install-tl --profile texlive.profile

After installing it, add this line to your ``indico.conf`` file to use
your new TeXLive installation:

.. code-block:: python

    XELATEX_PATH = '/opt/texlive/bin/x86_64-linux/xelatex'

If you are in a production setup, reload uWSGI using
``touch /opt/indico/web/indico.wsgi`` to reload the config file.

As security-related updates are released frequently, it is also
a good idea to periodically update the TeXLive packages by running:

.. code-block:: shell

    /opt/texlive/bin/x86_64-linux/tlmgr update --self --all
