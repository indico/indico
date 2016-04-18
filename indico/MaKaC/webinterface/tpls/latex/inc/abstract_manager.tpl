<%page args="abstract,track_class,contrib_type,status,track_judgements"/>

<%inherit file="abstract.tpl" />

<%block name="management_data" args="status,track_judgements">
    \vspace{1em}

    \textbf{${_("Status:")}} ${status}
    \vspace{2em}

    \setdescription{leftmargin=2em,labelindent=2em}

    % if track_judgements and any(x[1] for x in track_judgements):
        \textbf{${_("Track Judgements:")}}
        \begin{description}
            % for track_name, judgement in track_judgements:
                % if judgement:
                    \small \item[${track_name}:] ${judgement}
                % endif
            % endfor
        \end{description}
    % endif

</%block>
