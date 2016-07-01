<%page args="abstract,track_class,contrib_type,status,track_judgements"/>

<%inherit file="abstract.tpl" />

<%block name="management_data" args="status,track_judgements">
    \vspace{1em}

    \textbf{${_("Status:") | latex_escape}} ${status | latex_escape}
    \vspace{2em}

    \setdescription{leftmargin=2em,labelindent=2em}

    % if track_judgements:
        \textbf{${_("Track Judgements:") | latex_escape}}
        \begin{description}
            % for track_name, judgement in track_judgements:
                % if judgement:
                    \small \item[${track_name | latex_escape}:] ${judgement | latex_escape}
                % endif
            % endfor
        \end{description}
    % endif

</%block>
