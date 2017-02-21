<%page args="items,title,conf_title"/>

<%inherit file="inc/document.tpl" />

<%block name="document_class">
    \documentclass[a4paper, 11pt, oneside]{book} %% document type
</%block>

<%block name="geometry">
\usepackage[a4paper, top=5em, bottom=10em]{geometry}
</%block>

<%block name="header_extra">
    \usepackage{fancyhdr} %% headers
    \usepackage{scrextend}

    \setlength{\headheight}{60pt}
    \pagestyle{fancy}
    \renewcommand{\headrulewidth}{0pt}
</%block>

<%block name="content">
    %% first page
    \frontmatter
    <%include file="inc/first_page.tpl" args="event=conf.as_event,title=title"/>

    %% body
    \mainmatter

    % for item in items:
        \newpage
        \fancyhead[L]{\small \rmfamily \color{gray} \truncateellipses{${conf.as_event.title.encode('utf-8') | latex_escape}}{80pt} / ${title | latex_escape}}
        \fancyhead[R]{\small \rmfamily \color{gray} \truncateellipses{${item.title | latex_escape}}{150pt}}
        \phantomsection
        \addcontentsline{toc}{section}{${item.title | latex_escape}}

        % if doc_type == 'abstract':
            <%include file="inc/abstract.tpl" args="abstract=item,
                track_class=get_track_classification(item),
                contrib_type=get_contrib_type(item)"/>
        % elif doc_type == 'abstract_manager':
            <%include file="inc/abstract_manager.tpl" args="abstract=item,
                track_class=get_track_classification(item),
                contrib_type=get_contrib_type(item),
                status=get_status(item),
                track_judgements=get_track_judgements(item)"/>
        % elif doc_type == 'contribution':
            <%include file="inc/contribution.tpl" args="contrib=item"/>
        % endif

        \fancyfoot[L]{\small \rmfamily \color{gray} \today}
        \fancyfoot[C]{}
        \fancyfoot[R]{\small \rmfamily \color{gray} ${ latex_escape(_("Page {0}"), ignore_braces=True).format(r"\thepage") }}
    % endfor
</%block>
