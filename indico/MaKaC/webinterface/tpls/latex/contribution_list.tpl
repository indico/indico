<%inherit file="inc/document.tpl" />

<%block name="document_class">
    \documentclass[a4paper, 11pt, oneside]{book} %% document type
</%block>

<%block name="header_extra">
    \usepackage{tocloft} %% table of contents
    \usepackage{titlesec}
    \usepackage{fancyhdr} %% headers

    \setlength{\headheight}{60pt}
    \pagestyle{fancy}
    \renewcommand{\headrulewidth}{0pt}
</%block>

<%block name="content">
    \setcounter{secnumdepth}{0} %% remove section heading numbering
    \setcounter{tocdepth}{0} %% remove table of contents numbering

    %% first page
    <%include file="inc/first_page.tpl" args="conf=conf,title=_('Book of Contributions')"/>

    %% TOC
    \begingroup
    \hypersetup{linkcolor=black}
    \renewcommand{\cftchapfont}{}
    \renewcommand{\contentsname}{${_("Table of contents")}}
    \renewcommand{\cftchapleader}{\cftdotfill{}}
    \tableofcontents
    \endgroup

    %% body

    % for contrib in contribs:
        \newpage
        \fancyhead[L]{\small \rmfamily \color{gray} \truncateellipses{${title | latex_escape}}{20} / Contributions Book}
        \fancyhead[R]{\small \rmfamily \color{gray} \truncateellipses{${contrib.getTitle() | latex_escape}}{45}}
        \addcontentsline{toc}{chapter}{${contrib.getTitle() | latex_escape}}

        <%include file="inc/contribution.tpl" args="contrib=contrib"/>

        \fancyfoot[L]{\small \rmfamily \color{gray} \today}
        \fancyfoot[R]{\small \rmfamily \color{gray} ${ _("Page") } \thepage}
    % endfor
</%block>
