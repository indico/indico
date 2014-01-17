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
    <%include file="inc/first_page.tpl" args="conf=conf,title=_('Book of Abstracts'),show_dates=True"/>
    \pagebreak

    % if conf.getBOAConfig().getText() != "":
        \fancyhead{}
        \vspace{1em}
        \normalsize {
            \rmfamily {
                ${md_convert(str(conf.getBOAConfig().getText()).decode('utf-8'))[7:-7].encode('utf-8')}
            }
        }
        \fancyfoot{}
    % endif
    %% body

    \pagebreak

    % for contrib in contribs:
        % if contrib.canAccess(aw):
            \fancyhead[L]{\small \rmfamily \color{gray} \truncateellipses{${conf.getTitle() | latex_escape}}{100} / ${_("Book of Abstracts")}}
            \addcontentsline{toc}{chapter}{${contrib.getTitle() | latex_escape}}

            <%include file="inc/contribution_condensed.tpl" args="contrib=contrib"/>

            \fancyfoot[C]{\small \rmfamily \color{gray} ${ _("Page {0}").format(r"\thepage") }}
        %endif
    % endfor
</%block>
