<%page args="abstract,track_class,contrib_type"/>

%% header

\setlength{\headheight}{20pt}
\pagestyle{fancy}
\renewcommand{\headrulewidth}{0pt}


{
    \small
    \sffamily
    \noindent
    ${_(u"Abstract ID")} : \textbf {${abstract.getId()}}
}

\vspace{2em}

\begin{center}
    \textbf {
        \LARGE
        \sffamily
        ${abstract.getTitle()}
    }
\end{center}

\vspace{1em}

% for field in fields:

    {\bf
        \noindent
        \large
        ${field.getCaption()}
    }
    \vspace{0.5em}

    \begin{addmargin}[1em]{1em}
        %% Markdown content
        \rmfamily {
            \allsectionsfont{\rmfamily}
            \sectionfont{\normalsize\rmfamily}
            \subsectionfont{\small\rmfamily}
            \small
            % if field._type == 'selection':
                ${md_convert(abstract.getField(field.getId()))}
            % else:
                ${md_convert(abstract.getField(field.getId()).value.decode('utf-8'))}
            % endif
        }
        \vspace{1.5em}
    \end{addmargin}

%endfor

\vspace{1.5em}

<%include file="person_list.tpl" args="caption=_('Primary author(s)'), list=abstract.getPrimaryAuthorsList()" />
<%include file="person_list.tpl" args="caption=_('Co-author(s)'), list=abstract.getCoAuthorList()" />
<%include file="person_list.tpl" args="caption=_('Presenter(s)'), list=abstract.getSpeakerList()" />

\vspace{0.5em}

% if track_class:
{
    {
        \bf
        \noindent ${_("Track Classification")} :
    }
    ${latex_escape(track_class)}
}
% endif

% if contrib_type:
{
    {
        \bf
        \noindent ${_("Contribution Type")} :
    }
    ${latex_escape(contrib_type.getName())}
}
% endif

% if abstract.getComments():
    \vspace{0.5em}
    \textbf{${_("Comments:")}}
    \begin{addmargin}[1em]{1em}
        ${abstract.getComments()}
    \end{addmargin}
% endif

<%block name="management_data">
</%block>

\vspace{0.5em}

${_("Submitted by {0} on {1}").format(
    r"\textbf{{{0}}}".format(abstract.getSubmitter().getFullName()),
    r"\textbf{{{0}}}".format(abstract.getSubmissionDate().strftime("%A %d %B %Y")))}
\fancyfoot[C]{\color{gray} ${_("Last modified:")} ${abstract.getModificationDate().strftime("%A %d %B %Y")}}
