<%page args="contrib"/>

%% header


\vspace{2em}

\begin{flushleft}
    \noindent
    {\bf
        \sffamily
        \large
        % if sorted_by == "boardNo":
            ${contrib.getTitle()}
        % else:
            ${contrib.getId()} - ${contrib.getTitle()}
        % endif
    }
    \\*
    \vspace{1em}
    \small
    % if contrib.getSession():
        ${contrib.getSession().getTitle()}
    % endif
    % if contrib.getBoardNumber():
        - ${_("Board:")} ${contrib.getBoardNumber()}
    % endif
    % if contrib.isScheduled():
        - ${formatDate(contrib.getAdjustedStartDate(tz), format="full")} ${formatTime(contrib.getAdjustedStartDate(tz), format="short")}
    % endif
    \\*
    % if contrib.getSpeakerList():
        \small {
            \bf
            ${_("Presenters:")}
            % for spk in contrib.getSpeakerList():
                ${spk.getFullName()}
                % if spk.getAffiliation().strip():
                    (${spk.getAffiliation()})
                % endif
                % if not loop.last:
                    ;
                % endif
            % endfor
        }
        \vspace{1em}
    % endif

    %% Markdown content
    \rmfamily {
        \allsectionsfont{\rmfamily}
        \sectionfont{\normalsize\rmfamily}
        \subsectionfont{\small\rmfamily}
        \small
        ${md_convert(str(contrib.getDescription()).decode('utf-8'))[7:-7].encode('utf-8')}
    }
\end{flushleft}
