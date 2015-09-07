<%page args="contrib"/>

%% header

{
    \small
    \sffamily
    \noindent
    ${_(u"Contribution ID")} : \textbf {${contrib.getId()}}
    \hfill
    ${_("Type")} : \textbf {${contrib.getType().getName() if contrib.getType() else _('not specified')}}
}

\vspace{2em}

\begin{center}
    \textbf {
        \LARGE
        \sffamily
        ${contrib.getTitle() | latex_escape}
    }
\end{center}

% if contrib.isScheduled():
    {
        \hfill
        \em
        \small
        \color{gray}
        ${formatDate(contrib.getAdjustedStartDate(tz), format="full")} ${formatTime(contrib.getAdjustedStartDate(tz), format="short", tz=tz)} (${':'.join(str(contrib.getDuration()).split(':')[:2])})
    }
% endif

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
            ${md_convert(str(contrib.getField(field.getId())).decode('utf-8')).encode('utf-8')}
        }
        \vspace{1.5em}
    \end{addmargin}

%endfor

\vspace{1.5em}

<%include file="person_list.tpl" args="caption=_('Primary author(s)'), list=contrib.getPrimaryAuthorsList()" />
<%include file="person_list.tpl" args="caption=_('Co-author(s)'), list=contrib.getCoAuthorList()" />
<%include file="person_list.tpl" args="caption=_('Presenter(s)'), list=contrib.getSpeakerList()" />

% if contrib.getSession():
{
    {
        \bf
        \noindent ${_("Session Classification")} :
    }
    ${latex_escape(contrib.getSession().getTitle()) or _("not yet classified")}
}

% endif

\vspace{1em}

% if contrib.getTrack():
{
    {
        \bf
        \noindent ${_("Track Classification")} :
    }
    ${latex_escape(contrib.getTrack().getTitle()) or _("not specified")}
}
% endif
