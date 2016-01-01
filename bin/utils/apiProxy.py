# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import hashlib
import hmac
import optparse
import requests
import sys
import time
import urllib
from contextlib import closing

from flask import Flask, request, Response, abort
from werkzeug.datastructures import MultiDict

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
    return items


def indico_request(path):
    request_values = MultiDict(request.values)
    method = request_values.pop('_method', request.method).upper()
    params = request_values.items(multi=True)
    data = build_indico_request(path, params, app.config['INDICO_API_KEY'], app.config['INDICO_SECRET_KEY'])
    request_args = {'params': data} if method == 'GET' else {'data': data}
    try:
        response = requests.request(method, app.config['INDICO_URL'] + path, verify=False, **request_args)
    except requests.HTTPError as e:
        response = e.response
    except requests.ConnectionError as e:
        return 'text/plain', str(e)
    content_type = response.headers.get('Content-Type', '').split(';')[0]
    with closing(response):
        return content_type, response.text


@app.route('/')
def index():
    return 'Please add an Indico HTTP API request to the path.'


@app.route('/<path:path>', methods=('GET', 'POST'))
def indicoproxy(path):
    if app.config['ALLOWED_IPS'] and request.remote_addr not in app.config['ALLOWED_IPS']:
        abort(403)
    content_type, resp = indico_request('/' + path)
    if not content_type:
        print 'WARNING: Did not receive a content type, falling back to text/plain'
        content_type = 'text/plain'
    return Response(resp, mimetype=content_type)


def main():
    parser = optparse.OptionParser()
    parser.add_option('-H', '--host', dest='host', default='127.0.0.1',
                      help='Host to listen on')
    parser.add_option('-p', '--port', type='int', dest='port', default=10081,
                      help='Port to listen on')
    parser.add_option('-d', '--debug', action='store_true', dest='debug', help='Debug mode')
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

    use_evalex = options.debug
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

    app.config['ALLOWED_IPS'] = options.allowed_ips
    app.config['INDICO_URL'] = options.indico_url.rstrip('/')
    app.config['INDICO_API_KEY'] = options.api_key
    app.config['INDICO_SECRET_KEY'] = options.secret_key

    print ' * Using indico at {}'.format(app.config['INDICO_URL'])
    print ' * To use this script, simply append a valid Indico HTTP API request to the URL shown' \
          ' below. It MUST NOT contain an API key, secret key or timestamp!'
    app.debug = options.debug
    app.run(host=options.host, port=options.port, use_evalex=use_evalex)


if __name__ == '__main__':
    main()
