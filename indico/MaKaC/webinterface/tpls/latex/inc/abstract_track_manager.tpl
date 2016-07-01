<%page args="abstract,track_class,contrib_type,status,track_view"/>

<%inherit file="abstract.tpl" />

<%block name="management_data" args="track_view">
    \vspace{1em}
    \textbf{${_("Track Status:")} |latex_escape} ${track_view[0]}
    % if track_view[1] is not None:
        % if not isinstance(track_view[1], list):
            (${track_view[1].getId() | latex_escape}: ``${track_view[1].getTitle() | latex_escape}'')
        % else:
        \setdescription{leftmargin=2em,labelindent=2em}
        \begin{description}
            % for elem in track_view[1]:
                \item[${elem[0] | latex_escape}] ${elem[1] | latex_escape}
            % endfor
        \end{description}
        % endif
    % endif

    \vspace{1em}
</%block>
