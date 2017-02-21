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
        <%include file="inc/first_page.tpl" args="event=conf.as_event,title=_('Report of Abstracts'),show_dates=True"/>
    </%block>

    % if boa_text:
        \begin{boa_text}
            \thispagestyle{fancy}
            \fancyhead{}
            \vspace{1em}
            \normalsize {
                \rmfamily {
                    ${md_convert(boa_text)}
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
            % if contrib.can_access(aw):
                \fancyhead[L]{\small \rmfamily \color{gray} \truncateellipses{${conf.as_event.title | latex_escape}}{300pt} / ${_("Report of Abstracts") | latex_escape}}
                \phantomsection
                \addcontentsline{toc}{chapter}{${contrib.title | latex_escape}}

                \vspace{3em}
                <%include file="inc/contribution_condensed.tpl" args="contrib=contrib"/>

                \fancyfoot[C]{\small \rmfamily \color{gray} ${ latex_escape(_("Page {0}"), ignore_braces=True).format(r"\thepage") }}
            %endif
        % endfor
    </%block>
</%block>
