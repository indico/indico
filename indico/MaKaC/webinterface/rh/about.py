from MaKaC.webinterface.rh import base
from MaKaC.webinterface.pages import about as aboutPages

class RHAbout(base.RH):

    def _process( self ):
        p = aboutPages.WPAbout(self)
        return p.display()