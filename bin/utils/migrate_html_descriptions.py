import re
import sys
from itertools import chain, ifilter

import click
import html5lib
from html2text import HTML2Text
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import HtmlLexer
from xml.dom import minidom

from indico.core.db.sqlalchemy.util.session import update_session_options
from indico.core.db import DBMgr, db
from indico.util.string import render_markdown
from indico.web.flask.app import make_app

from StringIO import StringIO

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


def _split_trailing_whitespace(text, _empty_or_trailing_ws_only=re.compile(r'()(\s*(?!.))', re.MULTILINE | re.DOTALL),
                               _trailing_ws_regex=re.compile(r'(.*?)((?<=[^\s])\s*(?!.))', re.MULTILINE | re.DOTALL)):
    match = _empty_or_trailing_ws_only_regex.match(text)
    if match:
        return match.groups(0)
    else:
        return _trailing_ws_regex.match(text).groups(0)


def _contains_problematic_space_near_delimiter(
        text,
        _space_after_starting_delimiter=re.compile(r'.*^[\*_]\s', re.MULTILINE | re.DOTALL)
        _space_around_delimiter_regex=re.compile(r'.*\s[\*_]\s', re.MULTILINE | re.DOTALL)):
    return (_space_around_delimiter_regex.match(text) is not None or
            _space_after_starting_delimiter.match(text) is not None)


def migrate_description(obj, verbose, html_log):
    h = HTML2Text()
    h.unicode_snob = True
    input_html = re.sub(r'^\r?\n$', '<br>', unicode(obj.description))

    parser = html5lib.HTMLParser(tree=html5lib.getTreeBuilder("dom"))
    document = parser.parse(input_html)

    convert_to_markdown = True
    dom_modified = False

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

    if convert_to_markdown:
        result = h.handle(result)

    if verbose:
        click.echo(click.style('\n' + ' ' * 80, bg='cyan', fg='black'))
        click.echo(click.style(repr(obj), fg='cyan'))
        click.echo(_deleted(highlight(unicode(input_html), HtmlLexer(), Terminal256Formatter())))
        click.echo(_added(result))

    if convert_to_markdown and re.search(r'</\w+>', result):
        click.echo(click.style('[FAIL] ', fg='yellow', bold=True) + click.style(repr(obj), fg='cyan'))
        click.echo(click.style(obj.description, fg='yellow', dim=True))
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


@click.command()
@click.option('--dry-run', help='Do not actually save to the DB', is_flag=True)
@click.option('-e', '--event', help='Process only contributions in the given event', type=int)
@click.option('-c', '--category', help='Process only contributions in the given category', type=int)
@click.option('-l', '--html-log', help='HTML log file with original and converted data', type=click.File('w'))
@click.option('-v', '--verbose', help='Be extra verbose', is_flag=True)
def main(event, category, dry_run, html_log, verbose):
    html_tag_regex = '<[a-zA-Z]+.*>'
    contribs = db.m.Contribution.find(db.m.Contribution.description.op('~')(html_tag_regex))
    log = StringIO() if html_log else None

    if event:
        contribs = contribs.filter(db.m.Contribution.event_id == event)
    elif category:
        contribs = contribs.join(db.m.Event).filter(db.m.Event.category_chain_overlaps(category))

    if log:
        log.write('<table style="width: 100%;">')
    for contrib in contribs:
        if '<html>' in unicode(contrib.description):
            click.echo(click.style('[HTML DOCUMENT] ', fg='red', bold=True) + repr(contrib))
        else:
            migrate_description(contrib, verbose, log)

    if not event:
        categories = db.m.Category.find(db.m.Category.description.op('~')(html_tag_regex))
        if category:
            categories = categories.filter(db.m.Category.id == category)
        for category in categories:
            migrate_description(category, verbose, log)

    events = db.m.Event.find(db.m.Event.description.op('~')(html_tag_regex))
    if event:
        events = events.filter(db.m.Event.id == event)
    if category:
        events = events.filter(db.m.Event.category_chain_overlaps(category))
    for event in events:
        migrate_description(event, verbose, log)

    if log:
        log.write('</table>')

    if html_log:
        log.seek(0)
        html_log.write(HTML_TPL.format(log.read()))

    if not dry_run:
        db.session.commit()


if __name__ == '__main__':
    update_session_options(db)
    with make_app().app_context():
        with DBMgr.getInstance().global_connection():
            main()
