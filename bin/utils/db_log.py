# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import fcntl
import logging.handlers
import os
import pickle
import pprint
import re
import signal
import struct
import termios
import textwrap
from socketserver import StreamRequestHandler, ThreadingTCPServer
from threading import Lock

import click
import sqlparse
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.agile import PythonLexer, PythonTracebackLexer
from pygments.lexers.sql import SqlLexer


ignored_line_re = re.compile(r'^(?:(?P<frame>\d+):)?(?P<file>.+?)(?::(?P<line>\d+))?$')
output_lock = Lock()


class LogRecordStreamHandler(StreamRequestHandler):
    def handle(self):
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            size = struct.unpack(b'>L', chunk)[0]
            chunk = self.connection.recv(size)
            while len(chunk) < size:
                chunk = chunk + self.connection.recv(size - len(chunk))
            obj = pickle.loads(chunk)
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

    def _format_request(self, obj):
        if obj['repl']:
            return '\x1b[38;5;243m<shell>\x1b[0m'
        elif obj['req_verb'] and obj['req_url']:
            return '{} {}'.format(obj['req_verb'], obj['req_url'])
        else:
            return '\x1b[38;5;243m<unknown>\x1b[0m'

    def handle_log(self, obj):
        if any(p.match(obj.get('req_path') or '') for p in self.server.ignored_request_paths):
            return
        sql_log_type = obj.get('sql_log_type')
        if sql_log_type == 'start_request':
            with output_lock:
                print('\n' * 5)
                print_linesep(True, 10)
                print('\x1b[38;5;70mBegin request\x1b[0m  {}'.format(self._format_request(obj)))
                print_linesep()
            return
        elif sql_log_type == 'end_request':
            with output_lock:
                fmt = '\x1b[38;5;202mEnd request\x1b[0m    {} [{} queries ({}) | {}]'
                print(fmt.format(self._format_request(obj),
                                 prettify_count(obj['sql_query_count']),
                                 prettify_duration(obj['req_query_duration'], True),
                                 prettify_duration(obj['req_duration'], True)))
                print_linesep(True, 196)
            return
        # XXX: `WITH` queries could be something different from SELECT but so far
        # we only use CTEs for selecting
        if self.server.ignore_selects and obj.get('sql_verb') in ('SELECT', 'WITH'):
            return
        ignored = obj.get('sql_verb') in ('SELECT', 'WITH') and self._check_ignored_sources(obj['sql_source'])
        if ignored:
            if sql_log_type == 'end':
                with output_lock:
                    print('\x1b[38;5;216mIgnored query\x1b[0m   {} [{:.06f}s]'.format(ignored['file'],
                                                                                      obj['sql_duration']))
                    print_linesep()
            return
        if sql_log_type == 'start':
            source = prettify_source(obj['sql_source'], self.server.traceback_frames) if obj['sql_source'] else None
            statement = prettify_statement(obj['sql_statement'])
            params = prettify_params(obj['sql_params']) if obj['sql_params'] else None
            with output_lock:
                if source:
                    print(prettify_caption('Source'))
                    print(source)
                    print()
                print(prettify_caption('Statement'))
                print(statement)
                if params:
                    print()
                    print(prettify_caption('Params'))
                    print(params)
        elif sql_log_type == 'end':
            with output_lock:
                print()
                print(prettify_caption('Duration'))
                print('    {}'.format(prettify_duration(obj['sql_duration'])))
                print_linesep()


class LogRecordSocketReceiver(ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, host, port, traceback_frames, ignore_selects, ignored_sources, ignored_request_paths):
        ThreadingTCPServer.__init__(self, (host, port), LogRecordStreamHandler)
        self.timeout = 1
        self.traceback_frames = traceback_frames
        self.ignore_selects = ignore_selects
        self.ignored_sources = [ignored_line_re.match(s).groupdict() for s in ignored_sources]
        self.ignored_request_paths = {self._process_path(x) for x in ignored_request_paths}

    def _process_path(self, path):
        regex = path[1:] if path[0] == '~' else re.escape(path)
        return re.compile(f'^{regex}$')


def terminal_size():
    h, w, hp, wp = struct.unpack(b'HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack(b'HHHH', 0, 0, 0, 0)))
    return w, h


def print_linesep(double=False, color=None):
    char = '\N{BOX DRAWINGS DOUBLE HORIZONTAL}' if double else '\N{BOX DRAWINGS LIGHT HORIZONTAL}'
    sep = terminal_size()[0] * char
    if color is None:
        print(sep)
    else:
        print(f'\x1b[38;5;{color}m{sep}\x1b[0m')


def indent(msg, level=4):
    indentation = level * ' '
    return indentation + msg.replace('\n', '\n' + indentation)


def prettify_caption(caption):
    return f'\x1b[38;5;75;04m{caption}\x1b[0m'


def prettify_duration(duration, is_total=False):
    if is_total:
        thresholds = [(0.5, 196), (0.25, 202), (0.1, 226), (0.05, 46), (None, 123)]
    else:
        thresholds = [(0.25, 196), (0.1, 202), (0.05, 226), (0.005, 46), (None, 123)]
    color = next(c for t, c in thresholds if t is None or duration >= t)
    return f'\x1b[38;5;{color}m{duration:.06f}s\x1b[0m'


def prettify_count(count):
    thresholds = [(50, 196), (30, 202), (20, 226), (10, 46), (None, 123)]
    color = next(c for t, c in thresholds if t is None or count >= t)
    return f'\x1b[38;5;{color}m{count}\x1b[0m'


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
    print('\rTerminating')
    os._exit(1)


@click.command()
@click.option('-p', '--port', type=int, default=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
              help='The port to bind the UDP listener to')
@click.option('-t', '--traceback-frames', type=int, default=3,
              help='Number of stack frames to show (max. 5)')
@click.option('-S', '--ignore-selects', is_flag=True, help='If SELECTs should be hidden')
@click.option('-i', '--ignored-sources', multiple=True, metavar='[FRAME:]FILE[:LINENO]',
              help='SELECT Query origins to ignore. May be used multiple times.  If no line is specified, the whole '
                   'file is ignored.  If no frame is specified, frame 1 (the topmost one in the log) will be used.')
@click.option('-I', '--ignored-request-paths', multiple=True, metavar='PATH',
              help='Request paths to ignore. May be used multiple times.  Matched against request.path (e.g. '
                   '/assets/js-vars/user.js). Prefix with ~ to use a regex match instead of an exact string match.')
def main(port, traceback_frames, ignore_selects, ignored_sources, ignored_request_paths):
    signal.signal(signal.SIGINT, sigint)
    print(f'Listening on 127.0.0.1:{port}')
    server = LogRecordSocketReceiver('localhost', port, traceback_frames=traceback_frames,
                                     ignore_selects=ignore_selects, ignored_sources=ignored_sources,
                                     ignored_request_paths=ignored_request_paths)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()


if __name__ == '__main__':
    main()
