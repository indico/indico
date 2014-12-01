# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the FreeSoftware Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from itertools import ifilter

# fossil classes
from MaKaC.common.timezoneUtils import datetimeToUnixTimeInt
from MaKaC.plugins import PluginsHolder, Observable
from MaKaC.common.utils import formatDateTime
from MaKaC.fossils.subcontribution import ISubContribParticipationFossil,\
    ISubContribParticipationFullFossil, ISubContributionFossil, ISubContributionWithSpeakersFossil
from MaKaC.fossils.contribution import IContributionParticipationFossil,\
    IContributionFossil, IContributionWithSpeakersFossil, IContributionParticipationMinimalFossil, \
    IContributionWithSubContribsFossil,\
    IContributionParticipationTTDisplayFossil, \
    IContributionParticipationTTMgmtFossil
from MaKaC.fossils.conference import IConferenceMinimalFossil, \
    IConferenceEventInfoFossil, IConferenceFossil,\
    ISessionFossil, ISessionSlotFossil, IMaterialMinimalFossil,\
    IMaterialFossil, IConferenceParticipationFossil,\
    IResourceMinimalFossil, ILinkMinimalFossil, ILocalFileMinimalFossil,\
    IResourceFossil, ILinkFossil, ILocalFileFossil,\
    ILocalFileExtendedFossil, IConferenceParticipationMinimalFossil,\
    ICategoryFossil, ILocalFileAbstractMaterialFossil
from MaKaC.common.fossilize import fossilizes, Fossilizable
from MaKaC.common.url import ShortURLMapper
from MaKaC.contributionReviewing import Review
from MaKaC.rb_location import CrossLocationQueries, CrossLocationDB
from indico.util.i18n import L_
from indico.util.string import safe_upper, safe_slice
from MaKaC.review import AbstractFieldContent


import re, os
import tempfile
import copy
import stat
from datetime import datetime, timedelta, time
from flask import session

from MaKaC.contributionReviewing import ReviewManager
from MaKaC.paperReviewing import ConferencePaperReview as ConferencePaperReview
from MaKaC.abstractReviewing import ConferenceAbstractReview as ConferenceAbstractReview

from pytz import timezone
from pytz import all_timezones

from persistent import Persistent
from BTrees.OOBTree import OOBTree, OOTreeSet, OOSet
from BTrees.OIBTree import OIBTree,OISet,union
import MaKaC
from MaKaC.common import indexes
from MaKaC.common.timezoneUtils import nowutc, maxDatetime
import MaKaC.fileRepository as fileRepository
from MaKaC.schedule import ConferenceSchedule, SessionSchedule,SlotSchedule,\
     PosterSlotSchedule, SlotSchTypeFactory, ContribSchEntry, \
     LinkedTimeSchEntry, BreakTimeSchEntry
import MaKaC.review as review
from MaKaC.common import utils
from MaKaC.common.Counter import Counter
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.common.Locators import Locator
from MaKaC.accessControl import AccessController, AdminList
from MaKaC.errors import MaKaCError, TimingError, ParentTimingError, EntryTimingError, NoReportError, FormValuesError
from MaKaC import registration, epayment
from MaKaC.evaluation import Evaluation
from MaKaC.trashCan import TrashCanManager
from MaKaC.user import AvatarHolder
from MaKaC.common import pendingQueues
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.participant import Participation
from MaKaC.common.log import LogHandler
import MaKaC.common.info as info
from MaKaC.badge import BadgeTemplateManager
from MaKaC.poster import PosterTemplateManager
from MaKaC.common import mail
from MaKaC.common.utils import getHierarchicalId
from MaKaC.i18n import _
from MaKaC.common.PickleJar import Updates
from MaKaC.common.PickleJar import if_else
from MaKaC.schedule import ScheduleToJson
from MaKaC.webinterface import urlHandlers

from MaKaC.common.logger import Logger
from MaKaC.common.contextManager import ContextManager
from MaKaC.webinterface.common.tools import escape_html
import zope.interface

from indico.modules.scheduler import Client, tasks
from indico.util.date_time import utc_timestamp, format_datetime
from indico.core.index import IIndexableByStartDateTime, IUniqueIdProvider, Catalog
from indico.core.db import DBMgr
from indico.core.db.event import SupportInfo
from indico.core.config import Config

from indico.util.redis import write_client as redis_write_client
import indico.util.redis.avatar_links as avatar_links


class CoreObject(Persistent):
    """
    CoreObjects are Persistent objects that are employed by Indico's core
    """

    zope.interface.implements(IUniqueIdProvider,
                              IIndexableByStartDateTime)

    def setModificationDate(self, date=None):
        """
        Method called to notify the current object has been modified.
        """
        if not date:
            date = nowutc()
        self._modificationDS = date

    def __conform__(self, proto):

        if proto == IIndexableByStartDateTime:
            return utc_timestamp(self.getStartDate())
        else:
            return None


class Locatable:
    """
    Inherited by objects that imply a physical location:
    * Conferences
    * Sessions
    * SessionSlots
    * Contributions
    * SubContributions
    """

    def getLocationParent(self):
        """
        Returns the object the location info should be inherited from
        (Overridden)
        """
        raise Exception("Unimplemented method")

    def getLocation(self):
        if self.getOwnLocation():
            return self.getOwnLocation()
        return self.getInheritedLocation()

    def getOwnLocation(self):
        if len(self.places) > 0:
            return self.places[0]
        return None

    def getInheritedLocation(self):
        return self.getLocationParent().getLocation()

    def getOwnRoom(self):
        if len(self.rooms) > 0:
            return self.rooms[0]
        return None

    def getRoom(self):
        if self.getOwnRoom():
            return self.getOwnRoom()
        return self.getInheritedRoom()

    def getInheritedRoom(self):
        return self.getLocationParent().getRoom()

    def setLocation(self, newLocation):
        oldLocation = self.getOwnLocation()
        if newLocation is None:
            if len(self.places) > 0:
                del self.places[0]
        elif len(self.places) > 0:
            self.places[0] = newLocation
        else:
            self.places.append(newLocation)
        self.notifyModification()

    def setRoom(self, newRoom):
        oldRoom = self.getOwnRoom()
        if newRoom is None:
            if len(self.rooms) > 0:
                del self.rooms[0]
        elif len(self.rooms) > 0:
            self.rooms[0] = newRoom
        else:
            self.rooms.append(newRoom)
        self.notifyModification()


class CommonObjectBase(CoreObject, Observable, Fossilizable):
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

    def getRecursiveAllowedToAccessList(self, onlyManagers=False):
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
            al = self.getAllowedToAccessList() + self.getManagerList() + \
                self.getOwner().getRecursiveManagerList()
            if al is not None:
                for av in al:
                    av_set.add(av)

        # If access settings are inherited (and PRIVATE) from its owners, look at those.
        elif apl == 0 and self.isProtected():
            # If event is protected, then get list of people/groups allowed
            # to access, and add that to the set of avatars.
            al = self.getAllowedToAccessList() + self.getManagerList()
            if al is not None:
                for av in al:
                    av_set.add(av)

            # Add list of avatars/groups allowed to access parents objects.
            owner = self.getOwner()
            if owner is not None:
                owner_al = owner.getRecursiveAllowedToAccessList(onlyManagers=True)
                if owner_al is not None:
                    for av in owner_al:
                        av_set.add(av)

        # return set containing whatever avatars/groups we may have collected
        return av_set


class CategoryManager(ObjectHolder):
    idxName = "categories"
    counterName = "CATEGORY"

    def add(self, category):
        ObjectHolder.add(self, category)
        # Add category to the name index
        nameIdx = indexes.IndexesHolder().getIndex('categoryName')
        nameIdx.index(category.getId(), category.getTitle().decode('utf-8'))

    def remove(self, category):
        ObjectHolder.remove(self, category)
        # remove category from the name index
        nameIdx = indexes.IndexesHolder().getIndex('categoryName')
        nameIdx.unindex(category.getId())
        Catalog.getIdx('categ_conf_sd').remove_category(category.getId())

    def _newId(self):
        """
        returns a new id for the category
        the id must not already exist in the collection
        """
        id = ObjectHolder._newId(self)
        while self.hasKey(id):
            id = ObjectHolder._newId(self)
        return id

    def getRoot(self):
        root = DBMgr.getInstance().getDBConnection().root()
        if not root.has_key("rootCategory"):
            r = Category()
            r.setName("Home")
            self.add(r)
            root["rootCategory"] = r
        return root["rootCategory"]

    def getDefaultConference(self):
        dconf = HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference()
        if dconf == None:
            return HelperMaKaCInfo.getMaKaCInfoInstance().setDefaultConference(DefaultConference())
        else:
            return dconf


class Category(CommonObjectBase):
    fossilizes(ICategoryFossil)

    def __init__(self):

        self.id = ""
        self.name = ""
        self.description = ""
        self.subcategories = {}
        self.materials = {}
        self.conferences = OOTreeSet()
        self._numConferences = 0
        self.owner = None
        self._defaultStyle = {"simple_event": "", "meeting": ""}
        self._order = 0
        self.__ac = AccessController(self)
        self.__confCreationRestricted = 1
        self.__confCreators = []
        self._visibility = 999
        self._statistics = {"events": None, "contributions": None, "resources": None,
                            "updated": None}
        self._icon = None
        self.materials = {}
        #self._materials = {}
        #self.material ={}
        self._tasksAllowed = False
        self._tasks = {}
        self._taskIdGenerator = 0
        self._tasksPublic = True
        self._tasksCommentPublic = True
        self._tasksManagers = []
        self._tasksCommentators = []
        self._taskAccessList = []
        self._timezone = ""
        self.__materialGenerator = Counter()
        self._notifyCreationList = ""

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        return cmp(self.getId(), other.getId())

    def __repr__(self):
        path = '/'.join(self.getCategoryPathTitles()[:-1])
        return '<Category({0}, {1}, {2})>'.format(self.getId(), self.getName(), path)

    def __str__(self):
        return "<Category %s@%s>" % (self.getId(), hex(id(self)))

    def getAccessController(self):
        return self.__ac

    def updateNonInheritingChildren(self, elem, delete=False):
        pass

    def getNotifyCreationList(self):
        """ self._notifyCreationList is a string containing the list of
        email addresses to send an email to when a new event is created"""
        try:
            return self._notifyCreationList
        except:
            self._notifyCreationList = ""
            return self._notifyCreationList

    def setNotifyCreationList(self, value):
        self._notifyCreationList = value

    def getUniqueId(self):
        return "cat%s" % self.getId()

    def setPaper(self, newPaper):
        if self.getPaper() is not None:
            raise MaKaCError(_("The paper for this conference has already been set"), _("Conference"))
        self.paper = newPaper
        self.paper.setOwner(self)
        self.notifyModification()

    def removePaper(self):
        if self.paper is None:
            return
        self.paper.delete()
        self.paper.setOwner(None)
        self.paper = None
        self.notifyModification()

    def recoverPaper(self, p):
        self.setPaper(p)
        p.recover()

    def getPaper(self):
        try:
            if self.paper:
                pass
        except AttributeError:
            self.paper = None
        return self.paper

    def setSlides(self, newSlides):
        if self.getSlides() is not None:
            raise MaKaCError(_("The slides for this conference have already been set"), _("Conference"))
        self.slides = newSlides
        self.slides.setOwner(self)
        self.notifyModification()

    def removeSlides(self):
        if self.slides is None:
            return
        self.slides.delete()
        self.slides.setOwner(None)
        self.slides = None
        self.notifyModification()

    def recoverSlides(self, s):
        self.setSlides(s)
        s.recover()

    def getSlides(self):
        try:
            if self.slides:
                pass
        except AttributeError:
            self.slides = None
        return self.slides

    def setVideo(self, newVideo):
        if self.getVideo() is not None:
            raise MaKaCError(_("The video for this conference has already been set"), _("Conference"))
        self.video = newVideo
        self.video.setOwner(self)
        self.notifyModification()

    def removeVideo(self):
        if self.getVideo() is None:
            return
        self.video.delete()
        self.video.setOwner(None)
        self.video = None
        self.notifyModification()

    def recoverVideo(self, v):
        self.setVideo(v)
        v.recover()

    def getVideo(self):
        try:
            if self.video:
                pass
        except AttributeError:
            self.video = None
        return self.video

    def setPoster(self, newPoster):
        if self.getPoster() is not None:
            raise MaKaCError(_("the poster for this conference has already been set"), _("Conference"))
        self.poster = newPoster
        self.poster.setOwner(self)
        self.notifyModification()

    def removePoster(self):
        if self.getPoster() is None:
            return
        self.poster.delete()
        self.poster.setOwner(None)
        self.poster = None
        self.notifyModification()

    def recoverPoster(self, p):
        self.setPoster(p)
        p.recover()

    def getPoster(self):
        try:
            if self.poster:
                pass
        except AttributeError:
            self.poster = None
        return self.poster

    def setMinutes(self, newMinutes):
        if self.getMinutes() is not None:
            raise MaKaCError(_("The Minutes for this conference has already been set"))
        self.minutes = newMinutes
        self.minutes.setOwner(self)
        self.notifyModification()

    def createMinutes(self):
        if self.getMinutes() is not None:
            raise MaKaCError(_("The minutes for this conference have already been created"), _("Conference"))
        self.minutes = Minutes()
        self.minutes.setOwner(self)
        self.notifyModification()
        return self.minutes

    def removeMinutes(self):
        if self.getMinutes() is None:
            return
        self.minutes.delete()
        self.minutes.setOwner(None)
        self.minutes = None
        self.notifyModification()

    def recoverMinutes(self, min):
        self.removeMinutes()  # To ensure that the current minutes are put in
                              # the trash can.
        self.minutes = min
        self.minutes.setOwner(self)
        min.recover()
        self.notifyModification()
        return self.minutes

    def getMinutes(self):
        #To be removed
        try:
           if self.minutes:
            pass
        except AttributeError, e:
            self.minutes = None
        return self.minutes

    def addMaterial(self, newMat):
        try:
            newMat.setId(str(self.__materialGenerator.newCount()))
        except:
            self.__materialGenerator = Counter()
            newMat.setId(self.__materialGenerator.newCount())
        newMat.setOwner(self)
        self.materials[newMat.getId()] = newMat
        self.notifyModification()

    def removeMaterial(self, mat):
        if mat.getId() in self.materials.keys():
            mat.delete()
            self.materials[mat.getId()].setOwner(None)
            del self.materials[mat.getId()]
            self.notifyModification()
            return "done: %s" % mat.getId()
        elif mat.getId().lower() == 'minutes':
            self.removeMinutes()
            return "done: %s" % mat.getId()
        elif mat.getId().lower() == 'paper':
            self.removePaper()
            return "done: %s" % mat.getId()
        elif mat.getId().lower() == 'slides':
            self.removeSlides()
            return "done: %s" % mat.getId()
        elif mat.getId().lower() == 'video':
            self.removeVideo()
            return "done: %s" % mat.getId()
        elif mat.getId().lower() == 'poster':
            self.removePoster()
            return "done: %s" % mat.getId()
        return "not done: %s" % mat.getId()

    def recoverMaterial(self, recMat):
    # Id must already be set in recMat.
        recMat.setOwner(self)
        self.materials[recMat.getId()] = recMat
        recMat.recover()
        self.notifyModification()

    def getMaterialRegistry(self):
        """
        Return the correct material registry for this type
        """
        from MaKaC.webinterface.materialFactories import CategoryMFRegistry
        return CategoryMFRegistry

    def getMaterialById(self, matId):
        if matId.lower() == 'paper':
            return self.getPaper()
        elif matId.lower() == 'slides':
            return self.getSlides()
        elif matId.lower() == 'video':
            return self.getVideo()
        elif matId.lower() == 'poster':
            return self.getPoster()
        elif matId.lower() == 'minutes':
            return self.getMinutes()
        elif self.materials.has_key(matId):
            return self.materials[matId]
        return None

    def getMaterialList(self):
        try:
            return self.materials.values()
        except:
            self.materials = {}
            return self.materials.values()

    def getAllMaterialList(self):
        l = self.getMaterialList()
        if self.getPaper():
            l.append(self.getPaper())
        if self.getSlides():
            l.append(self.getSlides())
        if self.getVideo():
            l.append(self.getVideo())
        if self.getPoster():
            l.append(self.getPoster())
        if self.getMinutes():
            l.append(self.getMinutes())
        return l

    def getTaskList(self):
        try:
            return self._tasks.values()
        except:
            self._tasks = {}
            return self._tasks.values()

    def getTitle(self):
        return self.name

    def getTasks(self):
        try:
            return self._tasks
        except:
            self._tasks = {}
            return self._tasks

    def getTask(self, taskId):
        return self.getTasks().get(taskId, None)

    def _getTasksAllowed(self):
        try:
            return self._tasksAllowed
        except:
            self._tasksAllowed = False
            return self._tasksAllowed

    def tasksAllowed(self):
        if self.hasSubcategories():
            return False
        return self._getTasksAllowed()

    def setTasksAllowed(self):
        if self.hasSubcategories():
            return False
        self._getTasksAllowed()
        self._tasksAllowed = True
        self.notifyModification()
        return True

    def setTasksForbidden(self):
        if len(self.getTaskList()) > 0:
            return False
        self._getTasksAllowed()
        self._tasksAllowed = False
        self.notifyModification()
        return False

    def _getNewTaskId(self):
        try:
            if self._taskIdGenerator:
                pass
        except:
            self._taskIdGenerator = 0
        self._taskIdGenerator = self._taskIdGenerator + 1
        return self._taskIdGenerator

    def newTask(self, user):
        if user is None:
            return None
        newTask = task.Task(self, self._getNewTaskId(), user)
        self.getTasks()["%s" % newTask.getId()] = newTask
        self.notifyModification()
        return newTask

    def tasksPublic(self):
        try:
            return self._tasksPublic
        except:
            self._tasksPublic = True
            return self._tasksPublic

    def setTasksPublic(self):
        self.tasksPublic()
        self._tasksPublic = True

    def setTasksPrivate(self):
        self.tasksPublic()
        self._tasksPublic = False

    def tasksCommentPublic(self):
        try:
            return self._tasksCommentPublic
        except:
            self._tasksCommentPublic = True
            return self._tasksCommentPublic

    def setTasksCommentPublic(self):
        self.tasksCommentPublic()
        self._tasksCommentPublic = True

    def setTasksCommentPrivate(self):
        self.tasksCommentPublic()
        self._tasksCommentPublic = False

    def getTasksManagerList(self):
        try:
            return self._tasksManagers
        except:
            self._tasksManagers = []
            self._p_changed = 1
            return self._tasksManagers

    def getTasksManager(self, index):
        length = len(self.getTasksManagerList())
        if index < 0 or index >= length:
            return None
        return self._tasksManagers[index]

    def addTasksManager(self, user):
        if user is None:
            return False
        self.getTasksManagerList().append(user)
        self._p_changed = 1
        return True

    def removeTasksManager(self, index):
        length = len(self.getTasksManagerList())
        if index < 0 or index >= length:
            return False
        del self.getTasksManagerList()[index]
        self._p_changed = 1
        return True

    def getTasksCommentatorList(self):
        try:
            return self._tasksCommentators
        except:
            self._tasksCommentators = []
            self._p_changed = 1
            return self._tasksCommentators

    def getTasksCommentator(self, index):
        length = len(self.getTasksCommentatorList())
        if index < 0 or index >= length:
            return None
        return self._tasksCommentators[index]

    def addTasksCommentator(self, user):
        if user is None:
            return False
        self.getTasksCommentatorList().append(user)
        self._p_changed = 1
        return True

    def removeTasksCommentator(self, index):
        length = len(self.getTasksCommentatorList())
        if index < 0 or index >= length:
            return False
        del self._tasksCommentators[index]
        self._p_changed = 1
        return True

    def getTasksAccessList(self):
        try:
            return self._tasksAccessList
        except:
            self._tasksAccessList = []
            self._p_changed = 1
            return self._tasksAccessList

    def getTasksAccessPerson(self, index):
        length = len(self.getTasksAccessList())
        if index < 0 or index >= length:
            return None
        return self._tasksAccessList[index]

    def addTasksAccessPerson(self, user):
        if user is None:
            return False
        self.getTasksAccessList().append(user)
        self._p_changed = 1
        return True

    def removeTasksAccessPerson(self, index):
        length = len(self.getTasksAccessList())
        if index < 0 or index >= length:
            return False
        del self.getTasksAccessList()[index]
        self._p_changed = 1
        return True

    def hasSubcategories(self):
        return len(self.subcategories.values()) > 0

    def getVisibility(self):
        """
        Returns category visibility, considering that it can be
        restricted by parent categories
        """
        owner = self.getOwner()
        visibility = int(self._visibility)

        # visibility can be restricted by parent categories
        if owner:
            return max(0, min(visibility, owner.getVisibility() + 1))
        else:
            return visibility

    def setVisibility(self, visibility=999):
        self._visibility = int(visibility)
        self._reindex()

    def isSuggestionsDisabled(self):
        try:
            return self._suggestions_disabled
        except AttributeError:
            self._suggestions_disabled = False
            return False

    def setSuggestionsDisabled(self, value):
        self._suggestions_disabled = value

    def _reindex(self):
        catIdx = indexes.IndexesHolder().getIndex('category')
        catIdx.reindexCateg(self)
        catDateIdx = indexes.IndexesHolder().getIndex('categoryDate')
        catDateIdx.reindexCateg(self)
        catDateAllIdx = indexes.IndexesHolder().getIndex('categoryDateAll')
        catDateAllIdx.reindexCateg(self)

    def isRoot(self):
        #to be improved
        return self.owner is None

    def getDefaultStyle(self, type):
        try:
            return self._defaultStyle[type]
        except:
            return ""

    def setDefaultStyle(self, type, style, subcatsStyle=False):
        try:
            self._defaultStyle[type] = style
        except:
            self._defaultStyle = {"simple_event": "", "meeting": ""}
            self._defaultStyle[type] = style
        self.notifyModification()
        #raise str(subcatsStyle)
        if subcatsStyle:

            categ = self.getSubCategoryList()

            for cat in categ:
                cat.setDefaultStyle(type, style, subcatsStyle)

    ##################################
    # Fermi timezone awareness       #
    ##################################
    def getTimezone(self):
        try:
            if self._timezone not in all_timezones:
                self.setTimezone('UTC')
            return self._timezone
        except:
            self.setTimezone('UTC')
            return 'UTC'

    def setTimezone(self, tz):
        self._timezone = tz

    def changeConfTimezones(self, tz):
        for conference in self.getConferenceList():
            conference.moveToTimezone(tz)

    ##################################
    # Fermi timezone awareness(end)  #
    ##################################

    def getOrder(self):
        try:
            return self._order
        except:
            self._order = 0
            return 0

    def setOrder(self, order):
        self._order = order

    def getId(self):
        return self.id

    def setId(self, newId):
        self.id = str(newId.strip())

    def getLocator(self):
        """Gives back (Locator) a globaly unique identification encapsulated
                in a Locator object for the category instance """
        d = Locator()
        d["categId"] = self.getId()
        return d

    def getCategory(self):
        return self

    def getOwner(self):
        return self.owner

    def setOwner(self, newOwner):
        if self.getOwner() is not None and newOwner is not None and self.getOwner() != newOwner:
            self.move(newOwner)
        else:
            self.owner = newOwner

    def getCategoryPath(self):
        if self.isRoot():
            return [self.getId()]
        else:
            l = self.getOwner().getCategoryPath()
            l.append(self.getId())
            return l

    def iterParents(self):
        categ = self
        while not categ.isRoot():
            categ = categ.getOwner()
            yield categ

    def getCategoryPathTitles(self):
        # Breadcrumbs
        breadcrumbs = []
        cat = self
        while cat:
            breadcrumbs.insert(0, cat.getTitle())
            cat = cat.getOwner()
        return breadcrumbs

    def delete(self, deleteConferences=0):
        """removes completely a category (and all its sub-items) from the
            system"""

        oldOwner = self.getOwner()

        if self.isRoot():
            raise MaKaCError(_("Root category cannot be deleted"), _("Category"))
        if not deleteConferences:
            if self.getNumConferences() > 0:
                raise MaKaCError(_("This category still contains some conferences, please remove them first"), _("Category"))
        for subcateg in self.getSubCategoryList():
            subcateg.delete(deleteConferences)
        for conference in self.getConferenceList():
            self.removeConference(conference, delete=True)
        self.getOwner()._removeSubCategory(self)
        CategoryManager().remove(self)
        for prin in self.__ac.getAccessList():
            if isinstance(prin, MaKaC.user.Avatar):
                prin.unlinkTo(self, "access")
        for prin in self.__ac.getModifierList():
            if isinstance(prin, MaKaC.user.Avatar):
                prin.unlinkTo(self, "manager")
        TrashCanManager().add(self)

        self._notify('deleted', oldOwner)

        return

    def move(self, newOwner):
        oldOwner = self.getOwner()
        catDateIdx = indexes.IndexesHolder().getIndex('categoryDate')
        catDateAllIdx = indexes.IndexesHolder().getIndex('categoryDateAll')

        catDateIdx.unindexCateg(self)
        catDateAllIdx.unindexCateg(self)

        self.getOwner()._removeSubCategory(self)
        newOwner._addSubCategory(self)
        self._reindex()
        catDateIdx.indexCateg(self)
        catDateAllIdx.indexCateg(self)

        self._notify('moved', oldOwner, newOwner)

    def getName(self):
        return self.name

    def setName(self, newName):
        oldName = self.name
        self.name = newName.strip()

        # Reindex when name changes
        nameIdx = indexes.IndexesHolder().getIndex('categoryName')
        nameIdx.unindex(self.getId())
        nameIdx.index(self.getId(), self.getTitle().decode('utf-8'))

        self._notify('categoryTitleChanged', oldName, newName)

    def getDescription(self):
        return self.description

    def setDescription(self, newDesc):
        self.description = newDesc.strip()

    def moveConference(self, conf, toCateg):
        """
        Moves a conference from this category to another one
        """
        self.removeConference(conf)
        toCateg._addConference(conf)
        conf._notify('moved', self, toCateg)

    def _addSubCategory(self, newSc):
        #categories can only contain either conferences either other categories
        #   but can never contain both. For the moment an exception is raised
        #   but this could be replaced by the following policy: if a
        #   sub-category is to be added to a category already containing
        #   conferences then the conferes are moved into the new sub-category
        #   and it is added to target category.
        #first, check that the category is registered if not raise an exception
        if len(self.conferences) > 0:
            for conf in self.getConferenceList():
                self.moveConference(conf, newSc)

        if len(self.conferences) > 0:
            raise MaKaCError(_("Cannot add subcategory: the current category already contains events"), _("Category"))
        newSc.setOwner(self)
        self.subcategories[newSc.getId()] = newSc
        self._incNumConfs(newSc.getNumConferences())

    def _removeSubCategory(self, sc):
        """if the given subcategory belongs to the current category it removes
            it from the subcategories list (don't use this method, use delete
            instead)
        """
        if sc in self.getSubCategoryList():
            self._decNumConfs(sc.getNumConferences())
            del self.subcategories[sc.getId()]
            sc.setOwner(None)

    def newSubCategory(self, protection):
        cm = CategoryManager()
        sc = Category()
        cm.add(sc)

        # set the protection
        sc.setProtection(protection)

        Catalog.getIdx('categ_conf_sd').add_category(sc.getId())
        sc._notify('created', self)

        self._addSubCategory(sc)
        sc.setOrder(self.getSubCategoryList()[-1].getOrder() + 1)

        return sc

    def _incNumConfs(self, num=1):
        """Increases the number of conferences for the current category in a given number.
            WARNING: Only Categories must use this method!!!"""
        self._numConferences = self.getNumConferences()
        self._numConferences += num
        if self.getOwner() is not None:
            self.getOwner()._incNumConfs(num)

    def _decNumConfs(self, num=1):
        """Decreases the number of conferences for the current category in a given number.
            WARNING: Only Categories must use this method!!!"""
        self._numConferences = self.getNumConferences()
        self._numConferences -= num
        if self.getOwner() is not None:
            self.getOwner()._decNumConfs(num)

    def _addConference(self, newConf):
        if len(self.subcategories) > 0:
            raise MaKaCError(_("Cannot add event: the current category already contains some sub-categories"), _("Category"))
        if newConf.getId() == "":
            raise MaKaCError(_("Cannot add to a category an event which is not registered"), _("Category"))
        self.conferences.insert(newConf)
        newConf.addOwner(self)
        self._incNumConfs(1)
        self.indexConf(newConf)

    def getAccessKey(self):
        return ""

    def getModifKey(self):
        return ""

    def indexConf(self, conf):
        # Specific for category changes, calls Conference.indexConf()
        # (date-related indexes)
        catIdx = indexes.IndexesHolder().getIndex('category')
        catIdx.indexConf(conf)
        conf.indexConf()

    def unindexConf(self, conf):
        catIdx = indexes.IndexesHolder().getIndex('category')
        catIdx.unindexConf(conf)
        conf.unindexConf()

    def newConference(self, creator, id="", creationDate=None, modificationDate=None):
        conf = Conference(creator, id, creationDate, modificationDate)
        ConferenceHolder().add(conf)
        self._addConference(conf)
        conf.linkCreator()

        conf._notify('created', self)

        return conf

    def removeConference(self, conf, notify=True, delete=False):
        if not (conf in self.conferences):
            return

        self.unindexConf(conf)

        self.conferences.remove(conf)
        if delete:
            conf.delete()
        conf.removeOwner(self, notify)
        self._decNumConfs(1)

    def getSubCategoryList(self):
        subcategs = self.subcategories.values()
        cl = []
        for categ in subcategs:
            cl.append("%04s%s-%s" % (categ.getOrder(), categ.getName().replace("-", ""), categ.getId()))
        cl.sort()
        res = []
        for c in cl:
            id = c.split("-")[1]
            res.append(self.subcategories[id])
        return res

    def iteritems(self, *args):
        return self.conferences.iteritems(*args)

    def itervalues(self, *args):
        return self.conferences.itervalues(*args)

    def getConferenceList(self, sortType=1):
        """returns the list of conferences included in the current category.
           Thanks to the used structure the list is sorted by date.
           We can choose other sorting types:

            sortType=1--> By date
            sortType=2--> Alphabetically
            sortType=3--> Alphabetically - Reversed
        """

        res = sorted(self.conferences, cmp=Conference._cmpByDate)

        if sortType == 2:
            res.sort(Conference._cmpTitle)
        elif sortType == 3:
            res.sort(Conference._cmpTitle)
            res = reversed(res)
        return res

    def iterConferences(self):
        """returns the iterator for conferences.
        """
        return self.conferences

    def iterAllConferences(self):
        """returns the iterator for conferences in all subcategories.
        """
        for conf in self.conferences:
            yield conf

        for subcateg in self.subcategories.itervalues():
            for conf in subcateg.iterAllConferences():
                yield conf

    def getAllConferenceList(self):
        """returns the list of all conferences included in the current category
        and in all its subcategories"""
        res = self.getConferenceList()
        subcategs = self.getSubCategoryList()
        if subcategs != []:
            for subcateg in subcategs:
                res.extend(subcateg.getAllConferenceList())
        return res

    def getRelativeEvent(self, which, conf=None):
        index = Catalog.getIdx('categ_conf_sd').getCategory(self.getId())
        if which == 'first':
            return list(index[index.minKey()])[0]
        elif which == 'last':
            return list(index[index.maxKey()])[-1]
        elif which in ('next', 'prev'):
            categIter = index.itervalues()
            if conf:
                prev = None
                for c in categIter:
                    if c == conf:
                        break
                    prev = c
                nextEvt = next(categIter, None)
                if which == 'next':
                    return nextEvt
                else:
                    return prev
            else:
                raise AttributeError("'conf' parameter missing")
        else:
            raise AttributeError("Unknown argument value: '%s'" % which)

    def _setNumConferences(self):
        self._numConferences = 0
        if self.conferences:
            self._incNumConfs(len(self.conferences))
        else:
            for sc in self.getSubCategoryList():
                self._incNumConfs(sc.getNumConferences())

    def getNumConferences(self):
        """returns the total number of conferences contained in the current
            category and all its sub-categories (if any)"""
        #this new approach will speed up considerably the counting of category
        #   conferences. However, it will give non accurate results for
        #   conferences within many categories (a conference will be counted
        #   twice in parent categories).
        #   Besides this approach will generate much more conflict errors. This
        #   can be reduced by simply isolating the counter in a separate object.
        try:
            if self._numConferences:
                pass
        except AttributeError:
            self._setNumConferences()
        return self._numConferences

    def _getRepository(self):
        dbRoot = DBMgr.getInstance().getDBConnection().root()
        try:
            fr = dbRoot["local_repositories"]["main"]
        except KeyError, e:
            fr = fileRepository.MaterialLocalRepository()
            dbRoot["local_repositories"] = OOBTree()
            dbRoot["local_repositories"]["main"] = fr
        return fr

    def removeResource(self, res):
        pass

    def setIcon(self, iconFile):
        iconFile.setOwner(self)
        iconFile.setId("icon")
        iconFile.archive(self._getRepository())
        iconFile.setProtection(-1)
        if self.getIcon() is not None:
            self._icon.delete()
        self._icon = iconFile
        self.notifyModification()

    def getIcon(self):
        try:
            if self._icon:
                pass
        except AttributeError, e:
            self._icon = None
        return self._icon

    def getIconURL(self):
        if self.getIcon() is None:
            return ""
        return self._icon.getURL()

    def removeIcon(self):
        if self.getIcon() is None:
            return
        self._icon.delete()
        self._icon = None
        self.notifyModification()

    def recoverIcon(self, icon):
        icon.setOwner(self)
        if self.getIcon() is not None:
            self._icon.delete()
        self._icon = icon
        icon.recover()
        self.notifyModification()

    def getManagerList(self):
        return self.__ac.getModifierList()

    def grantModification(self, prin):
        self.__ac.grantModification(prin)
        if isinstance(prin, MaKaC.user.Avatar):
            prin.linkTo(self, "manager")

    def revokeModification(self, prin):
        self.__ac.revokeModification(prin)
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "manager")

    def canModify(self, aw):
        return self.canUserModify(aw.getUser())

    def canUserModify(self, av):
        inherited = 0
        if self.getOwner() is not None:
            inherited = self.getOwner().canUserModify(av)
        return inherited or self.__ac.canModify(av)

    def getAllowedToAccessList(self):
        return self.__ac.getAccessList()

    def canKeyAccess(self, aw):
        # Categories don't allow access keys
        return False

    def canIPAccess(self, ip):
        if not self.__ac.canIPAccess(ip):
            return False

        # if category is inheriting, check protection above
        if self.getAccessProtectionLevel() == 0 and self.getOwner():
            return self.getOwner().canIPAccess(ip)
        return True

    def isProtected(self):
        return self.__ac.isProtected()

    def getAccessProtectionLevel(self):
        return self.__ac.getAccessProtectionLevel()

    def isItselfProtected(self):
        return self.__ac.isItselfProtected()

    def hasAnyProtection(self):
        if self.__ac.isProtected() or len(self.getDomainList()) > 0:
            return True
        if self.getAccessProtectionLevel() == -1:  # PUBLIC
            return False
        if self.getOwner() is not None:
            return self.getOwner().hasAnyProtection()
        return False

    def setProtection(self, private):
        """
        Allows to change the category's access protection
        """

        oldProtection = 1 if self.isProtected() else -1

        self.__ac.setProtection(private)
        self._notify('protectionChanged', oldProtection, private)

    def hasProtectedOwner(self):
        return self.__ac._getFatherProtection()

    def isAllowedToAccess(self, av):
        """Says whether an avatar can access a category independently of it is
            or not protected or domain filtered
        """
        if self.__ac.canUserAccess(av) or self.canUserModify(av):
            return True
        if not self.isItselfProtected() and self.getOwner():
            return self.getOwner().isAllowedToAccess(av)

    def canView(self, aw):
        if self.canAccess(aw):
            return True
        for conf in self.getConferenceList():
            if conf.canView(aw):
                return True
        for subcateg in self.getSubCategoryList():
            if subcateg.canView(aw):
                return True
        return False

    def canAccess(self, aw):
        if not self.hasAnyProtection():
            return True
        if not self.isProtected():
            # domain checking only triggered if the category is PUBLIC
            return self.canIPAccess(aw.getIP()) or \
                self.isAllowedToCreateConference(aw.getUser()) or \
                self.isAllowedToAccess(aw.getUser())
        return self.isAllowedToCreateConference(aw.getUser()) or \
            self.isAllowedToAccess(aw.getUser())

    def grantAccess(self, prin):
        self.__ac.grantAccess(prin)
        if isinstance(prin, MaKaC.user.Avatar):
            prin.linkTo(self, "access")

    def revokeAccess(self, prin):
        self.__ac.revokeAccess(prin)
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "access")

    def isConferenceCreationRestricted(self):
        return self.__confCreationRestricted

    def restrictConferenceCreation(self):
        self.__confCreationRestricted = 1

    def allowConferenceCreation(self):
        self.__confCreationRestricted = 0

    def grantConferenceCreation(self, prin):
        if prin not in self.__confCreators:
            self.__confCreators.append(prin)
            if isinstance(prin, MaKaC.user.Avatar):
                prin.linkTo(self, "creator")
            self._p_changed = 1

    def revokeConferenceCreation(self, prin):
        if prin in self.__confCreators:
            self.__confCreators.remove(prin)
            if isinstance(prin, MaKaC.user.Avatar):
                prin.unlinkTo(self, "creator")
            self._p_changed = 1

    def getConferenceCreatorList(self):
        return self.__confCreators

    def isAllowedToCreateConference(self, av):

        if self.canUserModify(av):
            return 1

        # Avatar is directly in the list
        if av in self.__confCreators:
            return 1

        # Otherwise, if  it is a member of one of the groups in the list...
        for group in self.__confCreators:
            if isinstance(group, MaKaC.user.Group):
                if group.containsUser(av):
                    return 1
            else:
                pass
        return 0

    def canCreateConference(self, av):
        if not self.isConferenceCreationRestricted():
            return 1
        return self.isAllowedToCreateConference(av)

    def requireDomain(self, dom):
        self.__ac.requireDomain(dom)
        self._notify('accessDomainAdded', dom)

    def freeDomain(self, dom):
        self.__ac.freeDomain(dom)
        self._notify('accessDomainRemoved', dom)

    def getDomainList(self):
        return self.__ac.getRequiredDomainList()

    def getStatistics(self):
        try:
            if self._statistics:
                pass
        except AttributeError, e:
            self._statistics = {}
        return self._statistics

    def notifyModification(self, raiseEvent=True):
        """Method called to notify the current category has been modified.
        """
        if raiseEvent:
            self._notify('infoChanged')
        self._p_changed = 1


class CustomLocation(Persistent):

    def __init__(self, **locationData):
        self.name = ""
        self.address = ""
        self.room = ""

    def setValues(self, data):
        self.setName(data.get("name", ""))
        self.setAddress(data.get("address", ""))
        self.setRoom(data.get("room", ""))

    def getValues(self):
        d = {}
        d["name"] = self.getName()
        d["address"] = self.getAddress()
        d["room"] = self.getRoom()
        return d

    def clone(self):
        newCL = CustomLocation()
        newCL.setValues(self.getValues())
        return newCL

    def setName(self, newName):
        self.name = newName

    def getName(self):
        return self.name

    def setAddress(self, newAddress):
        self.address = newAddress

    def getAddress(self):
        return self.address

    def setRoom(self, newRoom):
        self.room = newRoom

    def getRoom(self):
        return self.room


class CustomRoom(Persistent):

    def __init__(self):
        self.name = ""

    def setValues(self, data):
        self.setName(data.get("name", ""))
        self.setFullName(data.get("fullName"))

    def getValues(self):
        d = {}
        d["name"] = self.getName()
        d["fullName"] = self.getFullName()
        return d

    def getId(self):
        return "Custom"

    def clone(self):
        newCR = CustomRoom()
        newCR.setValues(self.getValues())
        return newCR

    def setName(self, newName):
        self.name = newName.strip()

    def getName(self):
        return self.name

    def retrieveFullName(self, location):
        if not location:
            return
        room = CrossLocationQueries.getRooms(roomName=self.name, location=location)
        self.fullName = room.getFullName() if room else None

    def setFullName(self, newFullName):
        self.fullName = newFullName

    def getFullName(self):
        if not hasattr(self, 'fullName'):
            self.fullName = None
        return self.fullName


class ConferenceParticipation(Persistent, Fossilizable, Observable):

    fossilizes(IConferenceParticipationFossil, IConferenceParticipationMinimalFossil)

    def __init__(self):
        self._firstName=""
        self._surName=""
        self._email=""
        self._affiliation=""
        self._address=""
        self._phone=""
        self._title=""
        self._fax=""

    def _notifyModification( self ):
        pass

    def setValues(self, data):
        self.setFirstName(data.get("firstName", ""))
        self.setFamilyName(data.get("familyName",""))
        self.setAffiliation(data.get("affilation",""))
        self.setAddress(data.get("address",""))
        self.setEmail(data.get("email",""))
        self.setFax(data.get("fax",""))
        self.setTitle(data.get("title",""))
        self.setPhone(data.get("phone",""))
        self._notifyModification()

    def getValues(self):
        data={}
        data["firstName"]=self.getFirstName()
        data["familyName"]=self.getFamilyName()
        data["affilation"]=self.getAffiliation()
        data["address"]=self.getAddress()
        data["email"]=self.getEmail()
        data["fax"]=self.getFax()
        data["title"]=self.getTitle()
        data["phone"]=self.getPhone()
        return data

    def setId(self, newId):
        self._id = newId

    def getId( self ):
        return self._id

    def setDataFromAvatar(self,av):
    # av is an Avatar object.
        if av is None:
            return
        self.setFirstName(av.getName())
        self.setFamilyName(av.getSurName())
        self.setEmail(av.getEmail())
        self.setAffiliation(av.getOrganisation())
        self.setAddress(av.getAddress())
        self.setPhone(av.getTelephone())
        self.setTitle(av.getTitle())
        self.setFax(av.getFax())
        self._notifyModification()

    def setDataFromOtherCP(self,cp):
    # cp is a ConferenceParticipation object.
        if cp is None:
            return
        self.setFirstName(cp.getFirstName())
        self.setFamilyName(cp.getFamilyName())
        self.setEmail(cp.getEmail())
        self.setAffiliation(cp.getAffiliation())
        self.setAddress(cp.getAddress())
        self.setPhone(cp.getPhone())
        self.setTitle(cp.getTitle())
        self.setFax(cp.getFax())
        self._notifyModification()

    def delete( self ):
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    @Updates (['MaKaC.conference.ConferenceParticipation',
                 'MaKaC.conference.SessionChair',
                 'MaKaC.conference.SlotChair'], 'firstName')
    def setFirstName(self,newName):
        tmp=newName.strip()
        if tmp==self._firstName:
            return
        self._firstName=tmp
        self._notifyModification()

    def getFirstName( self ):
        return self._firstName

    @Updates (['MaKaC.conference.ConferenceParticipation',
                 'MaKaC.conference.SessionChair',
                 'MaKaC.conference.SlotChair'], 'familyName')
    def setFamilyName(self,newName):
        tmp=newName.strip()
        if tmp==self._surName:
            return
        self._surName=tmp
        self._notifyModification()

    def getFamilyName( self ):
        return self._surName

    @Updates (['MaKaC.conference.ConferenceParticipation',
                 'MaKaC.conference.SessionChair',
                 'MaKaC.conference.SlotChair'], 'email')
    def setEmail(self,newMail):
        tmp=newMail.strip()
        if tmp==self._email:
            return
        self._email=newMail.strip()
        self._notifyModification()

    def getEmail( self ):
        return self._email

    @Updates (['MaKaC.conference.ConferenceParticipation',
                 'MaKaC.conference.SessionChair',
                 'MaKaC.conference.SlotChair'], 'affiliation')
    def setAffiliation(self,newAffil):
        self._affiliation=newAffil.strip()
        self._notifyModification()

    def getAffiliation(self):
        return self._affiliation

    @Updates (['MaKaC.conference.ConferenceParticipation',
                 'MaKaC.conference.SessionChair',
                 'MaKaC.conference.SlotChair'], 'address')
    def setAddress(self,newAddr):
        self._address=newAddr.strip()
        self._notifyModification()

    def getAddress(self):
        return self._address

    @Updates (['MaKaC.conference.ConferenceParticipation',
                 'MaKaC.conference.SessionChair',
                 'MaKaC.conference.SlotChair'], 'phone')
    def setPhone(self,newPhone):
        self._phone=newPhone.strip()
        self._notifyModification()

    def getPhone(self):
        return self._phone

    @Updates (['MaKaC.conference.ConferenceParticipation',
                 'MaKaC.conference.SessionChair',
                 'MaKaC.conference.SlotChair'], 'title')
    def setTitle(self,newTitle):
        self._title=newTitle.strip()
        self._notifyModification()

    def getTitle(self):
        return self._title

    @Updates (['MaKaC.conference.ConferenceParticipation',
                 'MaKaC.conference.SessionChair',
                 'MaKaC.conference.SlotChair'], 'fax')
    def setFax(self,newFax):
        self._fax=newFax.strip()
        self._notifyModification()

    def getFax(self):
        return self._fax

    def getFullName( self ):
        res = self.getFamilyName()
        if self.getFirstName() != "":
            if res.strip() != "":
                res = "%s, %s"%( res, self.getFirstName() )
            else:
                res = self.getFirstName()
        if self.getTitle() != "":
            res = "%s %s"%( self.getTitle(), res )
        return res

    def getFullNameNoTitle( self ):
        res = self.getFamilyName()
        if self.getFirstName() != "":
            if res.strip() != "":
                res = "%s, %s"%( res, self.getFirstName() )
            else:
                res = self.getFirstName()
        return res

    def getDirectFullName( self ):
        res = "%s %s"%( self.getFirstName(), self.getFamilyName() )
        res=res.strip()
        if self.getTitle() != "":
            res = "%s %s"%( self.getTitle(), res )
        return res

    def getAbrName(self):
        res = self.getFamilyName()
        if self.getFirstName():
            if res:
                res = "%s, " % res
            res = "%s%s." % (res, safe_upper(safe_slice(self.getFirstName(), 0, 1)))
        return res

    @staticmethod
    def _cmpFamilyName( cp1, cp2 ):
        o1 = "%s %s"%(cp1.getFamilyName(), cp1.getFirstName())
        o2 = "%s %s"%(cp2.getFamilyName(), cp2.getFirstName())
        o1=o1.lower().strip()
        o2=o2.lower().strip()
        return cmp( o1, o2 )


class ConferenceChair(ConferenceParticipation, Fossilizable):

    fossilizes(IConferenceParticipationFossil)

    def __init__(self):
        self._conf=None
        self._id=""
        ConferenceParticipation.__init__(self)

    def _notifyModification( self ):
        if self._conf != None:
            self._conf.notifyModification()

    def clone(self):
        newCC=ConferenceChair()
        newCC.setValues(self.getValues())
        return newCC

    def getConference(self):
        return self._conf

    def getId(self):
        return self._id

    def includeInConference(self,conf,id):
        if self.getConference()==conf and self.getId()==id.strip():
            return
        self._conf=conf
        self._id=id

    def delete( self ):
        self._conf=None
        ConferenceParticipation.delete(self)

    def getLocator(self):
        if self.getConference() is None:
            return None
        loc=self.getConference().getLocator()
        loc["chairId"]=self.getId()
        return loc

class SubmitterIndex(Persistent):
    """Index for contribution submitters.

        This class allows to index users with submission privileges over the
        conference contributions so the owner can answer optimally to the query
        if a user has any submission privilege over any contribution
        of the conference.
        It is implemented by simply using a BTree where the Avatar id is used
        as key (because it is unique and non variable) and a list of
        contributions over which he has submission privileges is kept as values.
        It is the responsability of the index owner (conference contributions)
        to keep it up-to-date i.e. notify conference sumitters additions and
        removals.
    """

    def __init__( self ):
        self._idx = OOBTree()
        self._idxEmail = OOBTree()

    def _getIdxEmail(self):
        try:
            return self._idxEmail
        except:
            self._idxEmail = OOBTree()
        return self._idxEmail

    def getContributions(self,av):
        """Gives a list with the contributions over which a user has
            coordination privileges
        """
        if av == None:
            return []
        ret = self._idx.get(av.getId(),[])
        if not ret:
            self._moveEmailtoId(av)
            ret = self._idx.get(av.getId(),[])
        return ret

    def index(self,av,contrib):
        """Registers in the index a submitter of a contribution.
        """
        if av==None or contrib==None:
            return
        if not self._idx.has_key(av.getId()):
            l=[]
            self._idx[av.getId()]=l
        else:
            l=self._idx[av.getId()]
        if contrib not in l:
            l.append(contrib)
            self._idx[av.getId()]=l

    def indexEmail(self, email, contrib):
        if not email or not contrib:
            return
        if not self._getIdxEmail().has_key(email):
            l = [contrib]
            self._getIdxEmail()[email] = l
        else:
            l = self._getIdxEmail()[email]
            if not contrib in l:
                l.append(contrib)
                self._getIdxEmail()[email] = l


    def unindex(self,av,contrib):
        if av==None or contrib==None:
            return
        l=self._idx.get(av.getId(),[])
        if contrib in l:
            l.remove(contrib)
            self._idx[av.getId()]=l

    def unindexEmail(self, email, contrib):
        if not email or not contrib:
            return
        if self._getIdxEmail().has_key(email):
            l = self._getIdxEmail()[email]
            if contrib in l:
                l.remove(contrib)
            if l == []:
                del self._getIdxEmail()[email]
            else:
                self._getIdxEmail()[email] = l

    def _moveEmailtoId(self, av):
        id = av.getId()
        email = av.getEmail()
        if not self._idx.has_key(id):
            if self._getIdxEmail().has_key(email):
                self._idx[id] = self._getIdxEmail()[email]
                del self._getIdxEmail()[email]


class ReportNumberHolder(Persistent):

    def __init__(self, owner):
        self._owner=owner
        self._reports={}

    def getOwner(self):
        return self._owner

    def addReportNumber(self, system, number):
        if system in self.getReportNumberKeys() or system in Config.getInstance().getReportNumberSystems().keys():
            try:
                if not number in self._reports[system]:
                    self._reports[system].append(number)
            except:
                self._reports[system]=[ number ]
            self.notifyModification()

    def removeReportNumber(self, system, number):
        if self.hasReportNumbersBySystem(system):
            if number in self._reports[system]:
                self._reports[system].remove(number)
                self.notifyModification()

    def removeReportNumberById(self, id):
        try:
            rn = self.listReportNumbers()[int(id)]
            self.removeReportNumber(rn[0], rn[1])
        except:
            pass

    def hasReportNumbersBySystem(self, system):
        return self._reports.has_key(system)

    def getReportNumbersBySystem(self, system):
        if self.hasReportNumbersBySystem(system):
            return self._reports[system]
        return None

    def getReportNumberKeys(self):
        return self._reports.keys()

    def listReportNumbersOnKey(self, key):
        reports=[]
        if key in self._reports.keys():
            # compatibility with previous versions
            if type(self._reports[key]) is str:
                self._reports[key] = [ self._reports[key] ]
            for number in self._reports[key]:
                reports.append([key, number])
        return reports

    def hasReportNumberOnSystem(self, system, number):
        if self.hasReportNumbersBySystem(system):
            if number in self._reports[system]:
                return True
        return False

    def listReportNumbers(self):
        reports=[]
        keys = self._reports.keys()
        keys.sort()
        for key in keys:
            # compatibility with previous versions
            if type(self._reports[key]) is str:
                self._reports[key] = [ self._reports[key] ]
            for number in self._reports[key]:
                reports.append([key, number])
        return reports

    def clone(self, owner):
        newR=ReportNumberHolder(owner)
        for key in self._reports.keys():
            for number in self._reports[key]:
                newR.addReportNumber(key, number)
        return newR

    def notifyModification(self):
        self._p_changed=1
        if self.getOwner() != None:
            self.getOwner().notifyModification()


class Conference(CommonObjectBase, Locatable):
    """This class represents the real world conferences themselves. Objects of
        this class will contain basic data about the confence and will provide
        access to other objects representing certain parts of the conferences
        (ex: contributions, sessions, ...).
    """

    fossilizes(IConferenceFossil, IConferenceMinimalFossil, IConferenceEventInfoFossil)

    def __init__(self, creator, id="", creationDate = None, modificationDate = None):
        """Class constructor. Initialise the class attributes to the default
            values.
           Params:
            confData -- (Dict) Contains the data the conference object has to
                be initialised to.
        """
        #IndexedObject.__init__(self)
        if creator == None:
            raise MaKaCError( _("A creator must be specified when creating a new Event"), _("Event"))
        self.__creator = creator
        self.id = id
        self.title = ""
        self.description = ""
        self.places = []
        self.rooms = []
        ###################################
        # Fermi timezone awareness        #
        ###################################
        self.startDate = nowutc()
        self.endDate = nowutc()
        self.timezone = ""
        ###################################
        # Fermi timezone awareness(end)   #
        ###################################
        self._screenStartDate = None
        self._screenEndDate = None
        self.contactInfo =""
        self.chairmanText = ""
        self.chairmans = []
        self._chairGen=Counter()
        self._chairs=[]
        self.sessions = {}
        self.__sessionGenerator = Counter() # Provides session unique
                                            #   identifiers for this conference
        self.contributions = {}
        self.__contribGenerator = Counter() # Provides contribution unique
                                            #   identifiers for this conference
        self.programDescription = ""
        self.program = []
        self.__programGenerator = Counter() # Provides track unique
                                            #   identifiers for this conference
        self.__ac = AccessController(self)
        self.materials = {}
        self.__materialGenerator = Counter() # Provides material unique
                                            # identifiers for this conference
        self.paper = None
        self.slides = None
        self.video = None
        self.poster = None
        self.minutes=None
        self.__schedule=None
        self.__owners = []
        if creationDate:
            self._creationDS = creationDate
        else:
            self._creationDS = nowutc() #creation timestamp
        if modificationDate:
            self._modificationDS = modificationDate
        else:
            self._modificationDS = nowutc() #modification timestamp

        self.alarmList = {}
        self.__alarmCounter = Counter()

        self.abstractMgr = review.AbstractMgr(self)
        self._logo = None
        self._trackCoordinators = TCIndex() #index for the track coordinators
        self._supportInfo = SupportInfo(self, "Support")
        self._contribTypes = {}
        self.___contribTypeGenerator = Counter()
        self._authorIdx=AuthorIndex()
        self._speakerIdx=AuthorIndex()
        self._primAuthIdx=_PrimAuthIdx(self)
        self._sessionCoordinators=SCIndex()
        self._sessionCoordinatorRights = []
        self._submitterIdx=SubmitterIndex()
        self._boa=BOAConfig(self)
        self._registrationForm = registration.RegistrationForm(self)
        self._evaluationCounter = Counter()
        self._evaluations = [Evaluation(self)]
        self._registrants = {} #key=registrantId; value=Registrant
        self._bookings = {}
        self._registrantGenerator = Counter()
        self._accessKey=""
        self._modifKey=""
        self._closed = False
        self._visibility = 999
        self._pendingQueuesMgr=pendingQueues.ConfPendingQueuesMgr(self)
        self._sections = []
        self._participation = Participation(self)
        self._logHandler = LogHandler()
        self._reportNumberHolder=ReportNumberHolder(self)
        self._enableSessionSlots = False
        self._enableSessions = False
        self._autoSolveConflict = True
        self.__badgeTemplateManager = BadgeTemplateManager(self)
        self.__posterTemplateManager = PosterTemplateManager(self)
        self._keywords = ""
        self._confPaperReview = ConferencePaperReview(self)
        self._confAbstractReview = ConferenceAbstractReview(self)
        self._orgText = ""
        self._comments = ""
        self._sortUrlTag = ""

        self._observers = []

    def __repr__(self):
        return '<Conference({0}, {1}, {2})'.format(self.getId(), self.getTitle(), self.getStartDate())

    def __str__(self):
        return "<Conference %s@%s>" % (self.getId(), hex(id(self)))

    @staticmethod
    def _cmpByDate(self, toCmp):
        res = cmp(self.getStartDate(), toCmp.getStartDate())
        if res != 0:
            return res
        else:
            return cmp(self, toCmp)

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

    def cleanCache( self ):
        if not ContextManager.get('clean%s'%self.getUniqueId(), False):
            ScheduleToJson.cleanConferenceCache(self)
            ContextManager.set('clean%s'%self.getUniqueId(), True)

    def updateNonInheritingChildren(self, elem, delete=False):
        self.getAccessController().updateNonInheritingChildren(elem, delete)

    def getKeywords(self):
        try:
            return self._keywords
        except:
            self._keywords = ""
            return ""

    def setKeywords(self, keywords):
        self._keywords = keywords

    # Room booking related ===================================================

    def getRoomBookingList( self ):
        """
        Returns list of bookings for this conference.
        """
        from MaKaC.plugins.RoomBooking.default.dalManager import DALManager

        if not DALManager.isConnected():
            return []

        resvs = []
        for resvGuid in self.getRoomBookingGuids():
            r = resvGuid.getReservation()
            if r == None:
                self.removeRoomBookingGuid( resvGuid )
            elif r.isValid:
                resvs.append( r )
        return resvs

    def getBookedRooms( self ):
        """
        Returns list of rooms booked for this conference.
        Returns [] if room booking module is off.
        """
        rooms = []

        for r in self.getRoomBookingList():
            if not r.room in rooms:
                rooms.append( r.room )
        return rooms

    def getRoomBookingGuids( self ):
        try:
            self.__roomBookingGuids
        except AttributeError:
            self.__roomBookingGuids = []
        return self.__roomBookingGuids

    def setRoomBookingGuids( self, guids ):
        self.__roomBookingGuids = guids

    def addRoomBookingGuid( self, guid ):
        self.getRoomBookingGuids().append( guid )
        self._p_changed = True

    def removeRoomBookingGuid( self, guid ):
        self.getRoomBookingGuids().remove( guid )
        self._p_changed = True

    def __TMP_PopulateRoomBookings( self ):
        # TEMPORARY GENERATION OF RESERVATIONS FOR CONFERENCE
        from MaKaC.rb_reservation import ReservationBase
        from MaKaC.rb_location import ReservationGUID, Location
        resvs = []
        resvs.append( ReservationBase.getReservations( resvID = 395887 ) )
        resvs.append( ReservationBase.getReservations( resvID = 381406 ) )
        resvs.append( ReservationBase.getReservations( resvID = 387688 ) )
        resvs.append( ReservationBase.getReservations( resvID = 383459 ) )

        resvGuids = []
        for resv in resvs:
            resvGuids.append( ReservationGUID( Location.getDefaultLocation(), resv.id ) )

        self.__roomBookingGuids = resvGuids


    # ========================================================================

    def getParticipation(self):
        try :
            if self._participation :
                pass
        except AttributeError :
            self._participation = Participation(self)
        return self._participation

    def getType( self ):
        import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
        wr = webFactoryRegistry.WebFactoryRegistry()
        wf = wr.getFactory(self)
        if wf != None:
            type = wf.getId()
        else:
            type = "conference"
        return type

    def getVerboseType( self ):
        # Like getType, but returns "Lecture" instead of "simple_type"
        type = self.getType()
        if type == "simple_event":
            type = "lecture"
        return type.capitalize()


    def getLogHandler(self):
        try :
            if self._logHandler:
                pass
        except AttributeError :
            self._logHandler = LogHandler()
        return self._logHandler


    def getEnableSessionSlots(self):
        #try :
        #    if self._enableSessionSlots  :
        #        pass
        #except AttributeError :
        #    self._enableSessionSlots = True
        #if self.getType() == "conference":
        #    return True
        #return self._enableSessionSlots
        return True

    def getEnableSessions(self):
        try :
            if self._enableSessions  :
                pass
        except AttributeError :
            self._enableSessions = True
        if self.getType() == "conference":
            return True
        return self._enableSessions

    def enableSessionSlots(self):
        self._enableSessionSlots = True

    def disableSessionSlots(self):
        self._enableSessionSlots = False

    def enableSessions(self):
        self._enableSessions = True

    def disableSessions(self):
        self._enableSessions = False

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
        if confData.get("locationName", "").strip() == "":
            self.setLocation(None)
        else:
            #if the location name is defined we must set a new location (or
            #   modify the existing one) for the conference
            loc = self.getLocation()
            if not loc:
                loc = CustomLocation()
            self.setLocation(loc)
            loc.setName(confData["locationName"])
            loc.setAddress(confData.get("locationAddress", ""))
        #same as for the location
        if confData.get("roomName", "").strip() == "":
                self.setRoom(None)
        else:
            room = self.getRoom()
            if not room:
                room = CustomRoom()
            self.setRoom(room)
            room.setName(confData["roomName"])
        self.notifyModification()

    def getVisibility ( self ):
        try:
            return int(self._visibility)
        except:
            self._visibility = 999
            return 999

    def getFullVisibility( self ):
        return max(0,min(self.getVisibility(), self.getOwnerList()[0].getVisibility()))

    def setVisibility( self, visibility=999 ):
        self._visibility = int(visibility)
        catIdx = indexes.IndexesHolder().getIndex('category')
        catIdx.reindexConf(self)
        catDateIdx = indexes.IndexesHolder().getIndex('categoryDate')
        catDateAllIdx = indexes.IndexesHolder().getIndex('categoryDateAll')
        catDateIdx.reindexConf(self)
        catDateAllIdx.reindexConf(self)

    def isClosed( self ):
        try:
            return self._closed
        except:
            self._closed = False
            return False

    def setClosed( self, closed=True ):
        self._closed = closed

    def indexConf( self ):
        # called when event dates change
        # see also Category.indexConf()

        calIdx = indexes.IndexesHolder().getIndex('calendar')
        calIdx.indexConf(self)
        catDateIdx = indexes.IndexesHolder().getIndex('categoryDate')
        catDateAllIdx = indexes.IndexesHolder().getIndex('categoryDateAll')
        catDateIdx.indexConf(self)
        catDateAllIdx.indexConf(self)
        nameIdx = indexes.IndexesHolder().getIndex('conferenceTitle')
        nameIdx.index(self.getId(), self.getTitle().decode('utf-8'))

        Catalog.getIdx('categ_conf_sd').index_obj(self)

    def unindexConf( self ):
        calIdx = indexes.IndexesHolder().getIndex('calendar')
        calIdx.unindexConf(self)
        catDateIdx = indexes.IndexesHolder().getIndex('categoryDate')
        catDateAllIdx = indexes.IndexesHolder().getIndex('categoryDateAll')
        catDateIdx.unindexConf(self)
        catDateAllIdx.unindexConf(self)
        nameIdx = indexes.IndexesHolder().getIndex('conferenceTitle')
        nameIdx.unindex(self.getId())

        Catalog.getIdx('categ_conf_sd').unindex_obj(self)

    def __generateNewContribTypeId( self ):
        """Returns a new unique identifier for the current conference sessions
        """
        try:
            return str(self.___contribTypeGenerator.newCount())
        except:
            self.___contribTypeGenerator = Counter()
            return str(self.___contribTypeGenerator.newCount())

    def addContribType(self, ct):
        try:
            if self._contribTypes:
                pass
        except:
            self._contribTypes = {}
        if ct in self._contribTypes.values():
            return
        id = ct.getId()
        if id == "":
            id = self.__generateNewContribTypeId()
            ct.setId(id)
        self._contribTypes[id] = ct
        self.notifyModification()

    def newContribType(self, name, description):
        ct = ContributionType(name, description, self)
        self.addContribType(ct)
        return ct

    def getContribTypeList(self):
        try:
            return self._contribTypes.values()
        except:
            self._contribTypes = {}
            self.notifyModification()
            return self._contribTypes.values()

    def getContribTypeById(self, id):
        try:
            if self._contribTypes:
                pass
        except:
            self._contribTypes = {}
            self.notifyModification()
        if id in self._contribTypes.keys():
            return self._contribTypes[id]
        return None

    def removeContribType(self, ct):
        try:
            if self._contribTypes:
                pass
        except:
            self._contribTypes = {}
        if not ct in self._contribTypes.values():
            return
        del self._contribTypes[ct.getId()]
        for cont in self.getContributionList():
            if cont.getType() == ct:
                cont.setType(None)
        ct.delete()
        self.notifyModification()

    def recoverContribType(self, ct):
        ct.setConference(self)
        self.addContribType(ct)
        ct.recover()

    def _getRepository( self ):
        dbRoot = DBMgr.getInstance().getDBConnection().root()
        try:
            fr = dbRoot["local_repositories"]["main"]
        except KeyError, e:
            fr = fileRepository.MaterialLocalRepository()
            dbRoot["local_repositories"] = OOBTree()
            dbRoot["local_repositories"]["main"] = fr
        return fr

    def removeResource( self, res ):
        pass

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

    def getLogoURL( self ):
        try:
            if self._logo == None:
                return ""
            return self._logo.getURL()
        except AttributeError:
            self._logo = None
            return ""

    def removeLogo(self):
        if self._logo is None:
            return
        self._logo.delete()
        self._logo = None
        self.notifyModification()

    def recoverLogo(self, logo):
        logo.setOwner(self)
        if self._logo != None:
            self._logo.delete()
        self._logo = logo
        logo.recover()
        self.notifyModification()

    def getSession(self):
        return None

    def getContribution(self):
        return None

    def getSubContribution(self):
        return None

    def getAbstractMgr(self):
        return self.abstractMgr

    def notifyModification( self, date = None, raiseEvent = True):
        """Method called to notify the current conference has been modified.
        """
        self.setModificationDate()

        if raiseEvent:
            self._notify('infoChanged')

        self.cleanCache()
        self._p_changed=1

    def getModificationDate( self ):
        """Returns the date in which the conference was last modified"""
        return self._modificationDS

    def getAdjustedModificationDate( self, tz ):
        """Returns the date in which the conference was last modified"""
        return self._modificationDS.astimezone(timezone(tz))

    def getCreationDate( self ):
        """Returns the date in which the conference was created"""
        return self._creationDS

    def getAdjustedCreationDate( self, tz ):
        """Returns the date in which the conference was created"""
        return self._creationDS.astimezone(timezone(tz))

    def getCreator( self ):
        return self.__creator

    def setCreator( self, creator):
        if self.__creator:
            self.__creator.unlinkTo(self, "creator")
        creator.linkTo(self, "creator")
        self.__creator = creator

    def linkCreator(self):
        self.__creator.linkTo(self, "creator")

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
        if self.getOwnerList() == []:
            return None
        return self.getOwnerList()[0]

    def getOwnerList( self ):
        return self.__owners

    def getOwnerPath( self ):
        l=[]
        owner = self.getOwnerList()[0]
        while owner != None and owner.getId() != "0":
            l.append(owner)
            owner = owner.getOwner()
        return l

    def getOwnerById( self, key ):
        """Returns one specific category which contains the conference.
           Params:
             - key: The "id" of the category.
        """
        for owner in self.__owners:
            if key == owner.getId():
                return owner
        return None

    def addOwner( self, newOwner ):
        if newOwner == None:
            return
        self.__owners.append( newOwner )
        self.notifyModification()

    def removeOwner( self, owner, notify=True ):
        if not (owner in self.__owners):
            return
        self.__owners.remove( owner )
        owner.removeConference( self )
        if notify:
            self.notifyModification()

    def getCategoriesPath(self):
        return [self.getOwnerList()[0].getCategoryPath()]

    def notifyContributions(self):

        for c in self.getContributionList():
            # take care of subcontributions
            for sc in c.getSubContributionList():
                sc._notify('deleted', c)

            c._notify('deleted', self)

    def delete( self ):
        """deletes the conference from the system.
        """
        #we notify the observers that the conference has been deleted
        try:
            self._notify('deleted', self.getOwner())
        except Exception, e:
            try:
                Logger.get('Conference').error("Exception while notifying the observer of a conference deletion for conference %s: %s" %
                            (self.getId(), str(e)))
            except Exception, e2:
                Logger.get('Conference').error("Exception while notifying a conference deletion: %s (origin: %s)" % (str(e2), str(e)))

        self.notifyContributions()

        #will have to remove it from all the owners (categories) and the
        #   conference registry
        ConferenceHolder().remove( self )
        for owner in self.__owners:
            owner.removeConference( self, notify=False )

        self.removeAllEvaluations()

        for alarm in self.getAlarmList():
            if not alarm.getEndedOn():
                self.removeAlarm(alarm)

        #Delete the RoomBooking associated reservations
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        if minfo.getRoomBookingModuleActive() and CrossLocationDB.isConnected():
            for resv in self.getRoomBookingList():
                resv.remove()

        #For each conference we have a list of managers. If we delete the conference but we don't delete
        #the link in every manager to the conference then, when the manager goes to his "My profile" he
        #will see a link to a conference that doesn't exist. Therefore, we need to delete that link as well
        for manager in self.getManagerList():
            if isinstance(manager, MaKaC.user.Avatar):
                manager.unlinkTo(self, "manager")

        creator = self.getCreator()
        creator.unlinkTo(self, "creator")

        # Remove all links in redis
        if redis_write_client:
            avatar_links.delete_event(self)

        # Remote short URL mappings
        sum = ShortURLMapper()
        sum.remove(self)

        TrashCanManager().add(self)

    def getConference( self ):
        return self

    def getObservers(self):
        if not hasattr(self, "_observers"):
            self._observers = []
        return self._observers

    def setDates( self, sDate, eDate=None, check=1, moveEntries=0):
        """
        Set the start/end date for a conference
        """

        oldStartDate = self.getStartDate()
        oldEndDate = self.getEndDate()

        # do some checks first
        if sDate > eDate:
            # obvious case
            raise MaKaCError( _("Start date cannot be after the end date"), _("Event"))

        elif sDate == oldStartDate and eDate == oldEndDate:
            # if there's nothing to do (yet another obvious case)
            return

        # if we reached this point, it means either the start or
        # the end date (or both) changed
        # If only the end date was changed, moveEntries = 0
        if sDate == oldStartDate:
            moveEntries = 0

        # Pre-check for moveEntries
        if moveEntries == 1:
            # in case the entries are to be simply shifted
            # we should make sure the interval is big enough
            # just store the old values for later

            oldInterval = oldEndDate - oldStartDate
            newInterval = eDate - sDate

            entries = self.getSchedule().getEntries()
            if oldInterval > newInterval and entries:
                eventInterval = entries[-1].getEndDate() - entries[0].getStartDate()
                diff = entries[0].getStartDate() - oldStartDate
                if sDate + diff + eventInterval > eDate:
                    raise TimingError(
                        _("The start/end dates were not changed since the selected "
                          "timespan is not large enough to accomodate the contained "
                          "timetable entries and spacings."),
                        explanation=_("You should try using a larger timespan."))

        # so, we really need to try changing something

        self.unindexConf()

        # set the dates
        self.setStartDate(sDate, check=0, moveEntries = moveEntries, index=False, notifyObservers = False)
        self.setEndDate(eDate, check=0, index=False, notifyObservers = False)

        # sanity check
        self._checkInnerSchedule()

        # reindex the conference
        self.indexConf()

        # notify observers
        try:
            self._notify('dateChanged', {'oldStartDate': oldStartDate, 'newStartDate': self.getStartDate(), 'oldEndDate': oldEndDate, 'newEndDate': self.getEndDate()})
        except Exception, e:
            try:
                Logger.get('Conference').error("Exception while notifying the observer of a start and end date change from %s - %s to %s - %s for conference %s: %s" %
                            (formatDateTime(oldStartDate), formatDateTime(oldEndDate),
                            formatDateTime(self.getStartDate()), formatDateTime(self.getEndDate()), self.getId(), str(e)))
            except Exception, e2:
                Logger.get('Conference').error("Exception while notifying a start and end date change: %s (origin: %s)" % (str(e2), str(e)))


    def _checkInnerSchedule( self ):
        self.getSchedule().checkSanity()

    def setStartDate(self, sDate, check = 1, moveEntries = 0, index = True, notifyObservers = True):
        """ Changes the current conference starting date/time to the one specified by the parameters.
        """
        if not sDate.tzname():
            raise MaKaCError("date should be timezone aware")
        if sDate == self.getStartDate():
            return
        ###################################
        # Fermi timezone awareness        #
        ###################################
        if not indexes.BTREE_MIN_UTC_DATE <= sDate <= indexes.BTREE_MAX_UTC_DATE:
            raise FormValuesError(_("The start date must be between {} and {}.").format(
                format_datetime(indexes.BTREE_MIN_UTC_DATE),
                format_datetime(indexes.BTREE_MAX_UTC_DATE)))
        ###################################
        # Fermi timezone awareness        #
        ###################################
        if check != 0:
            self.verifyStartDate(sDate)
        oldSdate = self.getStartDate()
        diff = sDate - oldSdate

        if index:
            self.unindexConf()
        self.startDate  = sDate
        if moveEntries and diff is not None:
            # If the start date changed, we move entries inside the timetable
            self.getSchedule()._startDate=None
            self.getSchedule()._endDate=None
            #if oldSdate.date() != sDate.date():
            #    entries = self.getSchedule().getEntries()[:]
            #else:
            #    entries = self.getSchedule().getEntriesOnDay(sDate.astimezone(timezone(self.getTimezone())))[:]
            entries = self.getSchedule().getEntries()[:]
            self.getSchedule().moveEntriesBelow(diff, entries)
        #datetime object is non-mutable so we must "force" the modification
        #   otherwise ZODB won't be able to notice the change
        self.notifyModification()
        if index:
            self.indexConf()

        # update the time for the alarms to be sent
        self._updateAlarms()

        # Update redis link timestamp
        if redis_write_client:
            avatar_links.update_event_time(self)

        #if everything went well, we notify the observers that the start date has changed
        if notifyObservers:
            try:
                self._notify('startDateChanged', {'newDate': sDate, 'oldDate': oldSdate})
            except Exception, e:
                try:
                    Logger.get('Conference').error("Exception while notifying the observer of a start date change from %s to %s for conference %s: %s" %
                    (formatDateTime(oldSdate), formatDateTime(sDate), self.getId(), str(e)))
                except Exception, e2:
                    Logger.get('Conference').error("Exception while notifying a start date change: %s (origin: %s)" % (str(e2), str(e)))


    def _updateAlarms(self):
        c = Client()
        # are there any alarms? if so, update the relative ones
        for alarm in self.getAlarmList():
            tbef = alarm.getTimeBefore()
            if tbef:
                # only relative alarms
                c.moveTask(alarm, self.getStartDate() - tbef)

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

        #if everything went well, we notify the observers that the start date has changed
        if notifyObservers:
            try:
                self._notify('startTimeChanged', sdate)
            #for observer in self.getObservers():
                    #observer.notifyEventDateChanges(sdate, self.startDate, None, None)
            except Exception, e:
                try:
                    Logger.get('Conference').error("Exception while notifying the observer of a start date change from %s to %s for conference %s: %s"%
                                                    (formatDateTime(sdate), formatDateTime(self.startDate), self.getId(), str(e)))
                except Exception, e2:
                    Logger.get('Conference').error("Exception while notifying a start time change: %s (origin: %s)"%(str(e2), str(e)))

    def getStartDate(self):
        """returns (datetime) the starting date of the conference"""
        return self.startDate

    def getUnixStartDate(self):
        return datetimeToUnixTimeInt(self.startDate)

    ###################################
    # Fermi timezone awareness        #
    ###################################

    def getAdjustedStartDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        return self.getStartDate().astimezone(timezone(tz))

    ###################################
    # Fermi timezone awareness(end)   #
    ###################################

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

    def calculateDayStartTime(self, day):
        """returns (date) the start date of the conference on a given day
        day is a tz aware datetime"""
        if self.getStartDate().astimezone(day.tzinfo).date() == day.date():
            return self.getStartDate().astimezone(day.tzinfo)
        return self.getSchedule().calculateDayStartDate(day)

    def verifyEndDate(self, edate):
        if edate<self.getStartDate():
            raise TimingError( _("End date cannot be before the start date"), _("Event"))
        if self.getSchedule().hasEntriesAfter(edate):
            raise TimingError(_("Cannot change end date to %s: some entries in the timetable would be outside this date (%s)") % (edate,self.getSchedule().getEntries()[-1].getStartDate()), _("Event"))

    def setEndDate(self, eDate, check = 1, index = True, notifyObservers = True):
        """ Changes the current conference end date/time to the one specified by the parameters.
        """
        if not eDate.tzname():
            raise MaKaCError("date should be timezone aware")
        if eDate == self.getEndDate():
            return
        if not indexes.BTREE_MIN_UTC_DATE <= eDate <= indexes.BTREE_MAX_UTC_DATE:
            raise FormValuesError(_("The end date must be between {} and {}.").format(
                format_datetime(indexes.BTREE_MIN_UTC_DATE),
                format_datetime(indexes.BTREE_MAX_UTC_DATE)))
        if check != 0:
            self.verifyEndDate(eDate)
        if index:
            self.unindexConf()

        oldEdate = self.endDate
        self.endDate  = eDate
        #datetime object is non-mutable so we must "force" the modification
        #   otherwise ZODB won't be able to notice the change
        self.notifyModification()
        if index:
            self.indexConf()

        #if everything went well, we notify the observers that the start date has changed
        if notifyObservers:
            try:
                self._notify('endDateChanged', {'newDate': eDate, 'oldDate': oldEdate})
            except Exception, e:
                try:
                    Logger.get('Conference').error("Exception while notifying the observer of a end date change from %s to %s for conference %s: " %
                              (formatDateTime(oldEdate), formatDateTime(eDate), self.getId(), str(e)))
                except Exception, e2:
                    Logger.get('Conference').error("Exception while notifying a end date change: %s (origin: %s)" % (str(e2), str(e)))


    def setEndTime(self, hours = 0, minutes = 0, notifyObservers = True):
        """ Changes the current conference end time (not date) to the one specified by the parameters.
        """
        edate = self.getEndDate()
        self.endDate = datetime( edate.year, edate.month, edate.day, int(hours), int(minutes) )
        self.verifyEndDate(self.endDate)
        self.notifyModification()

        #if everything went well, we notify the observers that the start date has changed
        if notifyObservers:
            try:
                self._notify('endTimeChanged', edate)
            #for observer in self.getObservers():
            except Exception, e:
                #observer.notifyEventDateChanges(None, None, edate, self.endDate)
                try:
                    Logger.get('Conference').error("Exception while notifying the observer of a end timet change from %s to %s for conference %s: %s" %
                                                    (formatDateTime(edate), formatDateTime(self.endDate), self.getId(), str(e)))
                except Exception, e2:
                    Logger.get('Conference').error("Exception while notifying a end time change: %s (origin: %s)"%(str(e2), str(e)))

    def getEndDate(self):
        """returns (datetime) the ending date of the conference"""
        return self.endDate

    ##################################
    # Fermi timezone awareness       #
    ##################################

    def getAdjustedEndDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        return self.getEndDate().astimezone(timezone(tz))

    ##################################
    # Fermi timezone awareness(end)  #
    ##################################

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

    def isEndDateAutoCal( self ):
        """Says whether the end date has been explicitely set for the session
            or it must be calculated automatically
        """
        return self._endDateAutoCal

    ####################################
    # Fermi timezone awareness         #
    ####################################
    def setTimezone(self, tz):
        try:
            oldTimezone = self.timezone
        except AttributeError:
            oldTimezone = tz
        self.timezone = tz
        #for observer in self.getObservers():
        try:
            #observer.notifyTimezoneChange(oldTimezone, tz)
            self._notify('timezoneChanged', oldTimezone)
        except Exception, e:
            try:
                Logger.get('Conference').error("Exception while notifying the observer of a timezone change from %s to %s for conference %s: %s" %
                                                (str(oldTimezone), str(tz), self.getId(), str(e)))
            except Exception, e2:
                Logger.get('Conference').error("Exception while notifying a timezone change: %s (origin: %s)"%(str(e2), str(e)))

    def getTimezone(self):
        try:
            return self.timezone
        except:
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



    ####################################
    # Fermi timezone awareness(end)    #
    ####################################

    def getTitle(self):
        """returns (String) the title of the conference"""
        return self.title

    def setTitle(self, title):
        """changes the current title of the conference to the one specified"""
        oldTitle = self.title

        self.title = title
        self.notifyModification()

        nameIdx = indexes.IndexesHolder().getIndex('conferenceTitle')
        nameIdx.unindex(self.getId())
        nameIdx.index(self.getId(), self.getTitle().decode('utf-8'))

        #we notify the observers that the conference's title has changed
        try:
            self._notify('eventTitleChanged', oldTitle, title)
        except Exception, e:
            Logger.get('Conference').exception("Exception while notifying the observer of a conference title change for conference %s: %s" %
                                               (self.getId(), str(e)))


    def getDescription(self):
        """returns (String) the description of the conference"""
        return self.description

    def setDescription(self, desc):
        """changes the current description of the conference"""
        oldDescription = self.description
        self.description = desc
        self._notify('eventDescriptionChanged', oldDescription, desc)
        self.notifyModification()

    def getSupportInfo(self):
        if not hasattr(self, "_supportInfo"):
            self._supportInfo = SupportInfo(self, "Support")
        return self._supportInfo

    def setSupportInfo(self, supportInfo):
        self._supportInfo = supportInfo

    def getChairmanText( self ):
        try:
            if self.chairmanText:
                pass
        except AttributeError, e:
            self.chairmanText = ""
        return self.chairmanText

    def setChairmanText( self, newText ):
        self.chairmanText = newText.strip()

    def appendChairmanText( self, newText ):
        self.setChairmanText( "%s, %s"%(self.getChairmanText(), newText.strip()) )
        self._chairGen=Counter()
        self._chairs=[]

    def _resetChairs(self):
        try:
            if self._chairs:
                return
        except AttributeError:
            self._chairs=[]
            for oc in self.chairmans:
                newChair=ConferenceChair()
                newChair.setDataFromAvatar(oc)
                self._addChair(newChair)

    def getChairList(self):
        """Method returning a list of the conference chairmans (Avatars)
        """
        self._resetChairs()
        return self._chairs

    def _addChair(self,newChair):
        for chair in self._chairs:
            if newChair.getEmail() != "" and newChair.getEmail() == chair.getEmail():
                return
        try:
            if self._chairGen:
                pass
        except AttributeError:
            self._chairGen=Counter()
        id = newChair.getId()
        if id == "":
            id=int(self._chairGen.newCount())
        if isinstance(newChair,ConferenceChair):
            newChair.includeInConference(self,id)
        self._chairs.append(newChair)
        if isinstance(newChair, MaKaC.user.Avatar):
            newChair.linkTo(self, "chair")
        self.notifyModification()

    def addChair(self,newChair):
        """includes the specified user in the list of conference
            chairs"""
        self._resetChairs()
        self._addChair(newChair)

    def removeChair(self,chair):
        """removes the specified user from the list of conference
            chairs"""
        self._resetChairs()
        if chair not in self._chairs:
            return
        self._chairs.remove(chair)
        if isinstance(chair, MaKaC.user.Avatar):
            chair.unlinkTo(self, "chair")
        chair.delete()
        self.notifyModification()

    def recoverChair(self, ch):
        self.addChair(ch)
        ch.recover()

    def getChairById(self,id):
        id=int(id)
        for chair in self._chairs:
            if chair.getId()==id:
                return chair
        return None

    def getAllSessionsConvenerList(self) :
        dictionary = {}
        for session in self.getSessionList() :
            for convener in session.getConvenerList() :
                key = convener.getEmail()+" "+convener.getFirstName().lower()+" "+convener.getFamilyName().lower()
                dictionary.setdefault(key, set()).add(convener)
            for slot in session.getSlotList():
                for convener in slot.getConvenerList() :
                    key = convener.getEmail()+" "+convener.getFirstName().lower()+" "+convener.getFamilyName().lower()
                    dictionary.setdefault(key, set()).add(convener)

        return dictionary

    def getContactInfo(self):
        return self.contactInfo

    def setContactInfo(self, contactInfo):
        self.contactInfo = contactInfo
        self.notifyModification()

    def getLocationParent( self ):
        """
        Returns the object from which the room/location
        information should be inherited.
        For Conferences, it's None, since they can't inherit
        from anywhere else.
        """
        return None

    def getLocation( self ):
        return self.getOwnLocation()

    def getAddress( self ):
        if self.getOwnLocation():
            return self.getOwnLocation().getAddress()
        else:
            return None

    def getRoom( self ):
        return self.getOwnRoom()

    def getLocationList(self):
        """Method returning a list of "location" objects which contain the
            information about the different places the conference is gonna
            happen
        """
        return self.places

    def getFavoriteRooms(self):
        roomList = []
        roomList.extend(self.getRoomList())
        #roomList.extend(map(lambda x: x._getName(), self.getBookedRooms()))

        return roomList

    def addLocation(self, newPlace):
        self.places.append( newPlace )
        self.notifyModification()

    def setAccessKey(self, accessKey=""):
        """sets the access key of the conference"""
        self._accessKey = accessKey
        self.notifyModification()

    def getAccessKey(self):
        try:
            return self._accessKey
        except AttributeError:
            self._accessKey = ""
            return self._accessKey

    def setModifKey(self, modifKey=""):
        """sets the modification key of the conference"""
        self._modifKey = modifKey
        self.notifyModification()

    def getModifKey(self):
        try:
            return self._modifKey
        except AttributeError:
            self._modifKey = ""
            return self._modifKey

    def __generateNewSessionId( self ):
        """Returns a new unique identifier for the current conference sessions
        """
        return str(self.__sessionGenerator.newCount())

    def addSession(self,newSession, check = 2, id = None):
        """Adds a new session object to the conference taking care of assigning
            a new unique id to it
        """
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""

        if self.hasSession(newSession):
            return
        if self.getSchedule().isOutside(newSession):
            if check == 1:
                 MaKaCError( _("Cannot add this session  (Start:%s - End:%s) Outside of the event's time table(Start:%s - End:%s)") % (newSession.getStartDate(),newSession.getEndDate(),self.getSchedule().getStartDate(), self.getSchedule().getEndDate()),"Event")
            elif check == 2:
              if self.getSchedule().getStartDate() > newSession.getStartDate():
                 self.setStartDate(newSession.getStartDate())
              if self.getSchedule().getEndDate() < newSession.getEndDate():
                 self.setEndDate(newSession.getEndDate())
        if id!=None:
            sessionId = id
        else:
            sessionId=self.__generateNewSessionId()
        self.sessions[sessionId]=newSession
        newSession.includeInConference(self,sessionId)
        #keep the session coordinator index updated
        for sc in newSession.getCoordinatorList():
            self.addSessionCoordinator(newSession,sc)
        self.notifyModification()

    def hasSession(self,session):
        if session != None and session.getConference()==self and \
                self.sessions.has_key(session.getId()):
            return True
        return False

    def removeSession(self,session, deleteContributions=False):
        if self.hasSession(session):
            for sc in session.getCoordinatorList():
                self.removeSessionCoordinator(session,sc)

            if deleteContributions:
                for contrib in session.getContributionList():
                    contrib.delete()

            del self.sessions[session.getId()]

            session.delete()
            self.notifyModification()

    def recoverSession(self, session, check, isCancelled):
        self.addSession(session, check, session.getId())
        session.recover(isCancelled)

    def getSessionById( self, sessionId ):
        """Returns the session from the conference list corresponding to the
            unique session id specified
        """
        return self.sessions.get(sessionId,None)

    def getRoomList(self):
        roomList =[]
        for session in self.sessions.values():
            if session.getRoom()!=None:
                roomname = session.getRoom().getName()
                if roomname not in roomList:
                    roomList.append(roomname)
        return roomList

    def getSessionList( self ):
        """Retruns a list of the conference session objects
        """
        return self.sessions.values()

    def getSessionListSorted( self ):
        """Retruns a sorted list of the conference sessions
        """
        res=[]
        for entry in self.getSchedule().getEntries():
            if isinstance(entry,LinkedTimeSchEntry) and \
                                isinstance(entry.getOwner(),SessionSlot):
                session=entry.getOwner().getSession()
                if session not in res:
                    res.append(session)
        return res

    def getSessionSlotList(self):
        return [slot for session in self.sessions.values() for slot in session.getSlotList()]

    def getNumberOfSessions(self):
        return len(self.sessions)

    def _generateNewContributionId(self):
        """Returns a new unique identifier for the current conference
            contributions
        """
        return str(self.__contribGenerator.newCount())

    def genNewAbstractId(self):
        return str(self.__contribGenerator.newCount())

    def syncContribCounter(self):
        self.__contribGenerator.sync(self.getAbstractMgr()._getOldAbstractCounter())
        return self.__contribGenerator._getCount()

    def addContribution(self,newContrib,id=""):
        """Adds a new contribution object to the conference taking care of
            assigning a new unique id to it
        """
        if self.hasContribution(newContrib):
            return
        if isinstance(newContrib.getCurrentStatus(),ContribStatusWithdrawn):
            raise MaKaCError( _("Cannot add a contribution which has been withdrawn"), _("Event"))
        if id is None or id=="":
            contribId=self._generateNewContributionId()
            while self.contributions.has_key(contribId):
                contribId=self._generateNewContributionId()
        else:
            contribId=str(id)
            if self.contributions.has_key(contribId):
                raise MaKaCError( _("Cannot add this contribution id:(%s) as it has already been used")%contribId, _("Event"))
        newContrib.includeInConference(self,contribId)
        self.contributions[contribId]=newContrib
        for auth in newContrib.getAuthorList():
            self.indexAuthor(auth)
        for spk in newContrib.getSpeakerList():
            self.indexSpeaker(spk)
        for sub in newContrib.getSubmitterList():
            self.addContribSubmitter(newContrib,sub)

        newContrib._notify('created', self)
        self.notifyModification()

    def hasContribution(self,contrib):
        return contrib.getConference()==self and \
                self.contributions.has_key(contrib.getId())

    def removeContribution( self, contrib, callDelete=True ):
        if not self.contributions.has_key( contrib.getId() ):
            return
        for sub in contrib.getSubmitterList()[:]:
            self.removeContribSubmitter(contrib,sub)
        for auth in contrib.getPrimaryAuthorList()[:]:
            contrib.removePrimaryAuthor(auth)
        for auth in contrib.getCoAuthorList()[:]:
            contrib.removeCoAuthor(auth)
        for spk in contrib.getSpeakerList()[:]:
            contrib.removeSpeaker(spk)
        del self.contributions[ contrib.getId() ]
        if callDelete:
            contrib.delete()
        #else:
        #    contrib.unindex()
        self.notifyModification()

    def recoverContribution(self, contrib):
        self.addContribution(contrib, contrib.getId())
        contrib.recover()

    # Note: this kind of factories should never be used as they only allow to
    #   create a single type of contributions
    def newContribution( self, id=None ):
        """Creates and returns a new contribution object already added to the
            conference list (all its data is set to the default)
        """
        c = Contribution()
        self.addContribution( c, id )
        return c

    def getOwnContributionById( self, id ):
        """Returns the contribution from the conference list corresponding to
            the unique contribution id specified
        """
        if self.contributions.has_key( id ):
            return self.contributions[ id ]
        return None

    def getContributionById( self, id ):
        """Returns the contribution  corresponding to the id specified
        """
        return self.contributions.get(str(id).strip(),None)

    def getContributionList(self):
        """Returns a list of the conference contribution objects
        """
        return self.contributions.values()

    def iterContributions(self):
        return self.contributions.itervalues()

    def getContributionListWithoutSessions(self):
        """Returns a list of the conference contribution objects which do not have a session
        """
        return [c for c in self.contributions.values() if not c.getSession()]


    def getContributionListSorted(self, includeWithdrawn=True, key="id"):
        """Returns a list of the conference contribution objects, sorted by key provided
        """
        contributions = self.contributions.values()
        if not includeWithdrawn:
            contributions = filter(lambda c: not isinstance(c.getCurrentStatus(), ContribStatusWithdrawn), contributions)
        contributions.sort(key = lambda c: getattr(c, key))
        return contributions

    def getNumberOfContributions(self, only_scheduled=False):
        if only_scheduled:
            return len(filter(lambda c: c.isScheduled(), self.contributions.itervalues()))
        else:
            return len(self.contributions)

    def hasSomethingOnWeekend(self, day):
        """Checks if the event has a session or contribution on the weekend indicated by `day`.

        `day` must be either a saturday or a sunday"""
        if day.weekday() == 5:
            weekend = (day, day + timedelta(days=1))
        elif day.weekday() == 6:
            weekend = (day, day - timedelta(days=1))
        else:
            raise ValueError('day must be on a weekend')
        return (any(c.startDate.date() in weekend and not isinstance(c.getCurrentStatus(), ContribStatusWithdrawn)
                    for c in self.contributions.itervalues() if c.startDate is not None) or
                any(s.startDate.date() in weekend for s in self.sessions.itervalues() if s.startDate is not None))

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
        newPos=self.getTrackPos(track)+1
        self.moveTrack(track,newPos)

    def _cmpTracks( self, t1, t2 ):
        o1 = self.program.index(t1)
        o2 = self.program.index(t2)
        return cmp( o1, o2 )

    def sortTrackList( self, l ):
        """Sorts out a list of tracks according to the current programme order.
        """
        if len(l) == 0:
            return []
        elif len(l) == 1:
            return [l[0]]
        else:
            res = []
            for i in l:
                res.append( i )
            res.sort( self._cmpTracks )
            return res

    def canIPAccess( self, ip ):
        if not self.__ac.canIPAccess( ip ):
            return False

        # if event is inheriting, check IP protection above
        if self.getAccessProtectionLevel() == 0:
            for owner in self.getOwnerList():
                if not owner.canIPAccess(ip):
                    return False

        return True

    def requireDomain( self, dom ):
        self.__ac.requireDomain( dom )
        self._notify('accessDomainAdded', dom)

    def freeDomain( self, dom ):
        self.__ac.freeDomain( dom )
        self._notify('accessDomainRemoved', dom)

    def getDomainList( self ):
        return self.__ac.getRequiredDomainList()

    def isProtected( self ):
        """Tells whether a conference is protected for accessing or not
        """
        return self.__ac.isProtected()

    def getAccessProtectionLevel( self ):
        return self.__ac.getAccessProtectionLevel()

    def isItselfProtected( self ):
        return self.__ac.isItselfProtected()

    def hasAnyProtection( self ):
        """Tells whether a conference has any kind of protection over it:
            access or domain protection.
        """
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
        return self.__ac._getFatherProtection()

    def setProtection( self, private ):
        """
        Allows to change the conference access protection
        """

        oldValue = 1 if self.isProtected() else -1

        self.getAccessController().setProtection( private )

        if oldValue != private:
            # notify listeners
            self._notify('protectionChanged', oldValue, private)

    def grantAccess( self, prin ):
        self.__ac.grantAccess( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.linkTo(self, "access")

    def revokeAccess( self, prin ):
        self.__ac.revokeAccess( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "access")

    def canView( self, aw ):
        """tells whether the specified access wrappers has access to the current
        object or any of its parts"""
        if self.canAccess( aw ):
            return True
        for session in self.getSessionList():
            if session.canView( aw ):
                return True
        for contrib in self.getContributionList():
            if contrib.canView( aw ):
                return True
        return False

    def isAllowedToAccess( self, av):
        """tells if a user has privileges to access the current conference
            (independently that it is protected or not)
        """
        if not av:
            return False
        if (av in self.getChairList()) or (self.__ac.canUserAccess( av )) or (self.canUserModify( av )):
            return True

        # if the conference is not protected by itself
        if not self.isItselfProtected():
            # then inherit behavior from parent category
            for owner in self.getOwnerList():
                if owner.isAllowedToAccess( av ):
                    return True

        # track coordinators are also allowed to access the conference
        for track in self.getTrackList():
            if track.isCoordinator( av ):
                return True

        # paper reviewing team should be also allowed to access
        if self.getConfPaperReview().isInReviewingTeam(av):
            return True

        if any(self._notify("isAllowedToAccess", {"conf": self, "user": av})):
            return True

        return False

    def canAccess( self, aw ):
        """Tells whether an access wrapper is allowed to access the current
            conference: when the conference is protected, only if the user is a
            chair or is granted to access the conference, when the client ip is
            not restricted.
        """

        # Allow harvesters (Invenio, offline cache) to access
        # protected pages
        if self.__ac.isHarvesterIP(aw.getIP()):
            return True

        # Managers have always access
        if self.canModify(aw):
            return True

        if self.isProtected():
            if self.isAllowedToAccess( aw.getUser() ):
                return True
            else:
                return self.canKeyAccess(aw)
        else:
            # Domain control is triggered just for PUBLIC events
            return self.canIPAccess(aw.getIP())

    def canKeyAccess(self, aw, key=None):
        accessKey = self.getAccessKey()
        if not accessKey:
            return False
        return key == accessKey or session.get('accessKeys', {}).get(self.getUniqueId()) == accessKey

    def canKeyModify(self, aw):
        modifKey = self.getModifKey()
        if not modifKey:
            return False
        return session.get('modifKeys', {}).get(self.id) == modifKey

    def grantModification( self, prin, sendEmail=True ):
        email = None
        if isinstance(prin, ConferenceChair):
            email = prin.getEmail()
        elif isinstance(prin, str):
            email = prin
        if email != None:
            if email == "":
                return
            ah = AvatarHolder()
            results=ah.match({"email":email}, exact=1)
            #No registered user in Indico with that email
            if len(results) == 0:
                self.__ac.grantModificationEmail(email)
                self.getConference().getPendingQueuesMgr().addPendingConfManager(prin, False)
                if sendEmail and isinstance(prin, ConferenceChair):
                    notif = pendingQueues._PendingConfManagerNotification( [prin] )
                    mail.GenericMailer.sendAndLog( notif, self.getConference() )
            #The user is registered in Indico and is activated as well
            elif len(results) == 1 and results[0] is not None and results[0].isActivated():
                self.__ac.grantModification(results[0])
                results[0].linkTo(self, "manager")
        else:
            self.__ac.grantModification( prin )
            if isinstance(prin, MaKaC.user.Avatar):
                prin.linkTo(self, "manager")

    def revokeModification( self, prin ):
        self.__ac.revokeModification( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "manager")

    def canUserModify( self, av ):
        if av == None:
            return False
        if ( av == self.getCreator()) or self.getAccessController().canModify( av ):
            return True
        for owner in self.getOwnerList():
            if owner.canUserModify( av ):
                return True
        return False

    def canModify( self, aw ):
        """Tells whether an access wrapper is allowed to modify the current
            conference: only if the user is granted to modify the conference and
            he is accessing from an IP address which is not restricted.
        """
        return self.canUserModify( aw.getUser() )  or self.canKeyModify( aw )

    def getManagerList( self ):
        return self.__ac.getModifierList()

    def addToRegistrars(self, av):
        self.getRegistrarList().append(av)
        self.notifyModification()
        if isinstance(av, MaKaC.user.Avatar):
            av.linkTo(self, "registrar")

    def removeFromRegistrars(self, av):
        self.getRegistrarList().remove(av)
        self.notifyModification()
        if isinstance(av, MaKaC.user.Avatar):
            av.unlinkTo(self, "registrar")

    def isRegistrar(self, av):
        if av == None:
            return False
        try:
            return av in self.getRegistrarList()
        except AttributeError:
            return False

    def getRegistrarList(self):
        try:
            return self.__registrars
        except AttributeError:
            self.__registrars = []
            return self.__registrars

    def canManageRegistration(self, av):
        return self.isRegistrar(av) or self.canUserModify(av)

    def getAllowedToAccessList( self ):
        return self.__ac.getAccessList()

    def addMaterial( self, newMat ):
        newMat.setId( str(self.__materialGenerator.newCount()) )
        newMat.setOwner( self )
        self.materials[ newMat.getId() ] =  newMat
        self.notifyModification()

    def removeMaterial( self, mat ):
        if mat.getId() in self.materials.keys():
            mat.delete()
            self.materials[mat.getId()].setOwner(None)
            del self.materials[ mat.getId() ]
            self.notifyModification()
        elif mat.getId().lower() == 'paper':
            self.removePaper()
            self.notifyModification()
        elif mat.getId().lower() == 'slides':
            self.removeSlides()
            self.notifyModification()
        elif mat.getId().lower() == 'minutes':
            self.removeMinutes()
            self.notifyModification()
        elif mat.getId().lower() == 'video':
            self.removeVideo()
            self.notifyModification()
        elif mat.getId().lower() == 'poster':
            self.removePoster()
            self.notifyModification()

    def recoverMaterial(self, recMat):
    # Id must already be set in recMat.
        recMat.setOwner(self)
        self.materials[recMat.getId()] = recMat
        recMat.recover()
        self.notifyModification()

    def getMaterialRegistry(self):
        """
        Return the correct material registry for this type
        """
        from MaKaC.webinterface.materialFactories import ConfMFRegistry
        return ConfMFRegistry

    def getMaterialById( self, matId ):
        if matId.lower() == 'paper':
            return self.getPaper()
        elif matId.lower() == 'slides':
            return self.getSlides()
        elif matId.lower() == 'video':
            return self.getVideo()
        elif matId.lower() == 'poster':
            return self.getPoster()
        elif matId.lower() == 'minutes':
            return self.getMinutes()
        elif self.materials.has_key(matId):
            return self.materials[ matId ]
        return None

    def getMaterialList( self ):
        return self.materials.values()

    def getAllMaterialList(self, sort=True):
        l = self.getMaterialList()
        if self.getPaper():
            l.append( self.getPaper() )
        if self.getSlides():
            l.append( self.getSlides() )
        if self.getVideo():
            l.append( self.getVideo() )
        if self.getPoster():
            l.append( self.getPoster() )
        if self.getMinutes():
            l.append( self.getMinutes() )
        if sort:
            l.sort(lambda x,y: cmp(x.getTitle(),y.getTitle()))
        return l

    def _getMaterialFiles(self, material):
        """
        Adaption of _getMaterialFiles in WPTPLConferenceDisplay for desired format, objects
        seemed mutually exclusive hence use of similar logic here specific to Conference.
        """
        files = []
        processed = []

        for res in material.getResourceList():
            try:
                ftype = res.getFileType()
                fname = res.getFileName()
                furl = urlHandlers.UHFileAccess.getURL(res)

                if fname in processed:
                    fname = "%s - %s" % (fname, processed.count(fname))

                processed.append(res.getFileName())
            except:
                # If we are here then the resource is a Link object.
                fname, ftype, furl = str(res.getURL()), "link", str(res.getURL())
            fdesc = res.getDescription()
            files.append({'title': fname,
                          'description': fdesc,
                          'type': ftype,
                          'url': furl})
        return files

    def getAllMaterialDict(self, child=None):
        """
        This method iterates through the children of the conference, creating
        a dictionary which maps type to material link URLs.
        """

        child = self if child is None else child

        node = {}
        node['title'] = child.getTitle()

        try:
            node['type'] = child.getType()
        except:
            # If we land here, it's a session which doesn't have 'getType'
            node['type'] = 'session'

        node['children'] = []
        node['material'] = []

        if node['type'] in ['conference', 'meeting']:
            for session in child.getSessionList():
                node['children'].append(self.getAllMaterialDict(session))

            for contrib in child.getContributionList():
                node['children'].append(self.getAllMaterialDict(contrib))

        for material in child.getAllMaterialList():
            files = self._getMaterialFiles(material)

            for f in files:
                materialNode = {}
                materialNode['type'] = 'material'
                materialNode['title'] = material.getTitle()

                if material.getTitle() != 'Minutes':
                    materialNode['title'] += ' - ' + f['title']

                materialNode['materialType'] = f['type']
                materialNode['url'] = str(f['url'])

                node['material'].append(materialNode)

        return node

    def setPaper( self, newPaper ):
        if self.getPaper() != None:
            raise MaKaCError( _("The paper for this conference has already been set"), _("Conference"))
        self.paper=newPaper
        self.paper.setOwner( self )
        self.notifyModification()

    def removePaper( self ):
        if self.paper is None:
            return
        self.paper.delete()
        self.paper.setOwner(None)
        self.paper = None
        self.notifyModification()

    def recoverPaper(self, p):
        self.setPaper(p)
        p.recover()

    def getPaper( self ):
        try:
            if self.paper:
                pass
        except AttributeError:
            self.paper = None
        return self.paper

    def setSlides( self, newSlides ):
        if self.getSlides() != None:
            raise MaKaCError( _("The slides for this conference have already been set"), _("Conference"))
        self.slides=newSlides
        self.slides.setOwner( self )
        self.notifyModification()

    def removeSlides( self ):
        if self.slides is None:
            return
        self.slides.delete()
        self.slides.setOwner( None )
        self.slides= None
        self.notifyModification()

    def recoverSlides(self, s):
        self.setSlides(s)
        s.recover()

    def getSlides( self ):
        try:
            if self.slides:
                pass
        except AttributeError:
            self.slides = None
        return self.slides

    def setVideo( self, newVideo ):
        if self.getVideo() != None:
            raise MaKaCError( _("The video for this conference has already been set"), _("Conference"))
        self.video=newVideo
        self.video.setOwner( self )
        self.notifyModification()

    def removeVideo( self ):
        if self.getVideo() is None:
            return
        self.video.delete()
        self.video.setOwner(None)
        self.video = None
        self.notifyModification()

    def recoverVideo(self, v):
        self.setVideo(v)
        v.recover()

    def getVideo( self ):
        try:
            if self.video:
                pass
        except AttributeError:
            self.video = None
        return self.video

    def setPoster( self, newPoster ):
        if self.getPoster() != None:
            raise MaKaCError( _("the poster for this conference has already been set"), _("Conference"))
        self.poster=newPoster
        self.poster.setOwner( self )
        self.notifyModification()

    def removePoster( self ):
        if self.getPoster() is None:
            return
        self.poster.delete()
        self.poster.setOwner(None)
        self.poster = None
        self.notifyModification()

    def recoverPoster(self, p):
        self.setPoster(p)
        p.recover()

    def getPoster( self ):
        try:
            if self.poster:
                pass
        except AttributeError:
            self.poster = None
        return self.poster

    def setMinutes( self, newMinutes ):
        if self.getMinutes() != None:
            raise MaKaCError( _("The Minutes for this conference has already been set"))
        self.minutes=newMinutes
        self.minutes.setOwner( self )
        self.notifyModification()

    def createMinutes( self ):
        if self.getMinutes() != None:
            raise MaKaCError( _("The minutes for this conference have already been created"), _("Conference"))
        self.minutes = Minutes()
        self.minutes.setOwner( self )
        self.notifyModification()
        return self.minutes

    def removeMinutes( self ):
        if self.getMinutes() is None:
            return
        self.minutes.delete()
        self.minutes.setOwner( None )
        self.minutes = None
        self.notifyModification()

    def recoverMinutes(self, min):
        self.removeMinutes() # To ensure that the current minutes are put in
                             # the trash can.
        self.minutes = min
        self.minutes.setOwner( self )
        min.recover()
        self.notifyModification()
        return self.minutes

    def getMinutes( self ):
        #To be removed
        try:
           if self.minutes:
            pass
        except AttributeError, e:
            self.minutes = None
        return self.minutes

    def _setSchedule( self, sch=None ):
        self.__schedule=ConferenceSchedule(self)
        for session in self.getSessionList():
            for slot in session.getSlotList():
                self.__schedule.addEntry(slot.getConfSchEntry())

    def getSchedule( self ):
        try:
            if not self.__schedule:
                self._setSchedule()
        except AttributeError, e:
            self._setSchedule()
        return self.__schedule

    def fit( self ):
        sch = self.getSchedule()

        sDate = sch.calculateStartDate()
        eDate = sch.calculateEndDate()
        self.setStartDate(sDate)
        self.setEndDate(eDate)

    def fitSlotsOnDay( self, day ):
        for entry in self.getSchedule().getEntriesOnDay(day) :
            if isinstance(entry.getOwner(), SessionSlot) :
                entry.getOwner().fit()

    def getDisplayMgr(self):
        """
        Return the display manager for the conference
        """
        from MaKaC.webinterface import displayMgr
        return displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self)

    def getDefaultStyle( self ):
        return self.getDisplayMgr().getDefaultStyle()

    def clone( self, startDate, options, eventManager=None, userPerformingClone = None ):
        # startDate must be in the timezone of the event (to avoid problems with daylight-saving times)
        cat = self.getOwnerList()[0]
        managing = options.get("managing",None)
        if managing is not None:
            creator = managing
        else:
            creator = self.getCreator()
        conf = cat.newConference(creator)
        if managing is not None :
            conf.grantModification(managing)
        conf.setTitle(self.getTitle())
        conf.setDescription(self.getDescription())
        conf.setTimezone(self.getTimezone())
        for loc in self.getLocationList():
            if loc is not None:
                conf.addLocation(loc.clone())
        if self.getRoom() is not None:
            conf.setRoom(self.getRoom().clone())
        startDate = timezone(self.getTimezone()).localize(startDate).astimezone(timezone('UTC'))
        timeDelta = startDate - self.getStartDate()
        endDate = self.getEndDate() + timeDelta
        conf.setDates( startDate, endDate, moveEntries=1 )
        conf.setContactInfo(self.getContactInfo())
        conf.setChairmanText(self.getChairmanText())
        conf.setVisibility(self.getVisibility())
        conf.setSupportInfo(self.getSupportInfo().clone(self))
        conf.setReportNumberHolder(self.getReportNumberHolder().clone(self))
        for ch in self.getChairList():
            conf.addChair(ch.clone())
        ContextManager.setdefault("clone.unique_id_map", {})[self.getUniqueId()] = conf.getUniqueId()
        # Display Manager
        from MaKaC.webinterface import displayMgr
        selfDispMgr=displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self)
        selfDispMgr.clone(conf)
        # Contribution Types' List (main detailes of the conference)
        for t in self.getContribTypeList() :
            conf.addContribType(t.clone(conf))
        if options.get("sessions", False):
            for entry in self.getSchedule().getEntries():
                if isinstance(entry,BreakTimeSchEntry):
                    conf.getSchedule().addEntry(entry.clone(conf))
        db_root = DBMgr.getInstance().getDBConnection().root()
        if db_root.has_key( "webfactoryregistry" ):
            confRegistry = db_root["webfactoryregistry"]
        else:
            confRegistry = OOBTree.OOBTree()
            db_root["webfactoryregistry"] = confRegistry
        meeting=False
        # if the event is a meeting or a lecture
        if confRegistry.get(str(self.getId()), None) is not None :
            meeting=True
            confRegistry[str(conf.getId())] = confRegistry[str(self.getId())]
        # if it's a conference, no web factory is needed
        # Tracks in a conference
        if options.get("tracks",False) :
            for tr in self.getTrackList() :
                conf.addTrack(tr.clone(conf))
        # Meetings' and conferences' sessions cloning
        if options.get("sessions",False) :
            for s in self.getSessionList() :
                newSes = s.clone(timeDelta, conf, options)
                ContextManager.setdefault("clone.unique_id_map", {})[s.getUniqueId()] = newSes.getUniqueId()
                conf.addSession(newSes)
        # Materials' cloning
        if options.get("materials",False) :
            for m in self.getMaterialList() :
                conf.addMaterial(m.clone(conf))
            if self.getPaper() is not None:
                conf.setPaper(self.getPaper().clone(conf))
            if self.getSlides() is not None:
                conf.setSlides(self.getSlides().clone(conf))
            if self.getVideo() is not None:
                conf.setVideo(self.getVideo().clone(conf))
            if self.getPoster() is not None:
                conf.setPoster(self.getPoster().clone(conf))
            if self.getMinutes() is not None:
                conf.setMinutes(self.getMinutes().clone(conf))
        # access and modification keys
        if options.get("keys", False) :
            conf.setAccessKey(self.getAccessKey())
            conf.setModifKey(self.getModifKey())
        # Access Control cloning
        if options.get("access",False) :
            conf.setProtection(self.getAccessController()._getAccessProtection())
            for mgr in self.getManagerList() :
                conf.grantModification(mgr)
            for user in self.getAllowedToAccessList() :
                conf.grantAccess(user)
            for right in self.getSessionCoordinatorRights():
                conf.addSessionCoordinatorRight(right)
            for domain in self.getDomainList():
                conf.requireDomain(domain)
        # conference's registration form
        if options.get("registration",False) :
            conf.setRegistrationForm(self.getRegistrationForm().clone(conf))

        # conference's evaluation
        if options.get("evaluation",False) :
            #Modify this, if you have now many evaluations.
            #You will have to clone every evaluations of this conference.
            conf.setEvaluations([self.getEvaluation().clone(conf)])

        #conference's abstracts
        if options.get("abstracts",False) :
            conf.abstractMgr = self.abstractMgr.clone(conf)
        # conference's alerts
        if options.get("alerts",False) :
            for alarm in self.getAlarmList() :
                # Indico does not clone absoulte alarms
                if alarm._relative is not None:
                    # .clone takes care of enqueuing it
                    alarm.clone(conf)
        # Meetings' and conferences' contributions cloning
        if options.get("contributions",False) :
            sch = conf.getSchedule()
            for cont in self.getContributionList():
                if cont.getSession() is None :
                    if not meeting:
                        nc = cont.clone(conf, options, timeDelta)
                        conf.addContribution(nc)
                        if cont.isScheduled() :
                            sch.addEntry(nc.getSchEntry())
                        ContextManager.setdefault("clone.unique_id_map", {})[cont.getUniqueId()] = nc.getUniqueId()
                    elif cont.isScheduled():
                        # meetings...only scheduled
                        nc = cont.clone(conf, options, timeDelta)
                        conf.addContribution(nc)
                        sch.addEntry(nc.getSchEntry())
                        ContextManager.setdefault("clone.unique_id_map", {})[cont.getUniqueId()] = nc.getUniqueId()
        # Participants' module settings and list cloning
        if options.get("participants",False) :
            self.getParticipation().clone(conf, options, eventManager)
        conf.notifyModification()

        #we inform the plugins in case they want to add anything to the new conference
        self._notify('cloneEvent', {'conf': conf, 'user': userPerformingClone, 'options': options})
        return conf

    def newAlarm(self, when, enqueue=True):

        if type(when) == timedelta:
            relative = when
            dtStart = None
        else:
            relative = None
            dtStart = when

        confRelId = self._getNextAlarmId()
        al = tasks.AlarmTask(self, confRelId,
                             startDateTime=dtStart,
                             relative=relative)

        self.addAlarm(al, enqueue)
        return al

    def removeAlarm(self, alarm):
        confRelId = alarm.getConfRelativeId()

        if confRelId in self.alarmList:
            del self.alarmList[confRelId]
            self._p_changed = 1

            tl = Client()
            tl.dequeue(alarm)
        else:
            raise Exception("alarm not in list!")

    def _getNextAlarmId(self):
        return self.__alarmCounter.newCount()

    def addAlarm(self, alarm, enqueue = True):
        if enqueue:
            tl = Client()
            tl.enqueue(alarm)

        self.alarmList[alarm.getConfRelativeId()] = alarm
        self._p_changed = 1

    def recoverAlarm(self, alarm):
        self.addAlarm(alarm)
        alarm.conf = self
        alarm.recover()

    def getAlarmList(self):
        return self.alarmList.values()

    def getAlarmById(self, id):
        """For given id returns corresponding Alarm or None if not found."""
        return self.alarmList.get(id, None)

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

    def _rebuildAuthorIndex(self):
        self._authorIdx=AuthorIndex()
        for contrib in self.getContributionList():
            if not isinstance(contrib.getCurrentStatus(),ContribStatusWithdrawn):
                for auth in contrib.getAuthorList():
                    self._authorIdx.index(auth)

    def getAuthorIndex(self):
        try:
            if self._authorIdx:
                pass
        except AttributeError:
            self._rebuildAuthorIndex()
        return self._authorIdx

    def indexAuthor(self,auth):
        c=auth.getContribution()
        if c.isAuthor(auth):
            if not isinstance(c.getCurrentStatus(),ContribStatusWithdrawn):
                self.getAuthorIndex().index(auth)
                if c.isPrimaryAuthor(auth):
                    self._getPrimAuthIndex().index(auth)

    def unindexAuthor(self,auth):
        c=auth.getContribution()
        if c.isAuthor(auth):
            self.getAuthorIndex().unindex(auth)
            if c.isPrimaryAuthor(auth):
                self._getPrimAuthIndex().unindex(auth)

    def _rebuildSpeakerIndex(self):
        self._speakerIdx=AuthorIndex()
        for contrib in self.getContributionList():
            if not isinstance(contrib.getCurrentStatus(),ContribStatusWithdrawn):
                for auth in contrib.getSpeakerList():
                    self._speakerIdx.index(auth)
                for subcontrib in contrib.getSubContributionList():
                    for auth in subcontrib.getSpeakerList():
                        self._speakerIdx.index(auth)

    def getSpeakerIndex(self):
        try:
            if self._speakerIdx:
                pass
        except AttributeError:
            self._rebuildSpeakerIndex()
        return self._speakerIdx

    def indexSpeaker(self,auth):
        c=auth.getContribution()
        if not isinstance(c.getCurrentStatus(),ContribStatusWithdrawn):
            self.getSpeakerIndex().index(auth)

    def unindexSpeaker(self,auth):
        c=auth.getContribution()
        if c and not isinstance(c.getCurrentStatus(),ContribStatusWithdrawn):
            self.getSpeakerIndex().unindex(auth)

    def getRegistrationForm(self):
        try:
            if self._registrationForm is None:
                self._registrationForm = registration.RegistrationForm(self)
        except AttributeError,e:
            self._registrationForm = registration.RegistrationForm(self)
        return self._registrationForm

    def setRegistrationForm(self,rf):
        self._registrationForm = rf
        rf.setConference(self)

    def removeRegistrationForm(self):
        try:
            self._registrationForm.delete()
            self._registrationForm.setConference(None)
            self._registrationForm = None
        except AttributeError:
            self._registrationForm = None

    def recoverRegistrationForm(self, rf):
        self.setRegistrationForm(rf)
        rf.recover()

    def getEvaluation(self, id=0):
        ############################################################################
        #For the moment only one evaluation per conference is used.                #
        #In the future if there are more than one evaluation, modify this function.#
        ############################################################################
        """ Return the evaluation given by its ID or None if nothing found.
            Params:
                id -- id of the wanted evaluation
        """
        for evaluation in self.getEvaluations():
            if str(evaluation.getId()) == str(id) :
                return evaluation
        if HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive():
            raise Exception(_("Error with id: expected '%s', found '%s'.")%(id, self.getEvaluations()[0].getId()))
        else:
            return self.getEvaluations()[0]

    def getEvaluations(self):
        if not hasattr(self, "_evaluations"):
            self._evaluations = [Evaluation(self)]
        return self._evaluations

    def setEvaluations(self, evaluationsList):
        self._evaluations = evaluationsList
        for evaluation in self._evaluations:
            evaluation.setConference(self)

    def removeEvaluation(self, evaluation):
        """remove the given evaluation from its evaluations."""
        evaluations = self.getEvaluations()
        if evaluations.count(evaluation)>0:
            evaluations.remove(evaluation)
        evaluation.removeReferences()
        self.notifyModification()

    def removeAllEvaluations(self):
        for evaluation in self.getEvaluations():
            evaluation.removeReferences()
        self._evaluations = []
        self.notifyModification()

    def _getEvaluationCounter(self):
        if not hasattr(self, "_evaluationCounter"):
            self._evaluationCounter = Counter()
        return self._evaluationCounter

    ## Videoconference bookings related
    def getBookings(self):
        try:
            if self._bookings:
                pass
        except AttributeError, e:
            self._bookings = {}
            self.notifyModification()
        return self._bookings

    def getBookingsList(self, sort = False):
        bl = self.getBookings().values()
        if sort:
            bl.sort()
        return bl

    def _getBookingGenerator(self):
        try:
            return self._bookingGenerator
        except AttributeError, e:
            self._bookingGenerator = Counter()
            return self._bookingGenerator

    def getNewBookingId(self):
        return str(self._getBookingGenerator().newCount())

    def addBooking(self, bp):
        if (bp.getId() == ""):
            bp.setId(self.getNewBookingId())
        self.getBookings()[bp.getId()] = bp
        self.notifyModification()

    def hasBooking(self,booking):
        return booking.getConference()==self and \
        self.getBookings().has_key(booking.getId())

    def removeBooking(self, booking):
        if self.hasBooking(booking):
            deletion= booking.deleteBooking()
            if deletion[0] != 1:
                del self.getBookings()[booking.getId()]
                self.notifyModification()
        return deletion

    def getBookingByType(self, type):
        if self.getBookings().has_key(type):
            return self.getBookings()[type]
        return None

    def getBookingById(self, id):
        if self.getBookings().has_key(id):
            return self.getBookings()[id]
        return None

    ## End of Videoconference bookings related

    def getModPay(self):
        try:
            if self._modPay is None:
                self._modPay= epayment.EPayment(self)
        except AttributeError,e:
            self._modPay= epayment.EPayment(self)
        return self._modPay


    def getRegistrants(self):
        try:
            if self._registrants:
                pass
        except AttributeError, e:
            self._registrants = {}
            self.notifyModification()
        return self._registrants

    def getRegistrantsByEmail(self, email=None):
        """
        Returns the index of registrants by email OR a specific registrant if an email address
        is passed as argument.
        """
        try:
            if self._registrantsByEmail:
                pass
        except AttributeError, e:
            self._registrantsByEmail = self._createRegistrantsByEmail()
            self.notifyModification()
        if email:
            return self._registrantsByEmail.get(email)
        return self._registrantsByEmail

    def _createRegistrantsByEmail(self):
        dicByEmail = {}
        for r in self.getRegistrantsList():
            dicByEmail[r.getEmail()] = r
        return dicByEmail

    def getRegistrantsList(self, sort = False):
        rl = self.getRegistrants().values()
        if sort:
            rl.sort(registration.Registrant._cmpFamilyName)
        return rl

    def _getRegistrantGenerator(self):
        try:
            return self._registrantGenerator
        except AttributeError, e:
            self._registrantGenerator = Counter()
            return self._registrantGenerator

    def addRegistrant(self, rp, user):
        rp.setId( str(self._getRegistrantGenerator().newCount()) )
        rp.setOwner( self )
        self.getRegistrants()[rp.getId()] = rp
        self._notify('registrantAdded', user)
        self.notifyModification()

    def updateRegistrantIndexByEmail(self, rp, newEmail):
        oldEmail = rp.getEmail()
        if oldEmail != newEmail:
            if self.getRegistrantsByEmail().has_key(oldEmail):
                del self.getRegistrantsByEmail()[oldEmail]
            self.getRegistrantsByEmail()[newEmail] = rp
            self.notifyModification()

    def hasRegistrant(self,rp):
        return rp.getConference()==self and \
                self.getRegistrants().has_key(rp.getId())

    def hasRegistrantByEmail(self, email):
        # Return true if there is someone with the email of the param "email"
        return self.getRegistrantsByEmail().has_key(email)

    def removeRegistrant(self, id):
        part = self.getRegistrants()[id]
        self._registrationForm.notifyRegistrantRemoval(self.getRegistrants()[id])
        del self.getRegistrantsByEmail()[self.getRegistrantById(id).getEmail()]
        del self.getRegistrants()[id]
        if part.getAvatar() is not None:
            part.getAvatar().removeRegistrant(part)
        self._notify('registrantRemoved', part)
        TrashCanManager().add(part)
        self.notifyModification()

    def getRegistrantById(self, id):
        if self.getRegistrants().has_key(id):
            return self.getRegistrants()[id]
        return None

    def _getPrimAuthIndex(self):
        try:
            if self._primAuthIdx:
                pass
        except AttributeError:
            self._primAuthIdx=_PrimAuthIdx(self)
        return self._primAuthIdx

    def getContribsMatchingAuth(self,query,onlyPrimary=True):
        if str(query).strip()=="":
            return self.getContributionList()
        res=self._getPrimAuthIndex().match(query)
        return [self.getContributionById(id) for id in res]

    def getCoordinatedSessions( self, av ):
        """Returns a list with the sessions for which a user is coordinator.
        """
        try:
            if self._sessionCoordinators:
                pass
        except AttributeError:
            self._sessionCoordinators = SCIndex()
        sessions = self._sessionCoordinators.getSessions( av )
        for session in self.getSessionList():
            if session not in sessions and av != None:
                for email in av.getEmails():
                    if email in session.getCoordinatorEmailList():
                        sessions.append(session)
                        break
        return sessions

    def getManagedSession( self, av ):
        ls = []
        for session in self.getSessionList():
            pending = False
            if av != None:
                for email in av.getEmails():
                    if email in session.getAccessController().getModificationEmail():
                        pending = True
                        break
            if av in session.getManagerList() or pending:
                ls.append(session)
        return ls

    def addSessionCoordinator(self,session,av):
        """Makes a user become coordinator for a session.
        """
        try:
            if self._sessionCoordinators:
                pass
        except AttributeError:
            self._sessionCoordinators = SCIndex()
        if self.sessions.has_key(session.getId()):
            session.addCoordinator(av)
            self._sessionCoordinators.index(av,session)

    def removeSessionCoordinator( self, session, av ):
        """Removes a user as coordinator for a session.
        """
        try:
            if self._sessionCoordinators:
                pass
        except AttributeError:
            self._sessionCoordinators = SCIndex()
        if self.sessions.has_key(session.getId()):
            session.removeCoordinator( av )
            self._sessionCoordinators.unindex(av,session)

    def _getSubmitterIdx(self):
        try:
            return self._submitterIdx
        except AttributeError:
            self._submitterIdx=SubmitterIndex()
        return self._submitterIdx

    def addContribSubmitter(self,contrib,av):
        self._getSubmitterIdx().index(av,contrib)

    def removeContribSubmitter(self,contrib,av):
        self._getSubmitterIdx().unindex(av,contrib)

    def getContribsForSubmitter(self,av):
        return self._getSubmitterIdx().getContributions(av)

    def getBOAConfig(self):
        try:
            if self._boa:
                pass
        except AttributeError:
            self._boa=BOAConfig(self)
        return self._boa

    def getSessionCoordinatorRights(self):
        try:
            if self._sessionCoordinatorRights:
                pass
        except AttributeError, e:
            self._sessionCoordinatorRights = []
            self.notifyModification()
        return self._sessionCoordinatorRights

    def hasSessionCoordinatorRight(self, right):
        return right in self.getSessionCoordinatorRights()

    def addSessionCoordinatorRight(self, right):
        if SessionCoordinatorRights().hasRight(right) and not self.hasSessionCoordinatorRight(right):
            self._sessionCoordinatorRights.append(right)
        self.notifyModification()

    def removeSessionCoordinatorRight(self, right):
        if SessionCoordinatorRights().hasRight(right) and self.hasSessionCoordinatorRight(right):
            self._sessionCoordinatorRights.remove(right)
        self.notifyModification()

    def hasEnabledSection(self, section):
        # This hack is there since there is no more enable/disable boxes
        # in the conference managment area corresponding to those features.
        # Until the managment area is improved to get a more user-friendly
        # way of enabling/disabling those features, we always make them
        # available for the time being, but we keep the previous code for
        # further improvements
        return True

    def getPendingQueuesMgr(self):
        try:
            if self._pendingQueuesMgr:
                pass
        except AttributeError, e:
            self._pendingQueuesMgr=pendingQueues.ConfPendingQueuesMgr(self)
        return self._pendingQueuesMgr

    def getAccessController(self):
        return self.__ac

    def _cmpTitle( c1, c2 ):
        o1 = c1.getTitle().lower().strip()
        o2 = c2.getTitle().lower().strip()
        return cmp( o1, o2 )
    _cmpTitle=staticmethod(_cmpTitle)

    def getReportNumberHolder(self):
        try:
            if self._reportNumberHolder:
                pass
        except AttributeError, e:
            self._reportNumberHolder=ReportNumberHolder(self)
        return self._reportNumberHolder

    def setReportNumberHolder(self, rnh):
        self._reportNumberHolder=rnh

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

    def indexConf(self):
        pass

    def __init__(self):
        """ Default constructor
        """
        try:
            Conference.__init__(self, AdminList.getInstance().getList()[0], "default")
        except IndexError:
            raise MaKaCError(_("""There are no admin users. The "default" conference that stores the template cannot be created.
                                Please add at least 1 user to the admin list."""))


class ConferenceHolder( ObjectHolder ):
    """Specialised ObjectHolder dealing with conference objects. It gives a
            common entry point and provides simple methods to access and
            maintain the collection of stored conferences (DB).
    """
    idxName = "conferences"
    counterName = "CONFERENCE"

    def _newId( self ):
        id = ObjectHolder._newId( self )
        return "%s"%id

    def getById( self, id, quiet=False ):
        """returns an object from the index which id corresponds to the one
            which is specified.
        """

        if (id == "default"):
            return CategoryManager().getDefaultConference()

        if type(id) is int:
            id = str(id)
        if self._getIdx().has_key(str(id)):
            return self._getIdx()[str(id)]
        elif quiet:
            return None
        else:
            raise NoReportError( _("The specified event with id \"%s\" does not exist or has been deleted.") % escape_html(str(id)) )


class Observer(object):
    """ Base class for Observer objects.
        Inheriting classes should overload the following boolean class attributes:
            _shouldBeTitleNotified
            _shouldBeDateChangeNotified
            _shouldBeLocationChangeNotified
            _shouldBeDeletionNotified
        And set them to True if they want to be notified of the corresponding event.
        In that case, they also have to implement the corresponding methods:
            _notifyTitleChange (for title notification)
            _notifyEventDateChanges and _notifyTimezoneChange (for date / timezone notification)
            _shouldBeLocationChangeNotified (for location notification)
            _notifyDeletion (for deletion notification).
        The interface for those methods is also specified in this class. If the corresponding
        class attribute is set to False but the method is not implemented, an exception will be thrown.
    """
    _shouldBeTitleNotified = False
    _shouldBeDateChangeNotified = False
    _shouldBeLocationChangeNotified = False
    _shouldBeDeletionNotified = False

    def getObserverName(self):
        name = "'Observer of class" + self.__class__.__name__
        try:
            conf = self.getOwner()
            name = name + " of event " + conf.getId() + "'"
        except AttributeError:
            pass
        return name

    def notifyTitleChange(self, oldTitle, newTitle):
        if self._shouldBeTitleNotified:
            self._notifyTitleChange(oldTitle, newTitle)

    def notifyEventDateChanges(self, oldStartDate = None, newStartDate = None, oldEndDate = None, newEndDate = None):
        if self._shouldBeDateChangeNotified:
            self._notifyEventDateChanges(oldStartDate, newStartDate, oldEndDate, newEndDate)

    def notifyTimezoneChange(self, oldTimezone, newTimezone):
        if self._shouldBeDateChangeNotified:
            self._notifyTimezoneChange(oldTimezone, newTimezone)

    def notifyLocationChange(self, newLocation):
        if self._shouldBeLocationChangeNotified:
            self._notifyLocationChange(newLocation)

    def notifyDeletion(self):
        if self._shouldBeDeletionNotified:
            self._notifyDeletion()

    def _notifyTitleChange(self, oldTitle, newTitle):
        """ To be implemented by inheriting classes
            Notifies the observer that the Conference object's title has changed
        """
        raise MaKaCError("Class " + str(self.__class__.__name__) + " did not implement method _notifyTitleChange")

    def _notifyEventDateChanges(self, oldStartDate, newStartDate, oldEndDate, newEndDate):
        """ To be implemented by inheriting classes
            Notifies the observer that the start and / or end dates of the object it is attached to has changed.
            If the observer finds any problems during whatever he needs to do as a consequence of
            the event dates changing, he should write strings describing the problems
            in the 'dateChangeNotificationProblems' context variable (which is a list of strings).
        """
        raise MaKaCError("Class " + str(self.__class__.__name__) + " did not implement method notifyStartDateChange")

    def _notifyTimezoneChange(self, oldTimezone, newTimezone):
        """ To be implemented by inheriting classes.
            Notifies the observer that the end date of the object it is attached to has changed.
            This method has to return a list of strings describing problems encountered during
            whatever the DateChangeObserver object does as a consequence of the notification.
            If there are no problems, the DateChangeObserver should return an empty list.
        """
        raise MaKaCError("Class " + str(self.__class__.__name__) + " did not implement method notifyTimezoneChange")

    def _notifyLocationChange(self):
        """ To be implemented by inheriting classes
            Notifies the observer that the location of the object it is attached to has changed.
        """
        raise MaKaCError("Class " + str(self.__class__.__name__) + " did not implement method notifyLocationChange")

    def _notifyDeletion(self):
        """ To be implemented by inheriting classes
            Notifies the observer that the Conference object it is attached to has been deleted
        """
        raise MaKaCError("Class " + str(self.__class__.__name__) + " did not implement method notifyDeletion")

class TitleChangeObserver(Observer):
    """ Base class for objects who want to be notified of a Conference object being deleted.
        Inheriting classes have to implement the notifyTitleChange method, and probably the __init__ method too.
    """

    def notifyTitleChange(self, oldTitle, newTitle):
        """ To be implemented by inheriting classes
            Notifies the observer that the Conference object's title has changed
        """
        raise MaKaCError("Class " + str(self.__class__.__name__) + " did not implement method notifyTitleChange")


class SessionChair(ConferenceParticipation):

    def __init__(self):
        self._session=None
        self._id=""
        ConferenceParticipation.__init__(self)

    def _notifyModification( self ):
        if self._session != None:
            self._session.notifyModification()

    def clone(self):
        chair = SessionChair()
        chair.setValues(self.getValues())
        return chair

    def getSession(self):
        return self._session

    def getConference(self):
        s=self.getSession()
        if s is None:
            return None
        return s.getConference()

    def includeInSession(self,session,id):
        if self.getSession()==session and self.getId()==id.strip():
            return
        self._session=session
        self._id=id

    def delete( self ):
        self._session=None
        ConferenceParticipation.delete(self)

    def getLocator(self):
        if self.getSession() is None:
            return None
        loc=self.getSession().getLocator()
        loc["convId"]=self.getId()
        return loc

    def isSessionManager(self):
        # pendings managers
        if self.getEmail() in self._session.getAccessController().getModificationEmail():
            return True
        # managers list
        for manager in self._session.getManagerList():
            if self.getEmail() == manager.getEmail():
                return True
        return False

    def isSessionCoordinator(self):
        # pendings coordinators
        if self.getEmail() in self._session.getConference().getPendingQueuesMgr().getPendingCoordinatorsKeys():
            return True
        # coordinator list
        for coord in self._session.getCoordinatorList():
            if self.getEmail() == coord.getEmail():
                return True
        return False


class SlotChair(ConferenceParticipation):

    def __init__(self):
        self._slot=None
        self._id=""
        ConferenceParticipation.__init__(self)

    def _notifyModification( self ):
        if self._slot != None:
            self._slot.notifyModification()

    def clone(self):
        chair = SlotChair()
        chair.setValues(self.getValues())
        return chair

    def getSlot(self):
        return self._slot

    def getSession(self):
        s=self.getSlot()
        if s is None:
            return None
        return s.getSession()

    def getConference(self):
        s=self.getSlot()
        if s is None:
            return None
        return s.getConference()

    def includeInSlot(self,slot,id):
        if self.getSlot()==slot and self.getId()==id.strip():
            return
        self._slot=slot
        self._id=id

    def delete( self ):
        self._slot=None
        ConferenceParticipation.delete(self)

    def getLocator(self):
        if self.getSlot() is None:
            return None
        loc=self.getSlot().getLocator()
        loc["convId"]=self.getId()
        return loc

class SessionCoordinatorRights:

    def __init__(self):
        self._rights = {"modifContribs": "Modify the contributions",
                        "unrestrictedSessionTT": "Unrestricted session timetable management"
                        }

    def hasRight(self, r):
        return self._rights.has_key(r)

    def getRights(self):
        return self._rights

    def getRightList(self, sort=False):
        l=self._rights.values()
        if sort:
            l.sort()
        return l

    def getRightKeys(self):
        return self._rights.keys()

    def getRight(self, id):
        if self._rights.has_key(id):
            return self._rights[id]
        return None

class SCIndex(Persistent):
    """Index for conference session coordinators.

        This class allows to index conference session coordinators so the owner
        can answer optimally to the query if a user is coordinating
        any conference session.
        It is implemented by simply using a BTree where the Avatar id is used
        as key (because it is unique and non variable) and a list of
        coordinated sessions is kept as keys. It is the responsability of the
        index owner (conference) to keep it up-to-date i.e. notify session
        coordinator additions and removals.
    """

    def __init__( self ):
        self._idx=OOBTree()


    def getSessions(self,av):
        """Gives a list with the sessions a user is coordinating.
        """
        if av == None:
            return []
        return self._idx.get(av.getId(),[])

    def index(self,av,session):
        """Registers in the index a coordinator of a session.
        """
        if av == None or session == None:
            return
        if not self._idx.has_key(av.getId()):
            l=[]
            self._idx[av.getId()]=l
        else:
            l=self._idx[av.getId()]
        if session not in l:
            l.append(session)
        self.notifyModification()

    def unindex(self,av,session):
        if av==None or session==None:
            return
        l=self._idx.get(av.getId(),[])
        if session in l:
            l.remove(session)
            self.notifyModification()

    def notifyModification(self):
        self._idx._p_changed=1


class Session(CommonObjectBase, Locatable):
    """This class implements a conference session, being the different parts
        in which the conference can be divided and the contributions can be
        organised in. The class contains necessary attributes to store session
        basic data and provides the operations related to sessions. In
        principle, a session has no sense to exist without being related to a
        conference but it is allowed for flexibility.
    """

    fossilizes(ISessionFossil)


    def __init__(self, **sessionData):
        """Class constructor. Initialise the class attributes to the default
            values.
           Params:
            sessionData -- (Dict) Contains the data the session object has to
                be initialised to.
        """
        self.conference=None
        self.id="not assigned"
        self.title=""
        self.description=""
        #################################
        # Fermi timezone awareness      #
        #################################
        self.startDate = nowutc()
        #################################
        # Fermi timezone awareness(end) #
        #################################

        self.duration=timedelta(minutes=1)
        self.places=[]
        self.rooms=[]
        self.conveners=[] # This attribute must not be used and should disappear someday
        self._conveners=[]
        self._convenerGen=Counter()
        self.convenerText=""
        self.contributions={}
        self._contributionDuration=timedelta(minutes=20)
        self.__ac=AccessController(self)
        self.materials={}
        self.__materialGenerator=Counter()
        self.minutes=None
        self._comments = ""
        self.slots={}
        self.__slotGenerator=Counter()
        self._setSchedule()
        self._coordinators=OOBTree()
        self._coordinatorsEmail = []
        self._code=""
        self._color="#e3f2d3"
        self._textColor="#202020"
        self._textColorToLinks=False
        self._ttType=SlotSchTypeFactory.getDefaultId()
        self._closed = False
        self._registrationSession = None
        self._creationDS = nowutc()
        self._modificationDS = nowutc()
        self._keywords = ""

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

    def getTimezone( self ):
        return self.getConference().getTimezone()

    def updateNonInheritingChildren(self, elem, delete=False, propagate=True):
        self.getAccessController().updateNonInheritingChildren(elem, delete)
        if propagate == True:
            self.notify_protection_to_owner(elem, delete)

    def notify_protection_to_owner(self, elem, delete=False):
        """ This methods notifies the owner that the protection has been changed,
            so it can update its list of non inheriting children """
        self.getOwner().updateNonInheritingChildren(elem, delete)

    def getKeywords(self):
        try:
            return self._keywords
        except:
            self._keywords = ""
            return ""

    def setKeywords(self, keywords):
        self._keywords = keywords

    def notifyModification( self, raiseEvent = True, date = None, cleanCache = True ):
        """Method called to notify the current session has been modified.
        """
        self.setModificationDate(date)

        parent = self.getConference()
        if parent:
            parent.setModificationDate(date)
        if cleanCache:
            for slot in self.getSlotList():
                slot.cleanCache()
        self._p_changed=1

    def getModificationDate( self ):
        """Returns the date in which the session was last modified"""
        try:
            return self._modificationDS
        except:
            self._modificationDS = nowutc()
            return self._modificationDS

    def getCreationDate( self ):
        """Returns the date in which the session was created"""
        try:
            return self._creationDS
        except:
            self._creationDS = nowutc()
            return self._creationDS

    def getLogInfo(self):
        data = {}
        data["subject"] = self.title
        data["session id"] = self.id
        data["session code"] = self._code
        data["title"] = self.title
        data["description"] = self.description
        data["start date"] = self.startDate
        data["duration"] = self.duration
        for p in self.places :
            data["place"] = p.getName()
        for r in self.rooms :
            data["room"] = r.getName()
        for sc in self.getConvenerList() :
            data["convener %s"%sc.getId()] = sc.getFullName()
        for co in self.getCoordinatorList() :
            data["coordinators %s"%co.getId()] = co.getFullName()

        return data

    def getEnableSessionSlots(self):
        try:
            return self.getConference().getEnableSessionSlots()
        except:
            return True

    def cmpSessionByTitle(session1, session2):
        return cmp(session1.getTitle(), session2.getTitle())
    cmpSessionByTitle = staticmethod(cmpSessionByTitle)

    def hasRegistrationSession(self):
        return self.getRegistrationSession() is not None

    def getRegistrationSession(self):
        try:
            if self._registrationSession:
                pass
        except AttributeError, e:
            self._registrationSession = None
        return self._registrationSession

    def setRegistrationSession(self, rs):
        self._registrationSession = rs

    def isClosed( self ):
        if self.getConference().isClosed():
            return True
        try:
            return self._closed
        except:
            self._closed = False
            return False

    def setClosed( self, closed=True ):
        self._closed = closed
        self.notifyModification(cleanCache = False)

    def includeInConference(self,conf,newId):
        self.conference=conf
        self.id=newId
        for slot in self.getSlotList():
            conf.getSchedule().addEntry(slot.getConfSchEntry(),2)
        self.getConference().addSession(self)
        self.notifyModification()

    def delete(self):
        while len(self.getConvenerList()) > 0:
            self.removeConvener(self.getConvenerList()[0])
        while len(self.getMaterialList()) > 0:
            self.removeMaterial(self.getMaterialList()[0])
        self.removeMinutes()
        for c in self.getCoordinatorList()[:]:
            self.removeCoordinator(c)
        while len(self.contributions.values())>0:
            self.removeContribution(self.contributions.values()[0])
        while len(self.slots.values())>0:
            self._removeSlot(self.slots.values()[0])
        if self.getConference() is not None:
            self.getConference().removeSession(self)
            if self.hasRegistrationSession():
                self.getConference().getRegistrationForm().getSessionsForm().removeSession(self.getId())
                self.getRegistrationSession().setRegistrationForm(None)
                TrashCanManager().add(self.getRegistrationSession())
            self.notify_protection_to_owner(self, delete=True)
            self.conference=None
            TrashCanManager().add(self)

    def recover(self, isCancelled):
        if self.hasRegistrationSession():
            if not isCancelled:
                self.getRegistrationSession().setRegistrationForm(self.getConference().getRegistrationForm())
                self.getConference().getRegistrationForm().getSessionsForm().addSession(self.getRegistrationSession())
            TrashCanManager().remove(self.getRegistrationSession())
        TrashCanManager().remove(self)

    def getLocator( self ):
        """Gives back a globaly unique identification encapsulated in a Locator
            object for the session instance
        """
        if self.conference == None:
            return Locator()
        lconf = self.conference.getLocator()
        lconf["sessionId"] = self.getId()
        return lconf

    def getConference( self ):
        return self.conference

    def getSession( self ):
        return self

    def getOwner( self ):
        return self.getConference()

    def getId( self ):
        return self.id

    def getUniqueId( self ):
        """returns (string) the unique identiffier of the item"""
        """used mainly in the web session access key table"""
        return "%ss%s" % (self.getConference().getUniqueId(),self.id)

    def getModifKey( self ):
        return self.getConference().getModifKey()

    def getAccessKey( self ):
        return self.getConference().getAccessKey()

    def getContribDuration(self):
        try:
            return self._contributionDuration
        except:
            self._contributionDuration = timedelta(minutes=20)
            return self._contributionDuration

    def setContribDuration(self, hour=0, min=20, dur=None):
        if dur is not None:
            self._contributionDuration=dur
        else:
            self._contributionDuration = timedelta(hours=hour,minutes=min)

    def fit(self):
        #if not self.getConference().getEnableSessionSlots():
        #    self.getSlotList()[0].fit()
        self.setStartDate(self.getMinSlotStartDate(),0,0)
        self.setEndDate(self.getMaxSlotEndDate(),0)

    def addSlot(self,newSlot):
        id = newSlot.getId()
        if id == "not assigned":
            newSlot.setId(str(self.__slotGenerator.newCount()))
        self.slots[newSlot.getId()]=newSlot
        self.fit()
        self.getSchedule().addEntry(newSlot.getSessionSchEntry(),2)
        if self.getConference() is not None:
            self.getConference().getSchedule().addEntry(newSlot.getConfSchEntry(),2)
        self.notifyModification()

    def _removeSlot(self,slot):
        del self.slots[slot.getId()]
        self.getSchedule().removeEntry(slot.getSessionSchEntry())
        if self.getConference() is not None:
            self.getConference().getSchedule().removeEntry(slot.getConfSchEntry())
        slot.delete()

    def removeSlot(self, slot, force=False):
        if self.slots.has_key(slot.getId()):
            if len(self.slots)==1 and not force:
                raise MaKaCError( _("A session must have at least one slot"), _("Session"))
            self._removeSlot(slot)
            self.fit()
            self.notifyModification()

    def recoverSlot(self, slot):
        self.addSlot(slot)
        slot.recover()

    def getSlotById(self,slotId):
        return self.slots.get(slotId,None)

    def getSlotList(self):
        return self.slots.values()

    def getSortedSlotList(self):
        sl = self.getSlotList()
        sl.sort(utils.sortSlotByDate)
        return sl

    def getMinSlotStartTime(self):
        min = (25,61)
        for slot in self.getSlotList():
            if slot.isMoreThanDay():
                return (0,0)
            shour = slot.getStartDate().hour
            smin = slot.getStartDate().minute
            if (shour, smin) < min:
                min = (shour, smin)
        return min

    def getMaxSlotEndTime(self):
        max = (-1,-1)
        for slot in self.getSlotList():
            if slot.isMoreThanDay():
                return (23, 59)
            endDate = slot.getEndDate()
            if (endDate.hour, endDate.minute) > max:
                newEndDate = endDate - timedelta(0, 0, 0)
                max = (newEndDate.hour, newEndDate.minute)
        return max

    def getMinSlotStartDate(self):
        slotList = self.getSlotList()
        if len(slotList)==0:
            return self.getStartDate()
        else:
            sDate = self.getEndDate()
            for slot in slotList:
                if slot.getStartDate() < sDate:
                    sDate = slot.getStartDate()
            return sDate

    def getMaxSlotEndDate(self):
        slotList = self.getSlotList()
        if len(slotList)==0:
            return self.getEndDate()
        else:
            eDate = self.getStartDate()
            for slot in slotList:
                if slot.getEndDate() > eDate:
                    eDate = slot.getEndDate()
            return eDate

    def _getCorrectColor(self, color):
        if not color.startswith("#"):
            color = "#%s"%color
        m = re.match("^#[0-9A-Fa-f]{6}$", color)
        if m:
            return color
        return None

    def _getCorrectBgColor(self, color):
        color=self._getCorrectColor(color)
        if color is None:
            return self._color
        return color

    def _getCorrectTextColor(self, color):
        color=self._getCorrectColor(color)
        if color is None:
            return self._textColor
        return color

    def setValues( self, sessionData,check=2,moveEntries=0 ):
        """Sets all the values of the current session object from a dictionary
            containing the following key-value pairs:
                title-(str)
                description-(str)
                locationName-(str) => name of the location, if not specified
                        it will be set to the conference location name.
                locationAddress-(str)
                roomName-(str) => name of the room, if not specified it will
                    be set to the conference room name.
                sDate - (datetime) => starting date of the session, if not
                        specified it will be set to now.
                eDate - (datetime) => ending date of the session, if not
                        specified the end date will be set to the start one
                durHour - (int) => hours of duration for each entry in the session
                                   by default.
                durMin - (int) => hours of duration for each entry in the session
                                   by default.
                _conveners - (str)
                check parameter:
                    0: no check at all
                    1: check and raise error in case of problem
                    2: check and adapt the owner dates
           Please, note that this method sets ALL values which means that if
            the given dictionary doesn't contain any of the keys the value
            will set to a default value.
        """

        self.setTitle( sessionData.get("title", "NO TITLE ASSIGNED") )
        self.setDescription( sessionData.get("description", "") )
        code = sessionData.get("code", "")
        if code.strip() == "":
            if self.getId()=="not assigned":
                self.setCode("no code")
            else:
                self.setCode(self.getId())
        else:
            self.setCode(code)
        bgcolor = sessionData.get("backgroundColor", "")
        if bgcolor.strip() != "":
            self.setColor(self._getCorrectBgColor(bgcolor))
        textcolor = sessionData.get("textColor", "")
        if textcolor.strip() != "":
            if sessionData.has_key("autotextcolor"):
                self.setTextColor(utils.getTextColorFromBackgroundColor(self.getColor()))
            else:
                self.setTextColor(self._getCorrectTextColor(textcolor))
        self.setTextColorToLinks(sessionData.has_key("textcolortolinks"))

        if "locationName" in sessionData:
            loc = self.getOwnLocation()
            if not loc:
                loc = CustomLocation()
            self.setLocation( loc )
            loc.setName( sessionData["locationName"] )
            loc.setAddress( sessionData.get("locationAddress", "") )
        else:
            self.setLocation(None)

        #same as for the location
        if "roomName" in sessionData:
            room = self.getOwnRoom()
            if not room:
                room = CustomRoom()
            self.setRoom( room )
            room.setName( sessionData["roomName"] )
        else:
            self.setRoom(None)

        if sessionData.get("sDate",None) is not None:
            self.setStartDate(sessionData["sDate"],check,moveEntries=moveEntries)
        if sessionData.get("eDate",None) is not None:
            self.setEndDate(sessionData["eDate"],check)
        self._checkInnerSchedule()
        if sessionData.get("contribDuration","")!="":
            self._contributionDuration = sessionData.get("contribDuration")
        else:
            self._contributionDuration = timedelta(hours=int(sessionData.get("durHour",0)), minutes=int(sessionData.get("durMin",20)))
        self.notifyModification()

    def move(self, sDate):
        """
        Move a session from the old start date to a new start date, and
        it moves all the entries of the session as well, without date validations.
        """
        if sDate is not None:
            oldStartDate=self.startDate
            self.startDate=copy.copy(sDate)
            diff=self.startDate-oldStartDate
            # Check date to not be prior conference start date and to not surpass conference end date
            # The schedule is returning the datetime object as timezone aware relative to the conference
            # timezone.  Must adjust the startdate accordingly for comparison. JMF
            conftz = self.getConference().getTimezone()
            if self.getStartDate() < self.getConference().getSchedule().getStartDate() or \
                    self.getEndDate() > self.getConference().getSchedule().getEndDate():
                raise MaKaCError( _("Impossible to move the session because it would be out of the conference dates"))
            for entry in self.getSchedule().getEntries():
                if isinstance(entry,LinkedTimeSchEntry) and \
                        isinstance(entry.getOwner(), SessionSlot):
                    e = entry.getOwner()
                    e.move(e.getStartDate() + diff)
            self.getSchedule().reSchedule()
            self.getConference().getSchedule().reSchedule()
            self.notifyModification()

    def clone(self, deltaTime, conf, options):
        ses = Session()
        conf.addSession(ses,check=0)
        ses.setTitle(self.getTitle())
        ses.setDescription(self.getDescription())
        startDate = self.getStartDate() + deltaTime
        ses.setStartDate(startDate, check=1)
        ses.setDuration(dur=self.getDuration())

        if self.getOwnLocation() is not None:
            ses.addLocation(self.getOwnLocation().clone())
        if self.getOwnRoom() is not None:
            ses.setRoom(self.getOwnRoom().clone())
        ses.setColor(self.getColor())
        ses.setTextColor(self.getTextColor())
        ses.setTextColorToLinks(self.isTextColorToLinks())
        ses.setCode(self.getCode())
        ses.setContribDuration(dur=self.getContribDuration())
        ses.setScheduleType(self.getScheduleType())
        ses.setComments(self.getComments())

        # Access Control cloning
        if options.get("access", False) :
            ses.setProtection(self.getAccessController()._getAccessProtection())
            for mgr in self.getManagerList() :
                ses.grantModification(mgr)
            for user in self.getAllowedToAccessList() :
                ses.grantAccess(user)
            for domain in self.getDomainList():
                ses.requireDomain(domain)
            for coord in self.getCoordinatorList():
                ses.addCoordinator(coord)

        #slots in timeschedule
        for slot in self.getSlotList() :
            newslot = slot.clone(ses, options)
            ses.addSlot(newslot)
            ContextManager.setdefault("clone.unique_id_map", {})[slot.getUniqueId()] = newslot.getUniqueId()

        ses.notifyModification()

        return ses


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

    def getColor(self):
        try:
            if self._color:
                pass
        except AttributeError:
            self._color="#e3f2d3"
        return self._color
    getBgColor=getColor

    def setColor(self,newColor):
        self._color=str(newColor).strip()
        self.notifyModification()
    setBgColor=setColor

    def getTextColor(self):
        try:
            if self._textColor:
                pass
        except AttributeError:
            self._textColor="#202020"
        return self._textColor

    def setTextColor(self,newColor):
        self._textColor=str(newColor).strip()
        self.notifyModification()

    def isTextColorToLinks(self):
        try:
            if self._textColorToLink:
                pass
        except AttributeError:
            self._textColorToLink=False
        return self._textColorToLink

    def setTextColorToLinks(self, v):
        self._textColorToLink=v
        self.notifyModification()

    def getStartDate(self):
        return self.startDate

    def getAdjustedStartDate(self,tz=None):
        if not tz:
            tz = self.getConference().getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        return self.startDate.astimezone(timezone(tz))

    def verifyStartDate(self, sdate, check=2):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem (default)
            2: check and adapt the owner dates
        """

        conf=self.getConference()

        if conf is not None and sdate < conf.getSchedule().getStartDate():
            if check==1:
                raise ParentTimingError( _("The session starting date cannot be prior to the event starting date"), _("Session"))
            elif check==2:
                ContextManager.get('autoOps').append((self, "OWNER_START_DATE_EXTENDED",
                                conf, sdate.astimezone(timezone(conf.getTimezone()))))
                conf.setStartDate(sdate,check=0,moveEntries=0)

    def setStartDate(self,newDate,check=2,moveEntries=0):
        """
           moveEntries parameter:
            0: do not move inner slots
            1: move
            2: do not move but check that session is not out of the conference dates
        """

        if not newDate.tzname():
            raise MaKaCError("date should be timezone aware")
        if check != 0:
            self.verifyStartDate(newDate,check)
        oldSdate = self.getStartDate()
        try:
            tz = str(self.getStartDate().tzinfo)
        except:
            tz = 'UTC'
        diff = newDate - oldSdate
        self.startDate=copy.copy(newDate)
        if moveEntries == 1 and diff is not None and diff != timedelta(0):
            # If the start date changed, we move entries inside the timetable
            newDateTz = newDate.astimezone(timezone(tz))
            if oldSdate.astimezone(timezone(tz)).date() != newDateTz.date():
                entries = self.getSchedule().getEntries()[:]
            else:
                entries = self.getSchedule().getEntriesOnDay(newDateTz)[:]
            self.getSchedule().moveEntriesBelow(diff, entries)

        if moveEntries != 0 and self.getConference() and \
               not self.getConference().getEnableSessionSlots() and \
               self.getSlotList() != [] and \
               self.getSlotList()[0].getStartDate() != newDate:
            self.getSlotList()[0].startDate = newDate

        if check == 1:
            self._checkInnerSchedule()
        self.notifyModification()

    def _checkInnerSchedule( self ):
        self.getSchedule().checkSanity()

    def getEndDate(self):
        return self.startDate+self.duration

    ####################################
    # Fermi timezone awareness         #
    ####################################

    def getAdjustedEndDate(self,tz=None):
        return self.getAdjustedStartDate(tz) + self.duration

    ####################################
    # Fermi timezone awareness(end)    #
    ####################################

    def verifyEndDate(self, edate,check=1):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates
        """
        try:
            tz = timezone(self.getConference().getTimezone())
        except:
            tz = timezone('UTC')
        # compare end date with start date
        if edate<=self.getStartDate():
            if check == 1:
                raise MaKaCError( _("End date cannot be prior to the Start date"), _("Session"))
            if check == 2:
                self.setStartDate(edate)
        # check conference dates
        if (self.getConference()):
            conf=self.getConference()
            confStartDate = conf.getSchedule().getStartDate()
            confEndDate = conf.getSchedule().getEndDate()
            if conf is not None and (edate>confEndDate or edate<=confStartDate):
                if check==1:
                    raise ParentTimingError( _("The end date has to be between the event dates (%s - %s)")%\
                        (confStartDate.astimezone(tz).strftime('%Y-%m-%d %H:%M'),\
                        confEndDate.astimezone(tz).strftime('%Y-%m-%d %H:%M')),\
                        _("Session"))
                if check==2:
                    if edate>confEndDate:
                        ContextManager.get('autoOps').append((self, "OWNER_END_DATE_EXTENDED",
                                                              self.getConference(),
                                                              edate.astimezone(tz)))
                        self.getConference().setEndDate(edate)
                    if edate<=confStartDate:
                        ContextManager.get('autoOps').append((self, "OWNER_START_DATE_EXTENDED",
                                                              self.getConference(),
                                                              edate.astimezone(tz)))
                        self.getConference().setStartDate(edate)
        # check inner schedule
        if len(self.getSlotList()) != 0 and self.getSlotList()[-1].getSchedule().hasEntriesAfter(edate):
            raise TimingError( _("Cannot change end date: some entries in the session schedule end after the new date"), _("Session"))

    def setEndDate(self,newDate,check=2):
        if not newDate.tzname():
            raise MaKaCError("date should be timezone aware")
        if check != 0:
            self.verifyEndDate(newDate,check)
        self.duration=newDate-self.getStartDate()
        # A session is not always linked to a conference (for eg. at creation time)
        #if self.getConference() and not self.getConference().getEnableSessionSlots() and self.getSlotList()[0].getEndDate() != newDate:
        #    self.getSlotList()[0].duration = self.duration
        self.notifyModification()

    def setDates(self,sDate,eDate,check=1,moveEntries=0):
        if eDate<=sDate:
            tz = timezone(self.getConference().getTimezone())
            raise MaKaCError(_("The end date (%s) cannot be prior to the start date (%s)") % (eDate.astimezone(tz).strftime('%Y-%m-%d %H:%M'),sDate.astimezone(tz).strftime('%Y-%m-%d %H:%M')),_("Session"))
        self.setStartDate(sDate,check,moveEntries)
        self.setEndDate(eDate,check)
        self._checkInnerSchedule()

    def getDuration( self ):
        return self.duration

    def setDuration(self,hours=0,minutes=15,dur=0):
        if dur==0:
            dur = timedelta(hours=int(hours),minutes=int(minutes))
            if dur.seconds <= 0:
                raise MaKaCError( _("The duration cannot be less than zero"), _("Session"))
        self.duration = dur
        self.verifyEndDate(self.getEndDate())
        self.notifyModification()

    def getStartOnDay(self, day, tz=None):
        if not tz:
            tz = self.getConference().getTimezone()
        if type(day) is datetime:
            day = day.astimezone(timezone(tz))
        if day.date() < self.getStartDate().astimezone(timezone(tz)).date() or day.date() > self.getEndDate().astimezone(timezone(tz)).date() :
            return None
        minTime = self.getEndDate()
        for e in self.getSchedule().getEntriesOnDay(day) :
            if e.getStartDate() < minTime :
                minTime = e.getStartDate()
        if minTime == self.getEndDate() :
            minTime = day.replace(hour=8, minute=0)#datetime.combine(day,time(hour=8, minute=0))
            if minTime < self.getStartDate() :
                return self.getStartDate()
        return minTime

    def getEndOnDay(self, day, tz=None):
        if not tz:
            tz = self.getConference().getTimezone()
        if type(day) is datetime:
            day = day.astimezone(timezone(tz))
        if day.date() < self.getStartDate().astimezone(timezone(tz)).date() or day.date() > self.getEndDate().astimezone(timezone(tz)).date() :
            return None
        maxTime = self.getStartDate();
        for e in self.getSchedule().getEntriesOnDay(day) :
            if e.getEndDate() > maxTime :
                maxTime = e.getEndDate()
        if maxTime == self.getStartDate() :
            maxTime = day.replace(hour=19, minute=0)#datetime.combine(day,time(19,0))
            if maxTime > self.getEndDate() :
                return self.getEndDate()
        return maxTime

    def getLocationParent( self ):
        """
        Returns the object from which the room/location
        information should be inherited
        """
        return self.getConference()

    def getLocationList(self):
        """Method returning a list of "location" objects which contain the
            information about the different places the conference is gonna
            happen
        """
        return self.places

    def addLocation(self, newPlace):
        self.places.append( newPlace )
        self.notifyModification()

    def _resetConveners(self):
        try:
            if self._conveners:
                return
        except AttributeError:
            self._conveners=[]
            for oc in self.conveners:
                newConv=SessionChair()
                newConv.setDataFromAvatar(oc)
                self._addConvener(newConv)

    def getConvenerList(self):
        self._resetConveners()
        return self._conveners

    def getAllConvenerList(self):
        convenerList = set()
        for slot in self.getSlotList():
            for convener in slot.getConvenerList():
                convenerList.add(convener)
        return convenerList

    def _addConvener(self,newConv):
        if newConv in self._conveners:
            return
        try:
            if self._convenerGen:
                pass
        except AttributeError:
            self._convenerGen=Counter()
        id = newConv.getId()
        if id == "":
            id=int(self._convenerGen.newCount())
        newConv.includeInSession(self,id)
        self._conveners.append(newConv)
        self.notifyModification()

    def addConvener(self,newConv):
        self._resetConveners()
        self._addConvener(newConv)
        if isinstance(newConv, MaKaC.user.Avatar):
            conv.unlinkTo(self, "convener")

    def removeConvener(self,conv):
        self._resetConveners()
        if conv not in self._conveners:
            return
        #--Pending queue: remove pending Convener waiting to became manager if anything
        self.getConference().getPendingQueuesMgr().removePendingManager(conv)
        #--
        #--Pending queue: remove pending Convener waiting to became coordinator if anything
        self.getConference().getPendingQueuesMgr().removePendingCoordinator(conv)
        #--
        self._conveners.remove(conv)
        if isinstance(conv, MaKaC.user.Avatar):
            conv.linkTo(self, "convener")
        conv.delete()
        self.notifyModification()

    def recoverConvener(self, con):
        self.addConvener(con)
        con.recover()

    def getConvenerById(self,id):
        id=int(id)
        for conv in self._conveners:
            if conv.getId()==id:
                return conv
        return None

    def getConvenerText( self ):
        #to be removed
        try:
            if self.convenerText:
                pass
        except AttributeError, e:
            self.convenerText = ""
        return self.convenerText

    def setConvenerText( self, newText ):
        self.convenerText = newText.strip()

    def appendConvenerText( self, newText ):
        self.setConvenerText( "%s, %s"%(self.getConvenerText(), newText.strip()) )

    def addContribution(self, newContrib, id=None):
        """Registers the contribution passed as parameter within the session
            assigning it a unique id.
        """
        if self.hasContribution(newContrib):
            return
        self.getConference().addContribution(newContrib,id)
        self.contributions[newContrib.getId()]=newContrib
        newContrib.setSession(self)

        self.updateNonInheritingChildren(newContrib)
        for child in newContrib.getAccessController().getNonInheritingChildren():
            self.updateNonInheritingChildren(child)

        self.notifyModification()

    def hasContribution(self,contrib):
        return contrib.getSession()==self and \
                self.contributions.has_key(contrib.getId())

    def removeContribution(self,contrib):
        """Removes the indicated contribution from the session
        """
        if not self.hasContribution(contrib):
            return
        if contrib.isScheduled():
            # unschedule the contribution
            contrib._notify("contributionUnscheduled")
            sch=contrib.getSchEntry().getSchedule()
            sch.removeEntry(contrib.getSchEntry())
        del self.contributions[contrib.getId()]

        self.updateNonInheritingChildren(contrib, delete=True, propagate=False)
        for child in contrib.getAccessController().getNonInheritingChildren():
            self.updateNonInheritingChildren(child, delete=True, propagate=False)

        contrib.setSession(None)

        self.notifyModification()

    def newContribution( self, params = None, id=None ):
        c = Contribution()
        if params:
            c.setValues(params)
        self.addContribution( c, id )
        return c

    def getContributionById(self,id):
        id=str(id).strip()
        if self.contributions.has_key( id ):
            return self.contributions[ id ]
        return None

    def getContributionList( self ):
        return self.contributions.values()

    def getNumberOfContributions(self, only_scheduled=False):
        if only_scheduled:
            return len(filter(lambda c: c.isScheduled(), self.contributions.itervalues()))
        else:
            return len(self.contributions)

    def canIPAccess( self, ip ):
        if not self.__ac.canIPAccess( ip ):
            return False
        if self.getOwner() != None:
            return self.getOwner().canIPAccess(ip)
        return True

    def isProtected( self ):
        # tells if a session is protected or not
        return (self.hasProtectedOwner() + self.getAccessProtectionLevel()) > 0

    def getAccessProtectionLevel( self ):
        return self.__ac.getAccessProtectionLevel()

    def isItselfProtected( self ):
        return self.__ac.isItselfProtected()

    def hasAnyProtection( self ):
        """Tells whether a session has any kind of protection over it:
            access or domain protection.
        """
        if self.__ac.isProtected():
            return True
        if self.getDomainList():
            return True
        if self.getAccessProtectionLevel() == -1:
            return False

        return self.getOwner().hasAnyProtection()

    def hasProtectedOwner( self ):
        if self.getOwner() != None:
            return self.getOwner().isProtected()
        return False

    def setProtection( self, private ):
        self.__ac.setProtection( private )
        self.notify_protection_to_owner(self)

    def grantAccess( self, prin ):
        self.__ac.grantAccess( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.linkTo(self, "access")

    def revokeAccess( self, prin ):
        self.__ac.revokeAccess( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "access")

    def canView( self, aw ):
        """tells whether the specified user has access to the current object
            or any of its sub-objects
        """
        if self.canAccess( aw ):
            return True

        if any(self._notify("isPluginTypeAdmin", {"user": aw.getUser()}) +
               self._notify("isPluginAdmin", {"user": aw.getUser(), "plugins": "any"})):
            return True

        for contrib in self.getContributionList():
            if contrib.canView( aw ):
                return True
        return False

    def isAllowedToAccess( self, user ):
        if not user:
            return False
        if user in self.getCoordinatorList() or self.__ac.canUserAccess( user ) \
            or self.canUserModify( user ) or (not self.isItselfProtected() and self.getOwner().isAllowedToAccess(user)):
            return True
        return False

    def canAccess( self, aw ):
        # Allow harvesters (Invenio, offline cache) to access
        # protected pages
        if self.__ac.isHarvesterIP(aw.getIP()):
            return True
        #####################################################

        # Managers have always access
        if self.canModify(aw):
            return True

        flag_allowed_to_access = self.isAllowedToAccess(aw.getUser())
        if not self.canIPAccess(aw.getIP()) and not self.canUserModify(aw.getUser()) and \
                not flag_allowed_to_access:
            return False
        if not self.isProtected():
            return True
        return flag_allowed_to_access or self.conference.canKeyAccess(aw)

    def grantModification(self, sb, sendEmail=True):
        if isinstance(sb, SessionChair) or isinstance(sb, SlotChair):
            ah = AvatarHolder()
            results = ah.match({"email": sb.getEmail()}, exact=1)
            r = None
            for i in results:
                if sb.getEmail().lower().strip() in [j.lower().strip() for j in i.getEmails()]:
                    r = i
                    break
            if r is not None and r.isActivated():
                self.__ac.grantModification(r)
                r.linkTo(self, "manager")
            elif sb.getEmail() != "":
                modificationEmailGranted = self.__ac.grantModificationEmail(sb.getEmail())
                if modificationEmailGranted and sendEmail:
                    notif = pendingQueues._PendingManagerNotification( [sb] )
                    mail.GenericMailer.sendAndLog( notif, self.getConference() )
        else:
            self.__ac.grantModification( sb )
            if isinstance(sb, MaKaC.user.Avatar):
                sb.linkTo(self, "manager")

    def revokeModification( self, prin ):
        self.__ac.revokeModification( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "manager")

    def canModify( self, aw ):
        return self.canUserModify( aw.getUser() ) or self.getConference().canKeyModify( aw )

    def canUserModify( self, av ):
        """Tells whether a user is allowed to modify the current session:
            only if the user is granted to modify the session or the user
            can modify the corresponding conference.
        """
        return self.getConference().canUserModify( av ) or self.__ac.canModify( av )

    def getManagerList( self ):
        return self.__ac.getModifierList()

    def getAllowedToAccessList( self ):
        return self.__ac.getAccessList()

    def addMaterial( self, newMat ):
        newMat.setId( str(self.__materialGenerator.newCount()) )
        newMat.setOwner( self )
        self.materials[ newMat.getId() ] =  newMat
        self.notifyModification()

    def removeMaterial( self, mat ):
        if mat.getId() in self.materials.keys():
            mat.delete()
            self.materials[mat.getId()].setOwner(None)
            del self.materials[ mat.getId() ]
            self.notifyModification()
            return "done: %s"%mat.getId()
        elif mat.getId().lower() == 'minutes':
            self.removeMinutes()
            return "done: %s"%mat.getId()
        return "not done: %s"%mat.getId()

    def recoverMaterial(self, recMat):
    # Id must already be set in recMat.
        recMat.setOwner( self )
        self.materials[ recMat.getId() ] = recMat
        recMat.recover()
        self.notifyModification()

    def getMaterialRegistry(self):
        """
        Return the correct material registry for this type
        """
        from MaKaC.webinterface.materialFactories import SessionMFRegistry
        return SessionMFRegistry

    def getMaterialById( self, matId ):
        if matId.lower() == 'minutes':
            return self.getMinutes()
        elif self.materials.has_key(matId):
            return self.materials[ matId ]
        return None

    def getMaterialList( self ):
        return self.materials.values()

    def getAllMaterialList(self, sort=True):
        l = self.getMaterialList()
        if self.getMinutes():
            l.append( self.getMinutes() )
        if sort:
            l.sort(lambda x,y: cmp(x.getTitle(),y.getTitle()))
        return l

    def _setSchedule(self):
        self.__schedule=SessionSchedule(self)
        sl=self.getSlotList()
        for slot in self.getSlotList():
            self.__schedule.addEntry(slot.getSchEntry())

    def getSchedule( self ):
        try:
            if self.__schedule is None or not isinstance(self.__schedule,SessionSchedule):
                self._setSchedule()
        except AttributeError, e:
            self._setSchedule()
        return self.__schedule

    def getMasterSchedule( self ):
        return self.getOwner().getSchedule()

    def requireDomain( self, dom ):
        self.__ac.requireDomain( dom )

    def freeDomain( self, dom ):
        self.__ac.freeDomain( dom )

    def getDomainList( self ):
        return self.__ac.getRequiredDomainList()

    def setComments(self,comm):
        self._comments = comm.strip()

    def getComments(self):
        try:
            if self._comments:
                pass
        except AttributeError,e:
            self._comments=""
        return self._comments

    def createMinutes( self ):
        if self.getMinutes() != None:
            raise MaKaCError( _("The minutes for this session have already been created"), _("Session"))
        self.minutes = Minutes()
        self.minutes.setOwner( self )
        self.notifyModification()
        return self.minutes

    def removeMinutes( self ):
        if self.minutes is None:
            return
        self.minutes.delete()
        self.minutes.setOwner( None )
        self.minutes = None
        self.notifyModification()

    def recoverMinutes(self, min):
        self.removeMinutes() # To ensure that the current minutes are put in
                             # the trash can.
        self.minutes = min
        self.minutes.setOwner( self )
        min.recover()
        self.notifyModification()
        return self.minutes

    def getMinutes( self ):
        #To be removed
        try:
           if self.minutes:
            pass
        except AttributeError, e:
            self.minutes = None

        return self.minutes

    def _addCoordinator(self, av):
        if av is None or self._coordinators.has_key(av.getId()):
            return
        self._coordinators[av.getId()]=av
        if self.getConference() is not None:
            self.getConference().addSessionCoordinator(self,av)

    def getCoordinatorEmailList(self):
        try:
            return self._coordinatorsEmail
        except:
            self._coordinatorsEmail = []
        return self._coordinatorsEmail

    def _addCoordinatorEmail(self, email):
        if not email in self.getCoordinatorEmailList():
            self.getCoordinatorEmailList().append(email)

    def removeCoordinatorEmail(self, email):
        if email in self.getCoordinatorEmailList():
            if email in self.getCoordinatorEmailList():
                self.getCoordinatorEmailList().remove(email)
                self._p_changed = 1

    def addCoordinator( self, sb, sendEmail=True ):
        """Grants coordination privileges to user.

            Arguments:
                sb -- It can be either:
                        (MaKaC.user.Avatar) the user to which
                        coordination privileges must be granted.
                      or:
                        (MaKaC.conference.SessionChair) a non-existing which
                        has to become indico user before to be granted with privileges.
        """
        try:
            if self._coordinators:
                pass
        except AttributeError, e:
            self._coordinators=OOBTree()

        if isinstance(sb, SessionChair):
            ah = AvatarHolder()
            results=ah.match({"email":sb.getEmail()}, exact=1)
            r=None

            for i in results:
                if sb.getEmail().lower().strip() in [j.lower().strip() for j in i.getEmails()]:
                    r=i
                    break

            if r is not None and r.isActivated():

                self._addCoordinator(r)
                r.linkTo(self, "coordinator")
            else:
                self.getConference().getPendingQueuesMgr().addPendingCoordinator(sb)
        else:
            self._addCoordinator(sb)
            if isinstance(sb, MaKaC.user.Avatar):
                sb.linkTo(self, "coordinator")

    def removeCoordinator( self, av ):
        """Revokes coordination privileges to user.

           Arguments:
            av -- (MaKaC.user.Avatar) user for which coordination privileges
                    must be revoked
        """
        try:
            if self._coordinators:
                pass
        except AttributeError, e:
            self._coordinators=OOBTree()

        if av is None or not self._coordinators.has_key(av.getId()):
            return
        del self._coordinators[av.getId()]
        if isinstance(av, MaKaC.user.Avatar):
            av.unlinkTo(self, "coordinator")
        if self.getConference() is not None:
            self.getConference().removeSessionCoordinator(self,av)

    def isCoordinator( self, av ):
        """Tells whether the specified user is a coordinator of the session.

           Arguments:
            av -- (MaKaC.user.Avatar) user to be checked

           Return value: (boolean)
        """
        try:
            if self._coordinators:
                pass
        except AttributeError, e:
            self._coordinators=OOBTree()
        if (av is not None) and self._coordinators.has_key(av.getId()):
            return True
        ret = False
        if isinstance(av, MaKaC.user.Avatar):
            for email in av.getEmails():
                if email in self.getCoordinatorEmailList():
                    self.addCoordinator(av)
                    self.removeCoordinatorEmail(email)
                    ret = True
        return ret

    def hasConvenerByEmail(self, email):
        for convener in self.getConvenerList():
            if email == convener.getEmail():
                return True
        return False


    def getCoordinatorList( self ):
        """Return all users which have privileges to coordinate the session.

            Return value: (list)
        """
        try:
            if self._coordinators:
                pass
        except AttributeError, e:
            self._coordinators=OOBTree()

        return self._coordinators.values()

    def canCoordinate(self,aw, right=""):
        """Tells if a user has coordination privileges.

            Only session coordinators have coordination privileges over a
            session.

            Params:
                aw -- (MaKaC.accessControl.AccessWrapper) User access
                    information for which the coordination privileges must be
                    checked.

            Return value: (boolean)
        """
        if right != "":
            return self.isCoordinator(aw.getUser()) and self.getConference().hasSessionCoordinatorRight(right)
        return self.isCoordinator(aw.getUser())


    def getScheduleType(self):
        try:
            if self._ttType:
                pass
        except AttributeError:
            self._ttType=SlotSchTypeFactory.getDefaultId()
        return self._ttType

    def setScheduleType(self,t):
        try:
            if self._ttType:
                pass
        except AttributeError:
            self._ttType=SlotSchTypeFactory.getDefaultId()
        t=str(t).strip().lower()
        if t not in SlotSchTypeFactory.getIdList() or t==self._ttType:
            return
        self._ttType=t
        for slot in self.getSlotList():
            slot.setScheduleType(t)

    def getAccessController(self):
        return self.__ac


    def _cmpTitle( s1, s2 ):
        s1=s1.getTitle().lower().strip()
        s2=s2.getTitle().lower().strip()
        return cmp( s1, s2 )
    _cmpTitle=staticmethod(_cmpTitle)


class SessionSlot(Persistent, Observable, Fossilizable, Locatable):

    fossilizes(ISessionSlotFossil)

    def __init__(self,session,**sessionSlotData):
        self.session = session
        self.id = "not assigned"
        self.title = ""
        self.startDate=None
        self.duration = timedelta(minutes=1)
        self.places = []
        self.rooms = []
        self._conveners = []
        self._convenerGen=Counter()
        self._schedule=SlotSchTypeFactory.getDefaultKlass()(self)
        self._sessionSchEntry=LinkedTimeSchEntry(self)
        self._confSchEntry=LinkedTimeSchEntry(self)
        self._contributionDuration = None

    def getTimezone( self ):
        return self.getConference().getTimezone()

    def getLogInfo(self):
        data = {}
        data["id"] = self.id
        data["title"] = self.title
        data["session"] = self.session.getTitle()
        data["start date"] = self.startDate
        data["duration"] = self.duration
        i = 0
        for p in self.places :
            data["place %s"%i] = p.getName()
            i+=1
        i = 0
        for r in self.rooms :
            data["room %s"%i] = r.getName()
            i+=1
        for c in self._conveners :
            data["convener %s"%c.getId()] = c.getFullName()
        return data

    def clone(self,session, options):

        slot = SessionSlot(session)
        slot.session = session
        slot.setTitle(self.getTitle())
        timeDifference = session.getConference().getStartDate() - self.getSession().getConference().getStartDate()
        slot.setStartDate(self.getStartDate() + timeDifference)
        slot.setDuration(dur=self.getDuration(), check=2)

        #places
        if self.getOwnLocation() is not None:
            slot.setLocation(self.getOwnLocation().clone())
        #rooms
        if self.getOwnRoom() is not None:
            slot.setRoom(self.getOwnRoom().clone())

        #chairs = conveners
        for ch in self.getOwnConvenerList() :
            slot.addConvener(ch.clone())

        #populate the timetable
        if options.get("contributions", False) :
            for entry in self.getEntries() :
                if isinstance(entry, BreakTimeSchEntry) :
                    newentry = entry.clone(slot)
                    slot.getSchedule().addEntry(newentry,0)
                elif isinstance(entry, ContribSchEntry) :
                    contrib = entry.getOwner()
                    newcontrib = contrib.clone(session, options, timeDifference)
                    slot.getSchedule().addEntry(newcontrib.getSchEntry(),0)
                    ContextManager.setdefault("clone.unique_id_map", {})[contrib.getUniqueId()] = newcontrib.getUniqueId()

        slot.setContribDuration(0, 0, self.getContribDuration())
        slot.notifyModification(cleanCache = False)

        return slot

    def fit( self ):
        """
        sets the start date of the slot to the start date of the first son
        and the end date to the end date of the last son
        """
        sch = self.getSchedule()
        entries = sch.getEntries()
        if len(entries) > 0:
            self.setStartDate(entries[0].getStartDate(),0,0)
            self.setEndDate(sch.calculateEndDate(), check=0)

    def recalculateTimes( self, type, diff ):
        """
        recalculate and reschedule the contributions of the session slot with a time "diff" of separation.
        """
        if type=="duration":
            entries = self.getSchedule().getEntries()[:]
            i=0
            while i<len(entries):
                entry=entries[i]
                if i+1 == len(entries):
                    dur=self.getEndDate()-entry.getStartDate()
                else:
                    nextentry=entries[i+1]
                    dur=nextentry.getStartDate()-entry.getStartDate()-diff
                if dur<timedelta(0):
                    raise EntryTimingError( _("""With the time between entries you've chosen, the entry "%s" will have a duration less than zero minutes. Please, choose another time""")%entry.getTitle())
                entry.setDuration(dur=dur)
                i+=1
            if len(entries) != 0 and self.getEndDate() < entry.getEndDate():
                self.setEndDate(entry.getEndDate(),2)
        elif type=="startingTime":
            st = self.getStartDate()
            entries = self.getSchedule().getEntries()[:]
            for entry in entries:
                entry.setStartDate(st,0,0)
                # add diff to last item end date if and only if the item is
                # not a break
                #if not isinstance(entry, BreakTimeSchEntry):
                #    st=entry.getEndDate()+diff
                #else:
                #    st=entry.getEndDate()
                st=entry.getEndDate()+diff
            if len(entries) != 0 and self.getEndDate() < st:
                self.setEndDate(st,2)

    def setValues(self,data,check=2, moveEntriesBelow=0):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates
        """

        # In order to move the entries below, it is needed to know the diff (we have to move them)
        # and the list of entries to move. It's is needed to take those datas in advance because they
        # are going to be modified before the moving.
        if moveEntriesBelow == 1:
            oldStartDate=copy.copy(self.getStartDate())
            oldDuration=copy.copy(self.getDuration())
            i=self.getConfSchEntry().getSchedule().getEntries().index(self.getConfSchEntry())+1
            entriesList = self.getConfSchEntry().getSchedule().getEntries()[i:]
        self.title=data.get("title", "NO TITLE ASSIGNED")
        # Do we move all entries in the slot
        move = int(data.get("move",0))

        if "locationName" in data:
            loc = self.getOwnLocation()
            if not loc:
                loc = CustomLocation()
            self.setLocation( loc )
            loc.setName( data["locationName"] )
            loc.setAddress( data.get("locationAddress", "") )
        else:
            self.setLocation( None )

        if "roomName" in data:
            room = self.getOwnRoom()
            if not room:
                room = CustomRoom()
            self.setRoom( room )
            room.setName( data["roomName"] )
        else:
            self.setRoom( None )
        sDate = eDate = None
        confTZ = self.getOwner().getConference().getTimezone()
        if data.get("sDate",None) is not None:
            sd = data.get("sDate")
            sDate = timezone(confTZ).localize(datetime(sd.year,sd.month,sd.day,sd.hour,sd.minute))
        elif data.get("sYear","")!="" and data.get("sMonth","")!="" and \
                data.get("sDay","")!="" and data.get("sHour","")!="" and \
                data.get("sMinute","")!="":
            sDate = timezone(confTZ).localize(datetime(int(data["sYear"]),int(data["sMonth"]),
                                        int(data["sDay"]),int(data["sHour"]),
                                        int(data["sMinute"])))
        if data.get("eDate",None) is not None:
            ed = data.get("eDate")
            eDate = timezone(confTZ).localize(datetime(ed.year,ed.month,ed.day,ed.hour,ed.minute))
        elif data.get("eYear","")!="" and data.get("eMonth","")!="" and \
                data.get("eDay","")!="" and data.get("eHour","")!="" and \
                data.get("eMinute","")!="":
            eDate = timezone(confTZ).localize(datetime(int(data["eYear"]),int(data["eMonth"]),
                                        int(data["eDay"]),int(data["eHour"]),
                                        int(data["eMinute"])))
        if sDate != None and eDate != None:
            sDateUTC = sDate.astimezone(timezone('UTC'))
            eDateUTC = eDate.astimezone(timezone('UTC'))
            self.setDates(sDateUTC,eDateUTC,check,moveEntries=move)
        elif sDate != None:
            sDateUTC = sDate.astimezone(timezone('UTC'))
            self.setStartDate(sDateUTC,check,moveEntries=move)
        if data.get("durHours","")!="" and data.get("durMins","")!="":
            self.setDuration(hours=data["durHours"],minutes=data["durMins"],check=check)
        if data.get("contribDurHours","")!="" and data.get("contribDurMins","")!="":
            self.setContribDuration(int(data["contribDurHours"]),int(data["contribDurMins"]))
        elif data.get("contribDuration","")!="":
            self.setContribDuration(dur=data.get("contribDuration"))
        else:
            self.setContribDuration(None,None)
        conveners = data.get("conveners",None)
        if conveners is not None:
            self.clearConvenerList()
            for conv in conveners:
                sc = SlotChair()
                sc.setTitle(conv.getTitle())
                sc.setFirstName(conv.getFirstName())
                sc.setFamilyName(conv.getFamilyName())
                sc.setAffiliation(conv.getAffiliation())
                sc.setEmail(conv.getEmail())
                self.addConvener(sc)
        if moveEntriesBelow == 1:
            diff = (self.getStartDate() - oldStartDate) + (self.getDuration() - oldDuration)
            self.getSchedule().moveEntriesBelow(diff, entriesList)
        self._checkInnerSchedule()
        self.notifyModification()

    def _checkInnerSchedule( self ):
        self.getSchedule().checkSanity()

    def setContribDuration(self, hour=0, min=0, dur=None):
        self._contributionDuration = None
        if dur is not None:
            self._contributionDuration=dur
        elif hour != None and min != None:
            self._contributionDuration = timedelta(hours=hour,minutes=min)

    def getContribDuration(self):
        """
        Duration by default for contributions within the slots.
        """
        try:
            if self._contributionDuration:
                pass
        except AttributeError, e:
            self._contributionDuration = None
        return self._contributionDuration

    def notifyModification( self, cleanCache = True, cleanCacheEntries = False):
        self.getSession().notifyModification(cleanCache = False)
        if cleanCache:
            self.cleanCache(cleanCacheEntries)
        self._p_changed = 1

    def cleanCache(self, cleanCacheEntries = False):
        if not ContextManager.get('clean%s'%self.getUniqueId(), False):
            ScheduleToJson.cleanCache(self)
            ContextManager.set('clean%s'%self.getUniqueId(), True)
            if cleanCacheEntries:
                for entry in self.getSchedule().getEntries():
                    entry.getOwner().cleanCache(cleanConference = False)

    def getLocator( self ):
        l=self.getSession().getLocator()
        l["slotId"]=self.getId()
        return l

    def getConference( self ):
        return self.getSession().getConference()

    def getSession(self):
        return self.session

    def getOwner(self):
        return self.session

    def getContributionList(self):
        return [e.getOwner() for e in ifilter(lambda e: isinstance(e, ContribSchEntry),
                                              self.getSchedule().getEntries())]

    def _setSchedule(self, klass):
        old_sch = self.getSchedule()
        self._schedule = klass(self)
        #after removing old entries, one could try to fit them into the new
        #   schedule, but there are several things to consider which are left
        #   for later implementation (breaks, entries not fitting in the
        #   slots,...)
        while len(old_sch.getEntries()) > 0:
            entry = old_sch.getEntries()[0]
            old_sch.removeEntry(entry)
        self.notifyModification()

    def getSchedule(self):
        return self._schedule

    def getMasterSchedule( self ):
        return self.getOwner().getSchedule()

    def getConfSchEntry( self ):
        try:
            if self._confSchEntry:
                pass
        except AttributeError:
            self._confSchEntry=LinkedTimeSchEntry(self)
        return self._confSchEntry

    def getSessionSchEntry( self ):
        try:
            if self._sessionSchEntry:
                pass
        except AttributeError:
            self._sessionSchEntry=self._schEntry
        return self._sessionSchEntry

    def setId( self, newId ):
        self.id=str(newId)
        self.notifyModification()

    def getId( self ):
        return self.id

    def getUniqueId( self ):
        """Returns (string) the unique identiffier of the item.
           Used mainly in the web session access key table"""
        return "%sl%s" % (self.getSession().getUniqueId(),self.id)

    def setTitle( self, newTitle ):
        self.title=newTitle
        self.notifyModification()

    def getTitle( self ):
        try:
            if self.title:
                pass
        except AttributeError,e:
            self.title=""
        return self.title

    def getFullTitle( self ):
        return self.getSession().getTitle() + (": " + self.getTitle() if self.getTitle() else "")

    def getName(self):
        return "slot %s"%self.getId()

    def getDescription(self):
        return self.getSession().getDescription()

    def setDates(self,sDate,eDate,check=2,moveEntries=0):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""

        if sDate>eDate:
            raise MaKaCError(_("End date cannot be prior to Start date"),_("Slot"))

        self.setStartDate(sDate, check, moveEntries, checkDuration=False)
        self.setDuration(0, 0, 0, eDate-sDate, check)
        self.notifyModification()

    def getEntries(self):
        entriesList = self.getSchedule().getEntries()
        return entriesList

    def move(self, sDate):
        diff=sDate-self.startDate
        self.startDate = sDate
        for slotEntry in self.getSchedule().getEntries():
            if isinstance(slotEntry, BreakTimeSchEntry):
                slotEntry.startDate = slotEntry.getStartDate() + diff
            else:
                se = slotEntry.getOwner()
                se.startDate = se.getStartDate() + diff
        self.getSchedule().reSchedule()

    def verifyStartDate(self, sDate,check=2):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""

        tz = timezone(self.getConference().getTimezone())

        if sDate < self.getSession().getStartDate():
            if check == 1:
                raise ParentTimingError(_("The slot \"%s\" cannot start (%s) before its parent session starts (%s)")%\
                    (self.getTitle(), sDate.astimezone(tz).strftime('%Y-%m-%d %H:%M'),\
                    self.getSession().getStartDate().astimezone(tz).strftime('%Y-%m-%d %H:%M')),\
                    _("Slot"))
            elif check == 2:
                self.getSession().setStartDate(sDate, check, 0)

    def setStartDate(self,sDate,check=2,moveEntries=0,checkDuration=True):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""
        if sDate is None:
            return
        if not sDate.tzname():
            raise MaKaCError("date should be timezone aware")
        if check != 0:
            #If not using .fit() at the end of this method, comment it out
            #if self.getSession().getStartDate() > sDate:
            #    self.getSession().duration += self.getSession().getStartDate() - sDate
            self.verifyStartDate(sDate,check)

        # calculate the difference betwwen old and new date
        difference = None
        if self.startDate is not None:
            difference = sDate - self.getStartDate()

        self.startDate=copy.copy(sDate)

        if difference != None and difference != timedelta(0) and moveEntries:
            ContextManager.get('autoOps').append((self, "ENTRIES_MOVED",
                                                  self, sDate.astimezone(timezone(self.getTimezone()))))
            self.getSchedule().moveEntriesBelow(difference,self.getSchedule().getEntries()[:])

        if self.getConference() and not self.getConference().getEnableSessionSlots() and self.getSession().getStartDate() != sDate:
            self.getSession().setStartDate(sDate, check, 0)
        if check != 0 and self.getSession() and checkDuration:
            self.verifyDuration(self.getDuration(), check=check)

        # synchronize with other timetables
        self.getSessionSchEntry().synchro()
        self.getConfSchEntry().synchro()
        self.getSession().fit()
        self.notifyModification()

    def setEndDate(self,eDate,check=2):
        if not eDate.tzname():
            raise MaKaCError("date should be timezone aware")
        if check != 0:
            self.verifyDuration(eDate-self.startDate, check)
        self.setDuration(dur=eDate-self.startDate,check=check)
        if self.getConference() and not self.getConference().getEnableSessionSlots() and self.getSession().getEndDate() != eDate:
            self.getSession().setEndDate(eDate, check)
        self.getSession().fit()
        self.notifyModification()

    def getStartDate( self ):
        return self.startDate

    def getAdjustedStartDate(self,tz=None):
        if not tz:
            tz = self.getConference().getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        return self.startDate.astimezone(timezone(tz))

    def getEndDate( self ):
        if self.startDate is None:
            return None
        return self.startDate+self.duration

    def getAdjustedEndDate( self, tz=None ):
        if not tz:
            tz = self.getConference().getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        if self.getEndDate():
            return self.getEndDate().astimezone(timezone(tz))
        return None

    def getDuration( self ):
        return self.duration

    def isMoreThanDay(self):
        if self.getDuration() >= timedelta(days=1):
            return True
        return False

    def verifyDuration(self, dur, check=1):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""

        tz = timezone(self.getConference().getTimezone())
        if dur <= timedelta(0):
            raise MaKaCError( _("The duration cannot be less than zero"), _("Slot"))
        if dur.days > 1:
            raise MaKaCError( _("The duration cannot be more than one day"), _("Slot"))
        if self.startDate is not None:
            sessionStartDate = self.getSession().getStartDate()
            sessionEndDate = self.getSession().getEndDate()
            # end date has to be between the session dates
            eDate = self.startDate + dur
            if eDate > sessionEndDate:
                if check==1:
                    raise EntryTimingError(_("The session slot cannot end (%s) after its parent session (%s)") \
                            % (eDate.astimezone(tz).strftime('%Y-%m-%d %H:%M'),\
                            sessionEndDate.astimezone(tz).strftime('%Y-%m-%d %H:%M')),\
                            _("Slot"))
                elif check==2:
                    ContextManager.get('autoOps').append((self, "OWNER_END_DATE_EXTENDED",
                                                          self.getSession(), eDate.astimezone(tz)))
                    self.getSession().setEndDate(eDate,check)
            if eDate.astimezone(tz).date() > self.startDate.astimezone(tz).date():
                raise TimingError( _("The time slot must end on the same day it has started"), _("Slot"))
            # do not modify if slot entries will be affected
            sch = self.getSchedule()
            entries = sch.getEntries()
            if entries != []:
                if eDate < sch.calculateEndDate():
                    raise TimingError(_("The session slot cannot end at (%s) because there is a contribution (%s) ending after that time. ")%\
                        (eDate.astimezone(tz).strftime('%Y-%m-%d %H:%M'),\
                        sch.calculateEndDate().astimezone(tz).strftime('%Y-%m-%d %H:%M')),\
                        _("Slot"))

    def setDuration(self, days=0,hours=0,minutes=0,dur=0,check=1):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""

        if dur==0:
            dur = timedelta(days=int(days),hours=int(hours),minutes=int(minutes))
        if dur==0 and check==2:
            ContextManager.get('autoOps').append((self, "DURATION_SET",
                                                  self, 1))
            dur = timedelta(minutes=1)
        if dur > timedelta(days=1) and check==2:
            pass#dur = timedelta(days=1)
        if check != 0:
            self.verifyDuration(dur, check)
        self.duration = dur
        self.getSessionSchEntry().synchro()
        self.getConfSchEntry().synchro()
        self.getSession().fit()
        self.notifyModification()

    def getLocationParent( self ):
        """
        Returns the object from which the room/location
        information should be inherited
        """
        return self.session.conference

    def delete(self):
        self._notify('deleted', self)
        self.getSchedule().clear()
        if self.getSession() is not None:
            self.getSession().removeSlot(self)
            self.session=None
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def getAccessController( self ):
        return self.getSession().getAccessController()

    def canAccess(self,aw):
        return self.getSession().canAccess(aw)

    def canView(self,aw):
        return self.getSession().canView(aw)

    def isProtected(self):
        return self.getSession().isProtected()

    def getAccessKey( self ):
        return self.getSession().getAccessKey()

    def setScheduleType(self,id):
        id=str(id).strip().lower()
        currentId=SlotSchTypeFactory.getId(self.getSchedule())
        if id not in SlotSchTypeFactory.getIdList() or id==currentId:
            return
        self._setSchedule(SlotSchTypeFactory.getScheduleKlass(id))

    def getConvenerList(self):
        try:
            if self._conveners:
                pass
        except AttributeError:
            self._conveners = []
        if self._conveners == []:
            return self.getSession().getConvenerList()
        return self._conveners

    def addConvener(self,newConv):
        if newConv in self._conveners:
            return
        try:
            if self._convenerGen:
                pass
        except AttributeError:
            self._convenerGen=Counter()
        id = newConv.getId()
        if id == "":
            id=int(self._convenerGen.newCount())
        newConv.includeInSlot(self,id)
        self._conveners.append(newConv)
        self.notifyModification()

    def removeConvener(self,conv):
        if conv not in self._conveners:
            return
        self._conveners.remove(conv)
        conv.delete()
        self.notifyModification()

    def recoverConvener(self, con):
        self.addConvener(con)
        con.recover()

    def getConvenerById(self,id):
        id=int(id)
        for conv in self._conveners:
            if conv.getId()==id:
                return conv
        return None

    def getOwnConvenerList(self):
        try:
            if self._conveners:
                pass
        except AttributeError:
            self._conveners = []
        return self._conveners

    def clearConvenerList(self):
        while len(self.getOwnConvenerList()) > 0:
            self._conveners.pop()
        self.notifyModification()

    def getColor(self):
        res=""
        if self.getSession() is not None:
            res=self.getSession().getColor()
        return res

    def getTextColor(self):
        res=""
        if self.getSession() is not None:
            res=self.getSession().getTextColor()
        return res

    def getAllMaterialList(self, sort=True):
        return self.getSession().getAllMaterialList(sort=sort)

    def getRecursiveAllowedToAccessList(self):
        return self.getSession().getRecursiveAllowedToAccessList()

    def canModify(self, aw):
        return self.getSession().canModify(aw)


class ContributionParticipation(Persistent, Fossilizable):

    fossilizes(IContributionParticipationFossil, IContributionParticipationMinimalFossil,\
               IContributionParticipationTTDisplayFossil,\
               IContributionParticipationTTMgmtFossil)

    def __init__( self ):
        self._contrib = None
        self._id = ""
        self._firstName = ""
        self._surName = ""
        self._email = ""
        self._affiliation = ""
        self._address = ""
        self._phone = ""
        self._title = ""
        self._fax = ""

    def _notifyModification( self ):
        if self._contrib != None:
            self._contrib.notifyModification()

    def setValues(self, data):
        self.setFirstName(data.get("firstName", ""))
        self.setFamilyName(data.get("familyName",""))
        self.setAffiliation(data.get("affilation",""))
        self.setAddress(data.get("address",""))
        self.setEmail(data.get("email",""))
        self.setFax(data.get("fax",""))
        self.setTitle(data.get("title",""))
        self.setPhone(data.get("phone",""))
        self._notifyModification()

    def getValues(self):
        data={}
        data["firstName"]=self.getFirstName()
        data["familyName"]=self.getFamilyName()
        data["affilation"]=self.getAffiliation()
        data["address"]=self.getAddress()
        data["email"]=self.getEmail()
        data["fax"]=self.getFax()
        data["title"]=self.getTitle()
        data["phone"]=self.getPhone()
        return data

    def clone(self):
        part = ContributionParticipation()
        part.setValues(self.getValues())
        return part

    def setDataFromAvatar(self,av):
    # av is an Avatar object.
        if av is None:
            return
        self.setFirstName(av.getName())
        self.setFamilyName(av.getSurName())
        self.setEmail(av.getEmail())
        self.setAffiliation(av.getOrganisation())
        self.setAddress(av.getAddress())
        self.setPhone(av.getTelephone())
        self.setTitle(av.getTitle())
        self.setFax(av.getFax())
        self._notifyModification()

    def setDataFromOtherCP(self,cp):
    # cp is a ContributionParticipation object.
        if cp is None:
            return
        self.setFirstName(cp.getFirstName())
        self.setFamilyName(cp.getFamilyName())
        self.setEmail(cp.getEmail())
        self.setAffiliation(cp.getAffiliation())
        self.setAddress(cp.getAddress())
        self.setPhone(cp.getPhone())
        self.setTitle(cp.getTitle())
        self.setFax(cp.getFax())
        self._notifyModification()

    def includeInContribution( self, contrib, id ):
        if self.getContribution() == contrib and self.getId()==id.strip():
            return
        self._contrib = contrib
        self._id = id

    def delete( self ):
        self._contrib = None
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def setId(self, newId):
        self._id = newId

    def getId( self ):
        return self._id

    def getContribution( self ):
        return self._contrib

    def getConference(self):
        return self._contrib.getConference()

    def getLocator(self):
        if self.getContribution() is None:
            return None
        loc=self.getContribution().getLocator()
        loc["authorId"]=self.getId()
        return loc

    def _unindex(self):
        contrib=self.getContribution()
        if contrib is not None:
            conf=contrib.getConference()
            if conf is not None:
                conf.unindexAuthor(self)
                conf.unindexSpeaker(self)

    def _index(self):
        contrib=self.getContribution()
        if contrib is not None:
            conf=contrib.getConference()
            if conf is not None:
                conf.indexAuthor(self)
                conf.indexSpeaker(self)

    @Updates ('MaKaC.conference.ContributionParticipation', 'firstName')
    def setFirstName( self, newName ):
        tmp=newName.strip()
        if tmp==self._firstName:
            return
        self._unindex()
        self._firstName=tmp
        self._index()
        self._notifyModification()

    def getFirstName( self ):
        return self._firstName

    def getName( self ):
        return self._firstName


    @Updates ('MaKaC.conference.ContributionParticipation', 'familyName')
    def setFamilyName( self, newName ):
        tmp=newName.strip()
        if tmp==self._surName:
            return
        self._unindex()
        self._surName=tmp
        self._index()
        self._notifyModification()

    def getFamilyName( self ):
        return self._surName

    def getSurName( self ):
        return self._surName


    @Updates ('MaKaC.conference.ContributionParticipation', 'email')
    def setEmail( self, newMail ):
        tmp=newMail.strip()
        if tmp==self._email:
            return
        self._unindex()
        self._email=newMail.strip()
        self._index()
        self._notifyModification()

    def getEmail( self ):
        return self._email

    @Updates ('MaKaC.conference.ContributionParticipation', 'affiliation')
    def setAffiliation( self, newAffil ):
        self._affiliation = newAffil.strip()
        self._notifyModification()

    def getAffiliation( self ):
        if self._affiliation.lower() == "unknown":
            return ""
        return self._affiliation

    @Updates ('MaKaC.conference.ContributionParticipation', 'address')
    def setAddress( self, newAddr ):
        self._address = newAddr.strip()
        self._notifyModification()

    def getAddress( self ):
        return self._address

    @Updates('MaKaC.conference.ContributionParticipation', 'phone')
    def setPhone( self, newPhone ):
        self._phone = newPhone.strip()
        self._notifyModification()

    def getPhone( self ):
        return self._phone

    @Updates ('MaKaC.conference.ContributionParticipation', 'title')
    def setTitle( self, newTitle ):
        self._title = newTitle.strip()
        self._notifyModification()

    def getTitle( self ):
        return self._title

    @Updates ('MaKaC.conference.ContributionParticipation', 'fax')
    def setFax( self, newFax ):
        self._fax = newFax.strip()
        self._notifyModification()

    def getFax( self ):
        try:
            if self._fax:
                pass
        except AttributeError:
            self._fax=""
        return self._fax

    def getDirectFullName( self ):
        res = self.getDirectFullNameNoTitle()
        if self.getTitle() != "":
            res = "%s %s"%( self.getTitle(), res )
        return res

    def getDirectFullNameNoTitle(self, upper=True):
        familyName = safe_upper(self.getFamilyName()) if upper else self.getFamilyName()
        return "{0} {1}".format(self.getFirstName(), familyName).strip()

    def getFullName(self):
        res = self.getFullNameNoTitle()
        if self.getTitle():
            res = "%s %s" % (self.getTitle(), res)
        return res

    def getFullNameNoTitle(self):
        res = safe_upper(self.getFamilyName())
        if self.getFirstName():
            if res.strip():
                res = "%s, %s" % (res, self.getFirstName())
            else:
                res = self.getFirstName()
        return res

    def getAbrName(self):
        res = self.getFamilyName()
        if self.getFirstName():
            if res:
                res = "%s, " % res
            res = "%s%s." % (res, safe_upper(self.getFirstName()[0]))
        return res

    def isSubmitter(self):
        if self.getContribution() is None:
            return False
        return self.getContribution().canUserSubmit(self)

    def isPendingSubmitter(self):
        if self.getContribution() is None:
            return False
        if self.getContribution().getConference() is None:
            return False
        return self.getContribution().getConference().getPendingQueuesMgr().isPendingSubmitter(self)

    def _cmpFamilyName( cp1, cp2 ):
        o1 = "%s %s"%(cp1.getFamilyName(), cp1.getFirstName())
        o2 = "%s %s"%(cp2.getFamilyName(), cp2.getFirstName())
        o1=o1.lower().strip()
        o2=o2.lower().strip()
        return cmp( o1, o2 )
    _cmpFamilyName=staticmethod(_cmpFamilyName)


class AuthorIndex(Persistent):

    def __init__(self):
        self._idx=OOBTree()

    def _getKey(self,author):
        k = "%s %s %s"%(author.getFamilyName().lower(),author.getFirstName().lower(),author.getEmail().lower())
        return k.strip()

    def index(self,author):
        key=self._getKey(author)
        if not self._idx.has_key(key):
            self._idx[key]=[]
        l = self._idx[key]
        l.append(author)
        self._idx[key] = l
        self.notifyModification()

    def unindex(self,author):
        key=self._getKey(author)
        if self._idx.has_key(key):
            if author in self._idx[key]:
                l = self._idx[key]
                l.remove(author)
                self._idx[key] = l
                if len(self._idx[key])<=0:
                    del self._idx[key]
                self.notifyModification()

    def getParticipations(self):
        return self._idx.values()

    def getById(self, id):
        return self._idx.get(id,None)

    def getByAuthorObj(self, auth):
        return self.getById(self._getKey(auth))

    def getParticipationKeys(self):
        return self._idx.keys()

    def notifyModification(self):
        self._idx._p_changed = 1
        self._p_changed = 1

    def iteritems(self):
        return self._idx.iteritems()

    def match(self, criteria, exact=0):
        self._options = ['organisation', 'surName', 'name', 'email']
        l = []
        for item in self.getParticipations():
            if len(item)>0:
                ok = []
                for f,v in criteria.items():
                    if f == 'organisation' and v != '':
                        if  (exact == 0 and item[0].getAffiliation().lower().find(v.lower()) == -1) or (exact == 1 and item[0].getAffiliation().lower() != v.lower()):
                            ok.append(False)
                        else:
                            ok.append(True)
                    if f == 'surName' and v!= '':
                        if (exact == 0 and item[0].getSurName().lower().find(v.lower()) == -1) or (exact == 1 and item[0].getSurName().lower() != v.lower()):
                            ok.append(False)
                        else:
                            ok.append(True)
                    if f == 'name' and v!= '':
                        if (exact == 0 and item[0].getName().lower().find(v.lower()) == -1) or (exact == 1 and item[0].getName().lower() != v.lower()):
                            ok.append(False)
                        else:
                            ok.append(True)
                    if f == 'email' and v!= '':
                        if (exact == 0 and item[0].getEmail().lower().find(v.lower()) == -1) or (exact == 1 and item[0].getEmail().lower() != v.lower()):
                            ok.append(False)
                        else:
                            ok.append(True)
                if len(ok) > 0 and not False in ok:
                    l.append(item[0])
        return l

class _AuthIdx(Persistent):

    def __init__(self,conf):
        self._conf=conf
        self._idx=OOBTree()

    def _getKey(self,auth):
        return "%s %s"%(auth.getFamilyName().lower(),auth.getFirstName().lower())

    def index(self,auth):
        if auth.getContribution() is None:
            raise MaKaCError( _("Cannot index an author of a contribution which has not been included in a Conference"), _("Author Index"))
        if auth.getContribution().getConference()!=self._conf:
            raise MaKaCError( _("cannot index an author of a contribution which does not belong to this Conference"), _("Author Index"))
        key=self._getKey(auth)
        contribId=str(auth.getContribution().getId())
        if not self._idx.has_key(key):
            self._idx[key]=OIBTree()
        if not self._idx[key].has_key(contribId):
            self._idx[key][contribId]=0
        self._idx[key][contribId]+=1

    def unindex(self,auth):
        if auth.getContribution() is None:
            raise MaKaCError( _("Cannot unindex an author of a contribution which is not included in a conference"), _("Author Index"))
        if auth.getContribution().getConference()!=self._conf:
            raise MaKaCError( _("Cannot unindex an author of a contribution which does not belong to this conference"), _("Author Index"))
        key=self._getKey(auth)
        if not self._idx.has_key(key):
            return
        contribId=str(auth.getContribution().getId())
        self._idx[key][contribId]-=1
        if self._idx[key][contribId]<=0:
            del self._idx[key][contribId]
        if len(self._idx[key])<=0:
            del self._idx[key]

    def match(self,query):
        query=query.lower().strip()
        res=OISet()
        for k in self._idx.keys():
            if k.find(query)!=-1:
                res=union(res,self._idx[k])
        return res


class _PrimAuthIdx(_AuthIdx):

    def __init__(self,conf):
        _AuthIdx.__init__(self,conf)
        for contrib in self._conf.getContributionList():
            for auth in contrib.getPrimaryAuthorList():
                self.index(auth)


class Contribution(CommonObjectBase, Locatable):
    """This class implements a conference contribution, being the concrete
        contributes of the conference participants. The class contains
        necessary attributes to store contribution basic meta data and provides
        the useful operations to access and manage them. A contribution can be
        attached either to a session or to a conference.
    """

    fossilizes(IContributionFossil, IContributionWithSpeakersFossil, IContributionWithSubContribsFossil)

    def __init__(self, **contribData):
        self.parent = None
        self._session = None
        self.id = ""
        self.title = ""
        self._fields = {}
        self.description = ""
        self.startDate = None
        self.duration = timedelta(0)
        self.speakers = []
        self.speakerText = ""
        self.place = None
        self.room = None
        self._boardNumber = ""
        self._resetSchEntry()
        self.__ac = AccessController(self)
        self.materials = {}
        self.__materialGenerator = Counter()
        self._subConts = []
        self.__subContGenerator = Counter()
        self.paper = None
        self.slides = None
        self.video = None
        self.poster = None
        self.minutes = None
        self.reviewing = None
        self._authorGen = Counter()
        self._authors = OOBTree()
        self._primaryAuthors = []
        self._coAuthors = []
        self._speakers = []
        self._track = None
        self._type = None
        self._status = ContribStatusNotSch(self)
        #List of allowed users to submit material
        self._submitters = []
        self._submittersEmail = []
        self._modificationDS = nowutc()
        self._keywords = ""
        self._reviewManager = ReviewManager(self)

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

    def __str__(self):
        if self.parent:
            parentId = self.parent.getId()
        else:
            parentId = None
        return "<Contribution %s:%s@%s>" % (parentId, self.getId(), hex(id(self)))

    def getTimezone(self):
        return self.getConference().getTimezone()

    def getReviewManager(self):
        if not hasattr(self, "_reviewManager"):
            self._reviewManager = ReviewManager(self)
        return self._reviewManager

    def updateNonInheritingChildren(self, elem, delete=False):
        self.getAccessController().updateNonInheritingChildren(elem, delete)
        self.notify_protection_to_owner(elem, delete)

    def notify_protection_to_owner(self, elem, delete=False):
        self.getOwner().updateNonInheritingChildren(elem, delete)

    def getKeywords(self):
        try:
            return self._keywords
        except:
            self._keywords = ""
            return ""

    def setKeywords(self, keywords):
        if type(keywords) is list:
            self._keywords = keywords[0]
        else:
            self._keywords = keywords
        self.notifyModification(cleanCache=False)

    def getFields(self, valueonly=False):
        try:
            if self._fields:
                pass
        except AttributeError:
            self._fields = {}
        if not valueonly:
            return self._fields
        else:
            return dict((k, v.value if isinstance(v, AbstractFieldContent) else v) for k, v in self._fields.iteritems())

    def removeField(self, field):
        if field in self.getFields():
            del self.getFields()[field]
            self.notifyModification()

    def setField(self, fid, v):
        if isinstance(v, AbstractFieldContent):
            v = v.value
        try:
            self.getFields()[fid].value = v

        # `AttritbuteError` may happen if the field is not yet an AbstractFieldContent
        # (lazy migration)
        # `KeyError` means that the attribute doesn't exist in the contrib, in which
        # case it should be created anyway
        except (AttributeError, KeyError):
            afm = self.getConference().getAbstractMgr().getAbstractFieldsMgr()
            for f in afm.getFields():
                if f.getId() == fid:
                    self.getFields()[fid] = AbstractFieldContent(f, v)
                    break
        self.notifyModification()

    def getField(self, field):
        if field in self.getFields():
            value = self.getFields()[field]
            if type(value) is list:
                return "".join(value)
            elif value is None:
                return ""
            else:
                return value
        else:
            return ""

    def getLogInfo(self):
        data = {}
        data["subject"] = self.getTitle()
        data["id"] = self.id
        data["title"] = self.title
        data["parent title"] = self.parent.getTitle()
        if self._session is not None:
            data["session title"] = self._session.getTitle()
        data["description"] = self.description
        if self.getConference():
            afm = self.getConference().getAbstractMgr().getAbstractFieldsMgr()
            for f in afm.getFields():
                id = f.getId()
                data[id] = self.getField(id)
        data["start date"] = "%s" % self.startDate
        data["duration"] = "%s" % self.duration
        if self._track is not None:
            data["track"] = self._track.getTitle()
        if self._type is not None:
            data["type"] = self._type
        data["speaker text"] = self.speakerText
        if self.place is not None:
            data["place"] = self.place.getName()
        if self.room is not None:
            data["room"] = self.room.getName()
        data["board number"] = self._boardNumber
        for sc in self.getSubContributionList():
            data["subcontribution %s" % sc.getId()] = sc.getTitle()
        for pa in self._primaryAuthors:
            data["primary author %s" % pa.getId()] = pa.getFullName()
        for ca in self._coAuthors:
            data["co-author %s" % ca.getId()] = ca.getFullName()
        for sp in self._speakers:
            data["speaker %s" % sp.getId()] = sp.getFullName()
        for s in self.getSubmitterList():
            if isinstance(s, MaKaC.user.Avatar):
                data["submitter"] = s.getFullName()
            else:
                data["submitter"] = s.getName()
        return data

    def setValues(self, data, check=2, moveEntriesBelow=0):
        """Sets all the values of the current contribution object from a
            dictionary containing the following key-value pairs:
                title-(str)
                description-(str)
                locationName-(str) => name of the location, if not specified
                        it will be set to the parent location name.
                locationAddress-(str)
                roomName-(str) => name of the room, if not specified it will
                    be set to the parent room name.
                year, month, day, sHour, sMinute - (str) => components of the
                        starting date of the session, if not specified it will
                        be set to now.
                durationHours, durationMinutes - (str)
                speakers - (str)
                check parameter:
                    0: no check at all
                    1: check and raise error in case of problem
                    2: check and adapt the owner dates
                moveEntries:
                    0: no move
                    1: moveEntries below the contribution
           Please, note that this method sets ALL values which means that if
            the given dictionary doesn't contain any of the keys the value
            will set to a default value.
        """

        # In order to move the entries below, it is needed to know the diff (we have to move them)
        # and the list of entries to move. It's is needed to take those datas in advance because they
        # are going to be modified before the moving.
        if moveEntriesBelow == 1:
            oldStartDate = copy.copy(self.getStartDate())
            oldDuration = copy.copy(self.getDuration())
            i = self.getSchEntry().getSchedule().getEntries().index(self.getSchEntry())+1
            entriesList = self.getSchEntry().getSchedule().getEntries()[i:]
        if data.has_key("title"):
            self.setTitle(data["title"])
        if data.has_key("keywords"):
            self.setKeywords(data["keywords"])
        if data.has_key("description"):
            self.setDescription(data["description"])
        if data.has_key("type") and self.getConference():
            self.setType(self.getConference().getContribTypeById(data["type"]))
        if self.getConference():
            afm = self.getConference().getAbstractMgr().getAbstractFieldsMgr()
            for f in afm.getFields():
                id = f.getId()
                if data.has_key("f_%s" % id):
                    self.setField(id, data["f_%s" % id])

        if "locationName" in data:
            loc = self.getOwnLocation()
            if not loc:
                loc = CustomLocation()
            self.setLocation(loc)
            loc.setName(data["locationName"])
            loc.setAddress(data.get("locationAddress", ""))
        else:
            self.setLocation(None)

        #same as for the location
        if "roomName" in data:
            room = self.getOwnRoom()
            if not room:
                room = CustomRoom()
            self.setRoom(room)
            room.setName(data["roomName"])
            room.retrieveFullName(data.get("locationName", ""))
        else:
            self.setRoom(None)

        tz = 'UTC'
        if self.getConference():
            tz = self.getConference().getTimezone()
        if data.get("targetDay", "") != "" and data.get("sHour", "") != "" and data.get("sMinute", "") != "" and check == 2:
            ############################################
            # Fermi timezone awareness                 #
            ############################################
            me = timezone(tz).localize(datetime(int(data["targetDay"][0:4]),
                                                int(data["targetDay"][5:7]), int(data["targetDay"][8:])))
            sdate = timezone(tz).localize(datetime(me.year, me.month,
                                                   me.day, int(data["sHour"]), int(data["sMinute"])))
            self.setStartDate(sdate.astimezone(timezone('UTC')), check=2)
        if data.get("sYear", "") != "" and data.get("sMonth", "") != "" and \
                data.get("sDay", "") != "" and data.get("sHour", "") != "" and \
                data.get("sMinute", "") != "":
            self.setStartDate(timezone(tz).localize(datetime(int(data["sYear"]),
                              int(data["sMonth"]), int(data["sDay"]),
                              int(data["sHour"]),  int(data["sMinute"]))).astimezone(timezone('UTC')),
                              check=2)
            ############################################
            # Fermi timezone awareness(end)            #
            ############################################
        if data.get("durTimedelta", "") != "":
            self.setDuration(check=check, dur=data["durTimedelta"])
        elif data.get("durHours", "") != "" and data.get("durMins", "") != "":
            self.setDuration(data["durHours"], data["durMins"], check)
        else:
            h = data.get("durHours", "").strip()
            m = data.get("durMins", "").strip()
            if h != "" or m != "":
                h = h or "0"
                m = m or "0"
                if h != "0" or m != "0":
                    self.setDuration(int(h), int(m), check)
        if data.has_key("boardNumber"):
            self.setBoardNumber(data.get("boardNumber", ""))
        if moveEntriesBelow == 1:
            diff = (self.getStartDate() - oldStartDate) + (self.getDuration() - oldDuration)
            self.getConference().getSchedule().moveEntriesBelow(diff, entriesList)
        self.notifyModification()

    def clone(self, parent, options, deltaTime = 0):
        cont = Contribution()
        parent.addContribution(cont)
        cont.setTitle( self.getTitle() )
        cont.setDescription( self.getDescription() )
        for k, v in self.getFields().items():
            cont.setField(k, v)
        cont.setKeywords( self.getKeywords() )
        if deltaTime == 0 :
            deltaTime = parent.getStartDate() - self.getOwner().getStartDate()

        startDate = None
        if self.startDate is not None :
            startDate = self.getStartDate() + deltaTime
        cont.setStartDate( startDate )

        cont.setDuration( dur=self.getDuration() )

        if self.getOwnLocation() is not None:
            cont.setLocation(self.getOwnLocation().clone())
        if self.getOwnRoom() is not None:
            cont.setRoom(self.getOwnRoom().clone())
        cont.setBoardNumber(self.getBoardNumber())
        cont.setReportNumberHolder(self.getReportNumberHolder().clone(self))

        cont.setStatus(self.getCurrentStatus())

        if self.getType() is not None :
            for ct in cont.getConference().getContribTypeList() :
                if ct.getName() == self.getType().getName() :
                    cont.setType(ct)
                    break

        if options.get("tracks", False) :
            if self.getTrack() is not None :
                for tr in cont.getConference().getTrackList() :
                    if tr.getTitle() == self.getTrack().getTitle() :
                        cont.setTrack(tr)
                        break
            else :
                cont.setTrack(None)

        if options.get("access", False) :
            cont.setProtection(self.getAccessController()._getAccessProtection())
            for u in self.getAllowedToAccessList() :
                cont.grantAccess(u)
            for mgr in self.getManagerList() :
                cont.grantModification(mgr)
            for sub in self.getSubmitterList() :
                cont.grantSubmission(sub)
            for domain in self.getDomainList():
                cont.requireDomain(domain)

        if options.get("authors", False) :
            for a in self.getPrimaryAuthorList() :
                cont.addPrimaryAuthor(a.clone())
            for ca in self.getCoAuthorList() :
                cont.addCoAuthor(ca.clone())
            for sp in self.getSpeakerList():
                cont.newSpeaker(sp.clone())
            cont.setSpeakerText(self.getSpeakerText())

        if options.get("materials", False) :
            for m in self.getMaterialList() :
                cont.addMaterial(m.clone(cont))
            if self.getPaper() is not None:
                cont.setPaper(self.getPaper().clone(cont))
            if self.getSlides() is not None:
                cont.setSlides(self.getSlides().clone(cont))
            if self.getVideo() is not None:
                cont.setVideo(self.getVideo().clone(cont))
            if self.getPoster() is not None:
                cont.setPoster(self.getPoster().clone(cont))
            if self.getMinutes() is not None:
                cont.setMinutes(self.getMinutes().clone(cont))
            if self.getReviewing() is not None:
                cont.setReviewing(self.getReviewing().clone(cont))

        if options.get("subcontribs", False) :
            for sc in self.getSubContributionList() :
                cont.addSubContribution(sc.clone(cont, self, options))
        return cont

    def notifyModification( self, date = None, raiseEvent = True, cleanCache = True):
        self.setModificationDate(date)

        if raiseEvent:
            self._notify('infoChanged')


        if cleanCache:
            self.cleanCache()

        parent = self.getParent()
        if parent:
            parent.setModificationDate()
        self._p_changed = 1

    def cleanCache(self, cleanConference = True):
        # Do not clean cache if already cleaned
        if not ContextManager.get('clean%s'%self.getUniqueId(), False):
            ScheduleToJson.cleanCache(self)
            ContextManager.set('clean%s'%self.getUniqueId(), cleanConference)

    def getCategoriesPath(self):
        return self.getConference().getCategoriesPath()

    def getModifKey( self ):
        return self.getConference().getModifKey()

    def getAccessKey( self ):
        return self.getConference().getAccessKey()

    def getLocator( self ):
        """Gives back a globaly unique identification encapsulated in a Locator
            object for the contribution instance
        """
        if self.getConference() == None:
            return Locator()
        lconf = self.getConference().getLocator()
        if self.getSession() is not None:
            lconf["sessionId"] = self.getSession().getId()
        lconf["contribId"] = self.getId()
        return lconf

    def _setConference( self, conf ):
        self.parent = conf

    def _setId( self, id ):
        self.id = id

    def includeInConference( self, conf, id ):
        """sets the conference of a contribution
        """
        if self.getConference() is not None:
            #raise MaKaCError("the contribution is already included in a conference")
            pass
        else:
            self._setConference( conf )
            self._setId( id )

    def delete( self ):
        """deletes a contribution and all of its subitems
        """

        oldParent = self.getConference()

        if oldParent != None:
            self._notify('deleted', oldParent)

            self.setTrack(None)
            for mat in self.getMaterialList():
                self.removeMaterial(mat)
            self.removePaper()
            self.removeSlides()
            self.removeVideo()
            self.removePoster()
            self.removeMinutes()
            self.removeReviewing()

            self.notify_protection_to_owner(self, delete=True)

            self.setSession(None)

            while len(self.getSubContributionList()) > 0:

                sc = self.getSubContributionList()[0]

                self.removeSubContribution(sc)


            # delete it from parent session (if it exists)
            if self.getOwner() != self.getConference():

                self.getOwner().removeContribution( self )

            # (always) delete it from the parent conference
            self.getConference().removeContribution( self, callDelete=False )

            self._setConference( None )

            self.setStatus(ContribStatusNone(self))

            TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def setId( self, newId ):
        self._setId(newId)

    def getId( self ):
        return self.id

    def getUniqueId( self ):
        """returns (string) the unique identifier of the item"""
        """used mainly in the web session access key table"""
        return "%st%s" % (self.getConference().getUniqueId(),self.id)

    def setTitle( self, newTitle, notify = True ):
        oldTitle = self.title
        self.title = newTitle.strip()

        if notify:
            self._notify('contributionTitleChanged', oldTitle, newTitle)
            self.notifyModification()

    def getTitle( self ):
        if self.title.strip() == "":
            return "(no title)"
        return self.title

    def getDescription(self):
        return str(self.getField("content"))

    def setDescription(self, desc):
        self.setField("content", desc)

    def setParent(self,parent):
        self.parent=parent
        self.notifyModification(cleanCache = False)
        if self.parent==None:
            return

    def getParent( self ):
        if self.getSession() is not None:
            return self.getSession()
        return self.getConference()

    def getOwner( self ):
        return self.getParent()

    def setOwner(self, owner):
        self.setParent(owner)

    def getConference( self ):
        return self.parent

    def getSession( self ):
        try:
            if self._session:
                pass
        except AttributeError:
            self._session=None
        return self._session

    def setSession(self,session):
        if self.getSession()==session:
            return
        if self.isScheduled():
            schEntry=self.getSchEntry()
            schEntry.getSchedule().removeEntry(schEntry)
        oldSession=self.getSession()
        if oldSession is not None:
            oldSession.removeContribution(self)
        self._session=session
        if session is not None:
            session.addContribution(self)

    def getContribution(self):
        return self

    def _resetSchEntry(self):
        self.__schEntry=ContribSchEntry(self)

    def getSchEntry(self):
        if self.__schEntry is None or \
                        not isinstance(self.__schEntry,ContribSchEntry):
            self._resetSchEntry()
        return self.__schEntry

    def isScheduled(self):
        #For the moment we do it like this
        return self.getSchEntry().getSchedule() is not None

    def isWithdrawn(self):
        return isinstance(self.getCurrentStatus(), ContribStatusWithdrawn)

    def getLocationParent(self):
        """
        Returns the object from which the room/location
        information should be inherited
        """
        if not self.getConference().getEnableSessionSlots() and self.getSession():
            return self.getSession()
        if self.isScheduled():
            return self.getSchEntry().getSchedule().getOwner()
        return self.getOwner()

    def getOwnLocation(self):
        return self.place

    def setLocation(self, newLocation):
        oldLocation = self.place
        self.place = newLocation
        self._notify('locationChanged', oldLocation, newLocation)
        self.notifyModification()

    def getOwnRoom(self):
        return self.room

    def setRoom(self, newRoom):
        oldRoom = self.room
        self.room = newRoom
        self._notify('roomChanged', oldRoom, newRoom)
        self.notifyModification()

    def setBoardNumber(self, newBoardNum):
        self._boardNumber=str(newBoardNum).strip()

    def getBoardNumber(self):
        try:
            if self._boardNumber:
                pass
        except AttributeError:
            self._boardNumber=""
        return self._boardNumber

    def verifyStartDate(self, sDate, check=2):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""

        tz = timezone(self.getConference().getTimezone())
        if self.getSchEntry().getSchedule():
            owner = self.getSchEntry().getSchedule().getOwner()
        else:
            owner = self.getOwner()
        if sDate < owner.getStartDate():
            if check == 1:
                raise ParentTimingError(_("The contribution <i>\"%s\"</i> cannot start before (%s) its parent (%s)") %\
                    (self.getTitle(), sDate.astimezone(tz).strftime('%Y-%m-%d %H:%M'),\
                    owner.getStartDate().astimezone(tz).strftime('%Y-%m-%d %H:%M')),\
                    _("Contribution"))
            if check == 2:
                ContextManager.get('autoOps').append((self, "OWNER_START_DATE_EXTENDED",
                                                      owner, sDate.astimezone(tz)))
                owner.setDates(sDate,owner.getEndDate(), check)
        if sDate > owner.getEndDate():
            if check == 1:
                raise ParentTimingError(_("The contribution <i>\"%s\"</i> cannot start after (%s) its parent end date(%s)") %\
                    (self.getTitle(), sDate.astimezone(tz).strftime('%Y-%m-%d %H:%M'),\
                    owner.getEndDate().astimezone(tz).strftime('%Y-%m-%d %H:%M')),\
                    _("Contribution"))
            if check == 2:
                owner.setEndDate(sDate+self.getDuration(),check)
        # Check that after modifying the start date, the end date is still within the limits of the slot
        if self.getDuration() and sDate + self.getDuration() > owner.getEndDate():
            if check==1:
                raise ParentTimingError("The contribution cannot end after (%s) its parent ends (%s)"%\
                        ((sDate + self.getDuration()).astimezone(tz).strftime('%Y-%m-%d %H:%M'),\
                        owner.getAdjustedEndDate().strftime('%Y-%m-%d %H:%M')),\
                         _("Contribution"))
            elif check==2:
                # update the schedule
                owner.setEndDate(sDate + self.getDuration(),check)
                ContextManager.get('autoOps').append((self, "OWNER_END_DATE_EXTENDED",
                                                          owner, owner.getAdjustedEndDate()))

    def setStartDate(self, newDate, check=2, moveEntries=0):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""
        if newDate == None:
            self.startDate=None
            return
        if not newDate.tzname():
            raise MaKaCError("date should be timezone aware")

        if newDate != None and check != 0:
            self.verifyStartDate(newDate, check)
        self._notify("contributionUnscheduled")
        self.startDate=copy.copy(newDate)
        self._notify("contributionScheduled")
        self.getSchEntry().synchro()
        self.notifyModification()

    def getStartDate(self):
        return self.startDate

    def getAdjustedStartDate(self, tz=None):
        if self.getStartDate() is None:
            return None
        if not tz:
            tz = self.getConference().getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        return self.getStartDate().astimezone(timezone(tz))

    def getEndDate(self):
        if self.getStartDate() is None:
            return None
        return self.getStartDate()+self.getDuration()

    def getAdjustedEndDate(self, tz=None):
        if not tz:
            tz = self.getConference().getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        if self.getEndDate():
            return self.getEndDate().astimezone(timezone(tz))
        return None

    def getDuration(self):
        return self.duration

    def verifyDuration(self, check=2):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""

        tz = timezone(self.getConference().getTimezone())

        endDate = self.getEndDate()

        if self.getSchEntry().getSchedule() is not None:
            owner = self.getSchEntry().getSchedule().getOwner()
            if endDate > owner.getEndDate():
                if check==1:
                    raise ParentTimingError(_("The contribution \"%s\" ending date (%s) has to fit between its parent's dates (%s - %s)") %\
                            (self.getTitle(), endDate.astimezone(tz).strftime('%Y-%m-%d %H:%M'),\
                            owner.getStartDate().astimezone(tz).strftime('%Y-%m-%d %H:%M'),\
                            owner.getEndDate().astimezone(tz).strftime('%Y-%m-%d %H:%M')),\
                            _("Contribution"))
                elif check==2:
                    ContextManager.get('autoOps').append((self, "OWNER_END_DATE_EXTENDED",
                                                          owner, self.getAdjustedEndDate()))
                    owner.setEndDate(endDate, check)

    def setDuration(self, hours=0, minutes=15, check=2, dur=0):
        """check parameter:
            0: no check at all
            1: check and raise error in case of problem
            2: check and adapt the owner dates"""

        if dur!=0:
            self.duration=dur
        else:
            self.duration=timedelta(hours=int(hours),minutes=int(minutes))
        if check != 0:
            self.verifyDuration(check)
        self.getSchEntry().synchro()
        self.notifyModification()

    def _addAuthor(self, part):
        """
        """
        try:
            if self._authors:
                pass
        except AttributeError:
            self._authors = OOBTree()
        try:
            if self._authorGen:
                pass
        except AttributeError:
            self._authorGen=Counter()
        newId = part.getId()
        if newId == "":
            newId = str( self._authorGen.newCount() )
        self._authors[newId] = part
        part.includeInContribution( self, newId )

    def _removeAuthor(self, part):
        """
        """
        try:
            if self._authors:
                pass
        except AttributeError:
            self._authors = OOBTree()
        if not self._authors.has_key( part.getId() ):
            return
        del self._authors[ part.getId() ]
        if not self.isSpeaker(part):
            part.delete()

    def addPrimaryAuthor(self, part, index=None):
        """
        """
        try:
            if self._primaryAuthors:
                pass
        except AttributeError:
            self._primaryAuthors = []
        self._addAuthor( part )
        if index is not None:
            self._primaryAuthors.insert(index, part)
        else:
            self._primaryAuthors.append( part )
        if self.getConference() is not None:
            self.getConference().indexAuthor(part)
        self.notifyModification(cleanCache = False)

    def removePrimaryAuthor(self, part, removeSpeaker=1, removePendingSubm=True):
        """
        """
        try:
            if self._primaryAuthors:
                pass
        except AttributeError:
            self._primaryAuthors = []
        if part not in self._primaryAuthors:
            return
        if self.getConference() is not None:
            self.getConference().unindexAuthor(part)
        self._primaryAuthors.remove( part )
        if removeSpeaker:
            self.removeSpeaker( part )
        self._removeAuthor( part )
        if removePendingSubm:
            #--Pending queue: remove pending participant waiting to became submitter if anything
            self.getConference().getPendingQueuesMgr().removePendingSubmitter(part)
            #--
        self.notifyModification(cleanCache = False)

    def recoverPrimaryAuthor(self, pa, isPendingSubmitter):
        self.addPrimaryAuthor(pa)
        pa.recover()
        if isPendingSubmitter:
            self.getConference().getPendingQueuesMgr().addPendingSubmitter(pa, False)

    def isPrimaryAuthor(self, part):
        """
        """
        try:
            if self._primaryAuthors:
                pass
        except AttributeError:
            self._primaryAuthors = []
        return part in self._primaryAuthors

    def isCoAuthor(self, part):
        try:
            if self._coAuthors:
                pass
        except AttributeError:
            self._coAuthors = []
        return part in self._coAuthors

    def isPrimaryAuthorByEmail(self, email):
        for prAuthor in self.getPrimaryAuthorList():
            if prAuthor.getEmail() == email:
                return True
        return False

    def isCoAuthorByEmail(self, email):
        for coAuthor in self.getCoAuthorList():
            if coAuthor.getEmail() == email:
                return True
        return False

    def isSpeakerByEmail(self, email):
        for speaker in self.getSpeakerList():
            if speaker.getEmail() == email:
                return True
        return False

    def changePosPrimaryAuthor(self, part, index):
        """
        """
        try:
            if self._primaryAuthors:
                pass
        except AttributeError:
            self._primaryAuthors=[]
        if not part in self._primaryAuthors:
            return
        self._primaryAuthors.remove(part)
        self._primaryAuthors.insert(index,part)
        self.notifyModification(cleanCache = False)

    def upPrimaryAuthor(self, part):
        """
        """
        try:
            if self._primaryAuthors:
                pass
        except AttributeError:
            self._primaryAuthors=[]
        try:
            idx=self._primaryAuthors.index(part)
        except ValueError:
            return
        if idx==0:
            return
        self._primaryAuthors.remove(part)
        self._primaryAuthors.insert(idx-1,part)
        self.notifyModification(cleanCache=False)

    def downPrimaryAuthor(self, part):
        """
        """
        try:
            if self._primaryAuthors:
                pass
        except AttributeError:
            self._primaryAuthors=[]
        try:
            idx=self._primaryAuthors.index(part)
        except ValueError:
            return
        if idx>len(self._primaryAuthors):
            return
        self._primaryAuthors.remove(part)
        self._primaryAuthors.insert(idx+1,part)
        self.notifyModification(cleanCache = False)

    def newAuthorsList(self, prAuthors, coAuthors):
        ''' calculate new lists of both kind of authors, because something has
            been changed the position by drag and drop '''
        newPrList = self.calculateNewAuthorList(prAuthors, "prAuthor")
        newCoList = self.calculateNewAuthorList(coAuthors, "coAuthor")
        self.setPrimaryAuthorList(newPrList)
        self.setCoAuthorList(newCoList)

    def calculateNewAuthorList(self, list, kind):
        result = []
        if kind == "prAuthor":
            for auth in list:
                author = self.getPrimaryAuthorById(auth['id'])
                if author:
                    result.append(author)
                else:
                    author = self.getCoAuthorById(auth['id'])
                    if author:
                        result.append(author)

        elif kind == "coAuthor":
            for auth in list:
                author = self.getCoAuthorById(auth['id'])
                if author:
                    result.append(author)
                else:
                    author = self.getPrimaryAuthorById(auth['id'])
                    if author:
                        result.append(author)
        return result

    def getPrimaryAuthorById(self, authorId):
        for author in self.getPrimaryAuthorList():
            if authorId == author.getId():
                return author
        return None

    def getCoAuthorById(self, authorId):
        for author in self.getCoAuthorList():
            if authorId == author.getId():
                return author
        return None

    def setPrimaryAuthorList(self, l):
        self._primaryAuthors = l
        self.notifyModification(cleanCache = False)

    def setCoAuthorList(self, l):
        self._coAuthors = l
        self.notifyModification(cleanCache = False)

    def changePosCoAuthor(self, part, index):
        """
        """
        try:
            if self._coAuthors:
                pass
        except AttributeError:
            self._coAuthors=[]
        if not part in self._coAuthors:
            return
        self._coAuthors.remove(part)
        self._coAuthors.insert(index,part)
        self.notifyModification(cleanCache = False)

    def upCoAuthor(self, part):
        """
        """
        try:
            if self._coAuthors:
                pass
        except AttributeError:
            self._coAuthors=[]
        try:
            idx=self._coAuthors.index(part)
        except ValueError:
            return
        if idx==0:
            return
        self._coAuthors.remove(part)
        self._coAuthors.insert(idx-1,part)
        self.notifyModification(cleanCache = False)

    def downCoAuthor(self, part):
        """
        """
        try:
            if self._coAuthors:
                pass
        except AttributeError:
            self._coAuthors=[]
        try:
            idx=self._coAuthors.index(part)
        except ValueError:
            return
        if idx>len(self._coAuthors):
            return
        self._coAuthors.remove(part)
        self._coAuthors.insert(idx+1,part)
        self.notifyModification(cleanCache = False)

    def getPrimaryAuthorList(self):
        """
        """
        try:
            if self._primaryAuthors:
                pass
        except AttributeError:
            self._primaryAuthors = []
        return self._primaryAuthors

    getPrimaryAuthorsList = getPrimaryAuthorList

    def getAuthorList(self):
        """
        """
        try:
            if self._authors:
                pass
        except  AttributeError:
            self._authors = OOBTree()
        return self._authors.values()

    def getAllAuthors(self):
        """ This method returns a list composed by the primary authors
            and co-authors. The different with getAuthorList() is the type
            of the output.
        """
        return self.getPrimaryAuthorList() + self.getCoAuthorList()

    def addCoAuthor(self, part, index=None):
        """
        """
        try:
            if self._coAuthors:
                pass
        except AttributeError:
            self._coAuthors = []
        self._addAuthor( part )
        if index is not None:
            self._coAuthors.insert(index, part)
        else:
            self._coAuthors.append( part )
        if self.getConference() is not None:
            self.getConference().indexAuthor(part)
        self.notifyModification(cleanCache = False)

    def removeCoAuthor(self, part, removeSpeaker=1, removePendingSubm=True):
        """
        """
        try:
            if self._coAuthors:
                pass
        except AttributeError:
            self._coAuthors = []
        if part not in self._coAuthors:
            return
        if self.getConference() is not None:
            self.getConference().unindexAuthor(part)
        self._coAuthors.remove( part )
        if removeSpeaker:
            self.removeSpeaker( part )
        self._removeAuthor( part )
        if removePendingSubm:
            #--Pending queue: remove pending participant waiting to became submitter if anything
            self.getConference().getPendingQueuesMgr().removePendingSubmitter(part)
            #--
        self.notifyModification(cleanCache = False)

    def recoverCoAuthor(self, ca, isPendingSubmitter):
        self.addCoAuthor(ca)
        ca.recover()
        if isPendingSubmitter:
            self.getConference().getPendingQueuesMgr().addPendingSubmitter(ca, False)

    def getCoAuthorList(self):
        """
        """
        try:
            if self._coAuthors:
                pass
        except AttributeError:
            self._coAuthors = []
        return self._coAuthors

    def getAuthorById(self, authorId):
        """
        """
        try:
            if self._authors:
                pass
        except AttributeError:
            self._authors = OOBTree()
        return self._authors.get( authorId.strip(), None )

    def isAuthor(self, part):
        """
        """
        try:
            if self._authors:
                pass
        except AttributeError:
            self._authors = OOBTree()
        return self._authors.has_key( part.getId() )

    def getSpeakerById(self, authorId):
        """
        """
        try:
            if self._speakers:
                pass
        except AttributeError:
            self._speakers = []
        for spk in self._speakers:
            if spk.getId() == authorId:
                return spk
        return None

    def changePosSpeaker(self, part, index):
        """
        """
        try:
            if self._speakers:
                pass
        except AttributeError:
            self._speakers = []
        if not part in self._speakers:
            return
        self._speakers.remove(part)
        self._speakers.insert(index,part)
        self.notifyModification()

    def addSpeaker(self, part, index=None):
        """
        Adds a speaker (ContributionParticipation object) to the contribution
        forcing it to be one of the authors of the contribution
        """
        try:
            if self._speakers:
                pass
        except AttributeError:
            self._speakers = []
        if not self.isAuthor( part ):
            raise MaKaCError( _("The Specified speaker is not the Author"), _("Contribution"))
        if index is not None:
            self._speakers.insert(index, part)
        else:
            self._speakers.append( part )
        if self.getConference() is not None:
            self.getConference().indexSpeaker(part)
        self.notifyModification()

    def newSpeaker(self, part):
        """
        Adds a new speaker (ContributionParticipation object) to the contribution
        setting the speakers ID and the fact it belongs to that contribution
        """
        try:
            if self._speakers:
                pass
        except AttributeError:
            self._speakers = []
        try:
            if self._authorGen:
                pass
        except AttributeError:
            self._authorGen=Counter()
        self._speakers.append( part )
        newId = part.getId()
        if newId == "":
            newId = str( self._authorGen.newCount() )
        part.includeInContribution(self, newId)
        if self.getConference() is not None:
            self.getConference().indexSpeaker(part)
        self.notifyModification()

    def removeSpeaker(self, part):
        """
        """
        try:
            if self._speakers:
                pass
        except AttributeError:
            self._speakers = []
        if part not in self._speakers:
            return
        self._speakers.remove( part )
        if self.getConference() is not None:
            self.getConference().unindexSpeaker(part)
        if part not in self.getAuthorList():
            part.delete()
            #--Pending queue: remove pending participant waiting to became submitter if anything
            self.getConference().getPendingQueuesMgr().removePendingSubmitter(part)
            #--
        self.notifyModification()

    def recoverSpeaker(self, spk, isPendingSubmitter):
        self.newSpeaker(spk)
        spk.recover()
        if isPendingSubmitter:
            self.getConference().getPendingQueuesMgr().addPendingSubmitter(spk, False)

    def isSpeaker(self, part):
        """
        """
        try:
            if self._speakers:
                pass
        except AttributeError:
            self._speakers = []
        return part in self._speakers

    def getSpeakerList(self):
        """
        """
        try:
            if self._speakers:
                pass
        except AttributeError:
            self._speakers = []
        return self._speakers

    def getSpeakerText(self):
        #to be removed
        try:
            if self.speakerText:
                pass
        except AttributeError, e:
            self.speakerText = ""
        return self.speakerText

    def setSpeakerText(self, newText):
        self.speakerText = newText.strip()

    def appendSpeakerText(self, newText):
        self.setSpeakerText("%s, %s" % (self.getSpeakerText(), newText.strip()))

    def canIPAccess(self, ip):
        if not self.__ac.canIPAccess( ip ):
            return False
        if self.getOwner() != None:
            return self.getOwner().canIPAccess(ip)
        return True

    def isProtected(self):
        # tells if a contribution is protected or not
        return (self.hasProtectedOwner() + self.getAccessProtectionLevel()) > 0

    def getAccessProtectionLevel(self):
        return self.__ac.getAccessProtectionLevel()

    def isItselfProtected(self):
        return self.__ac.isItselfProtected()

    def hasAnyProtection(self):
        """Tells whether a contribution has any kind of protection over it:
            access or domain protection.
        """
        if self.__ac.isProtected():
            return True
        if self.getDomainList():
            return True
        if self.getAccessProtectionLevel() == -1:
            return False
        if self.getOwner():
            return self.getOwner().hasAnyProtection()
        else:
            return False

    def hasProtectedOwner(self):
        if self.getOwner() != None:
            return self.getOwner().isProtected()
        return False

    def setProtection(self, private):

        oldValue = 1 if self.isProtected() else -1

        self.__ac.setProtection( private )
        self.notify_protection_to_owner(self)

        if oldValue != private:
            # notify listeners
            self._notify('protectionChanged', oldValue, private)

    def grantAccess(self, prin):
        self.__ac.grantAccess( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.linkTo(self, "access")
        self.notifyModification(raiseEvent = False)

    def revokeAccess( self, prin ):
        self.__ac.revokeAccess( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "access")
        self.notifyModification(raiseEvent = False)

    def canView( self, aw ):
        """tells whether the specified user has access to the current object
            or any of its sub-objects
        """
        if self.canAccess( aw ):
            return True
        if any(self._notify("isPluginAdmin", {"user": aw.getUser(), "plugins": "any"}) +
               self._notify("isPluginTypeAdmin", {"user": aw.getUser()})):
            return True
        ################################################################################################
        for sc in self.getSubContributionList():
            if sc.canView( aw ):
                return True
        return False

    def isAllowedToAccess( self, user ):
        if not user:
            return False
        return (not self.isItselfProtected() and self.getOwner().isAllowedToAccess( user )) or\
                self.__ac.canUserAccess( user ) or\
                self.canUserModify( user ) or \
                self.canUserSubmit(user)

    def canAccess( self, aw ):
        # Allow harvesters (Invenio, offline cache) to access
        # protected pages
        if self.__ac.isHarvesterIP(aw.getIP()):
            return True
        #####################################################

        if self.canModify(aw):
            return True

        if not self.canIPAccess(aw.getIP()) and not self.isAllowedToAccess( aw.getUser() ):
            return False
        if not self.isProtected():
            return True
        flag = self.isAllowedToAccess( aw.getUser() )
        return flag or self.getConference().canKeyAccess(aw)

    def grantModification( self, prin ):
        self.__ac.grantModification( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.linkTo(self, "manager")
        self.notifyModification(raiseEvent = False)

    def revokeModification( self, prin ):
        self.__ac.revokeModification( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "manager")
        self.notifyModification(raiseEvent = False)

    def canModify( self, aw ):
        return self.canUserModify( aw.getUser() ) or self.getConference().canKeyModify( aw )

    def canUserModify( self, av ):
        """Tells whether a user is allowed to modify the current contribution:
            only if the user is granted to modify the contribution or the user
            can modify any of its upper objects (i.e. conference or session).
        """
        return self.getParent().canUserModify( av ) or self.__ac.canModify( av )

    def getManagerList( self ):
        return self.__ac.getModifierList()

    def getAllowedToAccessList( self ):
        return self.__ac.getAccessList()

    def addMaterial( self, newMat ):
        newMat.setId( str(self.__materialGenerator.newCount()) )
        newMat.setOwner( self )
        self.materials[ newMat.getId() ] =  newMat
        self.notifyModification()

    def removeMaterial(self, mat):
        if mat.getId() in self.materials.keys():
            mat.delete()
            self.materials[mat.getId()].setOwner(None)
            del self.materials[ mat.getId() ]
            self.notifyModification()
        elif mat.getId().lower() == 'paper':
            self.removePaper()
        elif mat.getId().lower() == 'slides':
            self.removeSlides()
        elif mat.getId().lower() == 'minutes':
            self.removeMinutes()
        elif mat.getId().lower() == 'video':
            self.removeVideo()
        elif mat.getId().lower() == 'poster':
            self.removePoster()
        elif mat.getId().lower() == 'reviewing':
            self.removeReviewing()

    def recoverMaterial(self, recMat):
    # Id must already be set in recMat.
        recMat.setOwner( self )
        self.materials[ recMat.getId() ] =  recMat
        recMat.recover()
        self.notifyModification()

    def getMaterialRegistry(self):
        """
        Return the correct material registry for this type
        """
        from MaKaC.webinterface.materialFactories import ContribMFRegistry
        return ContribMFRegistry

    def getMaterialById( self, matId ):
        if matId.lower() == 'paper':
            return self.getPaper()
        elif matId.lower() == 'slides':
            return self.getSlides()
        elif matId.lower() == 'video':
            return self.getVideo()
        elif matId.lower() == 'poster':
            return self.getPoster()
        elif matId.lower() == 'minutes':
            return self.getMinutes()
        elif self.materials.has_key(matId):
            return self.materials[ matId ]
        return None

    def getMaterialList( self ):
        return self.materials.values()

    def getAllMaterialList(self, sort=True):
        l = self.getMaterialList()
        if self.getPaper():
            l.append( self.getPaper() )
        if self.getSlides():
            l.append( self.getSlides() )
        if self.getVideo():
            l.append( self.getVideo() )
        if self.getPoster():
            l.append( self.getPoster() )
        if self.getMinutes():
            l.append( self.getMinutes() )
        if sort:
            l.sort(lambda x,y: cmp(x.getTitle(),y.getTitle()))
        return l

    def getAllViewableMaterialList( self, aw=None ):
        if not aw:
            aw = ContextManager.get("currentAW", ContextManager.get("currentRH").getAW())
        return [mat for mat in self.getAllMaterialList() if mat.canView(aw)]


    def newSubContribution(self):
        newSub = SubContribution()
        self.addSubContribution(newSub)
        newSub._notify('created', self)
        return newSub

    def addSubContribution( self, newSubCont ):
        newSubCont.setId(str( self.__subContGenerator.newCount()) )
        newSubCont.setOwner( self )
        self._subConts.append( newSubCont )
        self.notifyModification(cleanCache = False)

    def removeSubContribution( self, subCont ):
        if subCont in self._subConts:
            subCont.delete()
            subCont.setOwner(None)
            self._subConts.remove(subCont)
            self.notifyModification(cleanCache = False)

    def recoverSubContribution( self, recSubCont ):
    # Id must already be set in recSubCont.
        recSubCont.setOwner( self )
        self._subConts.append( recSubCont )
        recSubCont.recover()
        self.notifyModification(cleanCache = False)

    def getSubContributionById(self, SCId):
        for sb in self._subConts:
            if sb.getId() == SCId:
                return sb

    def getSubContributionList(self):
        return self._subConts

    def iterSubContributions(self):
        return iter(self._subConts)

    def getNumberOfSubcontributions(self):
        return len(self._subConts)

    def upSubContribution(self, subcont):
        if subcont in self._subConts:
            if self._subConts.index(subcont) != 0:
                index = self._subConts.index(subcont)
                sb = self._subConts.pop(index)
                self._subConts.insert(index-1, sb)
                self.notifyModification(cleanCache = False)

    def downSubContribution(self, subCont):
        if subCont in self._subConts:
            if self._subConts.index(subCont) < len(self._subConts)-1:
                index = self._subConts.index(subCont)
                sb = self._subConts.pop(index)
                self._subConts.insert(index+1, sb)
                self.notifyModification(cleanCache = False)

    def setPaper( self, newPaper ):
        if self.getPaper() != None:
            raise MaKaCError( _("The paper for this contribution has already been set"), _("Contribution"))
        self.paper=newPaper
        self.paper.setOwner( self )
        self.notifyModification()

    def removePaper( self ):
        if self.paper is None:
            return
        self.paper.delete()
        self.paper.setOwner(None)
        self.paper = None
        self.notifyModification()

    def recoverPaper(self, p):
        self.setPaper(p)
        p.recover()

    def getPaper( self ):
        return self.paper

    def setSlides( self, newSlides ):
        if self.getSlides() != None:
            raise MaKaCError( _("The slides for this contribution have already been set"), _("contribution"))
        self.slides=newSlides
        self.slides.setOwner( self )
        self.notifyModification()

    def removeSlides( self ):
        if self.slides is None:
            return
        self.slides.delete()
        self.slides.setOwner( None )
        self.slides= None
        self.notifyModification()

    def recoverSlides(self, s):
        self.setSlides(s)
        s.recover()

    def getSlides( self ):
        return self.slides

    def setVideo( self, newVideo ):
        if self.getVideo() != None:
            raise MaKaCError( _("the video for this contribution has already been set"))
        self.video=newVideo
        self.video.setOwner( self )
        self.notifyModification()

    def removeVideo( self ):
        if self.getVideo() is None:
            return
        self.video.delete()
        self.video.setOwner(None)
        self.video = None
        self.notifyModification()

    def recoverVideo(self, v):
        self.setVideo(v)
        v.recover()

    def getVideo( self ):
        try:
            if self.video:
                pass
        except AttributeError:
            self.video = None
        return self.video

    def setPoster( self, newPoster ):
        if self.getPoster() != None:
            raise MaKaCError( _("the poster for this contribution has already been set"))
        self.poster=newPoster
        self.poster.setOwner( self )
        self.notifyModification()

    def removePoster( self ):
        if self.getPoster() is None:
            return
        self.poster.delete()
        self.poster.setOwner(None)
        self.poster = None
        self.notifyModification()

    def recoverPoster(self, p):
        self.setPoster(p)
        p.recover()

    def getPoster( self ):
        try:
            if self.poster:
                pass
        except AttributeError:
            self.poster = None
        return self.poster

    def setMinutes( self, newMinutes ):
        if self.getMinutes() != None:
            raise MaKaCError( _("the Minutes for this contribution has already been set"))
        self.minutes=newMinutes
        self.minutes.setOwner( self )
        self.notifyModification()

    def createMinutes( self ):
        if self.getMinutes() != None:
            raise MaKaCError( _("The minutes for this contribution have already been created"), _("Contribution"))
        self.minutes = Minutes()
        self.minutes.setOwner( self )
        self.notifyModification()
        return self.minutes

    def removeMinutes( self ):
        if self.getMinutes() is None:
            return
        self.minutes.delete()
        self.minutes.setOwner( None )
        self.minutes = None
        self.notifyModification()

    def recoverMinutes(self, min):
        self.removeMinutes() # To ensure that the current minutes are put in
                             # the trash can.
        self.minutes = min
        self.minutes.setOwner( self )
        min.recover()
        self.notifyModification()
        return self.minutes

    def getMinutes( self ):
        #To be removed
        try:
           if self.minutes:
            pass
        except AttributeError, e:
            self.minutes = None
        return self.minutes

    def setReviewing( self, newReviewing ):
        if self.getReviewing() != None:
            raise MaKaCError( _("The reviewing maretial for this contribution has already been set"), _("Contribution"))
        self.reviewing=newReviewing
        self.reviewing.setOwner( self )
        self.notifyModification()

    def removeReviewing( self ):
        if self.getReviewing() is None:
            return
        self.reviewing.delete()
        self.reviewing.setOwner(None)
        self.reviewing = None
        self.notifyModification()

    def recoverReviewing(self, p):
        self.setReviewing(p)
        p.recover()

    def getReviewing( self ):
        try:
            if self.reviewing:
                pass
        except AttributeError, e:
            self.reviewing = None
        return self.reviewing

    def getMasterSchedule( self ):
        return self.getOwner().getSchedule()

    def requireDomain( self, dom ):
        self.__ac.requireDomain( dom )
        self._notify('domainAdded', dom)

    def freeDomain( self, dom ):
        self.__ac.freeDomain( dom )
        self._notify('domainRemoved', dom)

    def getDomainList( self ):
        return self.__ac.getRequiredDomainList()

    def getTrack( self ):
        try:
            if self._track:
                pass
        except AttributeError:
            self._track = None
        return self._track

    def setTrack( self, newTrack ):
        currentTrack = self.getTrack()
        if newTrack == currentTrack:
            return
        if currentTrack:
            currentTrack.removeContribution( self )
        self._track = newTrack
        if self._track:
            self._track.addContribution( self )

    def removeTrack(self, track):
        if track == self._track:
            self._track = None

    def setType( self, newType ):
        self._type = newType

    def getType( self ):
        try:
            if self._type:
                pass
        except AttributeError:
            self._type = None
        return self._type

    def getModificationDate( self ):
        """Returns the date in which the contribution was last modified"""
        try:
            return self._modificationDS
        except:
            if self.getConference():
                self._modificationDS = self.getConference().getModificationDate()
            else:
                self._modificationDS = nowutc()
            return self._modificationDS

    def getCurrentStatus(self):
        try:
            if self._status:
                pass
        except AttributeError:
            self._status=ContribStatusNotSch(self)
        return self._status
    getStatus = getCurrentStatus

    def setStatus(self,newStatus):
        """
        """
        self._status=newStatus

    def withdraw(self,resp,comment):
        """ Remove or put a contribution in a conference
        """

        if self.isWithdrawn():
        #put back the authors in the author index
            for auth in self.getAuthorList():
                self.getConference().getAuthorIndex().index(auth)
            for spk in self.getSpeakerList():
                self.getConference().getSpeakerIndex().index(spk)
            #change the status of the contribution
            self._status=ContribStatusNotSch(self)

        else:
            #remove the authors from the author index
            if self.getConference() is not None:
                for auth in self.getAuthorList():
                    self.getConference().getAuthorIndex().unindex(auth)
                for spk in self.getSpeakerList():
                    self.getConference().unindexSpeaker(spk)
            #remove the contribution from any schedule it is included
            if self.isScheduled():
                self.getSchEntry().getSchedule().removeEntry(self.getSchEntry())
            self.getCurrentStatus().withdraw(resp,comment)


    def getSubmitterList(self, no_groups=False):
        try:
            if self._submitters:
                pass
        except AttributeError:
            self._submitters=[] #create the attribute
            self.notifyModification(raiseEvent = False)
        if no_groups:
            return filter(lambda s: not isinstance(s, MaKaC.user.Group), self._submitters)
        else:
            return self._submitters

    def _grantSubmission(self,av):
        if av not in self.getSubmitterList():
            self.getSubmitterList().append(av)
        if self.getConference() is not None:
            self.getConference().addContribSubmitter(self,av)
        if isinstance(av, MaKaC.user.Avatar):
            av.linkTo(self, "submission")
        self.notifyModification(raiseEvent = False)

    def _grantSubmissionEmail(self, email):
        """Returns True if submission email was granted. False if email was already in the list.
        """
        if not email.lower() in map(lambda x: x.lower(), self.getSubmitterEmailList()):
            self.getSubmitterEmailList().append(email.lower().strip())
            return True
        return False

    def revokeSubmissionEmail(self, email):
        if email in self.getSubmitterEmailList():
            self.getSubmitterEmailList().remove(email)
            self._p_changed=1

    def grantSubmission(self, sb, sendEmail=True):
        """Grants a user with submission privileges for the contribution
           - sb: can be an Avatar or an Author (primary author, co-author, speaker)
        """
        if isinstance(sb, ContributionParticipation) or isinstance(sb, SubContribParticipation):
            ah = AvatarHolder()
            results=ah.match({"email":sb.getEmail()}, exact=1, searchInAuthenticators=False)
            if not results:
                results=ah.match({"email":sb.getEmail()}, exact=1)
            r=None
            for i in results:
                if i.hasEmail(sb.getEmail()):
                    r=i
                    break
            if r and r.isActivated():
                self._grantSubmission(r)
            elif sb.getEmail():
                self.getConference().getPendingQueuesMgr().addPendingSubmitter(sb, False)
                submissionEmailGranted = self._grantSubmissionEmail(sb.getEmail())
                if submissionEmailGranted and sendEmail:
                    notif = pendingQueues._PendingSubmitterNotification( [sb] )
                    mail.GenericMailer.sendAndLog( notif, self.getConference() )
                    if self.getConference():
                        self.getConference().addContribSubmitter(self,sb)
        else:
            self._grantSubmission(sb)

    def _revokeSubmission(self, av):
        if av in self.getSubmitterList():
            self.getSubmitterList().remove(av)
        if self.getConference():
            self.getConference().removeContribSubmitter(self, av)
        if isinstance(av, MaKaC.user.Avatar):
            av.unlinkTo(self, "submission")
        self.notifyModification(raiseEvent = False)

    def revokeSubmission(self, sb):
        """Removes submission privileges for the specified user
            - sb: can be an Avatar or an Author (primary author, co-author, speaker)
        """
        if isinstance(sb, ContributionParticipation) or isinstance(sb, SubContribParticipation):
            ah = AvatarHolder()
            results = ah.match({"email": sb.getEmail()}, exact=1, searchInAuthenticators=False)
            r = None
            for i in results:
                if i.hasEmail(sb.getEmail()):
                    r=i
                    break
            if r:
                self._revokeSubmission(r)
            else:
                self.revokeSubmissionEmail(sb.getEmail())
        else:
            self._revokeSubmission(sb)

    def revokeAllSubmitters(self):
        self._submitters = []
        self.notifyModification(raiseEvent = False)

    def getSubmitterEmailList(self):
        try:
            return self._submittersEmail
        except:
            self._submittersEmail = []
        return self._submittersEmail

    def canUserSubmit(self, sb):
        """Tells whether a user can submit material for the current contribution
            - sb: can be an Avatar or an Author (primary author, co-author, speaker)
        """
        if sb is None:
            return False

        if isinstance(sb, ContributionParticipation) or isinstance(sb, SubContribParticipation):
            sbEmail = sb.getEmail()

            # Normally, we shouldn't get here unless we're adding someone as a Speaker or similar.
            # `no_groups` is used so that we do not consider group membership, as to not confuse the
            # user (since there will be speakers with "implicit" privileges) and avoid that hasEmail breaks
            return any(submitter.hasEmail(sbEmail) for submitter in self.getSubmitterList(no_groups=True)) or \
                   any(submitterEmail == sbEmail for submitterEmail in self.getSubmitterEmailList())

        for principal in self.getSubmitterList():
            if principal != None and principal.containsUser(sb):
                return True

        return False

    def getAccessController(self):
        return self.__ac

    def getReportNumberHolder(self):
        try:
            if self._reportNumberHolder:
                pass
        except AttributeError, e:
            self._reportNumberHolder=ReportNumberHolder(self)
        return self._reportNumberHolder

    def setReportNumberHolder(self, rnh):
        self._reportNumberHolder=rnh

    @classmethod
    def contributionStartDateForSort(cls, contribution):
        """ Function that can be used as "key" argument to sort a list of contributions by start date
            The contributions with no start date will be at the end with this sort
        """
        if contribution.getStartDate():
            return contribution.getStartDate()
        else:
            return maxDatetime()

    def getColor(self):
        res=""
        if self.getSession() is not None:
            res=self.getSession().getColor()
        return res

    def getTextColor(self):
        res=""
        if self.getSession() is not None:
            res=self.getSession().getTextColor()
        return res


class AcceptedContribution(Contribution):
    """This class represents a contribution which has been created from an
        abstract
    """

    def __init__(self, abstract):
        Contribution.__init__(self)
        abstract.getConference().addContribution(self, abstract.getId())
        self._abstract = abstract
        self.setTitle(abstract.getTitle())
        self._setFieldsFromAbstract()
        if isinstance(abstract.getCurrentStatus(), review.AbstractStatusAccepted):
            self.setTrack(abstract.getCurrentStatus().getTrack())
            self.setType(abstract.getCurrentStatus().getType())
        for auth in abstract.getAuthorList():
            c_auth = ContributionParticipation()
            self._setAuthorValuesFromAbstract(c_auth, auth)
            if abstract.isPrimaryAuthor(auth):
                self.addPrimaryAuthor(c_auth)
            else:
                self.addCoAuthor(c_auth)
            if abstract.isSpeaker(auth):
                self.addSpeaker(c_auth)
        self._grantSubmission(self.getAbstract().getSubmitter().getUser())

    def _setAuthorValuesFromAbstract(self, cAuth, aAuth):
        cAuth.setTitle(aAuth.getTitle())
        cAuth.setFirstName(aAuth.getFirstName())
        cAuth.setFamilyName(aAuth.getSurName())
        cAuth.setEmail(aAuth.getEmail())
        cAuth.setAffiliation(aAuth.getAffiliation())
        cAuth.setAddress(aAuth.getAddress())
        cAuth.setPhone(aAuth.getTelephone())

    def _setFieldsFromAbstract(self):
        for k, v in self._abstract.getFields().iteritems():
            self.setField(k, v)

    def getAbstract(self):
        return self._abstract

    def setAbstract(self, abs):
        self._abstract = abs

    def getSubmitterList(self, no_groups=False):
        try:
            if self._submitters:
                pass
        except AttributeError:
            self._submitters = []  # create the attribute
            self._grantSubmission(self.getAbstract().getSubmitter().getUser())
        if no_groups:
            return filter(lambda s: not isinstance(s, MaKaC.user.Group), self._submitters)
        else:
            return self._submitters

    def delete(self):
        """deletes a contribution and all of their subitems
        """
        abs = self.getAbstract()
        if abs:
            cs = abs.getCurrentStatus()
            if isinstance(cs, review.AbstractStatusAccepted):
                if cs.getTrack() is not None:
                    abs.addTrack(cs.getTrack())
            abs.setCurrentStatus(review.AbstractStatusSubmitted(abs))
            abs._setContribution(None)
            self.setAbstract(None)
        Contribution.delete(self)


class ContribStatus(Persistent):
    """
    """

    def __init__(self,contribution,responsible):
        self._setContrib(contribution)
        self._setResponsible(responsible)
        self._setDate()

    def clone(self, contribution, responsible):
        cs = ContribStatus(contribution, responsible)
        cs.setDate(self.getDate())
        return cs

    def _setContrib(self,newContrib):
        self._contrib=newContrib

    def getContrib(self):
        return self._contrib

    def _setResponsible(self,newResp):
        self._responsible=newResp

    def getResponsible(self):
        return self._responsible

    def _setDate(self):
        self._date=nowutc()

    def setDate(self, date):
        self._date = date

    def getDate(self):
        return self._date

    def withdraw(self,resp,comments=""):
        self._contrib.setStatus(ContribStatusWithdrawn(self.getContrib(),resp,comments))

class ContribStatusNotSch(ContribStatus):
    """
    """
    def __init__(self,contrib):
        ContribStatus.__init__(self,contrib,None)

    def clone(self, contribution):
        csns = ContribStatusNotSch(contribution)
        csns.setDate(self.getDate())
        return csns

ContribStatusSubmitted=ContribStatusNotSch

class ContribStatusSch(ContribStatus):
    """
    """
    def __init__(self,contrib):
        ContribStatus.__init__(self,contrib,None)

    def clone(self, contribution):
        css = ContribStatusSch(contribution)
        css.setDate(self.getDate())
        return css

class ContribStatusWithdrawn(ContribStatus):
    """
    """
    def __init__(self,contrib,resp,comments):
        ContribStatus.__init__(self,contrib,resp)
        self._setComment(comments)

    def clone(self, contribution):
        csw = ContribStatusWithdrawn(contribution)
        csw.setDate(self.getDate())
        csw.setComment(self.getComment())
        return csw

    def _setComment(self,text):
        self._comment=text.strip()

    def getComment(self):
        return self._comment

class ContribStatusNone(ContribStatus):
# This is a special status we assign to contributions that are put in the trash can.

    def __init__(self,contrib):
        ContribStatus.__init__(self,contrib,None)

    def clone(self, contribution):
        csn = ContribStatusNone(contribution)
        csn.setDate(self.getDate())
        return csn

class SubContribParticipation(Persistent, Fossilizable):

    fossilizes(ISubContribParticipationFossil, ISubContribParticipationFullFossil)

    def __init__( self ):
        self._subContrib = None
        self._id = ""
        self._firstName = ""
        self._surName = ""
        self._email = ""
        self._affiliation = ""
        self._address = ""
        self._phone = ""
        self._title = ""
        self._fax = ""

    def getConference(self):
        if self._subContrib is not None:
            return self._subContrib.getConference()
        return None

    def _notifyModification( self ):
        if self._subContrib != None:
            self._subContrib.notifyModification()

    def setValues(self, data):
        self.setFirstName(data.get("firstName", ""))
        self.setFamilyName(data.get("familyName",""))
        self.setAffiliation(data.get("affilation",""))
        self.setAddress(data.get("address",""))
        self.setEmail(data.get("email",""))
        self.setFax(data.get("fax",""))
        self.setTitle(data.get("title",""))
        self.setPhone(data.get("phone",""))
        self._notifyModification()

    def getValues(self):
        data={}
        data["firstName"]=self.getFirstName()
        data["familyName"]=self.getFamilyName()
        data["affilation"]=self.getAffiliation()
        data["address"]=self.getAddress()
        data["email"]=self.getEmail()
        data["fax"]=self.getFax()
        data["title"]=self.getTitle()
        data["phone"]=self.getPhone()
        return data

    def clone(self):
        part = SubContribParticipation()
        part.setValues(self.getValues())
        return part

    def setDataFromAvatar(self,av):
    # av is an Avatar object.
        if av is None:
            return
        self.setFirstName(av.getName())
        self.setFamilyName(av.getSurName())
        self.setEmail(av.getEmail())
        self.setAffiliation(av.getOrganisation())
        self.setAddress(av.getAddress())
        self.setPhone(av.getTelephone())
        self.setTitle(av.getTitle())
        self.setFax(av.getFax())
        self._notifyModification()

    def setDataFromAuthor(self,au):
    # au is a ContributionParticipation object.
        if au is None:
            return
        self.setFirstName(au.getFirstName())
        self.setFamilyName(au.getFamilyName())
        self.setEmail(au.getEmail())
        self.setAffiliation(au.getAffiliation())
        self.setAddress(au.getAddress())
        self.setPhone(au.getPhone())
        self.setTitle(au.getTitle())
        self.setFax(au.getFax())
        self._notifyModification()

    def setDataFromSpeaker(self,spk):
    # spk is a SubContribParticipation object.
        if spk is None:
            return
        self.setFirstName(spk.getFirstName())
        self.setFamilyName(spk.getFamilyName())
        self.setEmail(spk.getEmail())
        self.setAffiliation(spk.getAffiliation())
        self.setAddress(spk.getAddress())
        self.setPhone(spk.getPhone())
        self.setTitle(spk.getTitle())
        self.setFax(spk.getFax())
        self._notifyModification()

    def includeInSubContrib( self, subcontrib, id ):
        if self.getSubContrib() == subcontrib and self.getId()==id.strip():
            return
        self._subContrib = subcontrib
        self._id = id

    def delete( self ):
        self._subContrib = None
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    @Updates ('MaKaC.conference.SubContribParticipation', 'id')
    def setId(self, newId):
        self._id = newId

    def getId( self ):
        return self._id

    def getSubContrib( self ):
        return self._subContrib

    def getContribution( self ):
        if self._subContrib is not None:
            return self._subContrib.getContribution()
        return None

    def _unindex(self):
        contrib=self.getContribution()
        if contrib is not None:
            conf=contrib.getConference()
            if conf is not None:
                conf.unindexAuthor(self)
                conf.unindexSpeaker(self)

    def _index(self):
        contrib=self.getContribution()
        if contrib is not None:
            conf=contrib.getConference()
            if conf is not None:
                conf.indexAuthor(self)
                conf.indexSpeaker(self)

    @Updates ('MaKaC.conference.SubContribParticipation', 'firstName')
    def setFirstName( self, newName ):
        tmp=newName.strip()
        if tmp==self._firstName:
            return
        self._unindex()
        self._firstName=tmp
        self._index()
        self._notifyModification()

    def getFirstName( self ):
        return self._firstName

    def getName( self ):
        return self._firstName

    @Updates ('MaKaC.conference.SubContribParticipation', 'familyName')
    def setFamilyName( self, newName ):
        tmp=newName.strip()
        if tmp==self._surName:
            return
        self._unindex()
        self._surName=tmp
        self._index()
        self._notifyModification()

    def getFamilyName( self ):
        return self._surName

    def getSurName( self ):
        return self._surName

    @Updates ('MaKaC.conference.SubContribParticipation', 'email')
    def setEmail( self, newMail ):
        tmp=newMail.strip()
        if tmp==self._email:
            return
        self._unindex()
        self._email=newMail.strip()
        self._index()
        self._notifyModification()

    def getEmail( self ):
        return self._email

    @Updates ('MaKaC.conference.SubContribParticipation', 'affiliation')
    def setAffiliation( self, newAffil ):
        self._affiliation = newAffil.strip()
        self._notifyModification()

    def getAffiliation( self ):
        return self._affiliation

    @Updates ('MaKaC.conference.SubContribParticipation', 'address')
    def setAddress( self, newAddr ):
        self._address = newAddr.strip()
        self._notifyModification()

    def getAddress( self ):
        return self._address

    @Updates ('MaKaC.conference.SubContribParticipation', 'phone')
    def setPhone( self, newPhone ):
        self._phone = newPhone.strip()
        self._notifyModification()

    def getPhone( self ):
        return self._phone

    @Updates ('MaKaC.conference.SubContribParticipation', 'title')
    def setTitle( self, newTitle ):
        self._title = newTitle.strip()
        self._notifyModification()

    def getTitle( self ):
        return self._title

    def setFax( self, newFax ):
        self._fax = newFax.strip()
        self._notifyModification()

    def getFax( self ):
        try:
            if self._fax:
                pass
        except AttributeError:
            self._fax=""
        return self._fax

    def getFullName( self ):
        res = self.getFullNameNoTitle()
        if self.getTitle() != "":
            res = "%s %s"%( self.getTitle(), res )
        return res

    def getFullNameNoTitle(self):
        res = safe_upper(self.getFamilyName())
        if self.getFirstName():
            if res.strip():
                res = "%s, %s" % (res, self.getFirstName())
            else:
                res = self.getFirstName()
        return res

    def getAbrName(self):
        res = self.getFamilyName()
        if self.getFirstName():
            if res:
                res = "%s, " % res
            res = "%s%s." % (res, safe_upper(self.getFirstName()[0]))
        return res

    def getDirectFullName(self):
        res = self.getDirectFullNameNoTitle()
        if self.getTitle():
            res = "%s %s" % (self.getTitle(), res)
        return res

    def getDirectFullNameNoTitle(self, upper=True):
        surName = safe_upper(self.getFamilyName()) if upper else self.getFamilyName()
        return "{0} {1}".format(self.getFirstName(), surName).strip()


class SubContribution(CommonObjectBase, Locatable):
    """
    """

    fossilizes(ISubContributionFossil, ISubContributionWithSpeakersFossil)

    def __init__( self, **subContData ):
        self.parent = None
        self.id = ""
        self.title = ""
        self.description = ""
        self.__schEntry = None
        self.duration = timedelta( minutes=15 )
        self.speakers = []
        self.speakerText = ""

        self.materials = {}
        self.__materialGenerator = Counter() # Provides material unique
                                             # identifiers whithin the current
        self.poster = None                   # contribution
        self.paper = None
        self.slides = None
        self.video = None
        self.poster = None
        self.minutes = None
        self._authorGen = Counter()
        self._keywords = ""

    def __str__(self):
        if self.parent:
            parentId = self.parent.getId()
            if self.getConference():
                grandpaId = self.getConference().getId()
            else:
                grandpaId = None
        else:
            parentId = None
            grandpaId = None
        return "<SubCont %s:%s:%s@%s>" % (grandpaId, parentId, self.getId(), hex(id(self)))

    def updateNonInheritingChildren(self, elem, delete=False):
        self.getOwner().updateNonInheritingChildren(elem, delete)

    def getAccessController(self):
        return self.getOwner().getAccessController()

    def getKeywords(self):
        try:
            return self._keywords
        except:
            self._keywords = ""
            return ""

    def setKeywords(self, keywords):
        self._keywords = keywords

    def getLogInfo(self):
        data = {}

        data["subject"] = self.getTitle()
        data["id"] = self.id
        data["title"] = self.title
        data["parent title"] = self.getParent().getTitle()
        data["description"] = self.description
        data["duration"] = "%s"%self.duration
        data["minutes"] = self.minutes

        for sp in self.speakers :
            data["speaker %s"%sp.getId()] = sp.getFullName()

        return data


    def clone(self, deltaTime, parent, options):
        sCont =  SubContribution()
        sCont.setParent(parent)
        sCont.setTitle(self.getTitle())
        sCont.setDescription(self.getDescription())
        sCont.setKeywords(self.getKeywords())
        dur = self.getDuration()
        hours = dur.seconds / 3600
        minutes = (dur.seconds % 3600) / 60
        sCont.setDuration(hours, minutes)
        sCont.setReportNumberHolder(self.getReportNumberHolder().clone(self))

        # There is no _order attribute in this class

        if options.get("authors", False) :
            for s in self.getSpeakerList() :
                sCont.newSpeaker(s.clone())
            sCont.setSpeakerText(self.getSpeakerText())

        if options.get("materials", False) :
            for m in self.getMaterialList() :
                sCont.addMaterial(m.clone(sCont))
            if self.getPaper() is not None:
                sCont.setPaper(self.getPaper().clone(sCont))
            if self.getSlides() is not None:
                sCont.setSlides(self.getSlides().clone(sCont))
            if self.getVideo() is not None:
                sCont.setVideo(self.getVideo().clone(sCont))
            if self.getPoster() is not None:
                sCont.setPoster(self.getPoster().clone(sCont))
            if self.getMinutes() is not None:
                sCont.setMinutes(self.getMinutes().clone(sCont))


        sCont.notifyModification()
        return sCont

    def notifyModification(self, raiseEvent = True):
        parent = self.getParent()
        if parent:
            parent.setModificationDate()
        if raiseEvent:
            self._notify('infoChanged')
        self._p_changed = 1

    def getCategoriesPath(self):
        return self.getConference().getCategoriesPath()

    def getLocator( self ):
        """Gives back a globaly unique identification encapsulated in a Locator
            object for the contribution instance
        """

        lconf = self.getOwner().getLocator()
        lconf["subContId"] = self.getId()
        return lconf


    def setId( self, newId ):
        self.id = newId

    def getId( self ):
        return self.id

    def getUniqueId( self ):
        """returns (string) the unique identifier of the item"""
        """used mainly in the web session access key table"""
        return "%ssc%s" % (self.getParent().getUniqueId(),self.id)

    def setTitle( self, newTitle ):
        self.title = newTitle.strip()
        self.notifyModification()

    def getTitle( self ):
        if self.title.strip() == "":
            return "(no title)"
        return self.title

    def setDescription( self, newDesc ):
        self.description = newDesc.strip()
        self.notifyModification()

    def getDescription( self ):
        return self.description

    def setParent(self,parent):
        self.parent = parent
        if self.parent == None:
            return

    def getParent( self ):
        return self.parent

    def setOwner(self, owner):
        self.setParent(owner)

    def getOwner( self ):
        return self.getParent()

    def getConference( self ):
        return self.parent.getConference()

    def getSession( self ):
        return self.parent.getSession()

    def getContribution(self):
        return self.parent

    def getDuration( self ):
        return self.duration

    def setDuration( self, hours, minutes=0, dur=0 ):
        if dur!=0:
            self.duration=dur
        else:
            hours = int( hours )
            minutes = int( minutes )
            self.duration = timedelta(hours=hours,minutes=minutes )
        self.notifyModification()

    def getLocation( self ):
        return self.getOwner().getLocation()

    def getRoom( self ):
        return self.getOwner().getRoom()

    def getSpeakerById( self, id ):
        """
        """
        for spk in self.speakers:
            if spk.getId() == id:
                return spk
        return None

    def newSpeaker( self, spk ):
        """
        """
        self.speakers.append( spk )
        try:
            if self._authorGen:
                pass
        except AttributeError:
            self._authorGen=Counter()
        newId = spk.getId()
        if newId == "":
            newId = str( self._authorGen.newCount() )
        spk.includeInSubContrib(self, newId)
        if self.getConference() is not None:
            self.getConference().indexSpeaker(spk)
        self.notifyModification()

    def removeSpeaker( self, spk ):
        """
        """
        if spk not in self.speakers:
            return
        self.speakers.remove( spk )
        if self.getConference() is not None:
            self.getConference().unindexSpeaker(spk)
        spk.delete()
        self.notifyModification()

    def recoverSpeaker(self, spk):
        self.newSpeaker(spk)
        spk.recover()

    def isSpeaker( self, spk):
        """
        """
        return spk in self._speakers

    def getSpeakerList ( self ):
        """
        """
        return self.speakers

    def getSpeakerText( self ):
        #to be removed
        try:
            if self.speakerText:
                pass
        except AttributeError, e:
            self.speakerText = ""
        return self.speakerText

    def setSpeakerText( self, newText ):
        self.speakerText = newText.strip()

    def appendSpeakerText( self, newText ):
        self.setSpeakerText( "%s, %s"%(self.getSpeakerText(), newText.strip()) )

#    """
#    There is no _order attribute in this class -
#    the methods below are either obsolate or the feature has not been implemented
#    """
#    def setOrder( self, order ):
#        self._order = order
#        self.notifyModification()
#
#    def getOrder(self):
#        return self._order

    def canIPAccess( self, ip ):
        return self.getOwner().canIPAccess(ip)

    def isProtected( self ):
        return self.hasProtectedOwner()

    def getAccessProtectionLevel( self ):
        return self.getOwner().getAccessProtectionLevel()

    def hasAnyProtection( self ):
        """Tells whether a subContribution has any kind of protection over it:
            access or domain protection.
        """
        return self.getOwner().hasAnyProtection()

    def getManagerList( self ):
        return self.parent.getManagerList()

    def hasProtectedOwner( self ):
        if self.getOwner() != None:
            return self.getOwner().isProtected()
        return False

    def getAccessKey( self ):
        return self.getOwner().getAccessKey()

    def getModifKey( self ):
        return self.getConference().getModifKey()

    def canView( self, aw ):
        """tells whether the specified user has access to the current object
            or any of its sub-objects
        """
        if self.canAccess( aw ):
            return True
        return False

    def isAllowedToAccess( self, user ):
        return self.parent.isAllowedToAccess( user )

    def canAccess( self, aw ):
        return self.getOwner().canAccess(aw)

    def canModify( self, aw ):
        return self.canUserModify( aw.getUser() ) or self.getConference().canKeyModify( aw )

    def canUserModify( self, av ):
        """Tells whether a user is allowed to modify the current contribution:
            only if the user is granted to modify the contribution or the user
            can modify any of its upper objects (i.e. conference or session).
        """
        return self.getParent().canUserModify( av )

    def canUserSubmit( self, av ):
        return self.getOwner().canUserSubmit( av )

    def getAllowedToAccessList( self ):
        """Currently the SubContribution class has no access list.
        But instead of returning the owner Contribution's access list,
        I am returning an empty list. Methods such as getRecursiveAllowedToAccess()
        will call the owner Contribution anyway.
        """
        return []

    def addMaterial( self, newMat ):
        newMat.setId( str(self.__materialGenerator.newCount()) )
        newMat.setOwner( self )
        self.materials[ newMat.getId() ] =  newMat
        self.notifyModification()

    def removeMaterial( self, mat):
        if mat.getId() in self.materials.keys():
            mat.delete()
            self.materials[mat.getId()].setOwner(None)
            del self.materials[ mat.getId() ]
            self.notifyModification()
        elif mat.getId().lower() == 'paper':
            self.removePaper()
            self.notifyModification()
        elif mat.getId().lower() == 'slides':
            self.removeSlides()
            self.notifyModification()
        elif mat.getId().lower() == 'minutes':
            self.removeMinutes()
            self.notifyModification()
        elif mat.getId().lower() == 'video':
            self.removeVideo()
            self.notifyModification()
        elif mat.getId().lower() == 'poster':
            self.removePoster()
            self.notifyModification()

    def recoverMaterial(self, recMat):
    # Id must already be set in recMat.
        recMat.setOwner( self )
        self.materials[ recMat.getId() ] =  recMat
        recMat.recover()
        self.notifyModification()

    def getMaterialRegistry(self):
        """
        Return the correct material registry for this type
        """
        from MaKaC.webinterface.materialFactories import SubContributionMFRegistry
        return SubContributionMFRegistry

    def getMaterialById( self, matId ):
        if matId.lower() == 'paper':
            return self.getPaper()
        elif matId.lower() == 'slides':
            return self.getSlides()
        elif matId.lower() == 'video':
            return self.getVideo()
        elif matId.lower() == 'poster':
            return self.getPoster()
        elif matId.lower() == 'minutes':
            return self.getMinutes()
        elif self.materials.has_key(matId):
            return self.materials[ matId ]
        return None

    def getMaterialList( self ):
        return self.materials.values()

    def getAllMaterialList(self, sort=True):
        l = self.getMaterialList()
        if self.getPaper():
            l.append( self.getPaper() )
        if self.getSlides():
            l.append( self.getSlides() )
        if self.getVideo():
            l.append( self.getVideo() )
        if self.getMinutes():
            l.append( self.getMinutes() )
        if self.getPoster():
            l.append( self.getPoster() )
        if sort:
            l.sort(lambda x,y: cmp(x.getTitle(),y.getTitle()))
        return l

    def setPaper( self, newPaper ):
        if self.getPaper() != None:
            raise MaKaCError( _("The paper for this subcontribution has already been set"), _("Contribution"))
        self.paper=newPaper
        self.paper.setOwner( self )
        self.notifyModification()

    def removePaper( self ):
        if self.getPaper() is None:
            return
        self.paper.delete()
        self.paper.setOwner(None)
        self.paper = None
        self.notifyModification()

    def recoverPaper(self, p):
        self.setPaper(p)
        p.recover()

    def getPaper( self ):
        return self.paper

    def setSlides( self, newSlides ):
        if self.getSlides() != None:
            raise MaKaCError( _("The slides for this subcontribution have already been set"), _("Contribution"))
        self.slides=newSlides
        self.slides.setOwner( self )
        self.notifyModification()

    def removeSlides( self ):
        if self.getSlides() is None:
            return
        self.slides.delete()
        self.slides.setOwner( None )
        self.slides = None
        self.notifyModification()

    def recoverSlides(self, s):
        self.setSlides(s)
        s.recover()

    def getSlides( self ):
        return self.slides

    def setVideo( self, newVideo ):
        if self.getVideo() != None:
            raise MaKaCError( _("the video for this subcontribution has already been set"))
        self.video=newVideo
        self.video.setOwner( self )
        self.notifyModification()

    def removeVideo( self ):
        if self.getVideo() is None:
            return
        self.video.delete()
        self.video.setOwner(None)
        self.video = None
        self.notifyModification()

    def recoverVideo(self, v):
        self.setVideo(v)
        v.recover()

    def getVideo( self ):
        try:
            if self.video:
                pass
        except AttributeError:
            self.video = None
        return self.video

    def setPoster( self, newPoster ):
        if self.getPoster() != None:
            raise MaKaCError( _("the poster for this subcontribution has already been set"))
        self.poster=newPoster
        self.poster.setOwner( self )
        self.notifyModification()

    def removePoster( self ):
        if self.getPoster() is None:
            return
        self.poster.delete()
        self.poster.setOwner(None)
        self.poster = None
        self.notifyModification()

    def recoverPoster(self, p):
        self.setPoster(p)
        p.recover()

    def getPoster( self ):
        try:
            if self.poster:
                pass
        except AttributeError:
            self.poster = None
        return self.poster

    def setMinutes( self, newMinutes ):
        if self.getMinutes() != None:
            raise MaKaCError( _("the Minutes for this subcontribution has already been set"))
        self.minutes=newMinutes
        self.minutes.setOwner( self )
        self.notifyModification()

    def createMinutes( self ):
        if self.getMinutes() != None:
            raise MaKaCError( _("The minutes for this subcontribution have already been created"), _("Sub Contribution"))
        self.minutes = Minutes()
        self.minutes.setOwner( self )
        self.notifyModification()
        return self.minutes

    def removeMinutes( self ):
        if self.getMinutes() is None:
            return
        self.minutes.delete()
        self.minutes.setOwner( None )
        self.minutes = None
        self.notifyModification()

    def recoverMinutes(self, min):
        self.removeMinutes() # To ensure that the current minutes are put in
                             # the trash can.
        self.minutes = min
        self.minutes.setOwner( self )
        min.recover()
        self.notifyModification()
        return self.minutes

    def getMinutes( self ):
        #To be removed
        try:
           if self.minutes:
            pass
        except AttributeError, e:
            self.minutes = None
        return self.minutes

    def getMasterSchedule( self ):
        return self.getOwner().getSchedule()

    def delete(self):

        self._notify('deleted', self.getOwner())

        while len(self.getSpeakerList()) > 0:
            self.removeSpeaker(self.getSpeakerList()[0])
        for mat in self.getMaterialList():
            self.removeMaterial(mat)
        self.removePaper()
        self.removeSlides()
        self.removeVideo()
        self.removePoster()
        self.removeMinutes()
        TrashCanManager().add(self)

        #self.unindex()

    def recover(self):
        TrashCanManager().remove(self)

    def getReportNumberHolder(self):
        try:
            if self._reportNumberHolder:
                pass
        except AttributeError, e:
            self._reportNumberHolder=ReportNumberHolder(self)
        return self._reportNumberHolder

    def setReportNumberHolder(self, rnh):
        self._reportNumberHolder=rnh

class Material(CommonObjectBase):
    """This class represents a set of electronic documents (resources) which can
        be attached to a conference, a session or a contribution.
        A material can be of several types (achieved by specialising this class)
        and is like a container of files which have some relation among them.
        It contains the minimal set of attributes to store basic meta data and
        provides useful operations to access and manage it.
       Attributes:
        owner -- (Conference, Session or Contribution) Object to which the
            material is attached to
        id -- (string) Material unique identifier. Normally used to uniquely
            identify a material within a conference, session or contribution
        title -- (string) Material denomination
        description -- (string) Longer text describing in more detail material
            intentions
        type -- (string) String identifying the material classification
        resources -- (PMapping) Collection of resouces grouped within the
            material. Dictionary of references to Resource objects indexed
            by their unique relative id.
    """

    fossilizes(IMaterialMinimalFossil, IMaterialFossil)

    def __init__( self, materialData=None ):
        self.id = "not assigned"
        self.__resources = {}
        self.__resourcesIdGen = Counter()
        self.title = ""
        self.description = ""
        self.type = ""
        self.owner = None
        self.__ac = AccessController(self)
        self._mainResource = None

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        if self.getConference() == other.getConference():
            if self.getId().isdigit() and other.getId().isdigit():
                return cmp(int(self.getId()), int(other.getId()))
            else:
                return cmp(self.getId(), other.getId())
        return cmp(self.getConference(), other.getConference())

    def updateNonInheritingChildren(self, elem, delete=False):
        # We do not want to store the inherited children in a Category because the funcionallity is not used
        if not isinstance(self.getOwner(), Category):
            self.getAccessController().updateNonInheritingChildren(elem, delete)
            self.notify_protection_to_owner(elem, delete)

    def notify_protection_to_owner(self, elem, delete=False):
        self.getOwner().updateNonInheritingChildren(elem, delete)

    def setValues( self, params ):
        """Sets all the values of the current material object from a diccionary
            containing the following key-value pairs:
                title-(str)
                description-(str)
           Please, note that this method sets ALL values which means that if
            the given dictionary doesn't contain any of the keys the value
            will set to a default value.
        """
        self.setTitle(params.get("title", "NO TITLE ASSIGNED"))
        self.setDescription( params.get( "description", "" ) )
        self.notifyModification()

    def clone ( self, owner):
        mat = type(self)()
        mat.setTitle(self.getTitle())
        mat.setDescription(self.getDescription())
        mat.notifyModification()

        mat.setId(self.getId())
        mat.setOwner(owner)
        mat.setType(self.getType())

        mat.setProtection(self.getAccessController()._getAccessProtection())
        mat.setAccessKey(self.getAccessKey())
        rlist = self.getResourceList()
        for r in rlist:
            newres = r.clone(mat)
            mat.addResource(newres)

        mat.setMainResource(self.getMainResource())

        return mat

    def notifyModification( self ):
        parent = self.getOwner()
        if parent:
            parent.notifyModification(raiseEvent = False)
        self._p_changed = 1

    def getLocator( self ):
        if self.owner == None:
            return Locator()
        lconf = self.owner.getLocator()
        lconf["materialId"] = self.getId()
        return lconf

    def setId( self, newId ):
        self.id = str(newId).strip()

    def getId( self ):
        return self.id

    def getUniqueId( self ):
        """returns (string) the unique identifier of the item"""
        """used mainly in the web session access key table"""
        return "%sm%s" % (self.getOwner().getUniqueId(),self.id)

    def setOwner(self, newOwner):
        self.owner = newOwner

    def getOwner( self ):
        return self.owner

    def getCategory( self ):
        if isinstance(self.getOwner(), Category):
            return self.getOwner()
        return None

    def getConference( self ):
        owner = self.getOwner()
        if owner is None or isinstance(owner, Category):
            return None
        elif isinstance(owner, Conference):
            return owner
        else:
            return owner.getConference()

    def getSession( self ):
        if self.getContribution():
            return self.getContribution().getSession()
        if isinstance(self.getOwner(), Session):
            return self.getOwner()
        if isinstance(self.getOwner(), SubContribution):
            return self.getOwner().getSession()
        return None

    def getContribution( self ):
        if self.getSubContribution():
            return self.getSubContribution().getContribution()
        if isinstance(self.getOwner(), Contribution):
            return self.getOwner()
        return None

    def getSubContribution( self ):
        if isinstance(self.getOwner(), SubContribution):
            return self.getOwner()
        return None

    @Updates (['MaKaC.conference.Material',
                 'MaKaC.conference.Minutes',
                 'MaKaC.conference.Paper',
                 'MaKaC.conference.Slides',
                 'MaKaC.conference.Video',
                 'MaKaC.conference.Poster',
                 'MaKaC.conference.Reviewing'],'title')
    def setTitle( self, newTitle ):
        self.title = newTitle.strip()
        self.notifyModification()

    def getTitle( self ):
        return self.title

    @Updates (['MaKaC.conference.Material',
                 'MaKaC.conference.Minutes',
                 'MaKaC.conference.Paper',
                 'MaKaC.conference.Slides',
                 'MaKaC.conference.Video',
                 'MaKaC.conference.Poster',
                 'MaKaC.conference.Reviewing'], 'description')
    def setDescription( self, newDescription ):
        self.description = newDescription.strip()
        self.notifyModification()

    def getDescription( self ):
        return self.description

    def setType( self, newType ):
        self.type = newType.strip()
        self.notifyModification()

    def getType( self ):
        return self.type

    def getReviewingState(self):
        """ Returns the reviewing state of a material.
            The state is represented by an integer:
            0 : there's no reviewing state because the material does not belong to a contribution, or the conference
                has not reviewing module enabled, or the module is enabled but the mode is "no reviewing"
            1 : the material is not subject to reviewing, because this kind of material is not reviewable in the conference
            2 : the material is subject to reviewing, but has not been submitted yet by the author
            3 : the material is subject to reviewing, has been submitted by the author, but has not been judged yet
            4 : the material is subject to reviewing, has been submitted by the author, and has been judged as Accepted
            5 : the material is subject to reviewing, has been submitted by the author, and has been judged as Rejected
        """
        if isinstance(self.owner, Contribution):
            conference = self.owner.getConference()
            if conference.getConfPaperReview().getChoice() == ConferencePaperReview.NO_REVIEWING: #conference has no reviewing process
                return 0
            else: #conference has reviewing
                #if self.id in reviewableMaterials: #material is reviewable
                if isinstance(self, Reviewing): #material is reviewable
                    lastReview = self.owner.getReviewManager().getLastReview()
                    if lastReview.isAuthorSubmitted(): #author has submitted
                        refereeJudgement = lastReview.getRefereeJudgement()
                        if refereeJudgement.isSubmitted(): #referee has submitted judgement
                            if refereeJudgement.getJudgement() == "Accept":
                                return 4
                            elif refereeJudgement.getJudgement() == "Reject":
                                return 5
                            else:
                                #we should never arrive here because referee judgements that are 'To be corrected'
                                #or a custom state should imply a new review being created, so the state is back to 2
                                raise MaKaCError("RefereeJudgement should be 'Accept' or 'Reject' in this method")
                        else: #referee has not  submitted judgement
                            return 3
                    else: #author has not submitted
                        return 2
                else: #material is not reviewable
                    return 1
        else: #material does not belong to a contribution
            return 0

    def _getRepository( self ):
        dbRoot = DBMgr.getInstance().getDBConnection().root()
        try:
            fr = dbRoot["local_repositories"]["main"]
        except KeyError, e:
            fr = fileRepository.MaterialLocalRepository()
            dbRoot["local_repositories"] = OOBTree()
            dbRoot["local_repositories"]["main"] = fr
        return fr

    def hasFile( self, name ):
        for f in self.getResourceList():
            if f.getName() == name:
                return True
        return False

    def addResource( self, newRes, forcedFileId = None ):
        newRes.setOwner( self )
        newRes.setId( str( self.__resourcesIdGen.newCount() ) )
        newRes.archive( self._getRepository(), forcedFileId = forcedFileId )
        self.__resources[newRes.getId()] = newRes
        self.notifyModification()
        Logger.get('storage').debug("Finished storing resource %s for material %s" % (newRes.getId(), self.getLocator()))

    def getResourceList(self, sort=True):
        list = self.__resources.values()
        if sort:
            list.sort(utils.sortFilesByName)
        return list

    def getNbResources(self ):
        return len(self.__resources)

    def getResourceById( self, id ):
        return self.__resources[id]

    def removeResource( self, res ):
        if res.getId() in self.__resources.keys():
            del self.__resources[ res.getId() ]
            res.delete()
            self.notifyModification()
        if self.getMainResource() is not None and \
                self._mainResource.getId() == res.getId():
            self._mainResource = None

    def recoverResource(self, recRes):
        recRes.setOwner(self)
        self.__resources[recRes.getId()] = recRes
        recRes.recover()
        self.notifyModification()

    def getMainResource(self):
        try:
            if self._mainResource:
                pass
        except AttributeError:
            self._mainResource = None
        return self._mainResource

    def setMainResource(self, mr):
        self._mainResource = mr

    def delete(self):
        self.__ac.unlinkAvatars('access')
        for res in self.getResourceList():
            self.removeResource( res )
        if self.getReviewingState():
            self.owner._reviewManager = ReviewManager(self.owner)
        self.notify_protection_to_owner(self, delete=True)
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def canIPAccess( self, ip ):
        if not self.__ac.canIPAccess( ip ):
            return False
        if self.getOwner() != None:
            return self.getOwner().canIPAccess(ip)
        return True

    def isProtected( self ):
        # tells if a material is protected or not
        return (self.hasProtectedOwner() + self.getAccessProtectionLevel()) > 0

    def getAccessProtectionLevel( self ):
        return self.__ac.getAccessProtectionLevel()

    def isItselfProtected( self ):
        return self.__ac.isItselfProtected()


    def hasProtectedOwner( self ):
        if self.getOwner() != None:
            return self.getOwner().isProtected()
        return False


    @Updates (['MaKaC.conference.Material',
                 'MaKaC.conference.Minutes',
                 'MaKaC.conference.Paper',
                 'MaKaC.conference.Slides',
                 'MaKaC.conference.Video',
               'MaKaC.conference.Poster',
               'MaKaC.conference.Reviewing'], 'protection', lambda(x): int(x))

    def setProtection( self, private ):
        self.__ac.setProtection( private )
        self.notify_protection_to_owner(self)
        self._p_changed = 1

    def isHidden( self ):
        return self.__ac.isHidden()

    @Updates (['MaKaC.conference.Material',
               'MaKaC.conference.Minutes',
               'MaKaC.conference.Paper',
               'MaKaC.conference.Slides',
               'MaKaC.conference.Video',
               'MaKaC.conference.Poster',
               'MaKaC.conference.Reviewing'], 'hidden')
    def setHidden( self, hidden ):
        self.__ac.setHidden( hidden )
        self._p_changed = 1


    @Updates (['MaKaC.conference.Material',
               'MaKaC.conference.Minutes',
               'MaKaC.conference.Paper',
               'MaKaC.conference.Slides',
               'MaKaC.conference.Video',
               'MaKaC.conference.Poster',
               'MaKaC.conference.Reviewing'], 'accessKey')

    def setAccessKey( self, pwd="" ):
        self.__ac.setAccessKey(pwd)
        self._p_changed = 1

    def getAccessKey( self ):
        return self.__ac.getAccessKey()

    def grantAccess( self, prin ):
        self.__ac.grantAccess( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.linkTo(self, "access")
        self._p_changed = 1

    def revokeAccess( self, prin ):
        self.__ac.revokeAccess( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "access")
        self._p_changed = 1

    def canView( self, aw ):
        """tells whether the specified user has access to the current object
            or any of its sub-objects
        """
        if self.isHidden() and not self.canAccess( aw ):
            return False
        else:
            return True

    def isAllowedToAccess( self, user ):
        return (not self.isItselfProtected() and self.getOwner().isAllowedToAccess( user )) or self.__ac.canUserAccess( user ) or self.canUserModify(user)

    def canAccess( self, aw ):

        # Allow harvesters (Invenio, offline cache) to access
        # protected pages
        if self.__ac.isHarvesterIP(aw.getIP()):
            return True
        #####################################################

        if any(self._notify("isPluginTypeAdmin", {"user": aw.getUser()}) +
               self._notify("isPluginAdmin", {"user": aw.getUser(), "plugins": "any"})):
            return True

        # Managers have always access
        if self.canModify(aw):
            return True

        canUserAccess = self.isAllowedToAccess(aw.getUser())
        canIPAccess = self.canIPAccess(aw.getIP())
        if not self.isProtected():
            return canUserAccess or canIPAccess
        else:
            canKeyAccess = self.canKeyAccess(aw)
            return canUserAccess or canKeyAccess

    def canKeyAccess(self, aw):
        key = session.get('accessKeys', {}).get(self.getUniqueId())
        if self.getAccessKey():
            # Material has an access key => require this key
            if not key:
                return False
            return self.__ac.canKeyAccess(key)
        elif self.getConference():
            # If it has no key we check the conference's key
            conf_key = session.get('accessKeys', {}).get(self.getConference().getUniqueId())
            return self.getConference().canKeyAccess(aw, conf_key)
        return False

    def grantModification( self, prin ):
        self.__ac.grantModification( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.linkTo(self, "manager")
        self._p_changed = 1

    def revokeModification( self, prin ):
        self.__ac.revokeModification( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "manager")
        self._p_changed = 1

    def canModify( self, aw ):
        return self.canUserModify( aw.getUser() ) or (self.getConference() and self.getConference().canKeyModify( aw ))

    def canUserModify( self, user ):
        """Tells whether a user is allowed to modify the current contribution:
            only if the user is granted to modify the contribution or the user
            can modify any of its upper objects (i.e. conference or session).
        """
        return self.getOwner().canUserModify( user )

    def getModifKey( self ):
        return self.getConference().getModifKey()

    def getManagerList( self ):
        return self.__ac.getModifierList()

    def getAllowedToAccessList( self ):
        return self.__ac.getAccessList()

    def requireDomain( self, dom ):
        self.__ac.requireDomain( dom )
        self._p_changed = 1

    def freeDomain( self, dom ):
        self.__ac.freeDomain( dom )
        self._p_changed = 1

    def getDomainList( self ):
        return self.__ac.getRequiredDomainList()

    def getAccessController(self):
        return self.__ac

    def isBuiltin(self):
        return False

class BuiltinMaterial(Material):
    """
    Non-customizable material types
    """
    def isBuiltin(self):
        return True


class Reviewing(BuiltinMaterial):

    def __init__( self, materialData = None ):
        Material.__init__( self, materialData )
        self.id = "reviewing"

    def setId( self, newId ):
        return

    def getContribution(self):
        if isinstance(self.getOwner(), Review):
            return self.getOwner().getContribution()
        return Material.getContribution(self)

class Paper(BuiltinMaterial):

    def __init__( self, materialData = None ):
        Material.__init__( self, materialData )
        self.id = "paper"

    def setId( self, newId ):
        return



class Slides(BuiltinMaterial):

    def __init__( self, materialData = None ):
        Material.__init__( self, materialData )
        self.id = "slides"

    def setId( self, newId ):
        return



class Video(BuiltinMaterial):

    def __init__( self, materialData = None ):
        Material.__init__( self, materialData )
        self.id = "video"

    def setId( self, newId ):
        return

class Poster(BuiltinMaterial):

    def __init__( self, materialData = None ):
        Material.__init__( self, materialData )
        self.id = "poster"

    def setId( self, newId ):
        return

class Minutes(BuiltinMaterial):

    def __init__( self, materialData = None ):
        Material.__init__( self, materialData )
        self.id = "minutes"
        self.title = "Minutes"
        self.file = None

    def clone ( self, owner):
        mat = Minutes()
        mat.setTitle(self.getTitle())
        mat.setDescription(self.getDescription())
        mat.notifyModification()

        mat.setId(self.getId())
        mat.setOwner(owner)
        mat.setType(self.getType())

        mat.setProtection(self.getAccessController()._getAccessProtection())
        mat.setAccessKey(self.getAccessKey())
        lrep = self._getRepository()
        flist = lrep.getFiles()
        rlist = self.getResourceList()
        for r in rlist :
            if r.getId()=="minutes":
                mat.setText(self.getText())
            elif  isinstance(r,Link):
                newlink = Link()
                newlink.setOwner(mat)
                newlink.setName(r.getName())
                newlink.setDescription(r.getDescription())
                newlink.setURL(r.getURL())
                mat.addResource(newlink)
            elif isinstance(r,LocalFile):
                newfile = LocalFile()
                newfile.setOwner(mat)
                newfile.setName(r.getName())
                newfile.setDescription(r.getDescription())
                newfile.setFilePath(r.getFilePath())
                newfile.setFileName(r.getFileName())
                mat.addResource(newfile)
            else :
                raise Exception( _("Unexpected object type in Resource List : ")+str(type(r)))

        mat.setMainResource(self.getMainResource())

        return mat

    def setId( self, newId ):
        return

    def setTitle( self, newTitle ):
        self.title = newTitle.strip()
        self.notifyModification()

    def _setFile( self, forcedFileId = None ):
        #XXX: unsafe; it must be changed by mkstemp when migrating to python 2.3
        tmpFileName = tempfile.mktemp()
        fh = open(tmpFileName, "w")
        fh.write(" ")
        fh.close()
        self.file = LocalFile()
        self.file.setId("minutes")
        self.file.setName("minutes")
        self.file.setFilePath(tmpFileName)
        self.file.setFileName("minutes.txt")
        self.file.setOwner(self)
        self.file.archive(self._getRepository(), forcedFileId = forcedFileId)

    def setText( self, text, forcedFileId = None ):
        if self.file:
            self.file.delete()
        self._setFile(forcedFileId = forcedFileId)
        self.file.replaceContent( text )
        self.getOwner().notifyModification()

    def getText( self ):
        if not self.file:
            return ""
        return self.file.readBin()

    def getResourceList(self, sort=True):
        res = Material.getResourceList(self, sort=sort)
        if self.file:
            res.insert(0, self.file)
        return res

    def getResourceById( self, id ):
        if id.strip() == "minutes":
            return self.file
        return Material.getResourceById( self, id )

    def removeResource(self, res):
        Material.removeResource(self, res)
        if self.file is not None and res.getId().strip() == "minutes":
            self.file = None
            res.delete()
            self.notifyModification()

    def recoverResource(self, recRes):
        if recRes.getId() == "minutes":
            recRes.setOwner(self)
            self.file = recRes
            recRes.recover()
            self.notifyModification()
        else:
            Material.recoverResource(self, recRes)


class Resource(CommonObjectBase):
    """This is the base class for representing individual resources which can
        be included in material containers for lately being attached to
        conference objects (i.e. conferences, sessions or contributions). This
        class provides basic data and operations to handle this resources.
       Resources can be of serveral types (files, links, ...) which means
        different specialisations of this class.
       Attributes:
        id -- (string) Allows to assign the resource a unique identifier. It
            is normally used to uniquely identify the resource among other
            resources included in a certain material.
        name -- (string) Short description about the purpose or the contents
            of the resource.
        description - (string) detailed and varied information about the
            resource.
        __owner - (Material) reference to the material object in which the
            current resource is included.
    """

    fossilizes(IResourceMinimalFossil, IResourceFossil)

    def __init__( self, resData = None ):
        self.id = "not assigned"
        self.name = ""
        self.description = ""
        self._owner = None
        self.__ac = AccessController(self)
        self.pdfConversionRequestDate = None

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

    def clone( self, conf, protection=True ):
        res = self.__class__()
        res.setName(self.getName())
        res.setDescription(self.getDescription())
        res.setOwner(conf)
        res.notifyModification()
        res.setId(self.getId())

        if protection:
            res.setProtection(self.getAccessController()._getAccessProtection())
        #res.__ac = self.getAccessController()

        return res

    def notifyModification( self ):
        parent = self.getOwner()
        if parent:
            parent.setModificationDate()
        self._p_changed = 1

    def getLocator( self ):
        if self._owner == None:
            return Locator()
        lconf = self._owner.getLocator()
        lconf["resId"] = self.getId()
        return lconf

    def setId( self, newId ):
        self.id = newId.strip()

    def getId( self ):
        return self.id

    def getUniqueId( self ):
        """returns (string) the unique identifier of the item
        used mainly in the web session access key table
        for resources, it is the same as the father material since
        only the material can be protected with an access key"""
        return self.getOwner().getUniqueId()

    def setOwner(self, newOwner):
        self._owner = newOwner

    def getOwner( self ):
        return self._owner

    def getCategory( self ):
        #raise "%s:%s:%s"%(self.getOwner(), Material, isinstance(self.getOwner, Material))

        if isinstance(self.getOwner(), Category):
            return self.getOwner()
        if isinstance(self.getOwner(), Material):
            return self.getOwner().getCategory()
        return None

    def getConference( self ):
        # this check owes itself to the fact that some
        # protection checking functions call getConference()
        # directly on resources, without caring whether they
        # are owned by Conferences or Categories
        if self._owner is None or isinstance(self._owner, Category):
            return None
        else:
            return self._owner.getConference()

    def getSession( self ):
        return self._owner.getSession()

    def getContribution( self ):
        return self._owner.getContribution()

    def getSubContribution( self ):
        return self._owner.getSubContribution()

    @Updates (['MaKaC.conference.Link',
                 'MaKaC.conference.LocalFile'], 'name')
    def setName( self, newName ):
        self.name = newName.strip()
        self.notifyModification()

    def getName( self ):
        return self.name

    @Updates (['MaKaC.conference.Link',
                 'MaKaC.conference.LocalFile'], 'description')
    def setDescription( self, newDesc ):
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
        if self._owner is not None:
            self.notify_protection_to_owner(delete=True)
            self._owner.removeResource(self)
            self.__ac.unlinkAvatars('access')
            self._owner = None
            TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def canIPAccess( self, ip ):
        if not self.__ac.canIPAccess( ip ):
            return False
        if self.getOwner() != None:
            return self.getOwner().canIPAccess(ip)
        return True

    def isProtected( self ):
        # tells if a resource is protected or not
        return (self.hasProtectedOwner() + self.getAccessProtectionLevel()) > 0

    def getAccessProtectionLevel( self ):
        return self.__ac.getAccessProtectionLevel()

    def isItselfProtected( self ):
        return self.__ac.isItselfProtected()

    def hasProtectedOwner( self ):
        if self.getOwner() != None:
            return self.getOwner().isProtected()
        return False

    def notify_protection_to_owner(self, delete=False):
        # Resources can be attached to other objects (e.g. Registrant),
        # but we wish to trigger the notification only when attached to materials (except paper reviewing)
        if isinstance(self.getOwner(), Material) and not isinstance(self.getOwner(), Reviewing):
            self.getOwner().updateNonInheritingChildren(self, delete)

    @Updates (['MaKaC.conference.Link',
               'MaKaC.conference.LocalFile'],'protection', lambda(x): int(x))

    def setProtection( self, private ):
        self.__ac.setProtection( private )
        self.notify_protection_to_owner()

    def grantAccess( self, prin ):
        self.__ac.grantAccess( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.linkTo(self, "access")

    def revokeAccess( self, prin ):
        self.__ac.revokeAccess( prin )
        if isinstance(prin, MaKaC.user.Avatar):
            prin.unlinkTo(self, "access")

    def canView( self, aw ):
        """tells whether the specified user has access to the current object
            or any of its sub-objects
        """
        return self.canAccess( aw )

    def isAllowedToAccess( self, user ):
        return self.__ac.canUserAccess( user ) or self.canUserModify( user ) or (not self.isItselfProtected() and self.getOwner().isAllowedToAccess( user ))

    def canAccess( self, aw ):
        # Allow harvesters (Invenio, offline cache) to access
        # protected pages
        if self.__ac.isHarvesterIP(aw.getIP()):
            return True
        #####################################################

        if any(self._notify("isPluginTypeAdmin", {"user": aw.getUser()}) +
               self._notify("isPluginAdmin", {"user": aw.getUser(), "plugins": "any"})):
            return True

        # Managers have always access
        if self.canModify(aw):
            return True

        if not self.canIPAccess(aw.getIP()) and not self.canUserModify(aw.getUser()) and \
                not self.isAllowedToAccess(aw.getUser()):
            return False
        if not self.isProtected():
            return True
        flag = self.isAllowedToAccess( aw.getUser() )
        return flag or self.canKeyAccess(aw) or self.getOwner().canKeyAccess(aw) or \
                (self.getConference() != None and self.getConference().canKeyAccess(aw) and self.getAccessKey() == "") or \
                (self.getConference() != None and self.getConference().canKeyAccess(aw) and self.getAccessKey() == self.getConference().getAccessKey())

    def grantModification( self, prin ):
        self.__ac.grantModification( prin )

    def revokeModification( self, prin ):
        self.__ac.revokeModification( prin )

    def canModify( self, aw ):
        return self.canUserModify( aw.getUser() ) or (self.getConference() and self.getConference().canKeyModify( aw ))

    def canUserModify( self, user ):
        """Tells whether a user is allowed to modify the current contribution:
            only if the user is granted to modify the contribution or the user
            can modify any of its upper objects (i.e. conference or session).
        """
        return self.getOwner().canUserModify( user )

    def getModifKey( self ):
        return self.getConference().getModifKey()

    def getManagerList( self ):
        return self.__ac.getModifierList()

    def getAllowedToAccessList( self ):
        return self.__ac.getAccessList()

    def getURL( self ):
        return ""

    def requireDomain( self, dom ):
        self.__ac.requireDomain( dom )

    def freeDomain( self, dom ):
        self.__ac.freeDomain( dom )

    def getDomainList( self ):
        return self.__ac.getRequiredDomainList()

    def getAccessController(self):
        return self.__ac

    def getAccessKey(self):
        if self.getOwner() is not None:
            return self.getOwner().getAccessKey()
        return ""

    def canKeyAccess(self, aw):
        accessKey = self.getAccessKey()
        key = session.get('accessKeys', {}).get(self.getUniqueId())
        if not key:
            return False
        elif accessKey and key == accessKey:
            return True
        elif not accessKey and key == self.getConference().getAccessKey():
            return True
        return False

    def getReviewingState(self):
        """ Returns the reviewing state of a resource, which is the reviewing state of the material to which it belongs.
            The state is represented by an integer:
            0 : there's no reviewing state because the resource doesn't belong to a material,
                the material does not belong to a contribution, or the conference does not have reviewing.
            1 : the material is not subject to reviewing, because this kind of material is not reviewable in the conference
            2 : the material is subject to reviewing, but has not been submitted yet by the author
            3 : the material is subject to reviewing, has been submitted by the author, but has not been judged yet
            4 : the material is subject to reviewing, has been submitted by the author, and has been judged as Accepted
            5 : the material is subject to reviewing, has been submitted by the author, and has been judged as Rejected
        """
        if isinstance(self.getOwner(), Material):
            return self.getOwner().getReviewingState()
        else: #ressource does not belong to a material
            return 0

    def setPDFConversionRequestDate( self, newPdfConversionRequestDate ):
        self.pdfConversionRequestDate = newPdfConversionRequestDate

    def getPDFConversionStatus(self):

        if not hasattr(self, "pdfConversionRequestDate"):
            self.pdfConversionRequestDate = None

        if self.pdfConversionRequestDate is not None and self.pdfConversionRequestDate + timedelta(seconds=50) > nowutc() :
            return 'converting'
        return None

class Link(Resource):
    """Specialises Resource class in order to represent web links. Objects of
        this class will contain necessary information to include in a conference
        object links to internet resources through a URL.
       Params:
        url -- (string) Contains the URL to the internet target resource.
    """

    fossilizes(ILinkMinimalFossil, ILinkFossil)

    def __init__( self, resData = None ):
        Resource.__init__( self, resData )
        self.url = ""

    def clone( self, conf ):
        link = Resource.clone(self, conf)
        link.setURL(self.getURL())
        return link

    @Updates ('MaKaC.conference.Link', 'url')
    def setURL( self, newURL ):
        self.url = newURL.strip()
        self.notifyModification()

    def getURL( self ):
        return self.url

    def getLocator(self):
        locator = Resource.getLocator(self)
        locator['fileExt'] = 'link'
        return locator

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

    fossilizes(ILocalFileMinimalFossil, ILocalFileFossil, ILocalFileExtendedFossil, ILocalFileAbstractMaterialFossil)

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
        if self.fileName == 'minutes.txt' and isinstance(self._owner, Minutes):
            # Hack to get a html extension when viewing minutes
            locator['fileExt'] = 'html'
        else:
            try:
                locator['fileExt'] = self.fileType.lower() or os.path.splitext(self.fileName)[1].lower().lstrip('.')
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

    def replaceContent( self, newContent ):
        if not self.isArchived():
            raise MaKaCError( _("File not available until it has been archived") , _("File Archiving"))
        self.__repository.replaceContent( self.__archivedId, newContent )

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

    def unArchive(self):
    # Not used.
        self.__repository = None
        self.__archivedId = ""

    def recover(self):
        if not self.isArchived():
            raise Exception( _("File is not archived, so it cannot be recovered."))
        if not self.__repository:
            raise Exception( _("Destination repository not set."))
        self.__repository.recoverFile(self)
        Resource.recover(self)
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
        self.subTracks = {}
        self.__SubTrackGenerator = Counter()
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

        for co in self.getCoordinatorList() :
            tr.addCoordinator(co)

        for subtr in self.getSubTrackList() :
            tr.addSubTrack(subtr.clone())

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
            abstract.removeTrack( self )

        # we must notify each contribution in the track about the deletion of the
        #   track
        while len(self._contributions)>0:
            k = self._contributions.keys()[0]
            contrib = self._contributions[k]
            del self._contributions[k]
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

    def canModify( self, aw ):
        return self.conference.canModify( aw )

    def canUserModify( self, av ):
        return self.conference.canUserModify( av )

    def canView( self, aw ):
        return self.conference.canView( aw )

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

    def __generateNewSubTrackId( self ):
        return str(self.__SubTrackGenerator.newCount())

    def addSubTrack( self, newSubTrack ):
        """Registers the contribution passed as parameter within the session
            assigning it a unique id.
        """
        if newSubTrack in self.subTracks.values():
            return
        subTrackId = newSubTrack.getId()
        if subTrackId == "not assigned":
            subTrackId = self.__generateNewSubTrackId()
        self.subTracks[subTrackId] = newSubTrack
        newSubTrack.setTrack( self )
        newSubTrack.setId( subTrackId )
        self.notifyModification()

    def removeSubTrack( self, subTrack ):
        """Removes the indicated contribution from the session
        """
        if subTrack in self.subTracks.values():
            del self.subTracks[ subTrack.getId() ]
            subTrack.setTrack( None )
            subTrack.delete()
            self.notifyModification()

    def recoverSubTrack(self, subTrack):
        self.addSubTrack(subTrack)
        subTrack.recover()

    def newSubTrack( self ):
        st = SubTrack()
        self.addSubTrack( st )
        return st

    def getSubTrackById( self, id ):
        if self.subTracks.has_key( id ):
            return self.subTracks[ id ]
        return None

    def getSubTrackList( self ):
        return self.subTracks.values()

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
            #abstract.removeTrack( self )

    def addCoordinator( self, av ):
        """Grants coordination privileges to user.

            Arguments:
                av -- (MaKaC.user.Avatar) the user to which
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
            av -- (MaKaC.user.Avatar) user for which coordination privileges
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
            av -- (MaKaC.user.Avatar) user to be checke

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

    def getModifKey( self ):
        return self.getConference().getModifKey()

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


class SubTrack(CoreObject):

    def __init__( self ):
        self.track = None
        self.id = "not assigned"
        self.title = ""
        self.description = ""

    def clone(self):
        sub = SubTrack()
        sub.setDescription(self.getDescription())
        sub.setTitle(self.getTitle())

        return sub


    def delete(self):
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def canModify( self, aw ):
        return self.track.canModify( aw )

    def canView( self, aw ):
        return self.track.canView( aw )

    def notifyModification( self ):
        parent = self.getTrack()
        if parent:
            parent.setModificationDate()
        self._p_changed = 1

    def getLocator( self ):
        """Gives back a globaly unique identification encapsulated in a Locator
            object for the session instance
        """
        if self.track == None:
            return Locator()
        lconf = self.track.getLocator()
        lconf["subTrackId"] = self.getId()
        return lconf

    def setTrack(self, track):
        self.track = track
        if track == None:
            return

    def getTrack( self ):
        return self.track

    def getOwner( self ):
        return self.getTrack()

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


class ContributionType(Persistent):

    def __init__(self, name, description, conference):
        self._id = ""
        self._name = name
        self._description = description
        self._conference = conference

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getName(self):
        return self._name

    def setName(self, name):
        self._name = name

    def getDescription(self):
        return self._description

    def setDescription(self, desc):
        self._description = desc

    def getConference(self):
        return self._conference

    def setConference(self, conf):
        self._conference = conf

    def getLocator( self ):
        if self._conference == None:
            return Locator()
        lconf = self._conference.getLocator()
        lconf["contribTypeId"] = self.getId()
        return lconf

    def canModify(self, aw):
        return self._conference.canModify(aw)

    def delete(self):
        self.setConference(None)
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    def clone(self, conference ):
        type = ContributionType(self.getName(), self.getDescription(),conference)
        return type


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
