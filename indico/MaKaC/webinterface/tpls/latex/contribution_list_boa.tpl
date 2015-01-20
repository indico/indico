<%inherit file="inc/document.tpl" />

<%block name="document_class">
    \documentclass[a4paper, 11pt, oneside]{book} %% document type
</%block>

<%block name="header_extra">
    \usepackage{fancyhdr} %% headers

    \setlength{\headheight}{60pt}
    \pagestyle{fancy}
    \renewcommand{\headrulewidth}{0pt}

    \newenvironment{boa_text}
    {
       \cleardoublepage
       \thispagestyle{empty}
       \vspace*{\stretch{1}}
       \begin{minipage}[t]{0.66\textwidth}
    }%
    {
       \end{minipage}
       \vspace*{\stretch{3}}
       \clearpage
    }

</%block>

<%block name="content">
    \setcounter{tocdepth}{0} %% remove table of contents numbering

    %% first page
    \frontmatter
    <%block name="first_page">
        <%include file="inc/first_page.tpl" args="conf=conf,title=_('Report of Abstracts'),show_dates=True"/>
    </%block>

    % if boa_text:
        \begin{boa_text}
            \thispagestyle{fancy}
            \fancyhead{}
            \vspace{1em}
            \normalsize {
                \rmfamily {
                    ${md_convert(str(boa_text).decode('utf-8')).encode('utf-8')}
                }
            }
            \fancyfoot[C]{\thepage}
        \end{boa_text}
    % endif

    <%block name="table_of_contents">
    </%block>

    %% body
    \mainmatter
    <%block name="book_body">
        % for contrib in contribs:
            % if contrib.canAccess(aw):
                \fancyhead[L]{\small \rmfamily \color{gray} \truncateellipses{${conf.getTitle() | latex_escape}}{300pt} / ${_("Report of Abstracts")}}
                \addcontentsline{toc}{chapter}{${contrib.getTitle() | latex_escape}}

                \vspace{3em}
                <%include file="inc/contribution_condensed.tpl" args="contrib=contrib"/>

                \fancyfoot[C]{\small \rmfamily \color{gray} ${ _("Page {0}").format(r"\thepage") }}
            %endif
        % endfor
    </%block>
</%block>
