# -*- coding: utf-8 -*-
# #
# #
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

import argparse
import cPickle
import fcntl
import logging
import logging.handlers
import os
import pprint
import signal
import SocketServer
import struct
import sys
import termios
import textwrap
from threading import Lock

import sqlparse
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.agile import PythonLexer, PythonTracebackLexer
from pygments.lexers.sql import SqlLexer


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

    def handle_log(self, obj):
        sql_log_type = obj.get('sql_log_type')
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

    def __init__(self, host, port, handler=LogRecordStreamHandler, traceback_frames=1):
        SocketServer.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.timeout = 1
        self.traceback_frames = traceback_frames


def terminal_size():
    h, w, hp, wp = struct.unpack('HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
    return w, h


def print_linesep():
    print terminal_size()[0] * u'\N{BOX DRAWINGS LIGHT HORIZONTAL}'


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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='port', type=int, default=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                        help='The port to bind the UDP listener to')
    parser.add_argument('-t', dest='traceback_frames', type=int, default=1,
                        help='Number of stack frames to show (max. 3)')
    parser.add_argument('--setup-help', action='store_true', help='Explain how to enable logging for script')
    return parser.parse_args()


def sigint(*unused):
    print '\rTerminating'
    os._exit(1)


def main():
    args = parse_args()
    if args.setup_help:
        print help_text
        sys.exit(1)
    signal.signal(signal.SIGINT, sigint)
    print 'Listening on 127.0.0.1:{}'.format(args.port)
    server = LogRecordSocketReceiver('localhost', args.port, traceback_frames=args.traceback_frames)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print


if __name__ == '__main__':
    main()
