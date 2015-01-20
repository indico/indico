# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import MaKaC.conference as conference
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
from indico.core.config import Config
from MaKaC.i18n import _

class MaterialFactory:
    """Defines the class base for Material factories.
    """
    _id = ""
    _title = ""
    _iconURL = ""
    _creationWC = None
    _modificationURL = ""
    _needsCreationPage = True
    _materialKlasses=[]

    def getId(cls):
        return cls._id
    getId = classmethod( getId )

    def getTitle(cls):
        return _(cls._title)
    getTitle = classmethod( getTitle )

    def getIconURL(cls):
        return cls._iconURL
    getIconURL = classmethod( getIconURL )

    def get( owner ):
        """returns the material"""
        return None
    get = staticmethod(get)

    def remove( owner ):
        """performs the deletion of the material from the owner"""
        return
    remove = staticmethod( remove )

    def canAdd( target ):
        """checks whether the material can be added to the target object"""
        return True
    canAdd = staticmethod( canAdd )

    def canDelete( target ):
        """checks whether the material can be deleted from the target object"""
        return False
    canDelete = staticmethod( canDelete )

    def getModificationURL( cls, mat ):
        """returns the URL for accessing to the modification view of the
            material"""
        return cls._modificationURL
    getModificationURL = classmethod(getModificationURL)

    def getCreationWC( cls, owner ):
        if not cls._creationWC:
            return None
        return cls._creationWC(owner, cls)
    getCreationWC = classmethod( getCreationWC )

    def needsCreationPage( cls ):
        return cls._needsCreationPage
    needsCreationPage = classmethod( needsCreationPage )

    def create( cls, target ):
        return None
    create = classmethod( create )

    def appliesToMaterial(cls,mat):
        for klass in cls._materialKlasses:
            if isinstance(mat,klass):
                return True
        return False
    appliesToMaterial=classmethod(appliesToMaterial)

class PaperFactory(MaterialFactory):

    _id = "paper"
    _title = "Paper"
    _iconURL = Config.getInstance().getSystemIconURL("paper")
    _materialKlasses=[conference.Paper]
    _needsCreationPage = False

    def get( owner ):
        """returns the material"""
        return owner.getPaper()
    get = staticmethod(get)

    def remove( owner ):
        """performs the deletion of the paper from the owner"""
        owner.removePaper()
    remove = staticmethod( remove )

    def canAdd( target ):
        #only one paper can be added to a contribution
        return target.getPaper() == None
    canAdd = staticmethod( canAdd )

    def canDelete( target ):
        #only a paper which is already set in a contribution can be deleted
        return target.getPaper() != None
    canDelete = staticmethod( canDelete )

    def getModificationURL( cls, mat ):
        """returns the URL for accessing to the modification view of the
            material"""
        return urlHandlers.UHMaterialModification.getURL( mat )
    getModificationURL = classmethod(getModificationURL)

    def create(cls, target ):
        m = conference.Paper()
        m.setTitle(cls.getTitle())
        target.setPaper( m )
        return m
    create = classmethod( create )


class SlidesFactory(MaterialFactory):

    _id = "slides"
    _title = "Slides"
    _iconURL = Config.getInstance().getSystemIconURL("slides")
    _materialKlasses=[conference.Slides]
    _needsCreationPage = False

    def get( owner ):
        """returns the material"""
        return owner.getSlides()
    get = staticmethod(get)

    def remove( owner ):
        """performs the deletion of the slides from the owner"""
        owner.removeSlides()
    remove = staticmethod( remove )

    def canAdd( target ):
        #only one slide can be added to a contribution
        return target.getSlides() == None
    canAdd = staticmethod( canAdd )

    def canDelete( target ):
        #only a slide which is already set in a contribution can be deleted
        return target.getSlides() != None
    canDelete = staticmethod( canDelete )

    def getModificationURL( cls, mat ):
        """returns the URL for accessing to the modification view of the
            material"""
        return urlHandlers.UHMaterialModification.getURL( mat )
    getModificationURL = classmethod(getModificationURL)

    def create(cls, target ):
        m = conference.Slides()
        m.setTitle(cls.getTitle())
        target.setSlides( m )
        return m
    create = classmethod( create )

class VideoFactory(MaterialFactory):

    _id = "video"
    _title = "Video"
    _iconURL = Config.getInstance().getSystemIconURL("video")
    _materialKlasses=[conference.Video]
    _needsCreationPage = False

    def get( owner ):
        """returns the material"""
        return owner.getVideo()
    get = staticmethod(get)

    def remove( owner ):
        """performs the deletion of the video from the owner"""
        owner.removeVideo()
    remove = staticmethod( remove )

    def canAdd( target ):
        #only one video can be added to a contribution
        return target.getVideo() == None
    canAdd = staticmethod( canAdd )

    def canDelete( target ):
        #only a video which is already set in a contribution can be deleted
        return target.getVideo() != None
    canDelete = staticmethod( canDelete )

    def getModificationURL( cls, mat ):
        """returns the URL for accessing to the modification view of the
            material"""
        return urlHandlers.UHMaterialModification.getURL( mat )
    getModificationURL = classmethod(getModificationURL)

    def create(cls, target ):
        m = conference.Video()
        m.setTitle(cls.getTitle())
        target.setVideo( m )
        return m
    create = classmethod( create )

class PosterFactory(MaterialFactory):

    _id = "poster"
    _title = "Poster"
    _iconURL = Config.getInstance().getSystemIconURL("poster")
    _materialKlasses=[conference.Poster]
    _needsCreationPage = False

    def get( owner ):
        """returns the material"""
        return owner.getPoster()
    get = staticmethod(get)

    def remove( owner ):
        """performs the deletion of the poster from the owner"""
        owner.removePoster()
    remove = staticmethod( remove )

    def canAdd( target ):
        #only one poster can be added to a contribution
        return target.getPoster() == None
    canAdd = staticmethod( canAdd )

    def canDelete( target ):
        #only a poster which is already set in a contribution can be deleted
        return target.getPoster() != None
    canDelete = staticmethod( canDelete )

    def getModificationURL( cls, mat ):
        """returns the URL for accessing to the modification view of the
            material"""
        return urlHandlers.UHMaterialModification.getURL( mat )
    getModificationURL = classmethod(getModificationURL)

    def create(cls, target ):
        m = conference.Poster()
        m.setTitle(cls.getTitle())
        target.setPoster( m )
        return m
    create = classmethod( create )

class MinutesFactory(MaterialFactory):

    _id = "minutes"
    _title = "Minutes"
    _iconURL = Config.getInstance().getSystemIconURL("material")
    _needsCreationPage = False
    _materialKlasses=[conference.Minutes]

    def get( owner ):
        """returns the material"""
        return owner.getMinutes()
    get = staticmethod(get)

    def remove( owner ):
        """performs the deletion of the minutes from the owner"""
        owner.removeMinutes()
    remove = staticmethod( remove )

    def canAdd( target ):
        #only one minutes can be added to a contribution
        return target.getMinutes() == None
    canAdd = staticmethod( canAdd )

    def canDelete( target ):
        #only a minutes which is already set in a contribution can be deleted
        return target.getMinutes() != None
    canDelete = staticmethod( canDelete )

    def getModificationURL( cls, mat ):
        """returns the URL for accessing to the modification view of the
            material"""
        return urlHandlers.UHMaterialModification.getURL( mat )
    getModificationURL = classmethod(getModificationURL)

    def create( target ):
        return target.createMinutes()
    create = staticmethod( create )

class ReviewingFactory(MaterialFactory):

    _id = "reviewing"
    _title = "Reviewing"
    _iconURL = Config.getInstance().getSystemIconURL("material")
    _materialKlasses=[conference.Reviewing]
    _needsCreationPage = False

    def get( owner ):
        """returns the material"""
        if isinstance(owner, conference.Contribution):
            return owner.getReviewing()
        else:
            # we supposed that it is a Review object
            return owner.getMaterialById(0)
    get = staticmethod(get)

    def remove( owner ):
        """performs the deletion of the paper from the owner"""
        owner.removeReviewing()
    remove = staticmethod( remove )

    def canAdd( target ):
        #only one paper can be added to a contribution
        return target.getReviewing() == None
    canAdd = staticmethod( canAdd )

    def canDelete( target ):
        #only a paper which is already set in a contribution can be deleted
        return target.getReviewing() != None
    canDelete = staticmethod( canDelete )

    def getModificationURL( cls, mat ):
        """returns the URL for accessing to the modification view of the
            material"""
        return urlHandlers.UHMaterialModification.getURL( mat )
    getModificationURL = classmethod(getModificationURL)

    def create(cls, target ):
        m = conference.Reviewing()
        m.setTitle(cls.getTitle())
        target.setReviewing( m )
        return m
    create = classmethod( create )


class DefaultMaterialFactory(MaterialFactory):

    """ Default factory, searches for material with same name,
    and creates new one if needed. """

    def __init__(self, matId):
        self.name = matId

    def get( self, owner ):
        """returns the material"""

        for mat in owner.getMaterialList():
            if mat.getTitle().lower() == self.name.lower():
                return mat

    def remove( self, owner ):
        """performs the deletion of the slides from the owner"""
        owner.removeMaterial(self.get(owner))

    def canAdd( self, target ):
        return True

    def canDelete( self, target ):
        return len(target.getMaterialList) > 0

    def getModificationURL( self, mat ):
        """returns the URL for accessing to the modification view of the
            material"""
        return urlHandlers.UHMaterialModification.getURL( mat )

    def create(self, target):
        m = conference.Material()
        m.setTitle(self.name)
        target.addMaterial( m )
        return m


    @classmethod
    def getInstance(cls, name):
        return cls(name)


class MaterialFactoryRegistry:
    """Keeps a list of material factories. When a new material type wants to be
        added one just needs to implement the corresponding factory and add the
        entry in the "_registry" attribute of this class
    """
    _registry = { PaperFactory._id: PaperFactory, \
                  SlidesFactory._id: SlidesFactory, \
                  MinutesFactory._id: MinutesFactory, \
                  VideoFactory._id: VideoFactory, \
                  PosterFactory._id: PosterFactory, \
                  ReviewingFactory._id: ReviewingFactory }

    _allowedMaterials = {
        'simple_event': ["paper", "slides", "poster", "minutes", "agenda", "pictures",
                         "text", "more information", "document", "list of actions",
                         "drawings", "proceedings", "live broadcast", "video",
                         "streaming video", "downloadable video", "notes", "summary"],

        'meeting': ["paper", "slides", "poster", "minutes", "agenda", "video",
                    "pictures", "text", "more information", "document", "list of actions",
                    "drawings", "proceedings", "live broadcast", "notes", "summary"],

        'conference': ["paper", "slides", "poster", "minutes", "notes", "summary"],

        'category': ["paper", "slides", "poster", "minutes", "agenda", "video", "pictures",
                     "text", "more information", "document", "list of actions", "drawings",
                     "proceedings", "live broadcast"]
    }

    @classmethod
    def getById( cls, matId ):
        return cls._registry.get(matId, DefaultMaterialFactory.getInstance(matId))

    @classmethod
    def getList( cls ):
        return cls._registry.values()

    @classmethod
    def getIdList( cls ):
        return cls._registry.keys()

    @classmethod
    def get(cls, material):
        for factory in cls._registry.values():
            if factory.appliesToMaterial(material):
                return factory

    @classmethod
    def getAllowed(cls, target):
        return cls._allowedMaterials[target.getConference().getType()]

    @classmethod
    def getMaterialList(cls, target):
        """
        Generates a list containing all the materials, with the
        corresponding Ids for those that already exist.
        The format is [(id, title), ...] and materials from the allowed
        material list and the existing material list are unified by title.
        """

        # NOTE: This method is a bit alien. It's just here because
        # we couldn't find a better place

        matDict = dict((title.lower(), title.title()) for title in cls.getAllowed(target))

        for material in target.getAllMaterialList():
            matDict[material.getId()] = material.getTitle()

        return sorted(matDict.iteritems(), key=lambda x: x[1])



class CategoryMFRegistry(MaterialFactoryRegistry):

    @classmethod
    def getAllowed(cls, target):
        return cls._allowedMaterials['category']


class ConfMFRegistry(MaterialFactoryRegistry):
    pass


class SessionMFRegistry(MaterialFactoryRegistry):

    _registry = { MinutesFactory._id: MinutesFactory }


class ContribMFRegistry(MaterialFactoryRegistry):
    pass

class SubContributionMFRegistry(MaterialFactoryRegistry):
    pass
