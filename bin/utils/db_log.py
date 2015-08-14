# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import cPickle
import fcntl
import logging
import logging.handlers
import os
import pprint
import re
import signal
import SocketServer
import struct
import sys
import termios
import textwrap
from threading import Lock

import click
import sqlparse
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.agile import PythonLexer, PythonTracebackLexer
from pygments.lexers.sql import SqlLexer


ignored_line_re = re.compile(r'^(?:(?P<frame>\d+):)?(?P<file>.+?)(?::(?P<line>\d+))?$')
output_lock = Lock()
help_text = textwrap.dedent("""
    To use this script, you need to add the following to your logging.conf:

    [logger_db]
    level=DEBUG
    handlers=db
    qualname=indico.db
    propagate=0

    [handler_db]
    class=handlers.SocketHandler
    level=DEBUG
    args=('localhost', 9020)


    Also add your new logger/handler to the loggers/handlers lists, e.g. like this:

    [loggers]
    keys=root,db

    [handlers]
    keys=indico,db,other,smtp
    """).strip()


class LogRecordStreamHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            size = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(size)
            while len(chunk) < size:
                chunk = chunk + self.connection.recv(size - len(chunk))
            obj = cPickle.loads(chunk)
            self.handle_log(obj)

    def _check_ignored_sources(self, source):
        if not source or not self.server.ignored_sources:
            return None
        for entry in self.server.ignored_sources:
            try:
                frame = source[int(entry['frame'] or 1) - 1]
            except IndexError:
                continue
            if frame[0].endswith(entry['file']) and (entry['line'] is None or frame[1] == int(entry['line'])):
                return entry
        return None

    def handle_log(self, obj):
        if obj.get('req_path') in self.server.ignored_request_paths:
            return
        sql_log_type = obj.get('sql_log_type')
        if sql_log_type == 'start_request':
            with output_lock:
                print '\n' * 5
                print_linesep(True, 10)
                print '\x1b[38;5;70mBegin request\x1b[0m   {}'.format(obj['req_url'] or '')
                print_linesep()
            return
        elif sql_log_type == 'end_request':
            with output_lock:
                print '\x1b[38;5;202mEnd request\x1b[0m     {} [{} queries | {:.06f}s]'.format(obj['req_url'],
                                                                                               obj['sql_query_count'],
                                                                                               obj['req_duration'])
                print_linesep(True, 196)
            return
        if self.server.ignore_selects and obj.get('sql_verb') == 'SELECT':
            return
        ignored = self._check_ignored_sources(obj['sql_source'])
        if ignored:
            if sql_log_type == 'end':
                with output_lock:
                    print '\x1b[38;5;216mIgnored query\x1b[0m   {} [{:.06f}s]'.format(ignored['file'],
                                                                                      obj['sql_duration'])
                    print_linesep()
            return
        if sql_log_type == 'start':
            source = prettify_source(obj['sql_source'], self.server.traceback_frames) if obj['sql_source'] else None
            statement = prettify_statement(obj['sql_statement'])
            params = prettify_params(obj['sql_params']) if obj['sql_params'] else None
            with output_lock:
                if source:
                    print prettify_caption('Source')
                    print source
                    print
                print prettify_caption('Statement')
                print statement
                if params:
                    print
                    print prettify_caption('Params')
                    print params
        elif sql_log_type == 'end':
            with output_lock:
                print
                print prettify_caption('Duration')
                print '    {:.06f}s'.format(obj['sql_duration'])
                print_linesep()


class LogRecordSocketReceiver(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, host, port, traceback_frames, ignore_selects, ignored_sources, ignored_request_paths):
        SocketServer.ThreadingTCPServer.__init__(self, (host, port), LogRecordStreamHandler)
        self.timeout = 1
        self.traceback_frames = traceback_frames
        self.ignore_selects = ignore_selects
        self.ignored_sources = [ignored_line_re.match(s).groupdict() for s in ignored_sources]
        self.ignored_request_paths = set(ignored_request_paths)


def terminal_size():
    h, w, hp, wp = struct.unpack('HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
    return w, h


def print_linesep(double=False, color=None):
    char = u'\N{BOX DRAWINGS DOUBLE HORIZONTAL}' if double else u'\N{BOX DRAWINGS LIGHT HORIZONTAL}'
    sep = terminal_size()[0] * char
    if color is None:
        print sep
    else:
        print u'\x1b[38;5;{}m{}\x1b[0m'.format(color, sep)


def indent(msg, level=4):
    indentation = level * ' '
    return indentation + msg.replace('\n', '\n' + indentation)


def prettify_caption(caption):
    return '\x1b[38;5;75;04m{}\x1b[0m'.format(caption)


def prettify_source(source, traceback_frames):
    if not traceback_frames:
        return None
    msg = 'Traceback (most recent call last):\n'
    frame_msg = textwrap.dedent("""
    File "{}", line {}, in {}
      {}\n""").strip()
    msg += indent('\n'.join(frame_msg.format(*frame) for frame in source[:traceback_frames]), 2)
    highlighted = highlight(msg, PythonTracebackLexer(), Terminal256Formatter(style='native'))
    # Remove first line (just needed for PythonTracebackLexer)
    highlighted = '\n'.join(highlighted.splitlines()[1:])
    return indent(highlighted, 2).rstrip()


def prettify_statement(statement):
    statement = sqlparse.format(statement, keyword_case='upper', reindent=True)
    return indent(highlight(statement, SqlLexer(), Terminal256Formatter(style='native'))).rstrip()


def prettify_params(args):
    args = pprint.pformat(args)
    return indent(highlight(args, PythonLexer(), Terminal256Formatter(style='native'))).rstrip()


def sigint(*unused):
    print '\rTerminating'
    os._exit(1)


@click.command()
@click.option('-p', '--port', type=int, default=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
              help='The port to bind the UDP listener to')
@click.option('-t', '--traceback-frames', type=int, default=3,
              help='Number of stack frames to show (max. 5)')
@click.option('-S', '--ignore-selects', is_flag=True, help='If SELECTs should be hidden')
@click.option('-i', '--ignored-sources', multiple=True, metavar='[FRAME:]FILE[:LINENO]',
              help='Query origins to ignore. May be used multiple times.  If no line is specified, the whole file is '
                   'ignored.  If no frame is specified, frame 1 (the topmost one in the log) will be used.')
@click.option('-I', '--ignored-request-paths', multiple=True, metavar='PATH',
              help='Request paths to ignore. May be used multiple times.  Matched against request.path (e.g. '
                   '/assets/js-vars/user.js).')
@click.option('-H', '--setup-help', is_flag=True, help='Explain how to enable db logging for this script')
def main(port, traceback_frames, ignore_selects, ignored_sources, ignored_request_paths, setup_help):
    if setup_help:
        print help_text
        sys.exit(1)
    signal.signal(signal.SIGINT, sigint)
    print 'Listening on 127.0.0.1:{}'.format(port)
    server = LogRecordSocketReceiver('localhost', port, traceback_frames=traceback_frames,
                                     ignore_selects=ignore_selects, ignored_sources=ignored_sources,
                                     ignored_request_paths=ignored_request_paths)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print


if __name__ == '__main__':
    main()
