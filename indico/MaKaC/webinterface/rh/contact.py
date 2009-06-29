from MaKaC.webinterface.rh import base
from MaKaC.webinterface.pages import contact as contactPages

class RHContact(base.RH):
    
    def _process( self ):
        p = contactPages.WPContact(self)
        return p.display()