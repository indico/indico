# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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

from __future__ import absolute_import

import os
import re
import textwrap
import uuid
from io import BytesIO
from mimetypes import guess_extension
from tempfile import NamedTemporaryFile
from urlparse import urlparse

import markdown
import requests
from lxml.html import html5parser
from PIL import Image
from requests.exceptions import ConnectionError, InvalidURL


__version__ = '2.1'


start_single_quote_re = re.compile(r"""(^|\s|")'""")
start_double_quote_re = re.compile(r'''(^|\s|'|`)"''')
end_double_quote_re = re.compile(r'"(,|\.|\s|$)')

Image.init()
IMAGE_FORMAT_EXTENSIONS = {format: ext for (ext, format) in Image.EXTENSION.viewitems()}

safe_mathmode_commands = {
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
    'vee', 'Vert', 'vert', 'vphantom', 'wedge', 'widehat', 'widetilde', 'wp', 'wr', 'Xi', 'xi', 'zeta', '\\'
}


class ImageURLException(Exception):
    pass


def unescape_html_entities(text):
    out = text.replace('&amp;', '&')
    out = out.replace('&lt;', '<')
    out = out.replace('&gt;', '>')
    out = out.replace('&quot;', '"')
    return out


def latex_escape(text, ignore_math=True, ignore_braces=False):
    if text is None:
        return ''

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

    math_placeholder = '[*LaTeXmath-{}*]'.format(unicode(uuid.uuid4()))

    def math_replace(m):
        math_segments.append(m.group(0))
        return math_placeholder

    if ignore_math:
        # Extract math-mode segments and replace with placeholder
        text = re.sub(r'\$[^\$]+\$|\$\$(^\$)\$\$', math_replace, text)

    pattern = re.compile('|'.join(re.escape(k) for k in chars.keys()))
    res = pattern.sub(substitute, text)

    if ignore_math:
        # Sanitize math-mode segments and put them back in place
        math_segments = map(sanitize_mathmode, math_segments)
        res = re.sub(re.escape(math_placeholder), lambda _: "\\protect " + math_segments.pop(0), res)

    return res


def sanitize_mathmode(text):
    def _escape_unsafe_command(m):
        command = m.group(1)
        return m.group(0) if command in safe_mathmode_commands else r'\\' + command

    return re.sub(r'\\([a-zA-Z]+|\\)', _escape_unsafe_command, text)


def escape_latex_entities(text):
    """Escape latex reserved characters."""
    out = text
    out = unescape_html_entities(out)
    out = start_single_quote_re.sub(r'\g<1>`', out)
    out = start_double_quote_re.sub(r'\g<1>``', out)
    out = end_double_quote_re.sub(r"''\g<1>", out)

    out = latex_escape(out)

    return out


def unescape_latex_entities(text):
    """Limit ourselves as this is only used for maths stuff."""
    out = text
    out = out.replace('\\&', '&')
    return out


def latex_render_error(message):
    """Generate nice error box in LaTeX document.

    :param message: The error message
    :returns: LaTeX code for error box
    """
    return textwrap.dedent(r"""
       \begin{tcolorbox}[width=\textwidth,colback=red!5!white,colframe=red!75!black,title={Indico rendering error}]
          \begin{verbatim}%s\end{verbatim}
       \end{tcolorbox}""" % latex_escape(message))


def latex_render_image(src, alt, tmpdir, strict=False):
    """Generate LaTeX code that includes an arbitrary image from a URL.

    This involves fetching the image from a web server and figuring out its
    MIME type. A temporary file will be created, which is not immediately
    deleted since it has to be included in the LaTeX code. It should be handled
    by the enclosing code.

    :param src: source URL of the image
    :param alt: text to use as ``alt="..."``
    :param tmpdir: the directory where to put any temporary files
    :param strict: whether a faulty URL should break the whole process
    :returns: a ``(latex_code, file_path)`` tuple, containing the LaTeX code
              and path to the temporary image file.
    """
    try:
        if urlparse(src).scheme not in ('http', 'https'):
            raise ImageURLException("URL scheme not supported: {}".format(src))
        else:
            try:
                resp = requests.get(src, verify=False, timeout=5)
            except InvalidURL:
                raise ImageURLException("Cannot understand URL '{}'".format(src))
            except (requests.Timeout, ConnectionError):
                raise ImageURLException("Problem downloading image ({})".format(src))
            except requests.TooManyRedirects:
                raise ImageURLException("Too many redirects downloading image ({})".format(src))
            extension = None

            if resp.status_code != 200:
                raise ImageURLException("[{}] Error fetching image".format(resp.status_code))

            if resp.headers.get('content-type'):
                extension = guess_extension(resp.headers['content-type'])
                # as incredible as it might seem, '.jpe' will be the answer in some Python environments
                if extension == '.jpe':
                    extension = '.jpg'
            if not extension:
                try:
                    # Try to use PIL to get file type
                    image = Image.open(BytesIO(resp.content))
                    # Worst case scenario, assume it's PNG
                    extension = IMAGE_FORMAT_EXTENSIONS.get(image.format, '.png')
                except IOError:
                    raise ImageURLException("Cannot read image data. Maybe not an image file?")
            with NamedTemporaryFile(prefix='indico-latex-', suffix=extension, dir=tmpdir, delete=False) as tempfile:
                tempfile.write(resp.content)
    except ImageURLException as e:
        if strict:
            raise
        else:
            return latex_render_error("Could not include image: {}".format(e.message)), None

    # Using graphicx and ajustbox package for *max width*
    return (textwrap.dedent(r"""
        \begin{figure}[H]
          \centering
          \includegraphics[max width=\linewidth]{%s}
          \caption{%s}
        \end{figure}
        """ % (os.path.basename(tempfile.name), latex_escape(alt))), tempfile.name)


def makeExtension(configs=None):
    return LaTeXExtension(configs=configs)


class LaTeXExtension(markdown.Extension):
    def __init__(self, configs=None):
        self.configs = configs
        self.reset()

    def extendMarkdown(self, md, md_globals):
        self.md = md

        # remove escape pattern -- \\(.*) -- as this messes up any embedded
        # math and we don't need to escape stuff any more for html
        self.md.inlinePatterns.deregister('escape')

        latex_tp = LaTeXTreeProcessor(self.configs)
        math_pp = MathTextPostProcessor()
        link_pp = LinkTextPostProcessor()
        unescape_html_pp = UnescapeHtmlTextPostProcessor()

        md.treeprocessors.register(latex_tp, 'latex', md.treeprocessors._priority[-1].priority - 1)
        md.postprocessors.register(unescape_html_pp, 'unescape_html', md.postprocessors._priority[-1].priority - 1)
        md.postprocessors.register(math_pp, 'math', md.postprocessors._priority[-1].priority - 1)
        md.postprocessors.register(link_pp, 'link', md.postprocessors._priority[-1].priority - 1)

        # Needed for LaTeX postprocessors not to choke on URL-encoded urls
        md.inlinePatterns.register(NonEncodedAutoMailPattern(markdown.inlinepatterns.AUTOMAIL_RE, md), 'automail',
                                   md.treeprocessors._priority[-1].priority - 1)

    def reset(self):
        pass


class NonEncodedAutoMailPattern(markdown.inlinepatterns.Pattern):
    """Reimplementation of AutoMailPattern to avoid URL-encoded links."""

    def handleMatch(self, m):
        el = markdown.util.etree.Element('a')
        email = self.unescape(m.group(2))
        if email.startswith("mailto:"):
            email = email[len("mailto:"):]
        el.text = markdown.util.AtomicString(''.join(email))
        mailto = "mailto:" + email
        mailto = "".join([markdown.util.AMP_SUBSTITUTE + '#%d;' %
                          ord(letter) for letter in mailto])
        el.set('href', latex_escape(mailto, ignore_math=False))
        return el


class LaTeXTreeProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, configs):
        self.configs = configs

    def run(self, doc):
        """
        Walk the dom converting relevant nodes to text nodes with relevant
        content.
        """
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
            buffer += r'\noindent\makebox[\linewidth]{\rule{\paperwidth}{0.4pt}}'
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
        elif (ournode.tag == 'pre' or (ournode.tag == 'pre' and ournode.parentNode.tag != 'pre')):
            buffer += """
\\begin{verbatim}
%s
\\end{verbatim}
""" % subcontent.strip()
        elif ournode.tag == 'q':
            buffer += "`%s'" % subcontent.strip()
        elif ournode.tag == 'p':
            if self.configs.get('apply_br'):
                subcontent = subcontent.replace('\n', '\\\\\\relax\n')
            buffer += '\n%s\n' % subcontent.strip()
        elif ournode.tag == 'strong':
            buffer += '\\textbf{%s}' % subcontent.strip()
        elif ournode.tag == 'em':
            buffer += '\\emph{%s}' % subcontent.strip()
        elif ournode.tag in ('table', 'thead', 'tbody', 'tr', 'th', 'td'):
            raise RuntimeError('Unexpected table in markdown data for LaTeX')
        elif ournode.tag == 'img':
            buffer += latex_render_image(ournode.get('src'), ournode.get('alt'), tmpdir=self.configs.get('tmpdir'))[0]
        elif ournode.tag == 'a':
            # this one gets escaped in convert_link_to_latex
            buffer += '<a href=\"%s\">%s</a>' % (ournode.get('href'), subcontent)
        else:
            buffer = subcontent

        if ournode.tail:
            buffer += escape_latex_entities(ournode.tail)

        return buffer


class UnescapeHtmlTextPostProcessor(markdown.postprocessors.Postprocessor):

    def run(self, text):
        return unescape_html_entities(text)

# ========================= MATH =================================


class MathTextPostProcessor(markdown.postprocessors.Postprocessor):

    def run(self, instr):
        """
        Convert all math sections in {text} whether latex, asciimathml or
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
        pat = re.compile(r'^\$\$([^$]*)\$\$\s*$', re.MULTILINE)
        out = pat.sub(repl_1, instr)
        # Jones, $x=3$, is ...
        pat3 = re.compile(r'\$([^$]+)\$(\s|$)')
        out = pat3.sub(repl_2, out)
        # # $100 million
        # pat2 = re.compile('([^\$])\$([^\$])')
        # out = pat2.sub('\g<1>\\$\g<2>', out)
        # some extras due to asciimathml
        # out = out.replace('\\lt', '<')
        # out = out.replace(' * ', ' \\cdot ')
        # out = out.replace('\\del', '\\partial')
        return out


# ========================== LINKS =================================

class LinkTextPostProcessor(markdown.postprocessors.Postprocessor):
    def run(self, instr):
        new_blocks = [re.sub(r'<a[^>]*>([^<]+)</a>', lambda m: convert_link_to_latex(m.group(0)).strip(), block)
                      for block in instr.split("\n\n")]
        return '\n\n'.join(new_blocks)


def convert_link_to_latex(instr):
    dom = html5parser.fragment_fromstring(instr)
    return u'\\href{%s}{%s}' % (latex_escape(dom.get('href'), ignore_math=True), dom.text)
