############################
# Fermi timezone awareness #
############################

from datetime import datetime
from pytz import timezone
from xml.sax.saxutils import quoteattr, escape
from MaKaC.common.Configuration import Config


def convertTime(d,tz):
    if str(d.tzinfo) == 'None':
       return_d = datetime(d.year,d.month,d.day,d.hour,d.minute,tzinfo=timezone('UTC'))
    else:
       return_d = d.astimezone(timezone(tz))
    return (return_d)

class TimezoneRegistry:
    _items = Config.getInstance().getTimezoneList()

    def getList( self ):
        return self._items

    getList=classmethod(getList)

# TODO: This one should probably removed. It's only used
#       on event display pages and there we now have a balloon popup.
#def getSelectItemsHTML( self, selTitle="", localTZ="" ):
#    l=[]
#    for title in self._items + ["LOCAL"] + ["My"]:
#        selected=""
#        if title==selTitle:
#            selected=" selected"
#        screenTitle = title
#        if localTZ != "" and title == "LOCAL" and selTitle == "LOCAL":
#            screenTitle = title + ": %s" % localTZ
#        l.append("""<option value=%s%s>%s</option>"""%(quoteattr(title),
#                                    selected, escape(screenTitle)))
#    return "".join(l)
#getSelectItemsHTML=classmethod(getSelectItemsHTML)

    def getShortSelectItemsHTML( self, selTitle="", localTZ="" ):
        l=[]
        for title in self._items:
            selected=""
            if title==selTitle:
                selected=" selected"
            screenTitle = title
            l.append("""<option value=%s%s>%s</option>"""%(quoteattr(title),
                                        selected, escape(screenTitle)))
        return "".join(l)
    getShortSelectItemsHTML=classmethod(getShortSelectItemsHTML)
        

class DisplayTimezoneRegistry:
    _items = ['MyTimezone','Event Timezone']

    def getList( self ):
        return self._items

    getList=classmethod(getList)

    def getSelectItemsHTML( self, selTitle="" ):
        l=[]
        for title in self._items:
            selected=""
            if title==selTitle:
                selected=" selected"
            l.append("""<option value=%s%s>%s</option>"""%(quoteattr(title),
                                        selected, escape(title)))
        return "".join(l)
    getSelectItemsHTML=classmethod(getSelectItemsHTML)
