\batchmode

<%block name="document_class">
\documentclass[a4paper, 11pt]{article} %% document type
</%block>

\usepackage[a4paper, top=1em, bottom=10em, left=5em, right=5em]{geometry}

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
\usepackage{hyperref}
\usepackage{sectsty}
\usepackage{xstring}
\usepackage[inline]{enumitem}

<%block name="header_extra">
</%block>


\begin{document}

    %% set fonts
    \renewcommand{\sfdefault}{cmbr}
    \renewcommand*{\familydefault}{\sfdefault}

    %% helper commands

    \newcommand{\truncateellipses}[2]{
       \StrLeft{#1}{#2}[\truncated]
       \truncated
       \IfStrEq{\truncated}{#1}{}{\dots}
    }

    %% remove section heading numbering
    \setcounter{secnumdepth}{0}

    <%block name="content">
    </%block>

\end{document}
