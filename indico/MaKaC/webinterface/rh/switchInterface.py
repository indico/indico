from MaKaC.webinterface.rh import base

class RHSwitch(base.RH):

    def _checkParams(self, params):
        self._whereTo = params.get('to','future')

        if self._whereTo not in ['past', 'prev', 'future']:
            raise Exception('Unknown value')

        self._returnURL = params.get( "returnURL", "")

    def _process( self ):
        self._req.headers_out["Set-Cookie"] = "INDICO_INTERFACE=%s; domain=.cern.ch;" % self._whereTo

        url = self._returnURL

        if self._whereTo == 'prev':
            url = url.replace('indico.cern.ch','indicoprev.cern.ch')
        self._redirect(url)
