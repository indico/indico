<%page args="contrib,affiliation_contribs"/>
\noindent
\rmfamily
% if contrib.getSession():
\small \textbf {${contrib.getSession().getTitle()}}
% endif
% if contrib.getBoardNumber():
    % if contrib.getSession():
        -
    % endif
    ${_("Board:")} ${contrib.getBoardNumber()}
% endif
% if contrib.getSession() or contrib.getBoardNumber():
/
% endif
\textbf{${contrib.getId()}}

\vspace{1em}

\textbf {\Large ${contrib.getTitle()}
}

\vspace{0.5em}

% if affiliation_contribs[contrib.getId()]['authors_affil']:
    \footnotesize {
        % if affiliation_contribs[contrib.getId()]['coauthors_affil']:
            \textbf {${_("Author(s):")}}
        % endif
        % for author, affil_id in affiliation_contribs[contrib.getId()]['authors_affil']:
            ${author.getFullName()}\textsuperscript{${affil_id}}
            % if not loop.last:
                ;
            % endif
        % endfor
    }
% endif

% if affiliation_contribs[contrib.getId()]['coauthors_affil']:
    \footnotesize {
        \textbf {${_("Co-author(s):")}}
        % for author, affil_id in affiliation_contribs[contrib.getId()]['coauthors_affil']:
            ${author.getFullName()}
            % if affil_id is not None:
                \textsuperscript{${affil_id}}
            % endif
            % if not loop.last:
                ;
            % endif
        % endfor
    }
% endif

% if affiliation_contribs[contrib.getId()]['affiliations']:
    \vspace{0.5em}
    \footnotesize \begin{description}
        % for affil, affil_id in affiliation_contribs[contrib.getId()]['affiliations'].items():
            \item[]\textsuperscript{${affil_id}} \em{${affil}}
        % endfor
    \end{description}
% endif

% if corresp_authors:
\textbf {${_("Corresponding Author(s):")}}
        ${",".join(corresp_authors)}
% endif

\vspace{0.5em}

%% Markdown content
\rmfamily {
    \allsectionsfont{\rmfamily}
    \sectionfont{\normalsize\rmfamily}
    \subsectionfont{\small\rmfamily}
    \small
    ${md_convert(str(contrib.getDescription()).decode('utf-8'))[7:-7].encode('utf-8')}
}
