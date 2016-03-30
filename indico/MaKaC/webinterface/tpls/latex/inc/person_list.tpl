<%page args="caption,list"/>

% if list:
    {
        \normalsize
        { \bf
          \noindent
          ${caption} :
        }\begin{itemize*}[label=,itemjoin={{;}}]
        % for person in list:
            \item {
                \small
                \rmfamily
                ${latex_escape(person.full_name)}
                %if person.affiliation:
                    (${latex_escape(person.affiliation)})
                %endif
            }
        % endfor
        \end{itemize*}
    }

    \vspace{0.5em}
%endif
