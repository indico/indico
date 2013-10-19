\batchmode %% suppress output
\documentclass[a4paper, 11pt]{article} %% document type
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
\usepackage{sectsty}
\allsectionsfont{\rmfamily}

\begin{document}
\setcounter{secnumdepth}{0} %% remove section heading numbering

${ body }

\end{document}
