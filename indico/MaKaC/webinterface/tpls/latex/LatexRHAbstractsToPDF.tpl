\batchmode %% suppress output
\documentclass[a4paper, 11pt, oneside]{book} %% document type
\textwidth = 440pt
\hoffset = -40pt %% - inch
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc} %% http://tex.stackexchange.com/questions/44694/fontenc-vs-inputenc
\usepackage[final, babel]{microtype} %% texblog.net/latex-archive/layout/pdflatex-microtype/
\usepackage[export]{adjustbox} %% images
\usepackage{amsmath} %% math equations
\usepackage{float} %% improved interface for floating objects
\usepackage{times} %% font family
\usepackage[usenames,dvipsnames]{xcolor}
\usepackage[pdftex,
            final,
            pdfstartview = FitV,
            colorlinks = true, 
            urlcolor = Violet,
            breaklinks = true]{hyperref}  %% hyperlinks configuration
\usepackage{tocloft} %% table of contents
\usepackage{sectsty} %% default font family
\allsectionsfont{\rmfamily} %% default font family
\usepackage{titlesec}
\titleformat{\chapter}
  {\sffamily \fontsize{25}{30} \selectfont \centering}{\thechapter.}{1em}{}
\usepackage{fancyhdr} %% headers
\pagestyle{fancyplain} { %% define first page header and footer
\fancyhead[L]{}
\fancyhead[C]{}
\fancyhead[R]{}
\fancyfoot[L]{}
\fancyfoot[C]{}
\fancyfoot[R]{}
}

\renewcommand{\headrulewidth}{0pt}

\begin{document}
\setcounter{secnumdepth}{0} %% remove section heading numbering
\setcounter{tocdepth}{0} %% remove table of contents numbering

${ first_page }

\begingroup
\hypersetup{linkcolor=black}
\renewcommand{\contentsname}{\centerline{\fontsize{18}{20}\selectfont Table of contents}}
\renewcommand{\cftchapleader}{\cftdotfill{\cftdotsep}}
\tableofcontents
\endgroup

\newpage
\fancyhead[L]{\small \selectfont \color{gray} ${ title } / Abstracts Book}
\fancyhead[C]{}
\fancyhead[R]{}
\fancyfoot[L]{\small \selectfont \color{gray} \today}
\fancyfoot[C]{}
\fancyfoot[R]{\small \selectfont \color{gray} ${ page_no } \thepage}

${ body }

\end{document}
