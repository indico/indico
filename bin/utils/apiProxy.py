# -*- coding: utf-8 -*-
##
##
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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

#!/usr/bin/env python

import hashlib
import hmac
import httplib
import json
import optparse
import sys
import time
import urllib
import urllib2

try:
    from flask import Flask, request, Response, abort
except ImportError:
    print 'FATAL: You need to install Flask to use this script.'
    raise

DEBUG = False

allowed_ips = []
api_key = None
secret_key = None

app = Flask(__name__)

def build_indico_request(path, params, api_key=None, secret_key=None, only_public=False):
    items = params.items() if hasattr(params, 'items') else list(params)
    if api_key:
        items.append(('apikey', api_key))
    if only_public:
        items.append(('onlypublic', 'yes'))
    if secret_key:
        items.append(('timestamp', str(int(time.time()))))
        items = sorted(items, key=lambda x: x[0].lower())
        url = '%s?%s' % (path, urllib.urlencode(items))
        signature = hmac.new(secret_key, url, hashlib.sha1).hexdigest()
        items.append(('signature', signature))
    if not items:
        return path
    return '%s?%s' % (path, urllib.urlencode(items))

def indico_request(path):
    req = build_indico_request(path, request.args.to_dict(True), api_key, secret_key)
    try:
        conn = urllib2.urlopen(urllib2.Request(indico_url + req))
    except urllib2.HTTPError, e:
        conn = e # yuck!
        content_type = 'application/json'
    else:
        # No exception -> get the real content type
        info = conn.info()
        content_type = None
        if 'Content-Type' in info:
            content_type = info['Content-Type'].split(';')[0]
    resp = conn.read()
    conn.close()
    return content_type, resp

@app.route('/')
def index():
    return 'Please add an Indico HTTP API request to the path.'

@app.route('/<path:path>')
def indicoproxy(path):
    if allowed_ips and request.remote_addr not in allowed_ips:
        abort(403)
    content_type, resp = indico_request('/' + path)
    if not content_type:
        print 'WARNING: Did not receive a content type, falling back to text/plain'
        content_type = 'text/plain'
    return Response(resp, mimetype=content_type)


def main():
    global allowed_ips, indico_url, api_key, secret_key

    parser = optparse.OptionParser()
    parser.add_option('-H', '--host', dest='host', default='127.0.0.1',
        help='Host to listen on')
    parser.add_option('-p', '--port', type='int', dest='port', default=10081,
        help='Port to listen on')
    if DEBUG:
        parser.add_option('--force-evalex', action='store_true', dest='evalex',
            help='Enable evalex (remote code execution) even when listening on a host' +
                 ' that is not localhost - use with care!')
    parser.add_option('-I', '--allow-ip', dest='allowed_ips', action='append',
        help='Only allow the given IP to access the script. Can be used multiple times.')
    parser.add_option('-i', '--indico', dest='indico_url', default='https://indico.cern.ch',
        help='The base URL of your indico installation')
    parser.add_option('-a', '--apikey', dest='api_key', help='The API key to use')
    parser.add_option('-s', '--secretkey', dest='secret_key', help='The secret key to use')
    options, args = parser.parse_args()

    use_evalex = DEBUG
    if options.host not in ('::1', '127.0.0.1'):
        if not options.allowed_ips:
            print 'Listening on a non-loopback interface is not permitted without IP restriction!'
            sys.exit(1)
        if use_evalex:
            if options.evalex:
                print 'Binding to non-loopback host with evalex enabled.'
                print 'This means anyone with access to this app is able to execute arbitrary' \
                    ' python code!'
            else:
                print 'Binding to non-loopback host; disabling evalex (aka remote code execution).'
                use_evalex = False

    allowed_ips = options.allowed_ips
    indico_url = options.indico_url.rstrip('/')
    api_key = options.api_key
    secret_key = options.secret_key

    print ' * Using indico at %s' % indico_url
    print ' * To use this script, simply append a valid Indico HTTP API request to the URL shown' \
        ' below. It MUST NOT contain an API key, secret key or timestamp!'
    app.debug = DEBUG
    app.run(host=options.host, port=options.port, use_evalex=use_evalex)

if __name__ == '__main__':
    main()
