.. _latex:

LaTeX
=====

Indico uses LaTeX (xelatex to be exact) to generate some PDF files such
as the *Book of Abstracts* and the PDF versions of contributions.

Since Indico requires quite a few LaTeX packages which are not always]
installed by default when using the texlive packages of the various
linux distrubtions, we recommend installing it manually.

The following commands should work fine to install everything you need.
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
    TEXMFLOCAL /opt/texlive/texmf-local
    TEXMFHOME ~/texmf
    TEXMFSYSCONFIG /opt/texlive/texmf-config
    TEXMFSYSVAR /opt/texlive/texmf-var
    TEXMFVAR ~/.texlive/texmf-var
    binary_x86_64-linux 1
    collection-basic 1
    collection-bibtexextra 1
    collection-binextra 1
    collection-context 1
    collection-fontsextra 1
    collection-fontsrecommended 1
    collection-fontutils 1
    collection-formatsextra 1
    collection-games 1
    collection-humanities 1
    collection-langarabic 1
    collection-langchinese 1
    collection-langcjk 1
    collection-langcyrillic 1
    collection-langczechslovak 1
    collection-langenglish 1
    collection-langeuropean 1
    collection-langfrench 1
    collection-langgerman 1
    collection-langgreek 1
    collection-langitalian 1
    collection-langjapanese 1
    collection-langkorean 1
    collection-langother 1
    collection-langpolish 1
    collection-langportuguese 1
    collection-langspanish 1
    collection-latex 1
    collection-latexextra 1
    collection-latexrecommended 1
    collection-luatex 1
    collection-mathscience 1
    collection-metapost 1
    collection-music 1
    collection-pictures 1
    collection-plaingeneric 1
    collection-pstricks 1
    collection-publishers 1
    collection-texworks 1
    collection-xetex 1
    option_adjustrepo 0
    option_autobackup 1
    option_backupdir tlpkg/backups
    option_desktop_integration 1
    option_doc 1
    option_file_assocs 1
    option_fmt 1
    option_letter 1
    option_path 0
    option_post_code 1
    option_src 1
    option_sys_bin /usr/local/bin
    option_sys_info /usr/local/share/info
    option_sys_man /usr/local/share/man
    option_w32_multi_user 0
    option_write18_restricted 1
    portable 0
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
