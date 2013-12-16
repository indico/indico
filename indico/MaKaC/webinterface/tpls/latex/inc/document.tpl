\documentclass[a4paper, 11pt]{article} %% document type


\usepackage[a4paper, top=4em, bottom=2em, left=5em, right=5em]{geometry}

\usepackage{cmbright}
\usepackage[T1]{fontenc}
\usepackage[utf8x]{inputenc}
\usepackage{textcomp}
\usepackage{textgreek}
\usepackage[english]{babel}
\usepackage[final, babel]{microtype} %% texblog.net/latex-archive/layout/pdflatex-microtype/
\usepackage{amsmath} %% math equations
\usepackage{float} %% improved interface for floating objects
\usepackage[export]{adjustbox}
\usepackage[usenames,dvipsnames]{xcolor}
\usepackage{scrextend}

\usepackage[final,
            pdfstartview = FitV,
            colorlinks = true,
            urlcolor = Violet,
            breaklinks = true]{hyperref}  %% hyperlinks configuration
\usepackage{sectsty}

\begin{document}

    %% set fonts
    \renewcommand{\sfdefault}{cmbr}
    \renewcommand*{\familydefault}{\sfdefault}

    %% remove section heading numbering
    \setcounter{secnumdepth}{0}

    <%block name="content">
    </%block>

\end{document}
