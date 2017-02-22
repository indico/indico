# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from BTrees.OOBTree import OOBTree
from flask import request, has_request_context, session
from persistent import Persistent
from pytz import all_timezones, timezone, utc
from sqlalchemy.orm import joinedload

from indico.core import signals
from indico.core.config import Config
from indico.core.db import DBMgr, db
from indico.modules.events.cloning import EventCloner
from indico.modules.events.features import features_event_settings
from indico.modules.events.models.legacy_mapping import LegacyEventMapping
from indico.modules.events.operations import create_event
from indico.modules.users.legacy import AvatarUserWrapper
from indico.util.caching import memoize_request
from indico.util.i18n import _
from indico.util.string import return_ascii, is_legacy_id
from indico.util.user import unify_user_args

from MaKaC import fileRepository
from MaKaC.common.fossilize import Fossilizable
from MaKaC.common.Locators import Locator
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.common.PickleJar import Updates
from MaKaC.errors import MaKaCError, NotFoundError
from MaKaC.paperReviewing import ConferencePaperReview as ConferencePaperReview
from MaKaC.trashCan import TrashCanManager


class CoreObject(Persistent):
    pass


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


def warn_on_access(fn):
    import warnings
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if Config.getInstance().getDebug():
            warnings.warn('Called {}'.format(fn.__name__), stacklevel=2)
        return fn(*args, **kwargs)

    return wrapper


class Conference(CommonObjectBase):
    """This class represents the real world conferences themselves. Objects of
        this class will contain basic data about the confence and will provide
        access to other objects representing certain parts of the conferences
        (ex: contributions, sessions, ...).
    """

    def __init__(self, id=''):
        self.id = id
        self._confPaperReview = ConferencePaperReview(self)

    @return_ascii
    def __repr__(self):
        return '<Conference({0}, {1}, {2})>'.format(self.id, self.title, self.startDate)

    @property
    @warn_on_access
    def startDate(self):
        return self.as_event.start_dt

    @property
    @warn_on_access
    def endDate(self):
        return self.as_event.end_dt

    @property
    @warn_on_access
    def timezone(self):
        return self.as_event.timezone.encode('utf-8')

    @property
    @warn_on_access
    def title(self):
        return self.as_event.title.encode('utf-8')

    @property
    @warn_on_access
    def description(self):
        return self.as_event.description.encode('utf-8')

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
    @warn_on_access
    def tz(self):
        from MaKaC.common.timezoneUtils import DisplayTZ
        return DisplayTZ(conf=self).getDisplayTZ()

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

    def getConfPaperReview(self):
        if not hasattr(self, "_confPaperReview"):
            self._confPaperReview = ConferencePaperReview(self)
        return self._confPaperReview

    @memoize_request
    def getContribTypeList(self):
        return self.as_event.contribution_types.all()

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
        return self.as_event.short_external_url

    @warn_on_access
    def getId( self ):
        """returns (string) the unique identifier of the conference"""
        return self.id

    def getUniqueId( self ):
        """returns (string) the unique identiffier of the item"""
        return "a%s" % self.id

    def setId(self, newId):
        """changes the current unique identifier of the conference to the
            one which is specified"""
        self.id = str(newId)

    def getLocator( self ):
        """Gives back (Locator) a globaly unique identification encapsulated in
            a Locator object for the conference instance """
        d = Locator()
        d["confId"] = self.id
        return d

    def delete(self, user=None):
        signals.event.deleted.send(self, user=user)
        ConferenceHolder().remove(self)
        TrashCanManager().add(self)
        self._p_changed = True

    def getConference( self ):
        return self

    @warn_on_access
    def getStartDate(self):
        """returns (datetime) the starting date of the conference"""
        return self.startDate

    @warn_on_access
    def getAdjustedStartDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        return self.getStartDate().astimezone(timezone(tz))

    @warn_on_access
    def getEndDate(self):
        """returns (datetime) the ending date of the conference"""
        return self.endDate

    @warn_on_access
    def getAdjustedEndDate(self,tz=None):
        if not tz:
            tz = self.getTimezone()
        if tz not in all_timezones:
            tz = 'UTC'
        return self.getEndDate().astimezone(timezone(tz))

    @warn_on_access
    def getTimezone(self):
        try:
            return self.timezone
        except AttributeError:
            return 'UTC'

    @warn_on_access
    def getTitle(self):
        """returns (String) the title of the conference"""
        return self.title

    def getSessionById(self, sessionId):
        """Returns the session from the conference list corresponding to the
            unique session id specified
        """
        if not sessionId.isdigit():
            return None
        return self.as_event.get_session(friendly_id=int(sessionId))

    def getReviewManager(self, contrib):
        return self.getConfPaperReview().getReviewManager(contrib)

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

    def clone(self, startDate):
        # startDate is in the timezone of the event
        old_event = self.as_event
        start_dt = old_event.tzinfo.localize(startDate).astimezone(utc)
        end_dt = start_dt + old_event.duration
        data = {
            'start_dt': start_dt,
            'end_dt': end_dt,
            'timezone': old_event.timezone,
            'title': old_event.title,
            'description': old_event.description,
            'visibility': old_event.visibility
        }
        event = create_event(old_event.category, old_event.type_, data,
                             features=features_event_settings.get(self, 'enabled'),
                             add_creator_as_manager=False)
        conf = event.as_legacy

        # Run the new modular cloning system
        EventCloner.run_cloners(old_event, event)
        signals.event.cloned.send(old_event, new_event=event)

        # Grant access to the event creator -- must be done after modular cloners
        # since cloning the event ACL would result in a duplicate entry
        with event.logging_disabled:
            event.update_principal(session.user, full_access=True)

        return conf

    def hasEnabledSection(self, section):
        # This hack is there since there is no more enable/disable boxes
        # in the conference managment area corresponding to those features.
        # Until the managment area is improved to get a more user-friendly
        # way of enabling/disabling those features, we always make them
        # available for the time being, but we keep the previous code for
        # further improvements
        return True


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
        event.assign_id()
        conf.setId(event.id)
        if conf.id in self._getIdx():
            raise RuntimeError('{} is already in ConferenceHolder'.format(conf.id))
        ObjectHolder.add(self, conf)

    def getById(self, id, quiet=False):
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
