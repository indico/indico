<%page args="conf,title,show_dates=False"/>


\begin{center}
    \huge \sffamily{${conf.getTitle() | latex_escape}}
\end{center}

%if show_dates:
    \begin{center}
        \textbf {
            ${conf.getAdjustedStartDate(tz).strftime("%A %d %B %Y")} - 
            ${conf.getAdjustedEndDate(tz).strftime("%A %d %B %Y")}
        }
    \end{center}

    % if conf.getLocation():
        \begin{center}
            ${conf.getLocation().getName()}
        \end{center}
    % endif

    \vspace{2em}
%endif

% if logo_img:
    \begin{figure}[h!]
        \includegraphics[max width=0.85\linewidth]{${logo_img}}
        \centering
    \end{figure}

    \vspace{4em}
% else:
    \vspace{2em}
% endif



\vspace{2em}

\begin{center}
    {\fontsize{40}{48}\selectfont \sffamily \textbf{${title}}}
\end{center}

% if show_url:
    \cfoot{\tt ${url}}
% else:
    \cfoot{}
%endif

\pagebreak