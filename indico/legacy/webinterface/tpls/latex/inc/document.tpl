<%
    import os
    import pkg_resources
    distribution = pkg_resources.get_distribution('indico-fonts')
    font_dir = os.path.join(distribution.location, 'indico_fonts')
    # Trailing slash is necessary
    font_dir = os.path.join(font_dir, '')
%>

<%block name="document_class">
\documentclass[a4paper, 15pt]{article} %% document type
</%block>

<%block name="geometry">
\usepackage[a4paper, top=1em, bottom=10em]{geometry}
</%block>

\usepackage{hyperref}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{fontspec}

\usepackage[english]{babel}
\usepackage[final, babel]{microtype} %% texblog.net/latex-archive/layout/pdflatex-microtype/

\usepackage{float} %% improved interface for floating objects
\usepackage[export]{adjustbox}
\usepackage[usenames,dvipsnames]{xcolor} %% named colors
\usepackage{sectsty} %% style sections
\usepackage{xstring}
\usepackage{tcolorbox}
\usepackage[inline]{enumitem}
\usepackage[breakall]{truncate}
\usepackage[parfill]{parskip}

<%block name="header_extra">
</%block>


\begin{document}

    %% set fonts
    \setmainfont{LinLibertine_R.otf}[
        BoldFont = LinLibertine_RB.otf,
        ItalicFont = LinLibertine_RI.otf,
        BoldItalicFont = LinLibertine_RBI.otf,
        Path = ${ font_dir }]
    \setsansfont{LinBiolinum_R.otf}[
        BoldFont = LinBiolinum_RB.otf,
        ItalicFont = LinBiolinum_RI.otf,
        Path = ${ font_dir }]

    %% no indentation
    \setlength{\parindent}{0cm}

    %% helper commands

    \newcommand{\truncateellipses}[2]{
       \truncate{#2}{#1}
    }

    %% remove section heading numbering
    \setcounter{secnumdepth}{0}

    <%block name="content">
    </%block>

\end{document}
