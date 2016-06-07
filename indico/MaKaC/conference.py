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

from sqlalchemy.orm import joinedload

from indico.modules.events.features import event_settings as features_event_settings
from indico.modules.events.features.util import get_feature_definitions, get_enabled_features
from MaKaC.common.timezoneUtils import datetimeToUnixTimeInt
from MaKaC.fossils.conference import (IConferenceMinimalFossil, IConferenceEventInfoFossil, IConferenceFossil,
                                      ICategoryFossil)
from MaKaC.common.fossilize import fossilizes, Fossilizable
from MaKaC.common.url import ShortURLMapper
from MaKaC.common.PickleJar import Updates
from indico.modules.events.cloning import EventCloner
from indico.modules.events.models.events import Event
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.modules.events.sessions import session_settings
from indico.modules.categories.models.legacy_mapping import LegacyCategoryMapping
from indico.modules.events.util import track_time_changes
from indico.modules.users.legacy import AvatarUserWrapper
from indico.modules.groups.legacy import GroupWrapper
from indico.util.caching import memoize_request
from indico.util.i18n import L_
from indico.util.string import return_ascii, is_legacy_id, to_unicode


import os
import stat
from datetime import datetime
from operator import methodcaller

from MaKaC.paperReviewing import ConferencePaperReview as ConferencePaperReview
from MaKaC.abstractReviewing import ConferenceAbstractReview as ConferenceAbstractReview

from flask import session, request, has_request_context
from pytz import timezone
from pytz import all_timezones

from persistent import Persistent
from BTrees.OOBTree import OOBTree, OOTreeSet
from MaKaC.common import indexes
from MaKaC.common.timezoneUtils import nowutc
import MaKaC.fileRepository as fileRepository
import MaKaC.review as review
from MaKaC.common.Counter import Counter
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.common.Locators import Locator
from MaKaC.accessControl import AccessController, AccessWrapper
from MaKaC.errors import MaKaCError, TimingError, NotFoundError, FormValuesError
from MaKaC.trashCan import TrashCanManager
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.badge import BadgeTemplateManager
from MaKaC.poster import PosterTemplateManager
from MaKaC.i18n import _

import zope.interface

from indico.core import signals
from indico.core.db import DBMgr, db
from indico.core.db.sqlalchemy.core import ConstraintViolated
from indico.core.db.event import SupportInfo
from indico.core.config import Config
from indico.core.index import IIndexableByStartDateTime, IUniqueIdProvider, Catalog
from indico.util.date_time import utc_timestamp, format_datetime
from indico.util.redis import write_client as redis_write_client
from indico.util.user import unify_user_args
from indico.util.redis import avatar_links
from indico.web.flask.util import url_for


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
        if isinstance(self, Category):
            return self.as_new.attached_items
        elif isinstance(self, Conference):
            return get_attached_items(self.as_event, include_empty=False, include_hidden=False, preload_event=True)
        else:
            raise ValueError("Object of type '{}' cannot have attachments".format(type(self)))


class CategoryManager(ObjectHolder):
    idxName = "categories"
    counterName = "CATEGORY"

    def getById(self, id_, quiet=False):
        orig_id = id_ = str(id_)
        if is_legacy_id(id_):
            mapping = LegacyCategoryMapping.find_first(legacy_category_id=id_)
            id_ = str(mapping.category_id) if mapping is not None else None
        category = self._getIdx().get(id_) if id_ is not None else None
        if category is None and not quiet:
            raise KeyError(id_ if id_ is not None else orig_id)
        return category

    def add(self, category):
        ObjectHolder.add(self, category)

    def remove(self, category):
        ObjectHolder.remove(self, category)
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
        self.conferences = OOTreeSet()
        self._numConferences = 0
        self.owner = None
        self._defaultStyle = {"simple_event": "", "meeting": ""}
        self._order = 0
        self.__ac = AccessController(self)
        self.__confCreationRestricted = 1
        self.__confCreators = []
        self._visibility = 999
        self._icon = None
        self._timezone = ""
        self._notifyCreationList = ""

    @property
    @memoize_request
    def as_new(self):
        return db.m.Category.get(int(self.id))

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        return cmp(self.getId(), other.getId())

    @return_ascii
    def __repr__(self):
        path = '/'.join(self.getCategoryPathTitles()[:-1])
        return '<Category({0}, {1}, {2})>'.format(self.getId(), self.getName(), path)

    @property
    def url(self):
        if self.isRoot():
            return url_for('misc.index')
        else:
            return url_for('category.categoryDisplay', self)

    @property
    def attachment_folders(self):
        return db.m.AttachmentFolder.find(object=self)

    @property
    def is_protected(self):
        return self.isProtected()

    def can_access(self, user, allow_admin=True):
        # used in attachments module
        if not allow_admin:
            raise NotImplementedError('can_access(..., allow_admin=False) is unsupported until ACLs are migrated')
        return self.canView(AccessWrapper(user.as_avatar if user else None))

    def can_manage(self, user, role=None, allow_admin=True):
        # used in attachments module
        if role is not None:
            raise NotImplementedError('can_access(..., role=...) is unsupported until ACLs are migrated')
        if not allow_admin:
            raise NotImplementedError('can_access(..., allow_admin=False) is unsupported until ACLs are migrated')
        return self.canUserModify(user.as_avatar if user else None)

    def getAccessController(self):
        return self.__ac

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

    def getTitle(self):
        return self.name

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
            if isinstance(prin, AvatarUserWrapper):
                prin.unlinkTo(self, "access")
        for prin in self.__ac.getModifierList():
            if isinstance(prin, AvatarUserWrapper):
                prin.unlinkTo(self, "manager")
        TrashCanManager().add(self)

        signals.category.deleted.send(self)

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

        signals.category.moved.send(self, old_parent=oldOwner, new_parent=newOwner)

    def getName(self):
        return self.name

    def setName(self, newName):
        oldName = self.name
        self.name = newName.strip()
        signals.category.title_changed.send(self, old=oldName, new=newName)

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
        signals.event.moved.send(conf, old_parent=self, new_parent=toCateg)

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
            self._p_changed = True
            sc.setOwner(None)

    def newSubCategory(self, protection):
        cm = CategoryManager()
        sc = Category()
        cm.add(sc)

        # set the protection
        sc.setProtection(protection)

        Catalog.getIdx('categ_conf_sd').add_category(sc.getId())
        signals.category.created.send(sc, parent=self)

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

    @unify_user_args
    def newConference(self, creator, title, start_dt, end_dt, timezone):
        conf = Conference()
        event = Event(creator=creator, category_id=int(self.id), title=to_unicode(title).strip(),
                      start_dt=start_dt, end_dt=end_dt, timezone=timezone)
        ConferenceHolder().add(conf, event)
        self._addConference(conf)

        signals.event.created.send(event)

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

        res = sorted(self.conferences, key=methodcaller('getStartDate'))

        if sortType == 2:
            res.sort(key=lambda x: x.getTitle().lower().strip())
        elif sortType == 3:
            res.sort(key=lambda x: x.getTitle().lower().strip(), reversed=True)
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

    def setIcon(self, iconFile):
        iconFile.setOwner(self)
        iconFile.setId("icon")
        iconFile.archive(self._getRepository())
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
        if isinstance(prin, AvatarUserWrapper):
            prin.linkTo(self, "manager")

    def revokeModification(self, prin):
        self.__ac.revokeModification(prin)
        if isinstance(prin, AvatarUserWrapper):
            prin.unlinkTo(self, "manager")

    def canModify(self, aw_or_user):
        if hasattr(aw_or_user, 'getUser'):
            aw_or_user = aw_or_user.getUser()
        return self.canUserModify(aw_or_user)

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
        if oldProtection != private:
            signals.category.protection_changed.send(self, old=oldProtection, new=private)

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
            return self.canIPAccess(request.remote_addr) or \
                self.isAllowedToCreateConference(aw.getUser()) or \
                self.isAllowedToAccess(aw.getUser())
        return self.isAllowedToCreateConference(aw.getUser()) or \
            self.isAllowedToAccess(aw.getUser())

    def grantAccess(self, prin):
        self.__ac.grantAccess(prin)
        if isinstance(prin, AvatarUserWrapper):
            prin.linkTo(self, "access")

    def revokeAccess(self, prin):
        self.__ac.revokeAccess(prin)
        if isinstance(prin, AvatarUserWrapper):
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
            if isinstance(prin, AvatarUserWrapper):
                prin.linkTo(self, "creator")
            self._p_changed = 1

    def revokeConferenceCreation(self, prin):
        if prin in self.__confCreators:
            self.__confCreators.remove(prin)
            if isinstance(prin, AvatarUserWrapper):
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
            if isinstance(group, GroupWrapper):
                if group.containsUser(av):
                    return 1
        return 0

    def canCreateConference(self, av):
        if not self.isConferenceCreationRestricted():
            return 1
        return self.isAllowedToCreateConference(av)

    def requireDomain(self, dom):
        self.__ac.requireDomain(dom)
        signals.category.domain_access_granted.send(self, domain=dom)

    def freeDomain(self, dom):
        self.__ac.freeDomain(dom)
        signals.category.domain_access_revoked.send(self, domain=dom)


    def getDomainList(self):
        return self.__ac.getRequiredDomainList()

    def notifyModification(self, raiseEvent=True):
        """Method called to notify the current category has been modified.
        """
        if raiseEvent:
            signals.category.data_changed.send(self)
        self._p_changed = 1


class Conference(CommonObjectBase):
    """This class represents the real world conferences themselves. Objects of
        this class will contain basic data about the confence and will provide
        access to other objects representing certain parts of the conferences
        (ex: contributions, sessions, ...).
    """

    fossilizes(IConferenceFossil, IConferenceMinimalFossil, IConferenceEventInfoFossil)

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
        self.__owners = []
        self._modificationDS = self._creationDS = nowutc()

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

        Catalog.getIdx('categ_conf_sd').index_obj(self)

    def unindexConf( self ):
        calIdx = indexes.IndexesHolder().getIndex('calendar')
        calIdx.unindexConf(self)
        catDateIdx = indexes.IndexesHolder().getIndex('categoryDate')
        catDateAllIdx = indexes.IndexesHolder().getIndex('categoryDateAll')
        catDateIdx.unindexConf(self)
        catDateAllIdx.unindexConf(self)

        Catalog.getIdx('categ_conf_sd').unindex_obj(self)

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

    def getCreationDate( self ):
        """Returns the date in which the conference was created"""
        return self._creationDS

    def getAdjustedCreationDate( self, tz ):
        """Returns the date in which the conference was created"""
        return self._creationDS.astimezone(timezone(tz))

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

    def delete(self, user=None):
        """deletes the conference from the system.
        """
        signals.event.deleted.send(self, user=user)

        # will have to remove it from all the owners (categories) and the
        #   conference registry
        ConferenceHolder().remove(self)
        for owner in self.__owners[:]:
            owner.removeConference(self, notify=False)

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

        # Pre-check for moveEntries

        self.unindexConf()

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

        # reindex the conference
        self.indexConf()

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
        if not indexes.BTREE_MIN_UTC_DATE <= sDate <= indexes.BTREE_MAX_UTC_DATE:
            raise FormValuesError(_("The start date must be between {} and {}.").format(
                format_datetime(indexes.BTREE_MIN_UTC_DATE),
                format_datetime(indexes.BTREE_MAX_UTC_DATE)))
        if check != 0:
            self.verifyStartDate(sDate)
        oldSdate = self.getStartDate()
        diff = sDate - oldSdate

        if index:
            self.unindexConf()
        if moveEntries:
            # If the start date changed, we move entries inside the timetable
            self.as_event.move_start_dt(sDate)
        else:
            self.startDate = sDate
        #datetime object is non-mutable so we must "force" the modification
        #   otherwise ZODB won't be able to notice the change
        self.notifyModification()
        if index:
            self.indexConf()

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
        signals.event.domain_access_granted.send(self, domain=dom)

    def freeDomain(self, dom):
        self.__ac.freeDomain(dom)
        signals.event.domain_access_revoked.send(self, domain=dom)

    def getDomainList(self):
        return self.__ac.getRequiredDomainList()

    def isProtected(self):
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
            signals.event.protection_changed.send(self, old=oldValue, new=private)

    def grantAccess( self, prin ):
        self.__ac.grantAccess( prin )
        if isinstance(prin, AvatarUserWrapper):
            prin.linkTo(self, "access")

    def revokeAccess( self, prin ):
        self.__ac.revokeAccess( prin )
        if isinstance(prin, AvatarUserWrapper):
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
        if self.__ac.canUserAccess(av) or self.canUserModify(av):
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

        return False

    def canAccess( self, aw ):
        """Tells whether an access wrapper is allowed to access the current
            conference: when the conference is protected, only if the user is a
            chair or is granted to access the conference, when the client ip is
            not restricted.
        """

        # Allow harvesters (Invenio, offline cache) to access
        # protected pages
        if has_request_context() and self.__ac.isHarvesterIP(request.remote_addr):
            return True

        if self.isProtected():
            if self.isAllowedToAccess(aw.getUser()):
                return True
            else:
                return self.canKeyAccess(aw) or self.canModify(aw)
        else:
            # Domain control is triggered just for PUBLIC events
            return self.canIPAccess(request.remote_addr) or self.canModify(aw)

    def canKeyAccess(self, aw, key=None):
        accessKey = self.getAccessKey()
        if not accessKey:
            return False
        return key == accessKey or session.get('accessKeys', {}).get(self.getUniqueId()) == accessKey

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

    def clone( self, startDate, options, eventManager=None, userPerformingClone = None ):
        # startDate must be in the timezone of the event (to avoid problems with daylight-saving times)
        cat = self.getOwnerList()[0]
        managing = options.get("managing",None)
        if managing is not None:
            creator = managing
        else:
            creator = self.as_event.creator
        conf = cat.newConference(creator, title=self.getTitle(), start_dt=self.getStartDate(), end_dt=self.getEndDate(),
                                 timezone=self.getTimezone())
        if managing is not None:
            with conf.as_event.logging_disabled:
                conf.as_event.update_principal(managing.user, full_access=True)
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

        db_root = DBMgr.getInstance().getDBConnection().root()
        if db_root.has_key( "webfactoryregistry" ):
            confRegistry = db_root["webfactoryregistry"]
        else:
            confRegistry = OOBTree.OOBTree()
            db_root["webfactoryregistry"] = confRegistry
        # if the event is a meeting or a lecture
        if confRegistry.get(str(self.getId()), None) is not None :
            confRegistry[str(conf.getId())] = confRegistry[str(self.getId())]
        # if it's a conference, no web factory is needed
        # Tracks in a conference
        if options.get("tracks",False) :
            for tr in self.getTrackList() :
                conf.addTrack(tr.clone(conf))
        # access and modification keys
        if options.get("keys", False) :
            conf.setAccessKey(self.getAccessKey())
        # Access Control cloning
        if options.get("access", False):
            conf.setProtection(self.getAccessController()._getAccessProtection())
            for entry in self.as_event.acl_entries:
                conf.as_event.update_principal(entry.principal, read_access=entry.read_access,
                                               full_access=entry.full_access, roles=entry.roles, quiet=True)
            for user in self.getAllowedToAccessList():
                conf.grantAccess(user)
            session_settings_data = session_settings.get_all(self)
            session_settings.set_multi(conf, {
                'coordinators_manage_contributions': session_settings_data['coordinators_manage_contributions'],
                'coordinators_manage_blocks': session_settings_data['coordinators_manage_blocks']
            })
            for domain in self.getDomainList():
                conf.requireDomain(domain)
        conf.notifyModification()

        # Copy the list of enabled features
        features_event_settings.set_multi(conf, features_event_settings.get_all(self))
        feature_definitions = get_feature_definitions()
        for feature in get_enabled_features(conf):
            feature_definitions[feature].enabled(conf)

        # Run the new modular cloning system
        EventCloner.run_cloners(self.as_event, conf.as_event)
        signals.event.cloned.send(self.as_event, new_event=conf.as_event)
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

    def indexConf(self):
        pass

    def notifyModification(self, *args, **kwargs):
        pass

    def __init__(self):
        Conference.__init__(self, id='default')


class ConferenceHolder( ObjectHolder ):
    """Specialised ObjectHolder dealing with conference objects. It gives a
            common entry point and provides simple methods to access and
            maintain the collection of stored conferences (DB).
    """
    idxName = "conferences"
    counterName = "CONFERENCE"

    def _newId(self):
        raise RuntimeError('Tried to get new event id from zodb')

    def add(self, conf, event):
        db.session.add(event)
        db.session.flush()
        conf.setId(event.id)
        if conf.id in self._getIdx():
            raise RuntimeError('{} is already in ConferenceHolder'.format(conf.id))
        ObjectHolder.add(self, conf)
        with event.logging_disabled:
            event.update_principal(event.creator, full_access=True)
        db.session.flush()

    def getById(self, id, quiet=False):
        if id == 'default':
            return CategoryManager().getDefaultConference()

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

    def getCategory(self):
        return self.getOwner() if isinstance(self.getOwner(), Category) else None

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
