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
                ${latex_escape(person.person.full_name)}
                %if person.person.affiliation:
                    (${latex_escape(person.person.affiliation)})
                %endif
            }
        % endfor
        \end{itemize*}
    }

    \vspace{0.5em}
%endif
