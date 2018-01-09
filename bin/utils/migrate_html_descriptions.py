# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import re
import subprocess
import sys
from contextlib import contextmanager
from cStringIO import StringIO
from itertools import chain, ifilter
from xml.dom import minidom

import click
import html5lib
from html2text import HTML2Text
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import HtmlLexer

from indico.core.db import db
from indico.util.string import render_markdown
from indico.web.flask.app import make_app


EMPTY_OR_TRALING_WS_ONLY_REGEX = re.compile(r'()(\s*(?!.))', re.MULTILINE | re.DOTALL)
TRAILING_WS_REGEX = re.compile(r'(.*?)((?<=[^\s])\s*(?!.))', re.MULTILINE | re.DOTALL)
HTML_TAG_REGEX = '<[a-zA-Z]+.*>'

HTML_TPL = b"""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Comparison log</title>
    <style>
        td {{
            white-space: normal;
        }}
    </style>
</head>
<body>
{}
</body>
</html>
"""

ROW_TPL = b"""<tr style="background-color: #ddd;">
    <td style="max-width: 10%;">{}</td>
    <td style="max-width: 45%; white-space: pre-wrap; word-wrap: break-word;">{}</td>
    <td style="max-width: 45%;">{}</td>
</tr>
"""


def _deleted(text):
    red_mark = click.style('- ', fg='red')
    return '\n'.join((red_mark + line) for line in text.split('\n'))


def _added(text):
    green_mark = click.style('+ ', fg='green')
    return '\n'.join((green_mark + click.style(line, fg='yellow')) for line in text.split('\n'))


def _new_row(html_log, obj, result):
    if html_log:
        if isinstance(obj, db.m.Category):
            obj_id = 'category {}'.format(obj.id)
        else:
            obj_id = '{} / {}'.format(obj.event_id, obj.id)
        html_log.write((ROW_TPL.format("{} ({})".format(obj.title.encode('utf-8'), obj_id),
                        obj.description.encode('utf-8'), render_markdown(result).encode('utf-8'))))


def _node_and_next_siblings(node):
    parent = node.parentNode
    return parent.childNodes[parent.childNodes.index(node):]


def _insertAfter(new_node, node):
    index = node.parentNode.childNodes.index(node)
    if index >= len(node.parentNode.childNodes) - 1:
        node.parentNode.appendChild(new_node)
    else:
        node.parentNode.insertBefore(new_node, node.parentNode.childNodes[index + 1])


def _depth_first_descendants(node):
    if node.childNodes:
        for child in node.childNodes:
            for descendant in _depth_first_descendants(child):
                yield descendant
    else:
        yield node


def _depth_first_descendants_from_end(node):
    if node.childNodes:
        for child in reversed(node.childNodes):
            for descendant in _depth_first_descendants_from_end(child):
                yield descendant
    else:
        yield node


def _is_text_node(node):
    return isinstance(node, minidom.Text)


def _get_first_text_node(node):
    return next(ifilter(_is_text_node, _depth_first_descendants(node)), None)


def _get_last_text_node(node):
    return next(ifilter(_is_text_node, _depth_first_descendants_from_end(node)), None)


def _split_leading_whitespace(text, _leading_whitespace_regex=re.compile(r'(\s*)(.*)')):
    return _leading_whitespace_regex.match(text).groups(0)


def _split_trailing_whitespace(text, _empty_or_trailing_ws_only_regex=EMPTY_OR_TRALING_WS_ONLY_REGEX,
                               _trailing_ws_regex=TRAILING_WS_REGEX):
    match = _empty_or_trailing_ws_only_regex.match(text)
    if match:
        return match.groups(0)
    else:
        return _trailing_ws_regex.match(text).groups(0)


def _contains_problematic_space_near_delimiter(
        text,
        _space_after_starting_delimiter=re.compile(r'.*^[\*_]\s', re.MULTILINE | re.DOTALL),
        _space_around_delimiter_regex=re.compile(r'.*\s[\*_]\s', re.MULTILINE | re.DOTALL)):
    return (_space_around_delimiter_regex.match(text) is not None or
            _space_after_starting_delimiter.match(text) is not None)


def convert_using_html2text(text):
    h = HTML2Text(bodywidth=0)
    h.unicode_snob = True
    return h.handle(text)


def convert_using_pandoc(text):
    sp = subprocess.Popen(['pandoc', '--from', 'html', '--to', 'markdown_strict-raw_html'],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    result, __ = sp.communicate(text.encode('utf-8'))
    return result.decode('utf-8')


def purify_html(input_html, obj):
    parser = html5lib.HTMLParser(tree=html5lib.getTreeBuilder("dom"))
    document = parser.parse(input_html)

    convert_to_markdown = True
    dom_modified = False

    # Group consecutive orphaned <li>s inside a <ul>
    for li in document.getElementsByTagName('li'):
        node = li
        has_proper_parent = False
        while node.tagName != 'body' and node.parentNode:
            node = node.parentNode
            if node.tagName in {'ul', 'ol'}:
                has_proper_parent = True

        if not has_proper_parent:
            sibling_items = []
            sibling = li
            while sibling and sibling.nodeType == minidom.Node.ELEMENT_NODE and sibling.tagName == 'li':
                sibling_items.append(sibling)
                sibling = sibling.nextSibling
                # jump over empty nodes
                while sibling and sibling.nodeType == minidom.Node.TEXT_NODE and sibling.data.isspace():
                    sibling = sibling.nextSibling

            container = document.createElement('ul')
            li.parentNode.replaceChild(container, li)
            print "!! Adding missing ul", obj
            container.appendChild(li)
            for child in sibling_items:
                if child != li:
                    container.appendChild(child)
            dom_modified = True

    # Handle missing <li>
    for ul in document.getElementsByTagName('ul'):
        for child in ul.childNodes:
            if isinstance(child, minidom.Comment) or isinstance(child, minidom.Text) and not child.data.isspace():
                print "!! Adding missing li", obj
                li = document.createElement('li')
                ul.insertBefore(li, child)
                ul.removeChild(child)
                li.appendChild(child)
                dom_modified = True

    # Markdown doesn't allow paragraph inside a list
    for ul in chain(document.getElementsByTagName('ul'), document.getElementsByTagName('ol')):
        for li in ul.childNodes:
            if not isinstance(li, (minidom.Text, minidom.Comment)):
                if li.getElementsByTagName('p'):
                    print "!! Cannot convert to markdown because a list contains a paragraph:", obj
                    convert_to_markdown = False

    # Markdown doesn't like a bold or italic section to start or end with a whitespace
    for element in chain(document.getElementsByTagName('em'), document.getElementsByTagName('strong'),
                         document.getElementsByTagName('i'),  document.getElementsByTagName('b')):
        first_text_node = _get_first_text_node(element)
        if first_text_node is not None:
            whitespace, text = _split_leading_whitespace(first_text_node.data)
            if whitespace:
                print "!! Moving leading whitespace outside of the element:", obj
                first_text_node.data = text
                element.parentNode.insertBefore(document.createTextNode(whitespace), element)
                dom_modified = True
        last_text_node = _get_last_text_node(element)
        if last_text_node is not None:
            text, whitespace = _split_trailing_whitespace(last_text_node.data)
            if whitespace:
                print "!! Moving trailing whitespace outside of the element:", obj, whitespace.__repr__()
                last_text_node.data = text
                _insertAfter(document.createTextNode(whitespace), element)
                dom_modified = True

    # Our markdown render don't handle * and _ followed by a whitespace after a newline correctly.
    # The descriptions using those sequences of characters will be left as HTML. When we use a
    # spec-compliant Markdown renderer those descriptions could be converted to Markdown
    #
    # For instance the following is not rendered properly:
    # Something
    # * a
    # * b
    # * c
    if _contains_problematic_space_near_delimiter("".join([x.toxml() for x
                                                           in document.getElementsByTagName('body')[0].childNodes])):
        print "!! Cannot convert to markdown because the description contains '_ ' or '* ' " \
              "at a position which is very likely to trigger bugs in our markdown renderer." \
              "(It is likely that this description is not being rendered properly in its current form.)", obj
        # I'm pretty sure that converting such descriptions now yields CommonMark-compliant Markdown but proper
        # testing with a compliant python parser has not been performed. I'm leaving those description as
        # HTML for now which should make it easier to find them when switching to a compliant Markdown renderer.
        convert_to_markdown = False

    if convert_to_markdown and dom_modified:
        result = "".join([x.toxml() for x in document.getElementsByTagName('body')[0].childNodes])
    else:
        result = input_html

    return result, convert_to_markdown


def migrate_description(obj, verbose, html_log, use_pandoc=False):
    input_html = re.sub(r'^\r?\n$', '<br>', unicode(obj.description))

    result, convert_to_markdown = purify_html(input_html, obj)

    if convert_to_markdown:
        if use_pandoc:
            result = convert_using_pandoc(result)
        else:
            result = convert_using_html2text(result)

    if verbose:
        click.echo(click.style('\n' + ' ' * 80, bg='cyan', fg='black'))
        click.echo(click.style(repr(obj), fg='cyan'))
        click.echo(_deleted(highlight(unicode(input_html), HtmlLexer(), Terminal256Formatter())))
        click.echo(_added(result))

    if convert_to_markdown and re.search(r'</\w+>', result):
        click.echo(click.style('[FAIL] ', fg='yellow', bold=True) + click.style(repr(obj), fg='cyan'))
        click.echo(click.style(obj.description, fg='red', dim=True))
        click.echo(click.style(result, fg='green', dim=True))
        choice = click.prompt("What do you want to do? [s = skip / c = change anyway / q = quit]")

        if choice == 's':
            return
        elif choice == 'q':
            sys.exit(1)
        else:
            _new_row(html_log, obj, result)
    else:
        _new_row(html_log, obj, result)

    obj.description = result


@contextmanager
def html_log_writer(f):
    log = StringIO()
    log.write('<table style="width: 100%;">')
    yield log
    log.write('</table>')
    log.seek(0)
    if f:
        f.write(HTML_TPL.format(log.read()))


@click.group()
@click.option('--dry-run', help='Do not actually save to the DB', is_flag=True)
@click.option('-l', '--html-log', help='HTML log file with original and converted data', type=click.File('w'))
@click.option('-v', '--verbose', help='Be extra verbose', is_flag=True)
@click.option('-p', '--use-pandoc', help="Use pandoc instead of html2text", is_flag=True)
@click.pass_context
def cli(ctx, dry_run, html_log, verbose, use_pandoc):
    ctx.obj.update({
        'dry_run': dry_run,
        'html_log': html_log,
        'verbose': verbose,
        'use_pandoc': use_pandoc
    })


@click.command()
@click.option('-e', '--event', help='Process only descriptions in the given event', type=int)
@click.option('-c', '--category', help='Process only descriptions for the given category', type=int)
@click.pass_context
def contribution_descriptions(ctx, event, category):
    contribs = db.m.Contribution.find(db.m.Contribution.description.op('~')(HTML_TAG_REGEX))

    with html_log_writer(ctx.obj['html_log']) as log:
        if event:
            contribs = contribs.filter(db.m.Contribution.event_id == event)
        elif category:
            contribs = contribs.join(db.m.Event).filter(db.m.Event.category_chain_overlaps(category))

        for contrib in contribs:
            if '<html>' in unicode(contrib.description):
                click.echo(click.style('[HTML DOCUMENT] ', fg='red', bold=True) + repr(contrib))
            else:
                migrate_description(contrib, ctx.obj['verbose'], log, use_pandoc=ctx.obj['use_pandoc'])

    if not ctx.obj['dry_run']:
        db.session.commit()


@click.command()
@click.option('-c', '--category', help='Process only descriptions for the given category', type=int)
@click.pass_context
def category_descriptions(ctx, category):
    with html_log_writer(ctx.obj['html_log']) as log:
        categories = db.m.Category.find(db.m.Category.description.op('~')(HTML_TAG_REGEX))
        if category:
            categories = categories.filter(db.m.Category.id == category)
        for category in categories:
            migrate_description(category, ctx.obj['verbose'], log, use_pandoc=ctx.obj['use_pandoc'])

    if not ctx.obj['dry_run']:
        db.session.commit()


cli.add_command(category_descriptions)
cli.add_command(contribution_descriptions)


if __name__ == '__main__':
    with make_app().app_context():
        cli(obj={})
