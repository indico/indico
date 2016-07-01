<%page args="conf,title,show_dates=False"/>

\begin{titlepage}

\thispagestyle{fancy}

\begin{center}
    \fontsize{30}{36}\selectfont \textbf{${conf.getTitle() | latex_escape}}
\end{center}

\vspace{2em}

%if show_dates:
    \begin{center}
        \Large
        ${conf.getAdjustedStartDate(tz).strftime("%A %d %B %Y") | latex_escape} -
        ${conf.getAdjustedEndDate(tz).strftime("%A %d %B %Y") | latex_escape}
    \end{center}

    % if conf.getLocation():
        \begin{center}
            \Large
            ${conf.getLocation().getName() | latex_escape}
        \end{center}
    % endif

    \vspace{2em}
%endif

% if logo_img:
    \begin{figure}[h!]
        \includegraphics[max width=0.85\linewidth, min width=0.5\linewidth]{${logo_img}}
        \centering
    \end{figure}

    \vspace{4em}
% else:
    \vspace{2em}
% endif



\vspace{2em}

\begin{center}
    {\fontsize{35}{42}\selectfont \sffamily \textbf{${title | latex_escape}}}
\end{center}

% if url:
    \fancyfoot[C]{\tt ${url | latex_escape}}
% else:
    \fancyfoot[C]{}
% endif

\end{titlepage}
