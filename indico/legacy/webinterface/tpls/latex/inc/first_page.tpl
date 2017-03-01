<%page args="event,title,show_dates=False"/>

\begin{titlepage}

\thispagestyle{fancy}

\begin{center}
    \fontsize{30}{36}\selectfont \textbf{${event.title.encode('utf-8') | latex_escape}}
\end{center}

\vspace{2em}

%if show_dates:
    \begin{center}
        \Large
        ${event.start_dt.astimezone(tz).strftime("%A %d %B %Y") | latex_escape} -
        ${event.end_dt.astimezone(tz).strftime("%A %d %B %Y") | latex_escape}
    \end{center}

    % if event.venue_name:
        \begin{center}
            \Large
            ${event.venue_name | latex_escape}
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
