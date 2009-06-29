from MaKaC.common.db import DBMgr
from MaKaC.rb_room import RoomBase
from datetime import datetime,timedelta
from MaKaC.rb_location import CrossLocationQueries
from MaKaC.rb_reservation import ReservationBase
from MaKaC.webinterface.mail import GenericMailer, GenericNotification

startdt = enddt = datetime.now()
startdt.replace( hour = 0, minute = 0)
enddt.replace( hour = 23, minute = 59)


DBMgr.getInstance().startRequest()

from MaKaC.plugins.RoomBooking.CERN.dalManagerCERN import DALManagerCERN
DALManagerCERN.connect()

def sendMail( resv ):
    subject = "feedback for videoconference session"
    email = resv.createdByUser().getEmail()
    toaddrs = [ email ]
    ccaddrs = [ "noreply-vcservice@cern.ch" ]
    name = resv.createdByUser().getStraightFullName()
    title = resv.reason
    room = resv.room.getFullName()
    body = """
    Dear %s,
    
    You have booked a CERN videoconference room for the meeting "%s" taking place today in room %s.
    
    You are welcome to give us feedback on this videoconference session if or when it is over by going to this URL:
    <https://espace.cern.ch/AVC-workspace/videoconference/Lists/User%%20Satisfaction%%20in%%20CERN%%20Videoconference%%20Rooms/NewForm.aspx>
    The information you will provide in this form will be kept private and read only by the IT service managers.

    Receiving feedback through this channel will allow us to improve the support for CERN Collaborative tools.

    Many thanks in advance for your help.
    Best regards
    IT-UDS-AVC - Collaborative Tools Service Managers

    [In case you booked this room for another person, could you please forward this email to her/him?]
    """ % (name, title, room)
    email = { "fromAddr": "noreply-indico-team@cern.ch", "toList": toaddrs, "ccList": ccaddrs, "subject": subject, "body": body }
    GenericMailer.send(GenericNotification(email))
    
resvex = ReservationBase()
resvex.usesAVC = True
resvex.isConfirmed = True
resvex.isCancelled = False
resvex.needsAVCSupport = True
resvs = CrossLocationQueries.getReservations( resvExample = resvex, days = [ startdt.date() ] )
sent = 0
for resv in resvs:
    if resv.repeatability != None or resv.endDT.date() == enddt.date():
        sendMail(resv)
        sent += 1
print "sent %s mails" % sent

DBMgr.getInstance().endRequest()
