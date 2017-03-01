<%inherit file="inc/document.tpl" />

<%block name="geometry">
\usepackage[a4paper, top=3em, bottom=10em]{geometry}
</%block>

<%block name="header_extra">
    \usepackage{scrextend}
    \pagenumbering{gobble}
    \usepackage{fancyhdr}

</%block>

<%block name="content">

    \fancyhead{}

    \begin{center}
        \large {
            \sffamily {
                \color{gray} \textbf{${conf.as_event.title.encode('utf-8') | latex_escape}}
            }
        }
    \end{center}

    % if logo_img:
        \begin{figure}[h!]
            \includegraphics[max width=0.85\linewidth, min width=0.5\linewidth, max height=10em]{${logo_img}}
            \centering
        \end{figure}
    % endif

        <%include file="inc/${doc_type}.tpl" args="status=status,
            track_view=track_view,
            track_judgements=track_judgements"/>
</%block>
