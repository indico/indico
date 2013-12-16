<%inherit file="inc/document.tpl" />

<%block name="content">

    %% first page

    \begin{center}
        \large {
            \sffamily {
                \textbf{${conf.getTitle() | latex_escape}}
            }
        }
    \end{center}

    \vspace{1em}

    % if logo_img:
        \begin{figure}[h!]
            \includegraphics[max width=0.85\linewidth]{${logo_img | latex_escape}}
            \centering
        \end{figure}
    % endif

    \vspace{2em}

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
            ${escape(contrib.getTitle())}
        }
    \end{center}


    \vspace{1em}

    % if contrib.isScheduled():

        \begin{flushright}
            \em
            \small
            \hfill
            ${formatDate(contrib.getAdjustedStartDate(tz), format="full")} ${formatTime(contrib.getAdjustedStartDate(tz), format="short")} (${':'.join(str(contrib.getDuration()).split(':')[:2])})

        \end{flushright}
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
                ${md_convert(str(contrib.getField(field.getId())).strip())[7:-7]}
            }
            \vspace{1.5em}
        \end{addmargin}

    %endfor

    \vspace{1.5em}

    <%include file="inc/person_list.tpl" args="caption=_('Primary author(s)'), list=contrib.getPrimaryAuthorsList()" />
    <%include file="inc/person_list.tpl" args="caption=_('Co-author(s)'), list=contrib.getCoAuthorList()" />
    <%include file="inc/person_list.tpl" args="caption=_('Presenter(s)'), list=contrib.getSpeakerList()" />

    {
        {
            \bf
            \noindent ${_("Session Classification")} :
        }
        ${escape(contrib.getSession().getTitle()) or _("not yet classified")}
    }

    \vspace{1em}

    {
        {
            \bf
            \noindent ${_("Track Classification")} :
        }
        ${escape(contrib.getTrack().getTitle()) or _("not specified")}
    }

</%block>