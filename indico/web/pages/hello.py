"""
The "pages" layer contains two kinds of class:

 * `WP*` classes - contain navigation logic, page structure, etc. - should be normally minimal;
 * `W*` classes - represent a template - should be ideally empty
"""

from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface import wcomponents


class WPHello(WPMainBase):

    def __init__(self, rh, name):
        WPMainBase.__init__(self, rh)
        self._name = name

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage('hello')

    def _getBody(self, params):
        wc = WHello()
        return wc.getHTML({
                'name': self._name
                })


class WHello(wcomponents.WTemplated):
    """
    This class automatically maps to the 'Hello.tpl' template under MaKaC.webinterface.tpls
    """
    pass
