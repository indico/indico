#!/usr/bin/env python2
"""Extension to python-markdown to support LaTeX (rather than html) output.

Authored by Rufus Pollock: <http://www.rufuspollock.org/>
Reworked by Julian Wulfheide (ju.wulfheide@gmail.com) and
Indico Project (indico-team@cern.ch)

Usage:
======

1. Command Line. A script entitled markdown2latex.py is automatically
installed. For details of usage see help::

    $ markdown2latex.py -h

2. As a python-markdown extension::

    >>> import markdown
    >>> md = markdown.Markdown(None, extensions=['latex'])
    >>> # text is input string ...
    >>> latex_out = md.convert(text)

3. Directly as a module (slight inversion of std markdown extension setup)::

    >>> import markdown
    >>> import mdx_latex
    >>> md = markdown.Markdown()
    >>> latex_mdx = mdx_latex.LaTeXExtension()
    >>> latex_mdx.extendMarkdown(md, markdown.__dict__)
    >>> out = md.convert(text)

History
=======

Version: 1.0 (November 15, 2006)

  * First working version (compatible with markdown 1.5)
  * Includes support for tables

Version: 1.1 (January 17, 2007)

  * Support for verbatim and images

Version: 1.2 (June 2008)

  * Refactor as an extension.
  * Make into a proper python/setuptools package.
  * Tested with markdown 1.7 but should work with 1.6 and (possibly) 1.5
    (though pre/post processor stuff not as worked out there)

Version 1.3: (July 2008)
  * Improvements to image output (width)

Version 1.3.1: (August 2009)
  * Tiny bugfix to remove duplicate keyword argument and set zip_safe=False
  * Add [width=\textwidth] by default for included images

Version 2.0: (June 2011)
  * PEP8 cleanup
  * Major rework since this was broken by new Python-Markdown releases

Version 2.1: (August 2013)
  * Add handler for non locally referenced images, hyperlinks and horizontal rules
  * Update math delimiters
"""

__version__ = '2.1'

# do some fancy importing stuff to allow use to override things in this module
# in this file while still importing * for use in our own classes
import re
import sys
import markdown
import xml.dom.minidom
from urlparse import urlparse
import httplib
import os
import tempfile
import urllib


start_single_quote_re = re.compile("(^|\s|\")'")
start_double_quote_re = re.compile("(^|\s|'|`)\"")
end_double_quote_re = re.compile("\"(,|\.|\s|$)")

safe_mathmode_commands = set([
    'above', 'abovewithdelims', 'acute', 'aleph', 'alpha', 'amalg', 'And', 'angle', 'approx', 'arccos', 'arcsin',
    'arctan', 'arg', 'array', 'Arrowvert', 'arrowvert', 'ast', 'asymp', 'atop', 'atopwithdelims', 'backslash',
    'backslash', 'bar', 'Bbb', 'begin', 'beta', 'bf', 'Big', 'big', 'bigcap', 'bigcirc', 'bigcup', 'Bigg', 'bigg',
    'Biggl', 'biggl', 'Biggm', 'biggm', 'Biggr', 'biggr', 'Bigl', 'bigl', 'Bigm', 'bigm', 'bigodot', 'bigoplus',
    'bigotimes', 'Bigr', 'bigr', 'bigsqcup', 'bigtriangledown', 'bigtriangleup', 'biguplus', 'bigvee', 'bigwedge',
    'bmod', 'bot', 'bowtie', 'brace', 'bracevert', 'brack', 'breve', 'buildrel', 'bullet', 'cap', 'cases', 'cdot',
    'cdotp', 'cdots', 'check', 'chi', 'choose', 'circ', 'clubsuit', 'colon', 'cong', 'coprod', 'cos', 'cosh', 'cot',
    'coth', 'cr', 'csc', 'cup', 'dagger', 'dashv', 'ddagger', 'ddot', 'ddots', 'deg', 'Delta', 'delta', 'det',
    'diamond', 'diamondsuit', 'dim', 'displaylines', 'displaystyle', 'div', 'dot', 'doteq', 'dots', 'dotsb', 'dotsc',
    'dotsi', 'dotsm', 'dotso', 'Downarrow', 'downarrow', 'ell', 'emptyset', 'end', 'enspace', 'epsilon', 'eqalign',
    'eqalignno', 'equiv', 'eta', 'exists', 'exp', 'fbox', 'flat', 'forall', 'frac', 'frak', 'frown', 'Gamma', 'gamma',
    'gcd', 'ge', 'geq', 'gets', 'gg', 'grave', 'gt', 'gt', 'hat', 'hbar', 'hbox', 'hdashline', 'heartsuit', 'hline',
    'hom', 'hookleftarrow', 'hookrightarrow', 'hphantom', 'hskip', 'hspace', 'Huge', 'huge', 'iff', 'iiint', 'iint',
    'Im', 'imath', 'in', 'inf', 'infty', 'int', 'intop', 'iota', 'it', 'jmath', 'kappa', 'ker', 'kern', 'Lambda',
    'lambda', 'land', 'langle', 'LARGE', 'Large', 'large', 'LaTeX', 'lbrace', 'lbrack', 'lceil', 'ldotp', 'ldots', 'le',
    'left', 'Leftarrow', 'leftarrow', 'leftharpoondown', 'leftharpoonup', 'Leftrightarrow', 'leftrightarrow',
    'leftroot', 'leq', 'leqalignno', 'lfloor', 'lg', 'lgroup', 'lim', 'liminf', 'limits', 'limsup', 'll', 'llap',
    'lmoustache', 'ln', 'lnot', 'log', 'Longleftarrow', 'longleftarrow', 'Longleftrightarrow', 'longleftrightarrow',
    'longmapsto', 'Longrightarrow', 'longrightarrow', 'lor', 'lower', 'lt', 'lt', 'mapsto', 'mathbb', 'mathbf',
    'mathbin', 'mathcal', 'mathclose', 'mathfrak', 'mathinner', 'mathit', 'mathop', 'mathopen', 'mathord', 'mathpunct',
    'mathrel', 'mathrm', 'mathscr', 'mathsf', 'mathstrut', 'mathtt', 'matrix', 'max', 'mbox', 'mid', 'middle', 'min',
    'mit', 'mkern', 'mod', 'models', 'moveleft', 'moveright', 'mp', 'mskip', 'mspace', 'mu', 'nabla', 'natural', 'ne',
    'nearrow', 'neg', 'negthinspace', 'neq', 'newline', 'ni', 'nolimits', 'normalsize', 'not', 'notin', 'nu', 'nwarrow',
    'odot', 'oint', 'oldstyle', 'Omega', 'omega', 'omicron', 'ominus', 'oplus', 'oslash', 'otimes', 'over', 'overbrace',
    'overleftarrow', 'overleftrightarrow', 'overline', 'overrightarrow', 'overset', 'overwithdelims', 'owns',
    'parallel', 'partial', 'perp', 'phantom', 'Phi', 'phi', 'Pi', 'pi', 'pm', 'pmatrix', 'pmb', 'pmod', 'pod', 'Pr',
    'prec', 'preceq', 'prime', 'prod', 'propto', 'Psi', 'psi', 'qquad', 'quad', 'raise', 'rangle', 'rbrace', 'rbrack',
    'rceil', 'Re', 'rfloor', 'rgroup', 'rho', 'right', 'Rightarrow', 'rightarrow', 'rightharpoondown', 'rightharpoonup',
    'rightleftharpoons', 'rlap', 'rm', 'rmoustache', 'root', 'S', 'scr', 'scriptscriptstyle', 'scriptsize',
    'scriptstyle', 'searrow', 'sec', 'setminus', 'sf', 'sharp', 'Sigma', 'sigma', 'sim', 'simeq', 'sin', 'sinh', 'skew',
    'small', 'smallint', 'smash', 'smile', 'Space', 'space', 'spadesuit', 'sqcap', 'sqcup', 'sqrt', 'sqsubseteq',
    'sqsupseteq', 'stackrel', 'star', 'strut', 'subset', 'subseteq', 'succ', 'succeq', 'sum', 'sup', 'supset',
    'supseteq', 'surd', 'swarrow', 'tan', 'tanh', 'tau', 'TeX', 'text', 'textbf', 'textit', 'textrm', 'textsf',
    'textstyle', 'texttt', 'Theta', 'theta', 'thinspace', 'tilde', 'times', 'tiny', 'to', 'top', 'triangle',
    'triangleleft', 'triangleright', 'tt', 'underbrace', 'underleftarrow', 'underleftrightarrow', 'underline',
    'underrightarrow', 'underset', 'Uparrow', 'uparrow', 'Updownarrow', 'updownarrow', 'uplus', 'uproot', 'Upsilon',
    'upsilon', 'varepsilon', 'varphi', 'varpi', 'varrho', 'varsigma', 'vartheta', 'vcenter', 'vdash', 'vdots', 'vec',
    'vee', 'Vert', 'vert', 'vphantom', 'wedge', 'widehat', 'widetilde', 'wp', 'wr', 'Xi', 'xi', 'zeta'
])


def unescape_html_entities(text):
    out = text.replace('&amp;', '&')
    out = out.replace('&lt;', '<')
    out = out.replace('&gt;', '>')
    out = out.replace('&quot;', '"')
    return out


def latex_escape(text, ignore_math=True, ignore_braces=False):
    chars = {
        "#": r"\#",
        "$": r"\$",
        "%": r"\%",
        "&": r"\&",
        "~": r"\~{}",
        "_": r"\_",
        "^": r"\^{}",
        "\\": r"\textbackslash{}",
        "\x0c": "",
        "\x0b": ""
    }

    if not ignore_braces:
        chars.update({
            "{": r"\{",
            "}": r"\}"})

    math_segments = []

    def substitute(x):
        return chars[x.group()]

    def math_replace(m):
        math_segments.append(m.group(0))
        return "[*LaTeXmath*]"

    if ignore_math:
        # Extract math-mode segments and replace with placeholder
        text = re.sub(r'\$[^\$]+\$|\$\$(^\$)\$\$', math_replace, text)

    pattern = re.compile('|'.join(re.escape(k) for k in chars.keys()))
    res = pattern.sub(substitute, text)

    if ignore_math:
        # Sanitize math-mode segments and put them back in place
        math_segments = map(sanitize_mathmode, math_segments)
        res = re.sub(r'\[\*LaTeXmath\*\]', lambda _: "\\protect " + math_segments.pop(0), res)

    return res


def sanitize_mathmode(text):
    def _escape_unsafe_command(m):
        command = m.group(2)
        return m.group(0) if command in safe_mathmode_commands else m.group(1) + r'\\' + command

    return re.sub(r'(^|[^\\])\\([a-zA-Z]+)', _escape_unsafe_command, text)


def escape_latex_entities(text):
    """Escape latex reserved characters."""
    out = text
    out = unescape_html_entities(out)
    out = start_single_quote_re.sub('\g<1>`', out)
    out = start_double_quote_re.sub('\g<1>``', out)
    out = end_double_quote_re.sub("''\g<1>", out)

    out = latex_escape(out)

    return out


def unescape_latex_entities(text):
    """Limit ourselves as this is only used for maths stuff."""
    out = text
    out = out.replace('\\&', '&')
    return out


def makeExtension(configs=None):
    return LaTeXExtension(configs=configs)


class LaTeXExtension(markdown.Extension):
    def __init__(self, configs=None):
        self.reset()

    def extendMarkdown(self, md, md_globals):
        self.md = md

        # remove escape pattern -- \\(.*) -- as this messes up any embedded
        # math and we don't need to escape stuff any more for html
        for key, pat in self.md.inlinePatterns.iteritems():
            if pat.pattern == markdown.inlinepatterns.ESCAPE_RE:
                self.md.inlinePatterns.pop(key)
                break

        #footnote_extension = FootnoteExtension()
        #footnote_extension.extendMarkdown(md, md_globals)

        latex_tp = LaTeXTreeProcessor()
        math_pp = MathTextPostProcessor()
        table_pp = TableTextPostProcessor()
        image_pp = ImageTextPostProcessor()
        link_pp = LinkTextPostProcessor()
        unescape_html_pp = UnescapeHtmlTextPostProcessor()

        md.treeprocessors['latex'] = latex_tp
        md.postprocessors['unescape_html'] = unescape_html_pp
        md.postprocessors['math'] = math_pp
        md.postprocessors['image'] = image_pp
        md.postprocessors['table'] = table_pp
        md.postprocessors['link'] = link_pp

    def reset(self):
        pass


class LaTeXTreeProcessor(markdown.treeprocessors.Treeprocessor):
    def run(self, doc):
        """Walk the dom converting relevant nodes to text nodes with relevant
        content."""
        latex_text = self.tolatex(doc)
        doc.clear()
        doc.text = latex_text

    def tolatex(self, ournode):
        buffer = ""
        subcontent = ""

        if ournode.text:
            subcontent += escape_latex_entities(ournode.text)

        if ournode.getchildren():
            for child in ournode.getchildren():
                subcontent += self.tolatex(child)

        if ournode.tag == 'h1':
            buffer += '\n\n\\section{%s}\n' % subcontent
        elif ournode.tag == 'h2':
            buffer += '\n\n\\subsection{%s}\n' % subcontent
        elif ournode.tag == 'h3':
            buffer += '\n\\subsubsection{%s}\n' % subcontent
        elif ournode.tag == 'h4':
            buffer += '\n\\paragraph{%s}\n' % subcontent
        elif ournode.tag == 'hr':
            buffer += '\\noindent\makebox[\linewidth]{\\rule{\paperwidth}{0.4pt}}'
        elif ournode.tag == 'ul':
            # no need for leading \n as one will be provided by li
            buffer += """
\\begin{itemize}%s
\\end{itemize}
""" % subcontent
        elif ournode.tag == 'ol':
            # no need for leading \n as one will be provided by li
            buffer += """
\\begin{enumerate}%s
\\end{enumerate}
""" % subcontent
        elif ournode.tag == 'li':
            buffer += """
  \\item %s""" % subcontent.strip()
        elif ournode.tag == 'blockquote':
            # use quotation rather than quote as quotation can support multiple
            # paragraphs
            buffer += """
\\begin{quotation}
%s
\\end{quotation}
""" % subcontent.strip()
        # ignore 'code' when inside pre tags
        # (mkdn produces <pre><code></code></pre>)
        elif (ournode.tag == 'pre' or
                             # TODO: Take a look here
             (ournode.tag == 'pre' and ournode.parentNode.tag != 'pre')):
            buffer += """
\\begin{verbatim}
%s
\\end{verbatim}
""" % subcontent.strip()
        elif ournode.tag == 'q':
            buffer += "`%s'" % subcontent.strip()
        elif ournode.tag == 'p':
            buffer += '\n%s\n' % subcontent.strip()
        # Footnote processor inserts all of the footnote in a sup tag
        elif ournode.tag == 'sup':
            buffer += '\\footnote{%s}' % subcontent.strip()
        elif ournode.tag == 'strong':
            buffer += '\\textbf{%s}' % subcontent.strip()
        elif ournode.tag == 'em':
            buffer += '\\emph{%s}' % subcontent.strip()
        # Keep table strcuture. TableTextPostProcessor will take care.
        elif ournode.tag == 'table':
            buffer += '\n\n<table>%s</table>\n\n' % subcontent
        elif ournode.tag == 'thead':
            buffer += '<thead>%s</thead>' % subcontent
        elif ournode.tag == 'tbody':
            buffer += '<tbody>%s</tbody>' % subcontent
        elif ournode.tag == 'tr':
            buffer += '<tr>%s</tr>' % subcontent
        elif ournode.tag == 'th':
            buffer += '<th>%s</th>' % subcontent
        elif ournode.tag == 'td':
            buffer += '<td>%s</td>' % subcontent
        elif ournode.tag == 'img':
            buffer += '<img src=\"%s\" alt=\"%s\" />' % (ournode.get('src'),
                      ournode.get('alt'))
        elif ournode.tag == 'a':
            buffer += '<a href=\"%s\">%s</a>' % (ournode.get('href'),
                      subcontent)
        else:
            buffer = subcontent

        if ournode.tail:
            buffer += escape_latex_entities(ournode.tail)

        return buffer


class UnescapeHtmlTextPostProcessor(markdown.postprocessors.Postprocessor):

    def run(self, text):
        return unescape_html_entities(text)

# ========================= MATHS =================================


class MathTextPostProcessor(markdown.postprocessors.Postprocessor):

    def run(self, instr):
        """Convert all math sections in {text} whether latex, asciimathml or
        latexmathml formatted to latex.

        This assumes you are using $$ as your mathematics delimiter (*not* the
        standard asciimathml or latexmathml delimiter).
        """
        def repl_1(matchobj):
            text = unescape_latex_entities(matchobj.group(1))
            tmp = text.strip()
            if tmp.startswith('\\[') or tmp.startswith('\\begin'):
                return text
            else:
                return '\\[%s\\]\n' % text

        def repl_2(matchobj):
            text = unescape_latex_entities(matchobj.group(1))
            return '$%s$%s' % (text, matchobj.group(2))

        # $$ ..... $$
        pat = re.compile('^\$\$([^\$]*)\$\$\s*$', re.MULTILINE)
        out = pat.sub(repl_1, instr)
        # Jones, $x=3$, is ...
        pat3 = re.compile(r'\$([^\$]+)\$(\s|$)')
        out = pat3.sub(repl_2, out)
        # # $100 million
        # pat2 = re.compile('([^\$])\$([^\$])')
        # out = pat2.sub('\g<1>\\$\g<2>', out)
        # some extras due to asciimathml
        # out = out.replace('\\lt', '<')
        # out = out.replace(' * ', ' \\cdot ')
        # out = out.replace('\\del', '\\partial')
        return out

# ========================= TABLES =================================


class TableTextPostProcessor(markdown.postprocessors.Postprocessor):

    def run(self, instr):
        """This is not very sophisticated and for it to work it is expected
        that:
            1. tables to be in a section on their own (that is at least one
            blank line above and below)
            2. no nesting of tables
        """
        converter = Table2Latex()
        new_blocks = []

        for block in instr.split('\n\n'):
            stripped = block.strip()
            # <table catches modified verions (e.g. <table class="..">
            if stripped.startswith('<table') and stripped.endswith('</table>'):
                latex_table = converter.convert(stripped).strip()
                new_blocks.append(latex_table)
            else:
                new_blocks.append(block)
        return '\n\n'.join(new_blocks)


class Table2Latex:
    """
    Convert html tables to Latex.

    TODO: escape latex entities.
    """

    def colformat(self):
        # centre align everything by default
        out = '|l' * self.maxcols + '|'
        return out

    def get_text(self, element):
        if element.nodeType == element.TEXT_NODE:
            return escape_latex_entities(element.data)
        result = ''
        if element.childNodes:
            for child in element.childNodes:
                text = self.get_text(child)
                if text.strip() != '':
                    result += text
        return result

    def process_cell(self, element):
        # works on both td and th
        colspan = 1
        subcontent = self.get_text(element)
        buffer = ""

        if element.tagName == 'th':
            subcontent = '\\textbf{%s}' % subcontent
        if element.hasAttribute('colspan'):
            colspan = int(element.getAttribute('colspan'))
            buffer += ' \multicolumn{%s}{|c|}{%s}' % (colspan, subcontent)
        # we don't support rowspan because:
        #   1. it needs an extra latex package \usepackage{multirow}
        #   2. it requires us to mess around with the alignment tags in
        #   subsequent rows (i.e. suppose the first col in row A is rowspan 2
        #   then in row B in the latex we will need a leading &)
        # if element.hasAttribute('rowspan'):
        #     rowspan = int(element.getAttribute('rowspan'))
        #     buffer += ' \multirow{%s}{|c|}{%s}' % (rowspan, subcontent)
        else:
            buffer += ' %s' % subcontent

        notLast = (element.nextSibling.nextSibling and
                   element.nextSibling.nextSibling.nodeType ==
                   element.ELEMENT_NODE and
                   element.nextSibling.nextSibling.tagName in ['td', 'th'])

        if notLast:
            buffer += ' &'

        self.numcols += colspan
        return buffer

    def tolatex(self, element):
        if element.nodeType == element.TEXT_NODE:
            return ""

        buffer = ""
        subcontent = ""
        if element.childNodes:
            for child in element.childNodes:
                text = self.tolatex(child)
                if text.strip() != "":
                    subcontent += text
        subcontent = subcontent.strip()

        if element.tagName == 'thead':
            buffer += subcontent

        elif element.tagName == 'tr':
            self.maxcols = max(self.numcols, self.maxcols)
            self.numcols = 0
            buffer += '\n\\hline\n%s \\\\' % subcontent

        elif element.tagName == 'td' or element.tagName == 'th':
            buffer = self.process_cell(element)
        else:
            buffer += subcontent
        return buffer

    def convert(self, instr):
        self.numcols = 0
        self.maxcols = 0
        dom = xml.dom.minidom.parseString(instr)
        core = self.tolatex(dom.documentElement)

        captionElements = dom.documentElement.getElementsByTagName('caption')
        caption = ''
        if captionElements:
            caption = self.get_text(captionElements[0])

        colformatting = self.colformat()
        table_latex = \
            """
            \\begin{table}[h]
            \\begin{tabular}{%s}
            %s
            \\hline
            \\end{tabular}
            \\\\[5pt]
            \\caption{%s}
            \\end{table}
            """ % (colformatting, core, caption)
        return table_latex


# ========================= IMAGES =================================

class ImageTextPostProcessor(markdown.postprocessors.Postprocessor):

    def run(self, instr):
        """Process all img tags

        Similar to process_tables this is not very sophisticated and for it
        to work it is expected that img tags are put in a section of their own
        (that is separated by at least one blank line above and below).
        """
        converter = Img2Latex()
        new_blocks = []
        for block in instr.split("\n\n"):
            stripped = block.strip()
            # <table catches modified verions (e.g. <table class="..">
            if stripped.startswith('<img'):
                latex_img = converter.convert(stripped).strip()
                new_blocks.append(latex_img)
            else:
                new_blocks.append(block)
        return '\n\n'.join(new_blocks)


class Img2Latex(object):
    def convert(self, instr):
        dom = xml.dom.minidom.parseString(instr)
        img = dom.documentElement
        src = img.getAttribute('src')

        if urlparse(src).scheme != '':
            src_urlparse = urlparse(src)
            conn = httplib.HTTPConnection(src_urlparse.netloc)
            conn.request('HEAD', src_urlparse.path)
            response = conn.getresponse()
            conn.close()
            if response.status == 200:
                filename = os.path.join(tempfile.mkdtemp(), src.split('/')[-1])
                urllib.urlretrieve(src, filename)
                src = filename

        alt = img.getAttribute('alt')
	# Using graphicx and ajustbox package for *max width*
        out = \
            """
            \\begin{figure}[H]
            \\centering
            \\includegraphics[max width=\\linewidth]{%s}
            \\caption{%s}
            \\end{figure}
            """ % (src, alt)
        return out


# ========================== LINKS =================================

class LinkTextPostProcessor(markdown.postprocessors.Postprocessor):

    def run(self, instr):
        # Process all hyperlinks
        converter = Link2Latex()
        new_blocks = []
        for block in instr.split("\n\n"):
            stripped = block.strip()
            match = re.search(r'<a[^>]*>([^<]+)</a>', stripped)
            # <table catches modified verions (e.g. <table class="..">
            if match:
                latex_link = re.sub(r'<a[^>]*>([^<]+)</a>',
                                    converter.convert(match.group(0)).strip(),
                                    stripped)
                new_blocks.append(latex_link)
            else:
                new_blocks.append(block)
        return '\n\n'.join(new_blocks)


class Link2Latex(object):
    def convert(self, instr):
        dom = xml.dom.minidom.parseString(instr)
        link = dom.documentElement
        href = link.getAttribute('href')

        desc = re.search(r'>([^<]+)', instr)
        out = \
            """
            \\href{%s}{%s}
            """ % (href, desc.group(0)[1:])
        return out


"""
========================= FOOTNOTES =================================

LaTeX footnote support.

Implemented via modification of original markdown approach (place footnote
definition in footnote market <sup> as opposed to putting a reference link).
"""


class FootnoteExtension (markdown.Extension):
    DEF_RE = re.compile(r"(\ ?\ ?\ ?)\[\^([^\]]*)\]:\s*(.*)")
    SHORT_USE_RE = re.compile(r"\[\^([^\]]*)\]", re.M)  # [^a]

    def __init__(self, configs=None):
        self.reset()

    def extendMarkdown(self, md, md_globals):
        self.md = md

        # Stateless extensions do not need to be registered
        md.registerExtension(self)

        # Insert a preprocessor before ReferencePreprocessor
        #index = md.preprocessors.index(md_globals['REFERENCE_PREPROCESSOR'])
        #preprocessor = FootnotePreprocessor(self)
        #preprocessor.md = md
        #md.preprocessors.insert(index, preprocessor)
        md.preprocessors.add('footnotes', FootnotePreprocessor(self), '_begin')

        ## Insert an inline pattern before ImageReferencePattern
        FOOTNOTE_RE = r"\[\^([^\]]*)\]"  # blah blah [^1] blah
        #index = md.inlinePatterns.index(md_globals['IMAGE_REFERENCE_PATTERN'])
        #md.inlinePatterns.insert(index, FootnotePattern(FOOTNOTE_RE, self))
        md.inlinePatterns.add('footnotes', FootnotePattern(FOOTNOTE_RE, self),
                              '_begin')

    def reset(self):
        self.used_footnotes = {}
        self.footnotes = {}

    def setFootnote(self, id, text):
        self.footnotes[id] = text


class FootnotePreprocessor:
    def __init__(self, footnotes):
        self.footnotes = footnotes

    def run(self, lines):
        self.blockGuru = BlockGuru()
        lines = self._handleFootnoteDefinitions(lines)

        # Make a hash of all footnote marks in the text so that we
        # know in what order they are supposed to appear.  (This
        # function call doesn't really substitute anything - it's just
        # a way to get a callback for each occurence.

        text = "\n".join(lines)
        self.footnotes.SHORT_USE_RE.sub(self.recordFootnoteUse, text)

        return text.split("\n")

    def recordFootnoteUse(self, match):
        id = match.group(1)
        id = id.strip()
        nextNum = len(self.footnotes.used_footnotes.keys()) + 1
        self.footnotes.used_footnotes[id] = nextNum

    def _handleFootnoteDefinitions(self, lines):
        """Recursively finds all footnote definitions in the lines.

            @param lines: a list of lines of text
            @returns: a string representing the text with footnote
                      definitions removed """

        i, id, footnote = self._findFootnoteDefinition(lines)

        if id:

            plain = lines[:i]

            detabbed, theRest = self.blockGuru.detectTabbed(lines[i + 1:])

            self.footnotes.setFootnote(id,
                                       footnote + "\n"
                                       + "\n".join(detabbed))

            more_plain = self._handleFootnoteDefinitions(theRest)
            return plain + [""] + more_plain

        else:
            return lines

    def _findFootnoteDefinition(self, lines):
        """Finds the first line of a footnote definition.

            @param lines: a list of lines of text
            @returns: the index of the line containing a footnote definition.
        """

        counter = 0
        for line in lines:
            m = self.footnotes.DEF_RE.match(line)
            if m:
                return counter, m.group(2), m.group(3)
            counter += 1
        return counter, None, None


class FootnotePattern(markdown.inlinepatterns.Pattern):

    def __init__(self, pattern, footnotes):
        markdown.inlinepatterns.Pattern.__init__(self, pattern)
        self.footnotes = footnotes

    def handleMatch(self, m, doc):
        sup = doc.createElement('sup')
        id = m.group(2)
        # stick the footnote text in the sup
        self.footnotes.md._processSection(sup,
                                          self.footnotes.footnotes[id].split("\n"))
        return sup


def template(template_fo, latex_to_insert):
    tmpl = template_fo.read()
    tmpl = tmpl.replace('INSERT-TEXT-HERE', latex_to_insert)
    return tmpl
    # title_items = [ '\\title', '\\end{abstract}', '\\thanks', '\\author' ]
    # has_title_stuff = False
    # for it in title_items:
    #    has_title_stuff = has_title_stuff or (it in tmpl)


def main():
    import optparse
    usage = \
        """usage: %prog [options] <in-file-path>

        Given a file path, process it using markdown2latex and print the result on
        stdout.

        If using template option template should place text INSERT-TEXT-HERE in the
        template where text should be inserted.
        """
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--template', dest='template',
                      default='',
                      help='path to latex template file (optional)')
    (options, args) = parser.parse_args()
    if not len(args) > 0:
        parser.print_help()
        sys.exit(1)
    inpath = args[0]
    infile = file(inpath)

    md = markdown.Markdown()
    mkdn2latex = LaTeXExtension()
    mkdn2latex.extendMarkdown(md, markdown.__dict__)
    out = md.convert(infile.read())

    if options.template:
        tmpl_fo = file(options.template)
        out = template(tmpl_fo, out)

    print out

if __name__ == '__main__':
    main()
