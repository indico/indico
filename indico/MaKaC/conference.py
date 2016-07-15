# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

import os
import stat
from datetime import datetime

from BTrees.OOBTree import OOBTree
from flask import request, has_request_context
from persistent import Persistent
from pytz import all_timezones, timezone
from sqlalchemy.orm import joinedload

from indico.core import signals
from indico.core.config import Config
from indico.core.db import DBMgr, db
from indico.core.db.event import SupportInfo
from indico.core.db.sqlalchemy.core import ConstraintViolated
from indico.modules.events.cloning import EventCloner
from indico.modules.events.features import event_settings as features_event_settings
from indico.modules.events.features.util import get_feature_definitions, get_enabled_features
from indico.modules.events.models.events import Event
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.modules.events.util import track_time_changes
from indico.modules.users.legacy import AvatarUserWrapper
from indico.util.caching import memoize_request
from indico.util.i18n import L_, _
from indico.util.redis import avatar_links
from indico.util.redis import write_client as redis_write_client
from indico.util.string import return_ascii, is_legacy_id, to_unicode
from indico.util.user import unify_user_args

from MaKaC import fileRepository, review
from MaKaC.abstractReviewing import ConferenceAbstractReview
from MaKaC.accessControl import AccessController
from MaKaC.badge import BadgeTemplateManager
from MaKaC.common.Counter import Counter
from MaKaC.common.fossilize import fossilizes, Fossilizable
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.Locators import Locator
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.common.PickleJar import Updates
from MaKaC.common.timezoneUtils import datetimeToUnixTimeInt
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.url import ShortURLMapper
from MaKaC.errors import MaKaCError, TimingError, NotFoundError, FormValuesError
from MaKaC.fossils.conference import IConferenceMinimalFossil, IConferenceEventInfoFossil, IConferenceFossil
from MaKaC.paperReviewing import ConferencePaperReview as ConferencePaperReview
from MaKaC.poster import PosterTemplateManager
from MaKaC.trashCan import TrashCanManager


class CoreObject(Persistent):
    """
    CoreObjects are Persistent objects that are employed by Indico's core
    """

    def setModificationDate(self, date=None):
        """
        Method called to notify the current object has been modified.
        """
        if not date:
            date = nowutc()
        self._modificationDS = date


class CommonObjectBase(CoreObject, Fossilizable):
    """
    This class is for holding commonly used methods that are used by several classes.
    It is inherited by the following classes:
      * Category
      * Conference
      * Session
      * Contribution
      * SubContribution
      * Material
      * Resource
    """

    def getRecursiveManagerList(self):
        av_set = set()

        # Get the AccessProtectionLevel for this
        apl = self.getAccessProtectionLevel()

        if apl == -1:
            pass
        elif apl == 1:
            for av in self.getManagerList():
                av_set.add(av)
            for av in self.getOwner().getRecursiveManagerList():
                av_set.add(av)
        else:
            for av in self.getManagerList():
                av_set.add(av)

            if self.getOwner():
                for av in self.getOwner().getRecursiveManagerList():
                    av_set.add(av)

        return list(av_set)

    def getRecursiveAllowedToAccessList(self, skip_managers=False, skip_self_acl=False):
        """Returns a set of Avatar resp. Group objects for those people resp.
        e-groups allowed to access this object as well as all parent objects.
        """

        # Initialize set of avatars/groups: this will hold those
        # people/groups explicitly
        # allowed to access this object
        av_set = set()

        # Get the AccessProtectionLevel for this
        apl = self.getAccessProtectionLevel()

        # If this object is "absolutely public", then return an empty set
        if apl == -1:
            pass

        # If this object is protected "all by itself", then get the list of
        # people/groups allowed to access it, plus managers of owner(s)
        elif apl == 1:
            al = None
            if not skip_self_acl:
                al = self.getAllowedToAccessList()
            if not skip_managers:
                al = al + self.getManagerList() + self.getOwner().getRecursiveManagerList()
            if al is not None:
                for av in al:
                    av_set.add(av)

        # If access settings are inherited (and PRIVATE) from its owners, look at those.
        elif apl == 0 and self.isProtected():
            # If event is protected, then get list of people/groups allowed
            # to access, and add that to the set of avatars.
            al = None
            if not skip_self_acl:
                al = self.getAllowedToAccessList()
            if not skip_managers:
                al = al + self.getManagerList()
            if al is not None:
                for av in al:
                    av_set.add(av)

            # Add list of avatars/groups allowed to access parents objects.
            owner = self.getOwner()
            if owner is not None:
                owner_al = owner.getRecursiveAllowedToAccessList(skip_managers=skip_managers)
                if owner_al is not None:
                    for av in owner_al:
                        av_set.add(av)

        # return set containing whatever avatars/groups we may have collected
        return av_set

    def canIPAccess(self, ip):
        domains = self.getAccessController().getAnyDomainProtection()
        if domains:
            return any(domain.belongsTo(ip) for domain in domains)
        else:
            return True

    @property
    @memoize_request
    def attached_items(self):
        """
        CAUTION: this won't return empty directories (used by interface), nor things the
        current user can't see
        """
        from indico.modules.attachments.util import get_attached_items
        if isinstance(self, Conference):
            return get_attached_items(self.as_event, include_empty=False, include_hidden=False, preload_event=True)
        else:
            raise ValueError("Object of type '{}' cannot have attachments".format(type(self)))


class Conference(CommonObjectBase):
    """This class represents the real world conferences themselves. Objects of
        this class will contain basic data about the confence and will provide
        access to other objects representing certain parts of the conferences
        (ex: contributions, sessions, ...).
    """

    fossilizes(IConferenceFossil, IConferenceMinimalFossil, IConferenceEventInfoFossil)

    @classmethod
    @unify_user_args
    def new(cls, category, creator, title, start_dt, end_dt, timezone, event_type, add_creator_as_manager=True):
        conf = cls()
        event = Event(creator=creator, category=category, title=to_unicode(title).strip(),
                      start_dt=start_dt, end_dt=end_dt, timezone=timezone, type_=event_type)
        ConferenceHolder().add(conf, event, add_creator_as_manager=add_creator_as_manager)
        signals.event.created.send(event)
        return conf

    def __init__(self, id=''):
        self.id = id
        self.places = []
        self.rooms = []
        self._screenStartDate = None
        self._screenEndDate = None
        self.contactInfo = ""
        self.chairmanText = ""
        self.sessions = {}
        self.programDescription = ""
        self.program = []
        self.__programGenerator = Counter()
        self.__ac = AccessController(self)
        self._modificationDS = nowutc()

        self.abstractMgr = review.AbstractMgr(self)
        self._logo = None
        self._trackCoordinators = TCIndex()
        self._supportInfo = SupportInfo(self, "Support")
        self._contribTypes = {}
        self.___contribTypeGenerator = Counter()
        self._boa = BOAConfig(self)
        self._accessKey = ""
        self._closed = False
        self._visibility = 999
        self.__badgeTemplateManager = BadgeTemplateManager(self)
        self.__posterTemplateManager = PosterTemplateManager(self)
        self._keywords = ""
        self._confPaperReview = ConferencePaperReview(self)
        self._confAbstractReview = ConferenceAbstractReview(self)
        self._orgText = ""
        self._comments = ""
        self._sortUrlTag = ""

    @return_ascii
    def __repr__(self):
        return '<Conference({0}, {1}, {2})>'.format(self.getId(), self.getTitle(), self.getStartDate())

    @property
    def startDate(self):
        return self.as_event.start_dt

    @startDate.setter
    def startDate(self, dt):
        self.as_event.start_dt = dt

    @property
    def endDate(self):
        return self.as_event.end_dt

    @endDate.setter
    def endDate(self, dt):
        self.as_event.end_dt = dt

    @property
    def timezone(self):
        return self.as_event.timezone.encode('utf-8')

    @timezone.setter
    def timezone(self, timezone):
        self.as_event.timezone = to_unicode(timezone).strip()

    @property
    def title(self):
        return self.as_event.title.encode('utf-8')

    @title.setter
    def title(self, title):
        self.as_event.title = to_unicode(title).strip()

    @property
    def description(self):
        return self.as_event.description.encode('utf-8')

    @description.setter
    def description(self, description):
        self.as_event.description = to_unicode(description).strip()

    @property
    def all_manager_emails(self):
        return self.as_event.all_manager_emails

    @property
    @memoize_request
    def as_event(self):
        """Returns the :class:`.Event` for this object

        :rtype: indico.modules.events.models.events.Event
        """
        from indico.modules.events.models.events import Event
        event_id = int(self.id)
        # this is pretty ugly, but the api sends queries in a loop in
        # some cases and we can't really avoid this for now.  If we
        # already have the event in the identity map we keep using
        # the simple id-based lookup though as lazyloading the acl
        # entries is just one query anyway
        if (has_request_context() and request.blueprint == 'api' and request.endpoint != 'api.jsonrpc' and
                (Event, (event_id,)) not in db.session.identity_map):
            acl_user_strategy = joinedload('acl_entries').defaultload('user')
            # remote group membership checks will trigger a load on _all_emails
            # but not all events use this so there's no need to eager-load them
            acl_user_strategy.noload('_primary_email')
            acl_user_strategy.noload('_affiliation')
            return Event.find(id=event_id).options(acl_user_strategy).one()
        else:
            # use get() so sqlalchemy can make use of the identity cache
            return Event.get_one(event_id)

    as_new = as_event

    @property
    @memoize_request
    def note(self):
        from indico.modules.events.notes.models.notes import EventNote
        return EventNote.get_for_linked_object(self.as_event)

    @property
    def tz(self):
        from MaKaC.common.timezoneUtils import DisplayTZ
        return DisplayTZ(conf=self).getDisplayTZ()

    @unify_user_args
    def log(self, *args, **kwargs):
        self.as_event.log(*args, **kwargs)

    @memoize_request
    def has_feature(self, feature):
        return self.as_event.has_feature(feature)

    def __cmp__(self, toCmp):
        if isinstance(toCmp, Conference):
            return cmp(self.getId(), toCmp.getId())
        else:
            return cmp(hash(self), hash(toCmp))

    def __eq__(self, toCmp):
        return self is toCmp

    def __ne__(self, toCmp):
        return not(self is toCmp)

    def setUrlTag(self, tag):
        self._sortUrlTag = tag

    def getUrlTag(self):
        try:
            return self._sortUrlTag
        except:
            self._sortUrlTag = ""
        return self._sortUrlTag

    def setComments(self,comm=""):
        self._comments = comm.strip()

    def getComments(self):
        try:
            if self._comments:
                pass
        except AttributeError,e:
            self.setComments()
        return self._comments

    def getConfPaperReview(self):
        if not hasattr(self, "_confPaperReview"):
            self._confPaperReview = ConferencePaperReview(self)
        return self._confPaperReview

    def getConfAbstractReview(self):
        if not hasattr(self, "_confAbstractReview"):
            self._confAbstractReview = ConferenceAbstractReview(self)
        return self._confAbstractReview

    def getOrgText( self ):
        try:
            return self._orgText
        except:
            self.setOrgText()
            return ""

    def setOrgText( self, org="" ):
        self._orgText = org

    def getKeywords(self):
        try:
            return self._keywords
        except:
            self._keywords = ""
            return ""

    def setKeywords(self, keywords):
        self._keywords = keywords

    def getType(self):
        return self.as_event.type_.legacy_name

    def setValues(self, confData):
        """
            Sets SOME values of the current conference object from a dictionary
            containing the following key-value pairs:
                visibility-(str)
                title-(str)
                description-(str)
                supportEmail-(str)
                contactInfo-(str)
                locationName-(str) => name of the location, if not specified
                        it will be set to the conference location name.
                locationAddress-(str)
                roomName-(str) => name of the room, if not specified it will
                    be set to the conference room name.
            Please, note that this method sets SOME values which means that if
            needed it can be completed to set more values. Also note that if
            the given dictionary doesn't contain all the values, the missing
            ones will be set to the default values.
        """
        self.setVisibility(confData.get("visibility", "999"))
        self.setTitle(confData.get("title", _("NO TITLE ASSIGNED")))
        self.setDescription(confData.get("description", ""))
        self.getSupportInfo().setEmail(confData.get("supportEmail", ""))
        self.setContactInfo(confData.get("contactInfo", ""))
        self.notifyModification()

    def getVisibility(self):
        return self.as_event.visibility if self.as_event.visibility is not None else 999

    def getFullVisibility( self ):
        raise NotImplementedError('getFullVisibility')
        return max(0,min(self.getVisibility(), self.getOwnerList()[0].getVisibility()))

    def setVisibility(self, visibility=999):
        visibility = int(visibility)
        self.as_event.visibility = visibility if visibility != 999 else None

    def isClosed( self ):
        try:
            return self._closed
        except:
            self._closed = False
            return False

    def setClosed( self, closed=True ):
        self._closed = closed

    @memoize_request
    def getContribTypeList(self):
        return self.as_event.contribution_types.all()

    def getContribTypeById(self, tid):
        if not tid.isdigit():
            return None
        return self.as_event.contribution_types.filter_by(id=int(tid)).first()

    def _getRepository( self ):
        dbRoot = DBMgr.getInstance().getDBConnection().root()
        try:
            fr = dbRoot["local_repositories"]["main"]
        except KeyError, e:
            fr = fileRepository.MaterialLocalRepository()
            dbRoot["local_repositories"] = OOBTree()
            dbRoot["local_repositories"]["main"] = fr
        return fr

    def getURL(self):
        cid = self.getUrlTag()
        if not cid:
            cid = self.getId()
        return Config.getInstance().getShortEventURL() + cid

    def setLogo( self, logoFile ):
        logoFile.setOwner( self )
        logoFile.setId( "logo" )
        logoFile.archive( self._getRepository() )
        if self._logo != None:
            self._logo.delete()
        self._logo = logoFile
        self.notifyModification()

    def getLogo( self ):
        return self._logo

    def removeLogo(self):
        if self._logo is None:
            return
        self._logo.delete()
        self._logo = None
        self.notifyModification()

    def getAbstractMgr(self):
        return self.abstractMgr

    def notifyModification( self, date = None, raiseEvent = True):
        """Method called to notify the current conference has been modified.
        """
        self.setModificationDate()

        if raiseEvent and self.id:
            signals.event.data_changed.send(self, attr=None, old=None, new=None)

        self._p_changed=1

    def getModificationDate( self ):
        """Returns the date in which the conference was last modified"""
        return self._modificationDS

    def getAdjustedModificationDate( self, tz ):
        """Returns the date in which the conference was last modified"""
        return self._modificationDS.astimezone(timezone(tz))

    def getCreationDate(self):
        """Returns the date in which the conference was created"""
        return self.as_event.created_dt

    def getAdjustedCreationDate(self, tz):
        """Returns the date in which the conference was created"""
        return self.as_event.created_dt.astimezone(timezone(tz))

    def getId( self ):
        """returns (string) the unique identifier of the conference"""
        return self.id

    def getUniqueId( self ):
        """returns (string) the unique identiffier of the item"""
        """used mainly in the web session access key table"""
        return "a%s" % self.id

    def setId(self, newId):
        """changes the current unique identifier of the conference to the
            one which is specified"""
        self.id = str(newId)

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the conference instance """
        d = Locator()
        d["confId"] = self.getId()
        return d

    def getOwner( self ):
        raise NotImplementedError('getOwner')

    def getOwnerList(self):
        # TODO: check places where this is called whether to remove/adapt them
        raise NotImplementedError('getOwnerList')

    def getOwnerPath(self):
        # TODO: check places where this is called whether to remove/adapt them
        raise NotImplementedError('getOwnerPath')
        l=[]
        owner = self.getOwnerList()[0]
        while owner != None and owner.getId() != "0":
            l.append(owner)
            owner = owner.getOwner()
        return l

    def delete(self, user=None):
        signals.event.deleted.send(self, user=user)
        ConferenceHolder().remove(self)
        # Remove all links in redis
        if redis_write_client:
            avatar_links.delete_event(self)
        # Remote short URL mappings
        ShortURLMapper().remove(self)
        TrashCanManager().add(self)
        self._p_changed = True

    def getConference( self ):
        return self

    def setDates( self, sDate, eDate=None, check=1, moveEntries=0, enforce_constraints=True):
        """
        Set the start/end date for a conference
        """

        oldStartDate = self.getStartDate()
        oldEndDate = self.getEndDate()

        # do some checks first
        if sDate > eDate:
            # obvious case
            raise FormValuesError(_("Start date cannot be after the end date"), _("Event"))

        elif sDate == oldStartDate and eDate == oldEndDate:
            # if there's nothing to do (yet another obvious case)
            return

        # if we reached this point, it means either the start or
        # the end date (or both) changed
        # If only the end date was changed, moveEntries = 0
        if sDate == oldStartDate:
            moveEntries = 0

        # set the dates
        with db.session.no_autoflush:
            self.setStartDate(sDate, check=0, moveEntries = moveEntries, index=False, notifyObservers = False)
            self.setEndDate(eDate, check=0, index=False, notifyObservers = False)

            if enforce_constraints:
                try:
                    db.enforce_constraints()
                except ConstraintViolated:
                    raise TimingError(_("The start/end dates were not changed since the selected timespan is not large "
                                        "enough to accomodate the contained timetable entries and spacings."),
                                      explanation=_("You should try using a larger timespan."))

        # notify observers
        old_data = (oldStartDate, oldEndDate)
        new_data = (self.getStartDate(), self.getEndDate())
        if old_data != new_data:
            signals.event.data_changed.send(self, attr='dates', old=old_data, new=new_data)

    def setStartDate(self, sDate, check = 1, moveEntries = 0, index = True, notifyObservers = True):
        """ Changes the current conference starting date/time to the one specified by the parameters.
        """
        if not sDate.tzname():
            raise MaKaCError("date should be timezone aware")
        if sDate == self.getStartDate():
            return
        if check != 0:
            self.verifyStartDate(sDate)
        oldSdate = self.getStartDate()
        diff = sDate - oldSdate

        if moveEntries:
            # If the start date changed, we move entries inside the timetable
            self.as_event.move_start_dt(sDate)
        else:
            self.startDate = sDate
        #datetime object is non-mutable so we must "force" the modification
        #   otherwise ZODB won't be able to notice the change
        self.notifyModification()

        # Update redis link timestamp
        if redis_write_client:
            avatar_links.update_event_time(self)

        #if everything went well, we notify the observers that the start date has changed
        if notifyObservers:
            if oldSdate != sDate:
                signals.event.data_changed.send(self, attr='start_date', old=oldSdate, new=sDate)

    def verifyStartDate(self, sdate, check=1):
        if sdate>self.getEndDate():
            raise MaKaCError( _("End date cannot be before the Start date"), _("Event"))

    def setStartTime(self, hours=0, minutes=0, notifyObservers = True):
        """ Changes the current conference starting time (not date) to the one specified by the parameters.
        """

        sdate = self.getStartDate()
        self.startDate = datetime( sdate.year, sdate.month, sdate.day,
                                                    int(hours), int(minutes) )
        self.verifyStartDate(self.startDate)
        self.notifyModification()

    def getStartDate(self):
        """returns (datetime) the starting date of the conference"""
        return self.startDate

    def getUnixStartDate(self):
        return datetimeToUnixTimeInt(self.startDate)

    def getAdjustedStartDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        return self.getStartDate().astimezone(timezone(tz))

    def setScreenStartDate(self, date):
        if date == self.getStartDate():
            date = None
        self._screenStartDate = date
        self.notifyModification()

    def getScreenStartDate(self):
        try:
            date = self._screenStartDate
        except:
            date = self._screenStartDate = None
        if date != None:
            return date
        else:
            return self.getStartDate()

    def getAdjustedScreenStartDate(self, tz=None):
        if not tz:
            tz = self.getTimezone()
        return self.getScreenStartDate().astimezone(timezone(tz))

    def verifyEndDate(self, edate):
        if edate<self.getStartDate():
            raise TimingError( _("End date cannot be before the start date"), _("Event"))

    def setEndDate(self, eDate, check = 1, index = True, notifyObservers = True):
        """ Changes the current conference end date/time to the one specified by the parameters.
        """
        if not eDate.tzname():
            raise MaKaCError("date should be timezone aware")
        if eDate == self.getEndDate():
            return
        if check != 0:
            self.verifyEndDate(eDate)

        oldEdate = self.endDate
        self.endDate  = eDate
        #datetime object is non-mutable so we must "force" the modification
        #   otherwise ZODB won't be able to notice the change
        self.notifyModification()

        #if everything went well, we notify the observers that the start date has changed
        if notifyObservers:
            if oldEdate != eDate:
                signals.event.data_changed.send(self, attr='end_date', old=oldEdate, new=eDate)

    def setEndTime(self, hours = 0, minutes = 0, notifyObservers = True):
        """ Changes the current conference end time (not date) to the one specified by the parameters.
        """
        edate = self.getEndDate()
        self.endDate = datetime( edate.year, edate.month, edate.day, int(hours), int(minutes) )
        self.verifyEndDate(self.endDate)
        self.notifyModification()

    def getEndDate(self):
        """returns (datetime) the ending date of the conference"""
        return self.endDate

    def getAdjustedEndDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        return self.getEndDate().astimezone(timezone(tz))

    def setScreenEndDate(self, date):
        if date == self.getEndDate():
            date = None
        self._screenEndDate = date
        self.notifyModification()

    def getScreenEndDate(self):
        try:
            date = self._screenEndDate
        except:
            date = self._screenEndDate = None
        if date != None:
            return date
        else:
            return self.getEndDate()

    def getAdjustedScreenEndDate(self, tz=None):
        if not tz:
            tz = self.getTimezone()
        return self.getScreenEndDate().astimezone(timezone(tz))

    def setTimezone(self, tz):
        self.timezone = tz

    def getTimezone(self):
        try:
            return self.timezone
        except AttributeError:
            return 'UTC'

    def moveToTimezone(self, tz):
        if self.getTimezone() == tz:
            return
        sd=self.getAdjustedStartDate()
        ed=self.getAdjustedEndDate()
        self.setTimezone(tz)
        try:
            sDate = timezone(tz).localize(datetime(sd.year, \
                                 sd.month, \
                                 sd.day, \
                                 sd.hour, \
                                 sd.minute))
            eDate = timezone(tz).localize(datetime(ed.year, \
                                 ed.month, \
                                 ed.day, \
                                 ed.hour, \
                                 ed.minute))
        except ValueError,e:
            raise MaKaCError("Error moving the timezone: %s"%e)
        self.setDates( sDate.astimezone(timezone('UTC')), \
                       eDate.astimezone(timezone('UTC')),
                       moveEntries=1)

    def getTitle(self):
        """returns (String) the title of the conference"""
        return self.title

    def setTitle(self, title):
        """changes the current title of the conference to the one specified"""
        oldTitle = self.title

        self.title = title
        self.notifyModification()

        if oldTitle != title:
            signals.event.data_changed.send(self, attr='title', old=oldTitle, new=title)

    def getDescription(self):
        """returns (String) the description of the conference"""
        return self.description

    def setDescription(self, desc):
        """changes the current description of the conference"""
        oldDescription = self.description
        self.description = desc
        if oldDescription != desc:
            signals.event.data_changed.send(self, attr='description', old=oldDescription, new=desc)
        self.notifyModification()

    def getSupportInfo(self):
        if not hasattr(self, "_supportInfo"):
            self._supportInfo = SupportInfo(self, "Support")
        return self._supportInfo

    def setSupportInfo(self, supportInfo):
        self._supportInfo = supportInfo

    def getChairmanText(self):
        # this is only used in legacy data and not settable for new events
        # TODO: check whether we can get rid of it at some point
        try:
            if self.chairmanText:
                pass
        except AttributeError, e:
            self.chairmanText = ""
        return self.chairmanText

    def setChairmanText( self, newText ):
        self.chairmanText = newText.strip()

    def getContactInfo(self):
        return self.contactInfo

    def setContactInfo(self, contactInfo):
        self.contactInfo = contactInfo
        self.notifyModification()

    def getSessionById(self, sessionId):
        """Returns the session from the conference list corresponding to the
            unique session id specified
        """
        if not sessionId.isdigit():
            return None
        return self.as_event.get_session(friendly_id=int(sessionId))

    def getSessionList( self ):
        """Retruns a list of the conference session objects
        """
        return self.as_event.sessions

    getSessionListSorted = getSessionList

    def getNumberOfSessions(self):
        return len(self.as_event.sessions)

    def getReviewManager(self, contrib):
        return self.getConfPaperReview().getReviewManager(contrib)

    def getProgramDescription(self):
        try:
            return self.programDescription
        except:
            self.programDescription = ""
        return self.programDescription

    def setProgramDescription(self, txt):
        self.programDescription = txt

    def _generateNewTrackId( self ):
        """
        """
        return str(self.__programGenerator.newCount())

    def addTrack( self, newTrack ):
        """
        """
        #XXX: The conference program shoul be isolated in a separated object
        if newTrack in self.program:
            return

        trackId = newTrack.getId()
        if trackId == "not assigned":
            trackId = self._generateNewTrackId()
        self.program.append( newTrack )
        newTrack.setConference( self )
        newTrack.setId( trackId )
        self.notifyModification()

    def removeTrack( self, track ):
        if track in self.program:
            track.delete()
            if track in self.program:
                self.program.remove( track )
            self.notifyModification()

    def recoverTrack(self, track):
        self.addTrack(track)
        track.recover()

    def newTrack( self ):
        """
        """
        t = Track()
        self.addTrack( t )
        return t

    def getTrackById( self, id ):
        """
        """
        for track in self.program:
            if track.getId() == id.strip():
                return track
        return None

    def getTrackList( self ):
        """
        """
        return self.program

    def isLastTrack(self,track):
        """
        """
        return self.getTrackPos(track)==(len(self.program)-1)

    def isFirstTrack(self,track):
        """
        """
        return self.getTrackPos(track)==0

    def getTrackPos(self,track):
        """
        """
        return self.program.index(track)

    def moveTrack(self,track,newPos):
        """
        """
        self.program.remove(track)
        self.program.insert(newPos,track)
        self.notifyModification()

    def moveUpTrack(self,track):
        """
        """
        if self.isFirstTrack(track):
            return
        newPos=self.getTrackPos(track)-1
        self.moveTrack(track,newPos)

    def moveDownTrack(self,track):
        """
        """
        if self.isLastTrack(track):
            return
        newPos = self.getTrackPos(track) + 1
        self.moveTrack(track, newPos)

    def _cmpTracks(self, t1, t2):
        o1 = self.program.index(t1)
        o2 = self.program.index(t2)
        return cmp(o1, o2)

    def sortTrackList(self, l):
        """Sorts out a list of tracks according to the current programme order.
        """
        if len(l) == 0:
            return []
        elif len(l) == 1:
            return [l[0]]
        else:
            res = []
            for i in l:
                res.append(i)
            res.sort(self._cmpTracks)
            return res

    def requireDomain(self, dom):
        self.__ac.requireDomain(dom)
        # signals.event.domain_access_granted.send(self, domain=dom)

    def freeDomain(self, dom):
        self.__ac.freeDomain(dom)
        # signals.event.domain_access_revoked.send(self, domain=dom)

    def getDomainList(self):
        return self.__ac.getRequiredDomainList()

    def isProtected(self):
        """Tells whether a conference is protected for accessing or not
        """
        raise NotImplementedError('isProtected')
        return self.__ac.isProtected()

    def getAccessProtectionLevel( self ):
        raise NotImplementedError('getAccessProtectionLevel')
        return self.__ac.getAccessProtectionLevel()

    def isItselfProtected( self ):
        raise NotImplementedError('isItselfProtected')
        return self.__ac.isItselfProtected()

    def hasAnyProtection( self ):
        """Tells whether a conference has any kind of protection over it:
            access or domain protection.
        """
        raise NotImplementedError('hasAnyProtection')
        if self.isProtected():
            return True
        if self.getDomainList():
            return True

        if self.getAccessProtectionLevel() == -1:
            return False

        for owner in self.getOwnerList():
            if owner.hasAnyProtection():
                return True

        return False

    def hasProtectedOwner( self ):
        raise NotImplementedError('hasProtectedOwner')
        return self.__ac._getFatherProtection()

    def grantAccess( self, prin ):
        self.__ac.grantAccess( prin )
        if isinstance(prin, AvatarUserWrapper):
            prin.linkTo(self, "access")

    def revokeAccess( self, prin ):
        self.__ac.revokeAccess( prin )
        if isinstance(prin, AvatarUserWrapper):
            prin.unlinkTo(self, "access")

    def canAccess(self, aw):
        return self.as_event.can_access(aw.user)

    @unify_user_args
    def canUserModify(self, user):
        return self.as_event.can_manage(user)

    def canModify(self, aw_or_user):
        """Tells whether an access wrapper is allowed to modify the current
            conference: only if the user is granted to modify the conference and
            he is accessing from an IP address which is not restricted.
        """
        if hasattr(aw_or_user, 'getUser'):
            aw_or_user = aw_or_user.getUser()
        if isinstance(aw_or_user, AvatarUserWrapper):
            aw_or_user = aw_or_user.user
        return self.as_event.can_manage(aw_or_user)

    def getManagerList(self):
        managers = sorted([x.principal for x in self.as_event.acl_entries if x.has_management_role()],
                          key=lambda x: (x.is_single_person, x.name.lower()))
        return [x.as_legacy for x in managers]

    def getRegistrarList(self):
        registrars = sorted([x.principal for x in self.as_event.acl_entries if x.has_management_role('registration',
                                                                                                     explicit=True)],
                            key=lambda x: (x.is_single_person, x.name.lower()))
        return [x.as_legacy for x in registrars]

    def getAllowedToAccessList( self ):
        return self.__ac.getAccessList()

    def getDefaultStyle(self):
        return self.as_event.theme

    def clone(self, startDate, options, eventManager=None, userPerformingClone=None):
        # startDate must be in the timezone of the event (to avoid problems with daylight-saving times)
        managing = options.get("managing", None)
        if managing is not None:
            creator = managing
        else:
            creator = self.as_event.creator
        conf = Conference.new(self.as_event.category, creator=creator, title=self.getTitle(),
                              start_dt=self.getStartDate(), end_dt=self.getEndDate(), timezone=self.getTimezone(),
                              event_type=self.as_event.type_, add_creator_as_manager=False)
        conf.setTitle(self.getTitle())
        conf.setDescription(self.getDescription())
        conf.setTimezone(self.getTimezone())
        startDate = timezone(self.getTimezone()).localize(startDate).astimezone(timezone('UTC'))
        timeDelta = startDate - self.getStartDate()
        endDate = self.getEndDate() + timeDelta
        with track_time_changes():
            conf.setDates(startDate, endDate, moveEntries=1, enforce_constraints=False)
        conf.setContactInfo(self.getContactInfo())
        conf.setChairmanText(self.getChairmanText())
        conf.setVisibility(self.getVisibility())
        conf.setSupportInfo(self.getSupportInfo().clone(self))
        # Tracks in a conference
        if options.get("tracks",False) :
            for tr in self.getTrackList() :
                conf.addTrack(tr.clone(conf))
        conf.notifyModification()

        # Copy the list of enabled features
        features_event_settings.set_multi(conf, features_event_settings.get_all(self))
        feature_definitions = get_feature_definitions()
        for feature in get_enabled_features(conf):
            feature_definitions[feature].enabled(conf)

        # Run the new modular cloning system
        EventCloner.run_cloners(self.as_event, conf.as_event)
        signals.event.cloned.send(self.as_event, new_event=conf.as_event)

        # Grant access to the event creator -- must be done after modular cloners
        # since cloning the event ACL would result in a duplicate entry
        if managing is not None:
            with conf.as_event.logging_disabled:
                conf.as_event.update_principal(managing.user, full_access=True)

        return conf

    def getCoordinatedTracks( self, av ):
        """Returns a list with the tracks for which a user is coordinator.
        """
        try:
            if self._trackCoordinators:
                pass
        except AttributeError:
            self._trackCoordinators = TCIndex()
            self.notifyModification()
        return self._trackCoordinators.getTracks( av )

    def addTrackCoordinator( self, track, av ):
        """Makes a user become coordinator for a track.
        """
        try:
            if self._trackCoordinators:
                pass
        except AttributeError:
            self._trackCoordinators = TCIndex()
            self.notifyModification()
        if track in self.program:
            track.addCoordinator( av )
            self._trackCoordinators.indexCoordinator( av, track )
            self.notifyModification()

    def removeTrackCoordinator( self, track, av ):
        """Removes a user as coordinator for a track.
        """
        try:
            if self._trackCoordinators:
                pass
        except AttributeError:
            self._trackCoordinators = TCIndex()
            self.notifyModification()
        if track in self.program:
            track.removeCoordinator( av )
            self._trackCoordinators.unindexCoordinator( av, track )
            self.notifyModification()

    def getBOAConfig(self):
        try:
            if self._boa:
                pass
        except AttributeError:
            self._boa=BOAConfig(self)
        return self._boa

    def hasEnabledSection(self, section):
        # This hack is there since there is no more enable/disable boxes
        # in the conference managment area corresponding to those features.
        # Until the managment area is improved to get a more user-friendly
        # way of enabling/disabling those features, we always make them
        # available for the time being, but we keep the previous code for
        # further improvements
        return True

    def getAccessController(self):
        return self.__ac

    def getBadgeTemplateManager(self):
        try:
            if self.__badgeTemplateManager:
                pass
        except AttributeError:
            self.__badgeTemplateManager = BadgeTemplateManager(self)
        return self.__badgeTemplateManager

    def setBadgeTemplateManager(self, badgeTemplateManager):
        self.__badgeTemplateManager = badgeTemplateManager

    def getPosterTemplateManager(self):
        try:
            if self.__posterTemplateManager:
                pass
        except AttributeError:
            self.__posterTemplateManager = PosterTemplateManager(self)

        return self.__posterTemplateManager

    def setPosterTemplateManager(self, posterTemplateManager):
        self.__posterTemplateManager = posterTemplateManager


class DefaultConference(Conference):
    """ 'default' conference, which stores the
     default templates for posters and badges
    """

    def __init__(self):
        Conference.__init__(self, id='default')

    def __repr__(self):
        return '<DefaultConference()>'

    def getType(self):
        return 'conference'

    def notifyModification(self, *args, **kwargs):
        pass


class ConferenceHolder( ObjectHolder ):
    """Specialised ObjectHolder dealing with conference objects. It gives a
            common entry point and provides simple methods to access and
            maintain the collection of stored conferences (DB).
    """
    idxName = "conferences"
    counterName = "CONFERENCE"

    def _newId(self):
        raise RuntimeError('Tried to get new event id from zodb')

    def add(self, conf, event, add_creator_as_manager=True):
        db.session.add(event)
        db.session.flush()
        conf.setId(event.id)
        if conf.id in self._getIdx():
            raise RuntimeError('{} is already in ConferenceHolder'.format(conf.id))
        ObjectHolder.add(self, conf)
        if add_creator_as_manager:
            with event.logging_disabled:
                event.update_principal(event.creator, full_access=True)
        db.session.flush()

    def getById(self, id, quiet=False):
        if id == 'default':
            return HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference()

        id = str(id)
        if is_legacy_id(id):
            mapping = LegacyEventMapping.find_first(legacy_event_id=id)
            id = str(mapping.event_id) if mapping is not None else None
        event = self._getIdx().get(id) if id is not None else None
        if event is None and not quiet:
            raise NotFoundError(_("The event with id '{}' does not exist or has been deleted").format(id),
                                title=_("Event not found"))
        return event


class Resource(CommonObjectBase):
    def __init__(self, resData=None):
        self.id = "not assigned"
        self._owner = None

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        if self.getConference() == other.getConference():
            return cmp(self.getId(), other.getId())
        return cmp(self.getConference(), other.getConference())

    def notifyModification(self):
        self._p_changed = 1

    def getLocator(self):
        if self._owner is None:
            return Locator()
        lconf = self._owner.getLocator()
        lconf["resId"] = self.getId()
        return lconf

    def setId(self, newId):
        self.id = newId.strip()

    def getId(self):
        return self.id

    def setOwner(self, newOwner):
        self._owner = newOwner

    def getOwner(self):
        return self._owner

    def getConference(self):
        if self._owner is not None:
            return self._owner.getConference()

    @Updates(['MaKaC.conference.LocalFile'], 'name')
    def setName(self, newName):
        self.name = newName.strip()
        self.notifyModification()

    def getName(self):
        return self.name

    @Updates(['MaKaC.conference.LocalFile'], 'description')
    def setDescription(self, newDesc):
        self.description = newDesc.strip()
        self.notifyModification()

    def getDescription( self ):
        return self.description

    def archive( self, repository = None, forcedFileId = None ):
        """performs necessary operations to ensure the archiving of the
            resource. By default is doing nothing as the persistence of the
            system already ensures the archiving of the basic resource data"""
        return

    def delete(self):
        self._owner = None


class LocalFile(Resource):
    """Specialises Resource class in order to represent files which can be
        stored in the system. The user can choose to use the system as an
        archive of electronic files so he may want to attach a file which is
        in his computer to a conference so it remains there and must be kept
        in the system. This object contains the file basic metadata and provides
        the necessary operations to ensure the corresponding file is archived
        (it uses one of the file repositories of the system to do so) and keeps
        the reference for being able to access it afterwards.
       Params:
        fileName -- (string) Name of the file. Normally the original name of
            the user submitted file is kept.
        filePath -- (string) If it is set, it contains a local path to the
            file submitted by the user and uploaded in the system. This
            attribute is only temporary used so it keeps a pointer to a
            temporary uploaded file.
        __repository -- (FileRep) Once a file is archived, it is kept in a
            FileRepository for long term. This attribute contains a pointer
            to the file repository where the file is kept.
        __archivedId -- (string) It contains a unique identifier for the file
            inside the repository where it is archived.
    """

    def __init__( self, resData = None ):
        Resource.__init__( self, resData )
        self.fileName= ""
        self.fileType = ""
        self.filePath = ""
        self.__repository = None
        self.__archivedId = ""

    def clone( self, conf, protection=True ):
        localfile = Resource.clone(self, conf, protection)
        localfile.setFilePath(self.getFilePath())
        localfile.setFileName(self.getFileName())
        return localfile

    def getLocator(self):
        locator = Resource.getLocator(self)
        try:
            locator['fileExt'] = (self.fileType.lower() or
                                  os.path.splitext(self.fileName)[1].lower().lstrip('.') or None)
        except Exception:
            locator['fileExt'] = 'bin'  # no extension => use a dummy
        return locator

    def setFileName( self, newFileName, checkArchive=True ):
        """While the file is not archived sets the file name of the current
            object to the one specified (if a full path is specified the
            base name is extracted) replacing on it blanks by underscores.
        """
        if checkArchive and self.isArchived():
            raise MaKaCError( _("The file name of an archived file cannot be changed"), _("File Archiving"))
        #Using os.path.basename is not enough as it only extract filenames
        #   correclty depending on the server platform. So we need to convert
        #   to the server platform and apply the basename extraction. As I
        #   couldn't find a python function for this this is done manually
        #   although it can contain errors
        #On windows basename function seems to work properly with unix file
        #   paths
        if newFileName.count("/"):
            #unix filepath
            newFileName = newFileName.split("/")[-1]
        else:
            #windows file path: there "/" is not allowed on windows paths
            newFileName = newFileName.split("\\")[-1]
        self.fileName = newFileName.strip().replace(" ", "_")

    def getFileName( self ):
        return self.fileName

    def getFileType( self ):
        fileExtension = os.path.splitext( self.getFileName() )[1]
        if fileExtension != "":
            fileExtension = fileExtension[1:]
        cfg = Config.getInstance()
        if cfg.getFileType( fileExtension ) != "":
            return cfg.getFileType( fileExtension )
        else:
            return fileExtension

    def setFilePath( self, filePath ):
        if self.isArchived():
            raise MaKaCError( _("The path of an archived file cannot be changed"), _("File Archiving"))
        if not os.access( filePath.strip(), os.F_OK ):
            raise Exception( _("File does not exist : %s")%filePath.strip())
        self.filePath = filePath.strip()

    def getCreationDate( self):
        return self.__repository.getCreationDate(self.__archivedId)

    def getFilePath( self ):
        if not self.isArchived():
            return self.filePath
        return self.__repository.getFilePath(self.__archivedId)

    def getSize( self ):
        if not self.isArchived():
            return int(os.stat(self.getFilePath())[stat.ST_SIZE])
        return self.__repository.getFileSize( self.__archivedId )

    def setArchivedId( self, rep, id ):
        self.__repository = rep
        self.__archivedId = id

    def getRepositoryId( self ):
        return self.__archivedId

    def setRepositoryId(self, id):
        self.__archivedId = id

    def isArchived( self ):
        return self.__repository != None and self.__archivedId != ""

    def readBin( self ):
        if not self.isArchived():
            raise MaKaCError( _("File not available until it has been archived") , _("File Archiving"))
        return self.__repository.readFile( self.__archivedId  )

    def archive( self, repository=None, forcedFileId = None ):
        if self.isArchived():
            raise Exception( _("File is already archived"))
        if not repository:
            raise Exception( _("Destination repository not set"))
        if self.filePath == "":
            return _("Nothing to archive")
        repository.storeFile( self, forcedFileId = forcedFileId)
        self.filePath = ""
        self.notifyModification()

    def delete( self ):
        if not self.isArchived():
            os.remove( self.getFilePath() )
        try:
            self.__repository.retireFile( self )
        except AttributeError, e:
            pass
        Resource.delete( self )

    def getRepository(self):
        return self.__repository

    def __str__( self ):
        return self.getFileName()


class TCIndex( Persistent ):
    """Index for conference track coordinators.

        This class allows to index conference track coordinators so the owner
        can answer optimally to the query if a user is coordinating
        any conference track.
        It is implemented by simply using a BTree where the Avatar id is used
        as key (because it is unique and non variable) and a list of
        coordinated tracks is kept as keys. It is the responsability of the
        index owner (conference) to keep it up-to-date i.e. notify track
        coordinator additions and removals.
    """

    def __init__( self ):
        self._idx = OOBTree()


    def getTracks( self, av ):
        """Gives a list with the tracks a user is coordinating.
        """
        if av == None:
            return []
        return self._idx.get( av.getId(), [] )

    def indexCoordinator( self, av, track ):
        """Registers in the index a coordinator of a track.
        """
        if av == None or track == None:
            return
        if not self._idx.has_key( av.getId() ):
            l = []
        else:
            l = self._idx[av.getId()]
        if track not in l:
            l.append(track)
            # necessary, otherwise ZODB won't know it needs to update the BTree
            self._idx[av.getId()] = l
        self.notifyModification()

    def unindexCoordinator( self, av, track ):
        if av == None or track == None:
            return
        l = self._idx.get( av.getId(), [] )
        if track in l:
            l.remove( track )
            self._idx[av.getId()] = l
        self.notifyModification()

    def notifyModification(self):
        self._p_changed = 1


class Track(CoreObject):

    def __init__( self ):
        self.conference = None
        self.id = "not assigned"
        self.title = ""
        self.description = ""
        self._abstracts = OOBTree()
        self._coordinators = []
        self._contributions = OOBTree()
        self._code=""

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        if self.getConference() == other.getConference():
            return cmp(self.getId(), other.getId())
        return cmp(self.getConference(), other.getConference())

    def clone(self, conference):
        tr = Track()
        tr.setConference(conference)
        tr.setTitle(self.getTitle())
        tr.setCode(self.getCode())
        tr.setDescription(self.getDescription())
        for co in self.getCoordinatorList():
            tr.addCoordinator(co)
        return tr


    def delete( self ):
        """Deletes a track from the system. All the associated abstracts will
            also be notified so the track is no longer associated to them.
        """
        #XXX: Should we allow to delete a track when there are some abstracts
        #       or contributions submitted for it?!?!?!?!

        # we must notify each abstract in the track about the deletion of the
        #   track
        while len(self._abstracts)>0:
            k = self._abstracts.keys()[0]
            abstract = self._abstracts[k]
            del self._abstracts[k]
            self._p_changed = True
            abstract.removeTrack( self )

        # we must notify each contribution in the track about the deletion of the
        #   track
        while len(self._contributions)>0:
            k = self._contributions.keys()[0]
            contrib = self._contributions[k]
            del self._contributions[k]
            self._p_changed = True
            contrib.removeTrack( self )

        # we must delete and unindex all the possible track coordinators
        while len(self._coordinators)>0:
            self.removeCoordinator(self._coordinators[0])

        # we must notify the conference about the track deletion
        if self.conference:
            conf = self.conference
            self.conference = None
            conf.removeTrack( self )

        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def canModify(self, aw_or_user):
        return self.conference.canModify(aw_or_user)

    def canUserModify( self, av ):
        return self.conference.canUserModify( av )

    def notifyModification( self ):
        parent = self.getConference()
        if parent:
            parent.setModificationDate()
        self._p_changed = 1

    def getLocator( self ):
        """Gives back a globaly unique identification encapsulated in a Locator
            object for the track instance
        """
        if self.conference == None:
            return Locator()
        lconf = self.conference.getLocator()
        lconf["trackId"] = self.getId()
        return lconf

    def setConference(self, conference):
        self.conference = conference

    def getConference( self ):
        return self.conference

    def getOwner( self ):
        return self.getConference()

    def setId( self, newId ):
        self.id = str(newId)

    def getId( self ):
        return self.id

    def setTitle( self, newTitle ):
        self.title = newTitle
        self.notifyModification()

    def getTitle( self ):
        return self.title

    def setDescription(self, newDescription ):
        self.description = newDescription
        self.notifyModification()

    def getDescription(self):
        return self.description

    def getCode(self):
        try:
            if self._code:
                pass
        except AttributeError:
            self._code=self.id
        return self._code

    def setCode(self,newCode):
        self._code=str(newCode).strip()

    def getAbstractList( self ):
        """
        """
        try:
            if self._abstracts:
                pass
        except AttributeError:
            self._abstracts = OOBTree()
        return self._abstracts.values()

    def getAbstractById( self, id ):
        try:
            if self._abstracts:
                pass
        except AttributeError:
            self._abstracts = OOBTree()
        return self._abstracts.get(str(id).strip())

    def hasAbstract( self, abstract ):
        """
        """
        try:
            if self._abstracts:
                pass
        except AttributeError:
            self._abstracts = OOBTree()
        return self._abstracts.has_key( abstract.getId() )

    def addAbstract( self, abstract ):
        """Adds an abstract to the track abstract list.

            Notice that this method doesn't notify the abstract about the track
            addition.
        """
        if not self.hasAbstract( abstract ):
            self._abstracts[ abstract.getId() ] = abstract
            #abstract.addTrack( self )

    def removeAbstract( self, abstract ):
        """Removes an abstract from the track abstract list.

            Notice that this method doesn't notify the abstract about the track
            removal.
        """
        if self.hasAbstract( abstract ):
            del self._abstracts[ abstract.getId() ]
            self._p_changed = True
            #abstract.removeTrack( self )

    def addCoordinator( self, av ):
        """Grants coordination privileges to user.

            Arguments:
                av -- (AvatarUserWrapper) the user to which
                    coordination privileges must be granted.
        """

        try:
            if self._coordinators:
                pass
        except AttributeError, e:
            self._coordinators = []
            self.notifyModification()

        if not (av in self._coordinators):
            self._coordinators.append( av )
            self.getConference().addTrackCoordinator( self, av )
            av.linkTo(self, "coordinator")
            self.notifyModification()

    def removeCoordinator( self, av ):
        """Revokes coordination privileges to user.

           Arguments:
            av -- (AvatarUserWrapper) user for which coordination privileges
                    must be revoked
        """
        try:
            if self._coordinators:
                pass
        except AttributeError, e:
            self._coordinators = []
            self.notifyModification()

        if av in self._coordinators:
            self._coordinators.remove( av )
            self.getConference().removeTrackCoordinator( self, av )
            av.unlinkTo(self, "coordinator")
            self.notifyModification()

    def isCoordinator( self, av ):
        """Tells whether the specified user is a coordinator of the track.

           Arguments:
            av -- (AvatarUserWrapper) user to be checke

           Return value: (boolean)
        """
        try:
            if self._coordinators:
                pass
        except AttributeError, e:
            self._coordinators = []

        return av in self._coordinators

    def getCoordinatorList( self ):
        """Return all users which have privileges to coordinate the track.

            Return value: (list)
        """
        try:
            if self._coordinators:
                pass
        except AttributeError, e:
            self._coordinators = []

        return self._coordinators

    def canCoordinate( self, aw ):
        """Tells if a user has coordination privileges.

            Only track coordinators have coordination privileges over a track.

            Params:
                aw -- (MaKaC.accessControl.AccessWrapper) User access
                    information for which the coordination privileges must be
                    checked.

            Return value: (boolean)
        """
        return self.isCoordinator( aw.getUser() ) or self.canModify( aw )

    def addContribution( self, newContrib ):
        """
        """
        try:
            if self._contributions:
                pass
        except AttributeError:
            self._contributions = OOBTree()
        if self._contributions.has_key( newContrib.getId() ):
            return
        self._contributions[ newContrib.getId() ] = newContrib
        newContrib.setTrack( self )

    def removeContribution( self, contrib ):
        """
        """
        try:
            if self._contributions:
                pass
        except AttributeError:
            self._contributions = OOBTree()
        if not self._contributions.has_key( contrib.getId() ):
            return
        del self._contributions[ contrib.getId() ]
        self._p_changed = True
        contrib.setTrack( None )

    def hasContribution( self, contrib ):
        try:
            if self._contributions:
                pass
        except AttributeError:
            self._contributions = OOBTree()
        return self._contributions.has_key( contrib.getId() )

    def getContributionList(self):
        try:
            if self._contributions:
                pass
        except AttributeError:
            self._contributions = OOBTree()
        return self._contributions.values()

    def canUserCoordinate( self, av ):
        return self.isCoordinator( av ) or self.canUserModify( av )


class BOAConfig(Persistent):
    """Contains the configuration of the Book of Abstracts of a conference
    """
    sortByTypes = {"number": L_("ID"),
                   "name": L_("Title"),
                   "sessionTitle": L_("Session title"),
                   "speaker": L_("Presenter"),
                   "schedule": L_("Schedule")}

    correspondingAuthorTypes = {"none": L_("Nobody"),
                   "submitter": L_("Submitter"),
                   "speakers": L_("Speakers")}

    def __init__(self,conf):
        self._conf=conf
        self._text=""
        self._showIds= False
        self._sortBy = "number"
        self._correspondingAuthor = "submitter"
        self._modificationDS = nowutc()
        self._cache = False

    def getText(self):
        return self._text

    def setText(self,newText):
        self._text=newText.strip()
        self._notifyModification()

    def getShowIds(self):
        if not hasattr(self, "_showIds"):
            self._showIds=False
        return self._showIds

    def setShowIds(self,showIds):
        self._showIds=showIds
        self._notifyModification()

    def getSortBy(self):
        if not hasattr(self, "_sortBy"):
            self._sortBy="number"
        return self._sortBy

    def setSortBy(self,sortBy):
        self._sortBy=sortBy
        self._notifyModification()

    @staticmethod
    def getSortByTypes():
        return BOAConfig.sortByTypes

    def getCorrespondingAuthor(self):
        if not hasattr(self, "_correspondingAuthor"):
            self._correspondingAuthor = "submitter"
        return self._correspondingAuthor

    def setCorrespondingAuthor(self, correspondingAuthor):
        self._correspondingAuthor = correspondingAuthor
        self._notifyModification()

    @staticmethod
    def getCorrespondingAuthorTypes():
        return BOAConfig.correspondingAuthorTypes

    def isCacheEnabled(self):
        if not hasattr(self, '_cache'):
            self._cache = False
        return self._cache

    def setCache(self, value):
        self._cache = value;

    def _notifyModification(self):
        self._modificationDS = nowutc()

    @property
    def lastChanged(self):
        if not hasattr(self, '_modificationDS'):
            self._modificationDS = nowutc()
        return self._modificationDS
