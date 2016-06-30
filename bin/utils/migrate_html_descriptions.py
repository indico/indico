import re
import sys

import click
from html2text import HTML2Text
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import HtmlLexer

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
        html_log.write((ROW_TPL.format("{} ({})".format(obj.title.encode('utf-8'), obj.event_id),
                        obj.description.encode('utf-8'), render_markdown(result).encode('utf-8'))))


def migrate_description(obj, verbose, html_log):
    h = HTML2Text()
    h.unicode_snob = True
    input_html = re.sub(r'^\r?\n$', '<br>', unicode(obj.description))
    result = h.handle(input_html)

    if verbose:
        click.echo(click.style('\n' + ' ' * 80, bg='cyan', fg='black'))
        click.echo(click.style(repr(obj), fg='cyan'))
        click.echo(_deleted(highlight(unicode(obj.description), HtmlLexer(), Terminal256Formatter())))
        click.echo(_added(result))

    if re.search(r'</\w+>', result):
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
    contribs = db.m.Contribution.find(db.m.Contribution.description.op('~')('</[a-zA-Z]+>'))
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
