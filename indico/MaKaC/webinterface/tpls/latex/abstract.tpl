<%inherit file="inc/document.tpl" />

<%block name="content">

    \begin{center}
        \large {
            \sffamily {
                \textbf{${conf.getTitle() | latex_escape}}
            }
        }
    \end{center}

    \vspace{1em}

    % if logo_img:
        \begin{figure}[h!]
            \includegraphics[max width=0.85\linewidth]{${logo_img | latex_escape}}
            \centering
        \end{figure}
    % endif

    \vspace{2em}

    <%include file="inc/contribution.tpl"/>
</%block>