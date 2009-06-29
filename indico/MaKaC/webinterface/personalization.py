# Some classes for personalization

from wcomponents import WTemplated

class WPersonalEvents(WTemplated):
    
    def __init__( self, avatar ):
        self._userAvatar = avatar
    
    def getVars( self ):
        vars = WTemplated.getVars(self)
        
        vars['user'] = self._userAvatar
              
        return vars
    
    def getHTML( self, params ):
        return WTemplated.getHTML( self, params )
    
class WPersAreaFrame(WTemplated):

    def __init__( self):
        pass
    
