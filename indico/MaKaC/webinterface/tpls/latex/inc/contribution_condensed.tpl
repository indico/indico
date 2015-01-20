<%page args="contrib, affiliation_contribs"/>
<% field_manager = contrib.getConference().getAbstractMgr().getAbstractFieldsMgr() %>

\noindent
\rmfamily
% if contrib.getSession():
\small \textbf {${contrib.getSession().getTitle() | latex_escape}}
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

\textbf {\Large ${contrib.getTitle() | latex_escape}
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
        % for affil, affil_id in sorted(affiliation_contribs[contrib.getId()]['affiliations'].items(), key=lambda x: x[1]):
            \item[]\textsuperscript{${affil_id}} {\em ${affil | latex_escape}}
        % endfor
    \end{description}
% endif

% if corresp_authors.get(contrib.getId()):
\textbf {${_("Corresponding Author(s):")}}
        ${", ".join(corresp_authors[contrib.getId()])}
% endif

\vspace{0.5em}

% if field_manager.hasActiveField('content'):
    %% Markdown content
    \setlength{\leftskip}{0.5cm}
    \rmfamily {
        \allsectionsfont{\rmfamily}
        \sectionfont{\normalsize\rmfamily}
        \subsectionfont{\small\rmfamily}
        \small
        ${ md_convert(str(contrib.getDescription()).decode('utf-8')).encode('utf-8') }
    }

    \vspace{1em}
    \setlength{\leftskip}{0pt}
% endif

% for field_id, content in contrib.getFields(valueonly=True).iteritems():
    % if field_id != 'content' and field_manager.hasActiveField(field_id):
        \textbf{${ field_manager.getFieldById(field_id).getCaption() }}:

        %% Markdown content
        \rmfamily {
            \allsectionsfont{\rmfamily}
            \sectionfont{\normalsize\rmfamily}
            \subsectionfont{\small\rmfamily}
            \small
            ${ md_convert(content.decode('utf-8')).encode('utf-8') }
        }

        \vspace{0.5em}
    % endif
% endfor
