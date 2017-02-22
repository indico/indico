<%page args="contrib, affiliation_contribs"/>

\noindent
\rmfamily
% if contrib.session:
\small \textbf {${contrib.session.title | latex_escape}}
% endif
% if contrib.board_number:
    % if contrib.session:
        -
    % endif
    ${_("Board:") | latex_escape} \verb|${contrib.board_number | latex_escape}|
% endif
% if contrib.session or contrib.board_number:
/
% endif
\textbf{${contrib.friendly_id}}

\vspace{1em}

\textbf {\Large ${contrib.title | latex_escape}
}

\vspace{0.5em}

% if affiliation_contribs[contrib.id]['authors_affil']:
    \footnotesize {
        % if affiliation_contribs[contrib.id]['coauthors_affil']:
            \textbf {${_("Author(s):") | latex_escape}}
        % endif
        % for author, affil_id in affiliation_contribs[contrib.id]['authors_affil']:
            ${author.full_name | latex_escape}\textsuperscript{${affil_id}}
            % if not loop.last:
                ;
            % endif
        % endfor
    }
% endif

% if affiliation_contribs[contrib.id]['coauthors_affil']:
    \footnotesize {
        \textbf {${_("Co-author(s):") | latex_escape}}
        % for author, affil_id in affiliation_contribs[contrib.id]['coauthors_affil']:
            ${author.full_name | latex_escape}
            % if affil_id is not None:
                \textsuperscript{${affil_id}}
            % endif
            % if not loop.last:
                ;
            % endif
        % endfor
    }
% endif

% if affiliation_contribs[contrib.id]['affiliations']:
    \vspace{0.5em}
    \footnotesize \begin{description}
        % for affil, affil_id in sorted(affiliation_contribs[contrib.id]['affiliations'].items(), key=lambda x: x[1]):
            \item[]\textsuperscript{${affil_id}} {\em ${affil | latex_escape}}
        % endfor
    \end{description}
% endif

% if corresp_authors.get(contrib.id):
\textbf {${_("Corresponding Author(s):") | latex_escape}}
        ${", ".join(corresp_authors[contrib.id]) | latex_escape}
% endif

\vspace{0.5em}

% if contrib.description:
    %% Markdown content
    \setlength{\leftskip}{0.5cm}
    \rmfamily {
        \allsectionsfont{\rmfamily}
        \sectionfont{\normalsize\rmfamily}
        \subsectionfont{\small\rmfamily}
        \small
        ${ md_convert(contrib.description) }
    }

    \vspace{1em}
    \setlength{\leftskip}{0pt}
% endif

% for field_value in contrib.field_values:
    \textbf{${ field_value.contribution_field.title | latex_escape}}:

    %% Markdown content
    \rmfamily {
        \allsectionsfont{\rmfamily}
        \sectionfont{\normalsize\rmfamily}
        \subsectionfont{\small\rmfamily}
        \small
        ${ md_convert(field_value.friendly_data) }
    }
% endfor
