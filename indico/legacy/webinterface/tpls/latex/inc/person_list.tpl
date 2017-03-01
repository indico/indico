<%page args="caption,list"/>

% if list:
    {
        \normalsize
        { \bf
          \noindent
          ${caption | latex_escape} :
        }\begin{itemize*}[label=,itemjoin={{;}}]
        % for person in list:
            \item {
                \small
                \rmfamily
                ${latex_escape(person.get_full_name(abbrev_first_name=False, show_title=True))}
                %if person.affiliation:
                    (${latex_escape(person.affiliation)})
                %endif
            }
        % endfor
        \end{itemize*}
    }
%endif
