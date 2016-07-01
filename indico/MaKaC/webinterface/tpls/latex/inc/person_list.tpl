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
                ${latex_escape(person.getFullName())}
                %if person.getAffiliation():
                    (${latex_escape(person.getAffiliation())})
                %endif
            }
        % endfor
        \end{itemize*}
    }

    \vspace{0.5em}
%endif