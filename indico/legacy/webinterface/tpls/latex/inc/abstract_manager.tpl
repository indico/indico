<%page args="abstract,track_class,contrib_type,status,track_judgements"/>

<%inherit file="abstract.tpl" />

<%block name="management_data" args="status,track_judgements">
    \vspace{1em}

    \textbf{${_("Status:") | latex_escape}} ${status | latex_escape}
    \vspace{2em}

    \setdescription{leftmargin=2em,labelindent=2em}

    % if track_judgements and any(x[1] for x in track_judgements):
        \textbf{${_("Track Reviews:") | latex_escape}}
        \begin{addmargin}[1em]{1em}
            % for track_name, judgement, details in track_judgements:
                % if judgement:
                    \small \textbf{${track_name | latex_escape}:}
                    \begin{addmargin}[1em]{1em}
                        \vspace{0.5em}

                        \textbf{${_("Judgments:")}} ${judgement | latex_escape}

                        % if details:
                            \vspace{0.5em}
                            \textbf{${_("Reviews:")}}
                            % for proposed_action, reviewer, comment in details:
                                \vspace{0.5em}
                                \begin{addmargin}[1em]{1em}
                                    \rmfamily {
                                        \allsectionsfont{\rmfamily}
                                        \sectionfont{\normalsize\rmfamily}
                                        \subsectionfont{\small\rmfamily}
                                        \small
                                        ${ reviewer | latex_escape }:
                                        \textbf{ ${proposed_action | latex_escape} }
                                        % if comment:
                                            (${ md_convert(comment)})
                                        % endif
                                    }
                                \end{addmargin}
                            % endfor
                        % endif
                    \end{addmargin}
                % endif
            % endfor
        \end{addmargin}
    % endif

</%block>
