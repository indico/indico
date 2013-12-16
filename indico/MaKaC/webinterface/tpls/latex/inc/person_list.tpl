<%page args="caption,list"/>

% if list:
    {
        \normalsize
        { \bf
          \noindent
          ${caption} :
        }
        \vspace{0.5em}

        % for person in list:
            {
                \small
                \rmfamily
                ${escape(person.getFullName())} (${escape(person.getAffiliation())})
            }
        % endfor
    }

    \vspace{1.5em}
%endif