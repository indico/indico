<%page args="abstract,track_class,contrib_type"/>

%% header

\setlength{\headheight}{20pt}
\pagestyle{fancy}
\renewcommand{\headrulewidth}{0pt}


{
    \small
    \sffamily
    \noindent
    ${_(u"Abstract ID") | latex_escape} : \textbf {${abstract.friendly_id}}
}

\vspace{2em}

\begin{center}
    \textbf {
        \LARGE
        \sffamily
        ${abstract.title | latex_escape}
    }
\end{center}

\vspace{1em}

{\bf
    \noindent
    \large
    ${_("Content")}
}

\begin{addmargin}[1em]{1em}
    %% Markdown content
    \rmfamily {
        \allsectionsfont{\rmfamily}
        \sectionfont{\normalsize\rmfamily}
        \subsectionfont{\small\rmfamily}
        \small
        ${md_convert(abstract.description)}
    }
    \vspace{1.5em}
\end{addmargin}

% for field in fields:

    {\bf
        \noindent
        \large
        ${field.title | latex_escape}
    }

    \begin{addmargin}[1em]{1em}
        %% Markdown content
        \rmfamily {
            \allsectionsfont{\rmfamily}
            \sectionfont{\normalsize\rmfamily}
            \subsectionfont{\small\rmfamily}
            \small
            ${md_convert(abstract.data_by_field[field.id].friendly_data if field.id in abstract.data_by_field else '')}
        }
        \vspace{1.5em}
    \end{addmargin}

%endfor

\vspace{1.5em}

<%include file="person_list.tpl" args="caption=_('Primary author(s)'), list=abstract.primary_authors" />
<%include file="person_list.tpl" args="caption=_('Co-author(s)'), list=abstract.secondary_authors" />
<%include file="person_list.tpl" args="caption=_('Presenter(s)'), list=abstract.speakers" />


% if track_class:
{
    {
        \bf
        \noindent ${_("Track Classification") | latex_escape} :
    }
    ${latex_escape(track_class)}
}
% endif

% if contrib_type:
{
    {
        \bf
        \noindent ${_("Contribution Type") | latex_escape} :
    }
    ${latex_escape(contrib_type.name)}
}
% endif

% if abstract.submission_comment:
    \textbf{${_("Comments:") | latex_escape}}
    \begin{addmargin}[1em]{1em}
        ${abstract.submission_comment | latex_escape}
    \end{addmargin}
% endif

<%block name="management_data">
</%block>


${latex_escape(_("Submitted by {0} on {1}"), ignore_braces=True).format(
    r"\textbf{{{0}}}".format(latex_escape(abstract.submitter.get_full_name(abbrev_first_name=False, show_title=True).encode('utf-8'))),
    r"\textbf{{{0}}}".format(latex_escape(abstract.submitted_dt.strftime("%A %d %B %Y"))))}
% if abstract.modified_dt:
    \fancyfoot[C]{\color{gray} ${_("Last modified:") | latex_escape} ${abstract.modified_dt.strftime("%A %d %B %Y") | latex_escape}}
% endif
