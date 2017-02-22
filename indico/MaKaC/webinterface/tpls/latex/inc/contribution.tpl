<%page args="contrib"/>

%% header

{
    \small
    \sffamily
    \noindent
    ${_(u"Contribution ID") | latex_escape} : \textbf {${contrib.friendly_id}}
    \hfill
    ${_("Type") | latex_escape} : \textbf {${latex_escape(contrib.type.name if contrib.type else _('not specified'))}}
}

\vspace{2em}

\begin{center}
    \textbf {
        \LARGE
        \sffamily
        ${contrib.title | latex_escape}
    }
\end{center}

% if contrib.is_scheduled:
    {
        \hfill
        \em
        \small
        \color{gray}
        ${latex_escape(formatDate(contrib.start_dt, format="full", timezone=tz))} ${latex_escape(formatTime(contrib.start_dt, format="short", tz=tz))} (${latex_escape(str(formatDuration(contrib.duration)))})
    }
% endif

\vspace{1em}

\begin{addmargin}[1em]{1em}
    %% Markdown content
    \rmfamily {
        \allsectionsfont{\rmfamily}
        \sectionfont{\normalsize\rmfamily}
        \subsectionfont{\small\rmfamily}
        \small
        ${md_convert(contrib.description)}
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
            ${md_convert(contrib.get_field_value(field.id))}
        }
        \vspace{1.5em}
    \end{addmargin}

%endfor

\vspace{1.5em}

<%include file="person_list.tpl" args="caption=_('Primary author(s)'), list=contrib.primary_authors" />
<%include file="person_list.tpl" args="caption=_('Co-author(s)'), list=contrib.secondary_authors" />
<%include file="person_list.tpl" args="caption=_('Presenter(s)'), list=contrib.speakers" />

% if contrib.session:
{
    {
        \bf
        \noindent ${_("Session Classification") | latex_escape} :
    }
    ${latex_escape(contrib.session.title or _("not yet classified"))}
}

% endif

\vspace{1em}

% if contrib.track:
{
    {
        \bf
        \noindent ${_("Track Classification") | latex_escape} :
    }
    ${latex_escape(contrib.track.title or _("not specified"))}
}
% endif
