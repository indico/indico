# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer


'''
This server is a remote logger used in scenarios where the client code
does not have access to developer tools (e.g., BrowserStack).

To log to this server, import `indico/web/client/js/utils/remote_logger.js`
into your any model and use `console.log()` as usual.
'''


class LoggerHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        content_length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(content_length)
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: {payload.decode("utf-8", errors="replace")}')
        self.send_response(200)
        self.end_headers()


if __name__ == '__main__':
    server = HTTPServer(('localhost', 9999), LoggerHandler)
    print('Logger server starting on http://localhost:9999')
    server.serve_forever()
