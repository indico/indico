"""
This is a request handler module. Classes here will receive data from the routing layer and
process it, forwarding the result to the Pages layer.
"""

from MaKaC.webinterface.rh import base
from indico.web.pages import hello as hello_pages


class RHHello(base.RH):
    """
    This is a request handler class.
    """

    def _checkParams( self, params ):
        """
        This method normally processes parameters, making any
        conversions that may be needed
        """
        # in this case, let's just take the parameter called "name"
        # and store it
        self._name = params.get('name', 'Indico user')
        base.RH._checkParams( self, params )

    def _process( self ):
        p = hello_pages.WPHello(self, self._name)
        return p.display()
