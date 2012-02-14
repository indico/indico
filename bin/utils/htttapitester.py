from flask import Flask, request, Response, abort
import hashlib
import httplib
import hmac
import json
import urllib
import time
from pprint import pprint

ALLOWED_IP = '137.138.130.27'
KEY_PAIRS = {
    'nickname': ('public-api-key', 'secret-key')
}

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

def indico_request(who, path):
    if who not in KEY_PAIRS:
        abort(400)
    keys = KEY_PAIRS[who]
    req = build_indico_request(path, request.args.to_dict(True), keys[0], keys[1])
    conn = urllib.urlopen('https://indico.cern.ch' + req)
    resp = conn.read()
    conn.close()
    return resp

app = Flask(__name__)
app.debug = True

@app.route('/<who>/<path:path>')
def indicoproxy(who, path):
    #if request.remote_addr != ALLOWED_IP:
    #    abort(403)
    resp = indico_request(who, '/' + path)
    return Response(resp, mimetype='application/json')

app.run(host='0.0.0.0', port=10081)
