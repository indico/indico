import copy
import logging
import time

from pytz import timezone
from pytz import common_timezones

# Required by specific tasks
from MaKaC.user import Avatar
from MaKaC.i18n import _
from MaKaC.common.Configuration import Config
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.Counter import Counter
# end required

from base import PeriodicTask, PeriodicUniqueTask, OneShotTask

class CategoryStatisticsUpdaterTask(PeriodicUniqueTask):
    '''Updates statistics associated with categories
    '''
    def __init__(self, cat, **kwargs):
        super(CategoryStatisticsUpdaterTask, self).__init__(**kwargs)
        self._cat = cat

    def run(self):
        from MaKaC.statistics import CategoryStatistics
        CategoryStatistics.updateStatistics(self._cat)
        

# TODO CERN Specific
class FoundationSyncTask(PeriodicUniqueTask):
    """
    Synchronizes room data (along with associated room managers 
    and equipment) with Foundation database.
    
    Also, updates list of CERN Official Holidays

    (This is object for a task class)
    """
    def __init__(self, **kwargs):
        super(FoundationSyncTask, self).__init__(**kwargs)
        obj.__init__(self)
        
    def run(self):
        from MaKaC.common.FoundationSync.foundationSync import FoundationSync
        FoundationSync().doAll()
        
        
        
class SendMailTask(OneShotTask):
    """
    """
    def __init__(self, **kwargs):
        super(SendMailTask, self).__init__(**kwargs)
        self.fromAddr = ""
        self.toAddr = []
        self.toUser = []
        self.ccAddr = []
        self.subject = ""
        self.text = ""
        self.smtpServer = Config.getInstance().getSmtpServer()
    
    def run(self):
        import smtplib
        from MaKaC.webinterface.mail import GenericMailer, GenericNotification
        
        addrs = [smtplib.quoteaddr(x) for x in self.toAddr]
        ccaddrs = [smtplib.quoteaddr(x) for x in self.ccAddr]
        
        for user in self.toUser:
            addrs.append(smtplib.quoteaddr(user.getEmail()))
            
        GenericMailer.send(GenericNotification({"fromAddr": self.fromAddr, 
                                                "toList": addrs, 
                                                "ccList": ccaddrs, 
                                                "subject": self.subject, 
                                                "body": self.text }))

        
    def setFromAddr(self, addr):
        self.fromAddr = addr
        self._p_changed = 1
    
    def getFromAddr(self):
        return self.fromAddr

    def initialiseToAddr( self ):
        self.toAddr = []
        self._p_changed=1
    
    def addToAddr(self, addr):
        if not addr in self.toAddr:
            self.toAddr.append(addr)
            self._p_changed=1

    def addCcAddr(self, addr):
        if not addr in self.ccAddr:
            self.ccAddr.append(addr)
            self._p_changed=1
    
    def removeToAddr(self, addr):
        if addr in self.toAddr:
            self.toAddr.remove(addr)
            self._p_changed=1
    
    def setToAddrList(self, addrList):
        """Params: addrList -- addresses of type : list of str."""
        self.toAddr = addrList
        self._p_changed=1
    
    def getToAddrList(self):
        return self.toAddr
    
    def setCcAddrList(self, addrList):
        """Params: addrList -- addresses of type : list of str."""
        self.ccAddr = addrList
        self._p_changed=1
    
    def getCcAddrList(self):
        return self.ccAddr
    
    def addToUser(self, user):
        if not user in self.toUser:
            self.toUser.append(user)
            self._p_changed=1
    
    def removeToUser(self, user):
        if user in self.toUser:
            self.toUser.remove(user)
            self._p_changed=1
    
    def getToUserList(self):
        return self.toUser
    
    def setSubject(self, subject):
        self.subject = subject
    
    def getSubject(self):
        return self.subject
    
    def setText(self, text):
        self.text = text
    
    def getText(self):
        return self.text
       


class AlarmTask(OneShotTask):
    """
    implement an alarm componment
    """
    def __init__(self, conf, **kwargs):
        super(AlarmTask, self).__init__(**kwargs)
        self.mail = sendMail()
        self.addObj(self.mail)
        self.conf = conf
        self.timeBefore = None
        self.text = ""
        self.note = ""
        self.confSumary = False
        self.toAllParticipants = False
        
    def getToAllParticipants(self):
        try: 
            return self.toAllParticipants
        except:
            self.toAllParticipants = False
            return self.toAllParticipants 
            
    def setToAllParticipants(self, toAllParticipants):
        self.toAllParticipants = toAllParticipants
    
    def clone(self, conference):
        alarm = AlarmTask(conference)
        alarm.initialiseToAddr()
        for addr in self.getToAddrList():
            alarm.addToAddr(addr)
        alarm.setFromAddr(self.getFromAddr())
        alarm.setSubject(self.getSubject())
        alarm.setConfSumary(self.getConfSumary())
        alarm.setNote(self.getNote())
        alarm.setText(self.getText())
        if self.getTimeBefore():
            alarm.setTimeBefore(copy.copy(self.getTimeBefore()))
        else:
            alarm.setStartDate(copy.copy(self.getStartDate()))
        alarm.setToAllParticipants(self.getToAllParticipants())
        return alarm
        
    def getStartDate(self):
        if self.timeBefore:
            return self.conf.getStartDate() - self.timeBefore
        else:
            return task.getStartDate(self)
    
    def getAdjustedStartDate(self,tz=None):
        if not tz:
            tz = self.conf.getTimezone()
        if tz not in common_timezones:
           tz = 'UTC'
        if self.timeBefore:
            return self.conf.getStartDate().astimezone(timezone(tz)) - self.timeBefore
        else:
            if task.getStartDate(self):
                return task.getStartDate(self).astimezone(timezone(tz))
            return None
        if self.getStartDate():
            return self.getStartDate().astimezone(timezone(tz))
        return None
    
    def setStartDate(self, date):
        #we don't need timeBefore if startDate is set
        self.startDate = date
        self.timeBefore = None
        self._p_changed=1
    
    def setTimeBefore(self, timeDelta):
        #we don't need startDate if timeBefore is set
        self.timeBefore = timeDelta
        self.startDate = None
        self._p_changed=1
    
    def getTimeBefore(self):
        return self.timeBefore
        
    def setFromAddr(self, addr):
        self.mail.setFromAddr(addr)

    def getFromAddr(self):
        return self.mail.getFromAddr()

    def initialiseToAddr(self):
        self.mail.initialiseToAddr()
    
    def addToAddr(self, addr):
        self.mail.addToAddr(addr)
    
    def addCcAddr(self, addr):
        self.mail.addCcAddr(addr)
    
    def removeToAddr(self, addr):
        self.mail.removeToAddr(addr)
    
    def setToAddrList(self, addrList):
        self.mail.setToAddrList(addrList)
    
    def getToAddrList(self):
        return self.mail.getToAddrList()
    
    def setCcAddrList(self, addrList):
        self.mail.setCcAddrList(addrList)
    
    def getCcAddrList(self):
        return self.mail.getCcAddrList()
    
    def addToUser(self, user):
        self.mail.addToUser(user)
        if isinstance(user, Avatar):
            user.linkTo(self, "to")
    
    def removeToUser(self, user):
        self.mail.removeToUser(user)
        if isinstance(user, Avatar):
            user.unlinkTo(self, "to")
    
    def getToUserList(self):
        return self.mail.getToUserList()
    
    def setSubject(self, subject):
        self.mail.setSubject(subject)
    
    def getSubject(self):
        return self.mail.getSubject()
    
    def setText(self, text):
        self.text = text
        self._setMailText()
        self._p_changed=1
    
    def getText(self):
        return self.text
    
    def getLocator(self):
        d = self.getOwner().getLocator()
        d["alarmId"] = self.getId()
        return d
    
    def canAccess(self, aw):
        return self.getOwner().canAccess(aw)
    
    def canModify(self, aw):
        return self.getOwner().canModify(aw)
    
    def _setMailText(self):
        text = self.text
        if self.note:
            text = text + "Note: %s" % self.note
        if self.confSumary:
            #try:
                from MaKaC.common.output import outputGenerator
                from MaKaC.accessControl import AdminList, AccessWrapper
                import MaKaC.webinterface.urlHandlers as urlHandlers
                admin = AdminList().getInstance().getList()[0]
                aw = AccessWrapper()
                aw.setUser(admin)
                path = Config.getInstance().getStylesheetsDir()
                if os.path.exists("%s/text.xsl" % path):
                    stylepath = "%s/text.xsl" % path
                outGen = outputGenerator(aw)
                vars = { \
                        "modifyURL": urlHandlers.UHConferenceModification.getURL( self.conf ), \
                        "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL, \
                        "contribModifyURLGen": urlHandlers.UHContributionModification.getURL, \
                        "subContribModifyURLGen":  urlHandlers.UHSubContribModification.getURL, \
                        "materialURLGen": urlHandlers.UHMaterialDisplay.getURL, \
                        "resourceURLGen": urlHandlers.UHFileAccess.getURL }
                confText = outGen.getOutput(self.conf,stylepath,vars)
                text += "\n\n\n" + confText
            #except:
            #    text += "\n\n\nSorry could not embed text version of the agenda..."
        self.mail.setText(text)
    
    def setNote(self, note):
        self.note = note
        self._setMailText()
        self._p_changed=1
    
    def getNote(self):
        return self.note
    
    def setConfSumary(self, val):
        self.confSumary = val
        self._setMailText()
        self._p_changed=1
    
    def getConfSumary(self):
        return self.confSumary

    def prerun(self):
        # Date checkings...
        from MaKaC.conference import ConferenceHolder
        from MaKaC.common.timezoneUtils import nowutc
        if not ConferenceHolder().hasKey(self.conf.getId()) or \
                self.conf.getStartDate() <= nowutc():
           self.conf.removeAlarm(self) 
           return True
        # Email
        self.setSubject("Event reminder: %s"%self.conf.getTitle())
        try:
            locationText = self.conf.getLocation().getName()
            if self.conf.getLocation().getAddress() != "":
                locationText += ", %s" % self.conf.getLocation().getAddress()
            if self.conf.getRoom().getName() != "":
                locationText += " (%s)" % self.conf.getRoom().getName()
        except:
            locationText = ""
        if locationText != "":
            locationText = _(""" _("Location"): %s""") % locationText
        
        if self.getToAllParticipants() :
            for p in self.conf.getParticipation().getParticipantList():
                self.addToUser(p)
        
        from MaKaC.webinterface import urlHandlers
        if Config.getInstance().getShortEventURL() != "":
            url = "%s%s" % (Config.getInstance().getShortEventURL(),self.conf.getId())
        else:
            url = urlHandlers.UHConferenceDisplay.getURL( self.conf )
        self.setText("""Hello,
    Please note that the event "%s" will start on %s (%s).
    %s
    
    You can access the full event here:
    %s
    
Best Regards

    """%(self.conf.getTitle(),\
                self.conf.getAdjustedStartDate().strftime("%A %d %b %Y at %H:%M"),\
                self.conf.getTimezone(),\
                locationText,\
                url,\
                ))
        self._setMailText()
        return False


class SampleOneShotTask(OneShotTask):
    def run(self):
        time.sleep(1)
        logging.getLogger('taskDaemon').debug('%s executed' % self.__class__.__name__)
        
        
class SamplePeriodicTask(PeriodicTask):
    def run(self):
        time.sleep(1)
        logging.getLogger('taskDaemon').debug('%s executed' % self.__class__.__name__)