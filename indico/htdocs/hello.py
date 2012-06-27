"""
This is Indico's routing layer. Notice how `index` gets called by default for `http://yourserver/indico/hello.py`.
Conversely, `http://yourserver/indico/hello.py/world`, is handled by the `world` function.
"""

import indico.web.rh.hello as hello


def index(req, **params):
    """
    This is an indico routing function
     * `req` - low level request object
     * `params` - request parameters (query string/post)
    """
    # Call request handler layer and return result
    return hello.RHHello(req).process(params)
