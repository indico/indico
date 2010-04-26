# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

#This file contain the definition of those classes which implement the export of metedata using OAI protocol
#Important: to write XML code, don't use 'print' function but the 'openTag', 'closeTag' and 'writeTag' for produce well formated XML
#The item and set identifier type is not define. it can be a string, a list, a reference to an object, etc... Just make function in the class DataInt which handle it

import os
import cPickle
import string
from string import split
import re
import time
import md5
from datetime import datetime
from pytz import timezone

import MaKaC.conference as conference
from MaKaC.conference import ConferenceHolder
import MaKaC.user as user
from MaKaC.common.utils import getHierarchicalId
from MaKaC.common.general import *
from MaKaC.common.xmlGen import XMLGen
from MaKaC.common import Config
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.output import outputGenerator
from MaKaC.common.indexes import IndexesHolder
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.common.logger import Logger

re_amp = re.compile('&')

class DataInt:
    """
        DataInt - main class for an OAI gateway (default: public)
    """

    def  __init__(self,XG):
        self.categoryRoot = conference.CategoryManager().getRoot()
        import MaKaC.accessControl as accessControl
        self.OAIuser = accessControl.AccessWrapper()
        self._XMLGen = XG
        self._config = Config.getInstance()
        self._info = HelperMaKaCInfo.getMaKaCInfoInstance()
        self._outGen = outputGenerator(self.OAIuser, self._XMLGen, dataInt=self)

        self.namespace               = self._config.getOAINamespace()
        self.iconfNamespace          = self._config.getIconfNamespace()
        self.iconfXSD                = self._config.getIconfXSD()
        self.oai_marcXSD             = self._config.getBaseURL() + "/oai_marc.xsd"
        self.repositoryName          = self._config.getRepositoryName()
        self.supportemail            = self._info.getSupportEmail()
        self.repositoryIdentifier    = self._config.getRepositoryIdentifier()

    def targetIsVisible(self, target):
        return not target.hasAnyProtection()

    def getIdPrefix(self):
        """
        Defines a prefix for the private record ids, so that
        the search engine will be able to tell public from private
        """

        return "p"

    def getVisibleConferenceIndex(self):
        ih = IndexesHolder()
        return ih.getById("OAIConferenceModificationDate")

    def getVisibleContributionIndex(self):
        ih = IndexesHolder()
        return ih.getById("OAIContributionModificationDate")

    def getInvisibleConferenceIndex(self):
        ih = IndexesHolder()
        return ih.getById("OAIPrivateConferenceModificationDate")

    def getInvisibleContributionIndex(self):
        ih = IndexesHolder()
        return ih.getById("OAIPrivateContributionModificationDate")

    def extractPrefixId(self, id):
        m = re.match("(\D)(.*)", id)

        if m:
            return m.group(1), m.group(2)
        else:
            return None, None

    def objToId(self, obj, separator=[':',':']):

        if type(separator) == str:
            separator = [separator]*2

        if isinstance(obj, conference.Conference):
            oid = obj.getId()
        elif isinstance(obj, conference.Contribution):
            oid = "%s%s%s"%(obj.getConference().getId(),separator[0],obj.getId())
        elif isinstance(obj, conference.SubContribution):
            oid = "%s%s%s%s%s"%(obj.getConference().getId(), separator[0], obj.getContribution().getId(), separator[1], obj.getId())
        else:
            oid = obj.getId()
        return "%s%s" % (self.getIdPrefix(), oid)

    def idToObj(self, origId):

        prefix, id = self.extractPrefixId(origId)

        if id == None:
            return None

        if self.isDeletedItem(origId):
            try:
                doh = conference.DeletedObjectHolder()
                obj = doh.getById(id)
                if obj:
                    return obj
            except KeyError:
                pass

        ids = id.split(":")
        if len(ids) == 1:
            return ConferenceHolder().getById(ids[0])
        elif len(ids) == 2:
            return ConferenceHolder().getById(ids[0]).getContributionById(ids[1])
        elif len(ids) == 3:
            return ConferenceHolder().getById(ids[0]).getContributionById(ids[1]).getSubContributionById(ids[2])
        return None

    def OAIGetItem(self, identifier):

        id = identifier[int(len("oai:" + self.namespace + ":")):]
        record = self.idToObj(id)

        prefix, _ = self.extractPrefixId(id)

        if self.isDeletedItem(id):
            return None, id
        elif prefix != self.getIdPrefix() or not record:
            return "idDoesNotExist", None
        else:
            return None, id

    def OAIGetDeletedItem(self, identifier, metadataPrefix=None):
        # change object holder
        doh = conference.DeletedObjectHolder()
        id = identifier[int(len("oai:" + self.namespace + ":")):]
        try:
            return doh.getById(id)
        except:
            return None

    def OAIGetItemList(self, MetadataFormat, set, date_from, date_until):

        Logger.get('oai').debug('OAIGetItemList called')

        #Return list of item identifier for the OAI set 'set', modified from 'date_from' until 'date_until' and which can be disseminated with 'MetadataFormat'.
        #self._XMLGen.writeTag("test","conf num:%d" %len(ConferenceHolder()) )

        if MetadataFormat in ["marcxml", "dc", "oai_dc"]:
            addContrib = True
        else:
            addContrib = False

        confIdx = self.getVisibleConferenceIndex()
        contIdx = self.getVisibleContributionIndex()
        prefix = self.getIdPrefix()

        # only set is given
        if set and not (date_from or date_until):

            objList = []

            if set[0] == "0":
                catId = set.split(":")[-1]
                items = IndexesHolder().getById("category").getItems(catId)
                Logger.get('oai').debug('Item list length (%s): %s' % (catId, len(items)) )
                for id in items:
                    conf = ConferenceHolder().getById(id)
                    if self.targetIsVisible(conf):
                        objList.append(self.objToId(conf))
                    if addContrib:
                        for contrib in conf.getContributionList():
                            if not isinstance(contrib.getCurrentStatus(), conference.ContribStatusWithdrawn) and self.targetIsVisible(contrib):
                                objList.append(self.objToId(contrib))
                                for subContrib in contrib.getSubContributionList():
                                    objList.append(self.objToId(subContrib))

            prefixObjList = objList
        else:

            # Logger.get('oai').debug('Fetching whole list of conferences (%s - %s)...' % (date_from, date_until))
            objList = confIdx.getConferencesIds(date_from, date_until)

            # Logger.get('oai').debug('Done!')

            if addContrib:
                # Logger.get('oai').debug('Fetching whole list of contributions...')
                objList.extend(contIdx.getContributionsIds(date_from, date_until))
                # Logger.get('oai').debug('Done!')

            if set:
                Logger.get('oai').debug('Checking set restrictions over %s records...' % len(objList))
                if set[0] == "0":
                    catId = set.split(":")[-1]
                    cat = conference.CategoryManager().getById(catId)

                    removeList = []

                    for objId in objList:

                        # event does not belong to category
                        if not cat in self.idToObj(prefix+objId).getConference().getOwnerPath():
                            removeList.append(objId)

                    for removeId in removeList:
                        objList.remove(removeId)
                else:
                    objList = []

                Logger.get('oai').debug('Done! (%s)' % len(objList))

            prefixObjList = []

            for obj in objList:
                prefixObjList.append("%s%s" % (prefix, obj))

        return prefixObjList

    def OAIGetDeletedItemList(self, MetadataFormat, set, date_from, date_until):

        #process deleted event
        doh = conference.DeletedObjectHolder()
        type = ["conf"]
        addContrib = False
        if MetadataFormat in ["marcxml", "dc", "oai_dc"]:
            type.append("cont")
            addContrib = True
        catId = None
        archive = False
        if set:
            catId = set.split(":")[-1]

        #Logger.get('oai').debug('Fetching all deleted objects (holder)...')
        ret = doh.getObjsIds(from_date=date_from, until_date=date_until, catId=catId, type=type, private=self.isPrivateDataInt())


        #Logger.get('oai').debug('Done!')

        #process private event
        confIdx = self.getInvisibleConferenceIndex()
        contIdx = self.getInvisibleContributionIndex()
        prefix = self.getIdPrefix()

        Logger.get('oai').debug('Fetching all deleted conferences (index)...')
        objList = confIdx.getConferencesIds(date_from, date_until)
        Logger.get('oai').debug('Done!')

        if addContrib:
            #Logger.get('oai').debug('Fetching all deleted contributions (index)...')
            objList.extend(contIdx.getContributionsIds(date_from, date_until))
            #Logger.get('oai').debug('Done!')


        if set:
            if set[0] == "0":
                catId = set.split(":")[-1]
                cat = conference.CategoryManager().getById(catId)

                removeList = []

                for objId in objList[:]:

                    obj = self.idToObj(prefix+objId)

                    if obj.__class__ == conference.DeletedObject:
                        catPath = obj.getCategoryPath()
                    else:
                        catPath = obj.getConference().getCategoriesPath()

                    if not cat in catPath:
                        removeList.append(objId)

                for removeId in removeList:
                    objList.remove(removeId)

            else:
                objList = []

        ret.extend(objList)

        prefixRet = []

        for obj in ret:
            prefixRet.append("%s%s" % (prefix, obj))

        return prefixRet

    def isDeletedItem(self, origId):
        """
        returns True if the item was deleted from the visible index
        (public or private depending on the gateway)
        returns False if either the item was not deleted, or simply
        does not exist (in the current OAI gateway) - meaning that i.e
        an 'r123' event does not exist in the public gateway
        """


        prefix, id = self.extractPrefixId(origId)

        doh = conference.DeletedObjectHolder()

        # if it's in the deleted object holder
        # it has been deleted from all the indexes
        if doh.hasKey(id):
            return True

        if prefix != self.getIdPrefix():
            # the item was not deleted: it simply does not exist
            # in this gateway - a private event cannot be retrieved
            # from a public gateway
            return False

        # event was not been explicitly deleted (from all indexes), but
        # simply switched indexes (i.e. from private to public)
        if len(id.split(":")) > 1:
            # contribution or subcontribution
            return id in self.getInvisibleContributionIndex().getContributionsIds(None,None)

        else:
            # conference
            return id in self.getInvisibleConferenceIndex().getConferencesIds(None,None)

    def getItemSetList(self,item):
        #return the list of set identifier where the item is a member
        obj = item
        if isinstance(item, str):
            obj = self.idToObj(item)
        if isinstance(obj, conference.DeletedObject):
            return obj.getCategoryPath()
        if isinstance(obj,conference.Contribution) or isinstance(obj, conference.SubContribution):
            obj=obj.getConference()
        li = obj.getOwnerList()

        return li

    def getItemId(self,item):
        #return an ID for the item. It can be different from system ID, but must be unique
        obj = item
        if isinstance(item, str):
            obj = self.idToObj(item)
        return getHierarchicalId(obj)


    def get_modification_date(self, item):
        #Returns the date of last modification for the item
        #try:
        obj = item
        if isinstance(item, str):
            obj = self.idToObj(item)
        date = obj.getOAIModificationDate()
        return string.zfill(date.year,4) + "-" + string.zfill(date.month,2) + "-" + string.zfill(date.day,2)





    def getRepositoryIdentifier(self):
        # return the identifier of the repository
        return self.repositoryIdentifier


    def getSampleIdentifier(self):
        # Return a sample of an OAI identifier for this repository
        return "oai:%s:40"%self.getRepositoryIdentifier()



    def get_sets(self):
        #Returns list of sets as [[spec,name,[descriptions]],[...]]
        out = self.listCategory(self.categoryRoot,"",[])
        # add archive category
        out.append(["arch","archive",["Set for all conference which are ready for archive"]])
        return out



    def listCategory(self,cat,path,list=[]):
        #recursive function to list the category
        #if category has conference, return
        #else, call recursive in sub-category
        if len(cat.getSubCategoryList())==0: #
#        if len(cat.getConferenceList())>0:   # to add only categories with conference
            out=list
            if path == "":
                temp = ""
            else:
                temp = path + ":"
            out.append([temp+cat.getId(),cat.getName(),[cat.getDescription()]])
            return out
        else:
            out=list
            if path == "":
                temp = ""
            else:
                temp = path + ":"
            out.append([temp+cat.getId(),cat.getName(),[cat.getDescription()]]) #to remove if we don't want add categories with sub-categories
            for c in cat.getSubCategoryList():
                if not c.isProtected():
                    out=self.listCategory(c,temp+cat.getId(),out)
            return out


    def getSetSpec(self,set):
        #return the setSpec for a set identifier
        if isinstance(set, str):
            return set
        if set.isRoot():
            return set.getId()
        else:
            return self.getSetSpec(set.getOwner()) + ":" + set.getId()

    def oaiidentifydescription(self):
        #Add description about the repository. Remember to use built-in methods
        self._XMLGen.openTag("description")
        self._XMLGen.openTag("oai-identifier",[["xmlns","http://www.openarchives.org/OAI/2.0/oai-identifier"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation","http://www.openarchives.org/OAI/2.0/oai-identifier http://www.openarchives.org/OAI/2.0/oai-identifier.xsd"]])
        self._XMLGen.writeTag("scheme","oai")
        self._XMLGen.writeTag("repositoryIdentifier",self.getRepositoryIdentifier())
        self._XMLGen.writeTag("delimiter",":")
        self._XMLGen.writeTag("sampleIdentifier",self.getSampleIdentifier())
        self._XMLGen.closeTag("oai-identifier")
        self._XMLGen.closeTag("description")
        self._XMLGen.openTag("description")
        self._XMLGen.openTag("eprints", [["xmlns","http://www.openarchives.org/OAI/1.1/eprints"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation","http://www.openarchives.org/OAI/1.1/eprints http://www.openarchives.org/OAI/1.1/eprints.xsd"]])
        self._XMLGen.openTag("content")
        self._XMLGen.writeTag("URL","http://foo.com")
        self._XMLGen.closeTag("content")
        self._XMLGen.openTag("metadataPolicy")
        self._XMLGen.writeTag("text","Free and unlimited use by anybody with obligation to refer to original record")
        self._XMLGen.closeTag("metadataPolicy")
        self._XMLGen.openTag("dataPolicy")
        self._XMLGen.writeTag("text","Full content, i.e. preprints may not be harvested by robots")
        self._XMLGen.closeTag("dataPolicy")
        self._XMLGen.openTag("submissionPolicy")
        self._XMLGen.writeTag("text","Submission restricted. Submitted documents are subject of approval by OAI repository admins.")
        self._XMLGen.closeTag("submissionPolicy")
        self._XMLGen.closeTag("eprints")
        self._XMLGen.closeTag("description")


    def getMetadataList(self,ID=None):
        #return a list as [["MetadataPrefix","schema","nameSpace",self.method_to_call ],[...]]
        #if ID is given, then return the list of metadata supported by this element

        if ID:
            ##get the confId and the contribId if there is one
            #id = ID[int(len("oai:" + self.namespace + ":")):]
            #t=id.split(".")
            #idConf,idContrib=t[0],""
            #if len(t)>1:
            #    idContrib=t[1]
            ##check the validity of the confId
            #try:
            #    conf = ConferenceHolder().getById(idConf)
            #except:
            #    return "idDoesNotExist", None
            #if idContrib:
            #    cont = conf.getContributionById(idContrib)
            err, obj = self.OAIGetItem(ID)

            #raise "%s  %s    %s"%(err, obj, ID)
            if err:
                return "idDoesNotExist", None
            obj = self.idToObj(obj)
            if isinstance(obj, conference.Contribution) or isinstance(obj, conference.SubContribution) or \
                (isinstance(obj, conference.DeletedObject) and (obj._objClass == conference.Contribution or obj._objClass == conference.SubContribution)):
                    return None, [["oai_dc", "http://www.openarchives.org/OAI/2.0/oai_dc.xsd", "http://www.openarchives.org/OAI/2.0/oai_dc/", self.toXMLDC], \
                        ["dc", "http://www.openarchives.org/OAI/2.0/oai_dc.xsd", "http://www.openarchives.org/OAI/2.0/oai_dc/", self.toXMLDC], \
                        ["marcxml",self.oai_marcXSD,self.iconfNamespace,self.toMarc]]
            else:
                return None, [["iconf", self.iconfXSD, self.iconfNamespace, self.confToXML], \
                    ["oai_dc", "http://www.openarchives.org/OAI/2.0/oai_dc.xsd", "http://www.openarchives.org/OAI/2.0/oai_dc/", self.toXMLDC], \
                    ["dc", "http://www.openarchives.org/OAI/2.0/oai_dc.xsd", "http://www.openarchives.org/OAI/2.0/oai_dc/", self.toXMLDC], \
                    ["marcxml",self.oai_marcXSD,self.iconfNamespace,self.toMarc]]
        else:
            return None, [["iconf", self.iconfXSD, self.iconfNamespace, self.confToXML], \
                ["oai_dc", "http://www.openarchives.org/OAI/2.0/oai_dc.xsd", "http://www.openarchives.org/OAI/2.0/oai_dc/", self.toXMLDC], \
                ["dc", "http://www.openarchives.org/OAI/2.0/oai_dc.xsd", "http://www.openarchives.org/OAI/2.0/oai_dc/", self.toXMLDC], \
                ["marcxml",self.oai_marcXSD,self.iconfNamespace,self.toMarc]]



    def toMarc(self,obj, out=None):
        if not out:
            out = self._XMLGen
        if isinstance(obj,conference.Conference):
            return self.confToXMLMarc(obj, out=out)
        elif isinstance(obj,conference.Contribution):
            return self.contToXMLMarc(obj, out=out)
        elif isinstance(obj, conference.SubContribution):
            return self.subContToXMLMarc(obj, out=out)
        raise "unknown object type"

    def confToXMLMarc(self,obj, out=None):
        if not out:
            out = self._XMLGen
        #out.openTag("oai_marc", [["type",""], ["level",""], ["xmlns",self.iconfNamespace],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "%s %s"%(self.iconfNamespace, self.oai_marcXSD)]])
        out.openTag("marc:record", [["xmlns:marc","http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        self._outGen.confToXMLMarc21(obj, out=out)
        out.closeTag("marc:record")

    def sessionToXMLMarc(self,obj, out=None):
        if not out:
            out = self._XMLGen
        out.openTag("marc:record", [["xmlns:marc","http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        self._outGen.sessionToXMLMarc21(obj, out=out)
        out.closeTag("marc:record")

    def contToXMLMarc(self,obj, out=None):
        if not out:
            out = self._XMLGen
        #out.openTag("oai_marc", [["type",""], ["level",""],["xmlns",self.iconfNamespace],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "%s %s"%(self.iconfNamespace, self.oai_marcXSD)]])
        out.openTag("marc:record", [["xmlns:marc", "http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        self._outGen.contribToXMLMarc21(obj, out=out)
        out.closeTag("marc:record")

    def subContToXMLMarc(self,obj, out=None):
        if not out:
            out = self._XMLGen
        #out.openTag("oai_marc", [["type",""], ["level",""],["xmlns",self.iconfNamespace],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "%s %s"%(self.iconfNamespace, self.oai_marcXSD)]])
        out.openTag("marc:record", [["xmlns:marc", "http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        self._outGen.subContribToXMLMarc21(obj, out=out)
        out.closeTag("marc:record")

    #Write here methods for build metadata (!!always using built-in methods!!)
    def toXMLDC(self, obj, out=None):
        if not out:
            out = self._XMLGen
        if type(obj) == conference.Conference:
            return self.confToXMLDC(obj, out=out)
        elif isinstance(obj, conference.Contribution):
            return self.contToXMLDC(obj, out=out)
        elif isinstance(obj, conference.SubContribution):
            return self.subContToXMLDC(obj, out=out)
        raise "Unknown object type: %s id=%s"%(obj, obj.getId())

    def subContToXMLDC(self, subCont, out=None):
        if not out:
            out = self._XMLGen
        out.openTag("oai_dc:dc",[["xmlns:oai_dc","http://www.openarchives.org/OAI/2.0/oai_dc/"],["xmlns:dc","http://purl.org/dc/elements/1.1/"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation","http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"]])
        #if subCont.getCreator() != None:
        #    self._XMLGen.writeTag("dc_creator",subCont.getCreator().name + " " + subCont.getCreator().surName)
        out.writeTag("dc:title",subCont.getTitle())
        out.writeTag("dc:description",subCont.description)
        if subCont.getContribution().startDate:
            out.writeTag("dc:date","%d-%s-%s" %(subCont.getContribution().startDate.year, string.zfill(subCont.getContribution().startDate.month,2), string.zfill(subCont.getContribution().startDate.day,2)))
        out.closeTag("oai_dc:dc")

    def contToXMLDC(self, cont, out=None):
        if not out:
            out = self._XMLGen
        out.openTag("oai_dc:dc",[["xmlns:oai_dc","http://www.openarchives.org/OAI/2.0/oai_dc/"],["xmlns:dc","http://purl.org/dc/elements/1.1/"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation","http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"]])
        #if cont.getCreator() != None:
        #    self._XMLGen.writeTag("dc_creator",cont.getCreator().name + " " + cont.getCreator().surName)
        out.writeTag("dc:title",cont.getTitle())
        out.writeTag("dc:description",cont.description)
        if cont.startDate:
            out.writeTag("dc:date","%d-%s-%s" %(cont.startDate.year, string.zfill(cont.startDate.month,2), string.zfill(cont.startDate.day,2)))
        out.closeTag("oai_dc:dc")

    def confToXMLDC(self,conf, out=None):
        if not out:
            out = self._XMLGen
        out.openTag("oai_dc:dc",[["xmlns:oai_dc","http://www.openarchives.org/OAI/2.0/oai_dc/"],["xmlns:dc","http://purl.org/dc/elements/1.1/"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation","http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"]])
        if conf.getCreator() != None:
            out.writeTag("dc:creator",conf.getCreator().name + " " + conf.getCreator().surName)
        out.writeTag("dc:title",conf.getTitle())
        out.writeTag("dc:description",conf.description)
        out.writeTag("dc:date","%d-%s-%s" %(conf.startDate.year, string.zfill(conf.startDate.month,2), string.zfill(conf.startDate.day,2)))
        out.closeTag("oai_dc:dc")

    def confToXML(self,conf,includeSession=1,includeContribution=1,includeMaterial=1, out=None):
        if not out:
            out = self._XMLGen
        #self._XMLGen.writeXML(self._outGen.getBasicXML(conf, includeSession, includeContribution, includeMaterial))
        out.openTag("iconf",[["xmlns",self.iconfNamespace],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", self.iconfNamespace + " " + self.iconfXSD]])
        self._outGen.confToXML(conf, includeSession, includeContribution, includeMaterial, out=out)
        out.closeTag("iconf")

    def get_earliest_datestamp(self):
        ih = IndexesHolder()
        date = []
        confIdx = self.getVisibleConferenceIndex()
        d = confIdx.getLowerIndex()
        if d:
            date.append(d)
        contIdx = self.getVisibleContributionIndex()
        d = contIdx.getLowerIndex()
        if d:
            date.append(d)
        doh = conference.DeletedObjectHolder()
        d = doh.get_earliest_datestamp()
        if d:
            date.append(d)
        if not date:
            return None
        return min(date)

    def isPrivateDataInt(self):
        return False

class PrivateDataInt(DataInt):

    def getIdPrefix(self):
        """
        Defines a prefix for the record ids, so that
        CDS will be able to tell public from private
        """

        return "r"

    def targetIsVisible(self, target):
        return target.hasAnyProtection()

    def getVisibleConferenceIndex(self):
        ih = IndexesHolder()
        return ih.getById("OAIPrivateConferenceModificationDate")

    def getVisibleContributionIndex(self):
        ih = IndexesHolder()
        return ih.getById("OAIPrivateContributionModificationDate")

    def getInvisibleConferenceIndex(self):
        ih = IndexesHolder()
        return ih.getById("OAIConferenceModificationDate")

    def getInvisibleContributionIndex(self):
        ih = IndexesHolder()
        return ih.getById("OAIContributionModificationDate")

    def isPrivateDataInt(self):
        return True

class OAIResponse:

    _accessURL = "oai.py"

    @classmethod
    def getURL( cls ):
        cfg = Config.getInstance()
        return "%s/%s"%(cfg.getBaseURL(), cls._accessURL)

    def __init__(self, hostname, uri, private):
        self.__hostname = hostname
        self.__uri = uri
        self.__private = private
        self._XMLGen = XMLGen()

        # if it's a private gateway
        if private:
            # PrivateDataInt provides info about private events
            self._DataInt = PrivateDataInt(self._XMLGen)
        else:
            # DataInt should only display public events
            self._DataInt = DataInt(self._XMLGen)

        self._config = Config.getInstance()

        ## OAI config variables

        self.nb_records_in_resume     = self._config.getNbRecordsInResume()
        self.nb_identifiers_in_resume = self._config.getNbIdentifiersInResume()
        self.oai_rt_expire            = self._config.getOAIRtExpire()
        self.runtimelogdir            = self._config.getUploadedFilesSharedTempDir() #Directory where the data for resuptio token are stocked

    def print_oai_header(self,verb,params={}):
        #Print OAI header
        self._XMLGen.openTag("OAI-PMH",[["xmlns","http://www.openarchives.org/OAI/2.0/"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation","http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"]])

        self._XMLGen.writeTag("responseDate",self.OAIGetResponseDate())
        if verb:
            list=[["verb",verb]]
            for i in ['identifier','fromDate',"untilDate",'set','metadataPrefix','resumptionToken']:
                if params.has_key(i):
                    if params[i] != "":
                        list.append([i,params[i]])
            self._XMLGen.writeTag("request",self.OAIGetRequestURL(), list)
            self._XMLGen.openTag(verb)
        else:
            self._XMLGen.writeTag("request", self.OAIGetRequestURL())

    def getHostName(self):
        return self.__hostname

    def getURI(self):
        return self.__uri

    def print_oai_footer(self, verb):
        "Print OAI footer"

        if verb:
            self._XMLGen.closeTag(verb)
        self._XMLGen.closeTag("OAI-PMH")


    def print_record(self, sysno, format='oai_dc', out=None):
        if not out:
            out = self._XMLGen
        #Prints record 'sysno' formatted accoding to 'format'.
        if not sysno:
            return

        if self._DataInt.isDeletedItem(self._DataInt.objToId(sysno)):
            self.print_deleted_record(sysno, out)
            return

        out.openTag("record")
        out.openTag("header")
        out.writeTag("identifier","oai:" + self._DataInt.namespace + ":" + self._DataInt.getIdPrefix() + self._DataInt.getItemId(sysno))
        out.writeTag("datestamp", self._DataInt.get_modification_date(sysno))
        for set in self._DataInt.getItemSetList(sysno):
            out.writeTag("setSpec", self._DataInt.getSetSpec(set))
        out.closeTag("header")
        out.openTag("metadata")



        for i in self._DataInt.getMetadataList()[1]:
            if i[0] == format:
                i[3](sysno, out=out)



        out.closeTag("metadata")
        out.closeTag("record")

    def print_deleted_record(self, sysno, out=None):
        if not out:
            out = self._XMLGen
        #Prints record 'sysno' formatted accoding to 'format'.

        out.openTag("record")
        out.openTag("header", [["status","deleted"]])
        out.writeTag("identifier","oai:" + self._DataInt.namespace + ":" + self._DataInt.getIdPrefix() + self._DataInt.getItemId(sysno))
        out.writeTag("datestamp", self._DataInt.get_modification_date(sysno))
        for set in self._DataInt.getItemSetList(sysno):
            out.writeTag("setSpec", self._DataInt.getSetSpec(set))
        out.closeTag("header")
        out.closeTag("record")


    def isDate(self, date):
        #date format must be "yyyy-mm-dd"
        if not len(date) == len("yyyy-mm-dd"):
            return False

        if date[4] != "-" or date[7] != "-":
            return False

        try:
            int(date[0:4])
            int(date[5:7])
            int(date[8:10])
            return True
        except:
            return False



    def oaiResponseMaker(self,param):
        "Main function which analyses the request and invokes search corresponding to an OAI verb"


        self._XMLGen.initXml()



        if param.has_key('verb'):
            verb = param['verb']#.value #value method is use only with CGI interface or with a file type parameter with modpython
            if isinstance(verb, list):
                self.oai_error("badArgument","multiple verb")
                return self._XMLGen.getXml()

            if param.has_key('metadataPrefix'):
                metadataPrefix = param['metadataPrefix']#.value
                if isinstance(metadataPrefix, list):
                    self.oai_error("badArgument","multiple metadataPrefix")
                    return self._XMLGen.getXml()
            else:
                metadataPrefix = ""

            if param.has_key('from'):
                fromDate = param['from']#.value
                if isinstance(fromDate, list):
                    self.oai_error("badArgument","multiple from")
                    return self._XMLGen.getXml()

                if not self.isDate(fromDate):
                    self.oai_error("badArgument","from: invalid date")
                    return self._XMLGen.getXml()
            else:
                fromDate = ""

            if param.has_key('until'):
                untilDate = param['until']#.value
                if isinstance(untilDate, list):
                    self.oai_error("badArgument","multiple until")
                    return self._XMLGen.getXml()

                if not self.isDate(untilDate):
                    self.oai_error("badArgument","until: invalid date")
                    return self._XMLGen.getXml()
            else:
                untilDate = ""

            if param.has_key('set'):
                set = param['set']#.value
                if isinstance(set, list):
                    self.oai_error("badArgument","multiple set")
                    return self._XMLGen.getXml()
            else:
                set = ""

            if param.has_key('identifier'):
                identifier = param['identifier']#.value
                if isinstance(identifier, list):
                    self.oai_error("badArgument","multiple identifier")
                    return self._XMLGen.getXml()
            else:
                identifier = ""

            if param.has_key('resumptionToken'):
                #resumptionToken exclusive
                if len(param) == 2:
                    resumptionToken = param['resumptionToken']#.value
                    if isinstance(resumptionToken, list):
                        self.oai_error("badArgument","multiple resumptionToken")
                        return self._XMLGen.getXml()
                else:
                    self.oai_error("badArgument","The request includes illegal arguments")
                    return self._XMLGen.getXml()
            else:
                resumptionToken = ""

            if verb == "Identify":
                if len(param) == 1:
                    self.OAIIdentify()
                else:
                    self.oai_error("badArgument","The request includes illegal arguments")

            elif verb == "ListMetadataFormats":
                self.OAIListMetadataFormats(identifier,resumptionToken)

            elif verb == "ListRecords":
                flag = 0
                err, metaList = self._DataInt.getMetadataList(identifier)
                if not err:
                    for meta in metaList:
                        if meta[0] == metadataPrefix:
                            flag = 1
                    if flag or resumptionToken:
                        self.OAIListRecords(fromDate,untilDate,set,metadataPrefix,resumptionToken)
                    else:
                        if metadataPrefix == "":
                            self.oai_error("badArgument","metadataPrefix missing")
                        else:
                            self.oai_error("cannotDisseminateFormat","invalid metadataPrefix")
                else:
                    self.oai_error(err,"invalid record Identifier")

            elif verb == "ListIdentifiers":
                flag = 0
                err, metaList = self._DataInt.getMetadataList(identifier)
                if not err:
                    for meta in metaList:
                        if meta[0] == metadataPrefix:
                            flag = 1
                    if flag or resumptionToken:
                        self.OAIListIdentifiers(metadataPrefix,fromDate,untilDate,set,resumptionToken)
                    else:
                        if metadataPrefix == "":
                            self.oai_error("badArgument","metadataPrefix missing")
                        else:
                            self.oai_error("cannotDisseminateFormat","invalid metadataPrefix")
                else:
                    self.oai_error(err,"invalid record Identifier")

            elif verb == "GetRecord":
                if identifier:
                    flag = 0
                    err, metaList = self._DataInt.getMetadataList(identifier)
                    if not err:
                        for meta in metaList:
                            if meta[0] == metadataPrefix:
                                flag = 1
                        if flag:
                            self.OAIGetRecord(identifier, metadataPrefix)
                        else:
                            if metadataPrefix == "":
                                self.oai_error("badArgument","metadataPrefix missing")
                            else:
                                self.oai_error("cannotDisseminateFormat","invalid metadataPrefix")
                    else:
                        self.oai_error(err,"invalid record Identifier")
                else:
                    self.oai_error("badArgument","Record Identifier Missing")

            elif verb == "ListSets":
                if (((len(param)) > 2 ) or ((len(param) == 2) and (resumptionToken == ""))):
                    self.oai_error("badArgument","The request includes illegal arguments")
                self.OAIListSets(resumptionToken)

            else:
                self.oai_error("badVerb","Illegal OAI verb")
        else:
            self.oai_error("badVerb","Illegal OAI verb")
        return self._XMLGen.getXml()


    def OAIListMetadataFormats(self, identifier,resumptionToken):
        "Generates response to OAIListMetadataFormats verb."



        err, list = self._DataInt.getMetadataList(identifier)

        if err:
            self.oai_error(err,"invalid record Identifier")
        else:
            self.print_oai_header("ListMetadataFormats",{'identifier':identifier,'resumptionToken':resumptionToken})
            for meta in list:
                self._XMLGen.openTag("metadataFormat")
                self._XMLGen.writeTag("metadataPrefix",meta[0])
                self._XMLGen.writeTag("schema",meta[1])
                self._XMLGen.writeTag("metadataNamespace",meta[2])
                self._XMLGen.closeTag("metadataFormat")
            self.print_oai_footer("ListMetadataFormats")


    def OAIListRecords(self, fromDate,untilDate,set,metadataPrefix,resumptionToken):
        "Generates response to OAIListRecords verb."


        Logger.get('oai').debug('Listing all records...')

        sysnos = []
        sysno = []


        # check if the resumptionToken did not expire
        if resumptionToken:
            filename = "%s/RTdata/%s" % (self.runtimelogdir, resumptionToken)
            if os.path.exists(filename) == 0:
                self.oai_error("badResumptionToken","ResumptionToken expired")
                return

        if resumptionToken:
            Logger.get('oai').debug('Resuming %s' % resumptionToken)
            sysno = self.OAICacheOut(resumptionToken)

            metadataPrefix = sysno.pop()
            #XML of record is already generated
            self.print_oai_header("ListRecords",{'fromDate':fromDate,"untilDate":untilDate,'set':set,'metadataPrefix':metadataPrefix,'resumptionToken':resumptionToken})

            sysnos = sysno[:self.nb_identifiers_in_resume]
            sysno = sysno[self.nb_identifiers_in_resume:]

            #Logger.get('oai').debug('sysno: %s sysnos: %s' % (len(sysno), len(sysnos)))

            for s in sysnos:
                if s:
                    self.print_record(self._DataInt.idToObj(s.replace('.',':')), metadataPrefix)

            if sysno:
                resumptionToken = self.OAIGenResumptionToken()
                extdate = self.OAIGetResponseDate(self.oai_rt_expire)
                if extdate:
                    self._XMLGen.writeTag("resumptionToken",resumptionToken, [["expirationDate",extdate]])
                else:
                    self._XMLGen.writeTag("resumptionToken",resumptionToken)
                self.OAICacheClean()
                sysno.append(metadataPrefix)

                Logger.get('oai').debug('Caching in resumption token %s...' % resumptionToken)
                self.OAICacheIn(resumptionToken,sysno)
                Logger.get('oai').debug('Done!')
            else:
                Logger.get('oai').warning('An empty record was generated!')
            self.print_oai_footer("ListRecords")
        else:
            #Generate the xml
            sysno = self._DataInt.OAIGetItemList(metadataPrefix, set, fromDate, untilDate)

            Logger.get('oai').debug('%s non-deleted items: %s' % (len(sysno), sysno))

            Logger.get('oai').debug('Adding deleted items...')

            deletedItems = self._DataInt.OAIGetDeletedItemList(metadataPrefix, set, fromDate, untilDate)

            Logger.get('oai').debug('%s deleted items: %s' % (len(deletedItems), deletedItems))

            sysno.extend(deletedItems)


            Logger.get('oai').debug('Done!')

            Logger.get('oai').debug('%s objects will be returned' % len(sysno))

            if len(sysno) == 0: # noRecordsMatch error
                self.oai_error("noRecordsMatch","no records correspond to the request")
            else:
                self.print_oai_header("ListRecords",{'fromDate':fromDate,"untilDate":untilDate,'set':set,'metadataPrefix':metadataPrefix,'resumptionToken':resumptionToken})
                sysnos = sysno[:self.nb_identifiers_in_resume]
                sysno = sysno[self.nb_identifiers_in_resume:]

                for s in sysnos:
                    if s:
                        obj = self._DataInt.idToObj(s.replace('.',':'))
                        self.print_record(obj, metadataPrefix)
                    else:
                        Logger.get('oai').warning('An empty record was generated!')

                if sysno:
                    resumptionToken = self.OAIGenResumptionToken()
                    extdate = self.OAIGetResponseDate(self.oai_rt_expire)
                    if extdate:
                        self._XMLGen.writeTag("resumptionToken",resumptionToken, [["expirationDate",extdate]])
                    else:
                        self._XMLGen.writeTag("resumptionToken",resumptionToken)
                    self.OAICacheClean()
                    sysno.append(metadataPrefix)
                    self.OAICacheIn(resumptionToken,sysno)
                self.print_oai_footer("ListRecords")

    def OAIListSets(self, resumptionToken):
        "Lists available sets for OAI metadata harvesting."

        # todo: flow control in ListSets

        self.print_oai_header("ListSets",{'resumptionToken':resumptionToken})

        sets = self._DataInt.get_sets()

        for s in sets:

            self._XMLGen.openTag("set")
            self._XMLGen.writeTag("setSpec", s[0])
            self._XMLGen.writeTag("setName", s[1])

            for se in s[2]:
                if se:
                    self._XMLGen.openTag("setDescription")
                    self._XMLGen.openTag("oai_dc:dc",[["xmlns:oai_dc","http://www.openarchives.org/OAI/2.0/oai_dc/"],["xmlns:dc","http://purl.org/dc/elements/1.1/"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation","http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"]])
                    self._XMLGen.writeTag("dc:description",se)
                    self._XMLGen.closeTag("oai_dc:dc")
                    self._XMLGen.closeTag("setDescription")
                    #self._XMLGen.writeTag("setDescription",se)
            self._XMLGen.closeTag("set")

        self.print_oai_footer("ListSets")

    def OAIGetRecord(self, identifier, metadataPrefix):
        """Returns record 'identifier' according to 'metadataPrefix' format for OAI metadata harvesting."""

        err, sysno = self._DataInt.OAIGetItem(identifier)


        if not err and sysno:
            #datestamp = self.get_modification_date(sysno)
            self.print_oai_header("GetRecord",{'identifier':identifier,'metadataPrefix':metadataPrefix})
            self.print_record(self._DataInt.idToObj(sysno), metadataPrefix)
            self.print_oai_footer("GetRecord")
        else:
            if err == "cannotDisseminateFormat":
                self.oai_error("cannotDisseminateFormat","This record cannot be disseminated with this format")
            else:
                self.oai_error("idDoesNotExist","invalid record Identifier")




    def OAIListIdentifiers(self, metadataPrefix, fromDate,untilDate,set,resumptionToken):
        "Prints OAI response to the ListIdentifiers verb."


        sysno = []
        sysnos = []

        if resumptionToken:
            filename = "%s/RTdata/%s" % (self.runtimelogdir, resumptionToken)
            if os.path.exists(filename) == 0:
                self.oai_error("badResumptionToken","ResumptionToken expired")
                return

        if resumptionToken:
            #sysnos = self.OAICacheOut(resumptionToken)
            sysno = self.OAICacheOut(resumptionToken)
            metadataPrefix = sysno.pop()
            #XML of record is already generated
            self.print_oai_header("ListIdentifiers",{'fromDate':fromDate,"untilDate":untilDate,'set':set,'metadataPrefix':metadataPrefix,'resumptionToken':resumptionToken})

            sysnos = sysno[:self.nb_identifiers_in_resume]
            sysno = sysno[self.nb_identifiers_in_resume:]

            for s in sysnos:
                if s:
                    if self._DataInt.isDeletedItem(self._DataInt.getItemId(s)):
                        self.print_deleted_record(s, self._XMLGen)
                    else:
                        self._XMLGen.openTag("header")
                        self._XMLGen.writeTag("identifier", "oai:" + self._DataInt.namespace + ":" + self._DataInt.getItemId(s)) #id
                        self._XMLGen.writeTag("datestamp", self._DataInt.get_modification_date(s))
                        for set in self._DataInt.getItemSetList(s):
                            self._XMLGen.writeTag("setSpec", self._DataInt.getSetSpec(set))
                        self._XMLGen.closeTag("header")
                        #self.print_record(self._DataInt.idToObj(s), metadataPrefix)
            if sysno:
                resumptionToken = self.OAIGenResumptionToken()
                extdate = self.OAIGetResponseDate(self.oai_rt_expire)
                if extdate:
                    self._XMLGen.writeTag("resumptionToken",resumptionToken, [["expirationDate",extdate]])
                else:
                    self._XMLGen.writeTag("resumptionToken",resumptionToken)
                self.OAICacheClean()
                sysno.append(metadataPrefix)
                self.OAICacheIn(resumptionToken,sysno)
            self.print_oai_footer("ListIdentifiers")
        else:
            #Generate the xml
            sysno = self._DataInt.OAIGetItemList(metadataPrefix, set, fromDate, untilDate)


            sysno.extend( self._DataInt.OAIGetDeletedItemList(metadataPrefix, set, fromDate, untilDate))
            if len(sysno) == 0: # noRecordsMatch error
                self.oai_error("noRecordsMatch","no records correspond to the request")
            else:
                self.print_oai_header("ListIdentifiers",{'fromDate':fromDate,"untilDate":untilDate,'set':set,'metadataPrefix':metadataPrefix,'resumptionToken':resumptionToken})
                sysnos = sysno[:self.nb_identifiers_in_resume]
                sysno = sysno[self.nb_identifiers_in_resume:]
                for s in sysnos:
                    if s:
                        if self._DataInt.isDeletedItem(self._DataInt.getItemId(s)):
                            self.print_deleted_record(s,self._XMLGen)
                        else:
                            self._XMLGen.openTag("header")
                            self._XMLGen.writeTag("identifier", "oai:" + self._DataInt.namespace + ":" + self._DataInt.getItemId(s)) #id
                            self._XMLGen.writeTag("datestamp", self._DataInt.get_modification_date(s))
                            for set in self._DataInt.getItemSetList(s):
                                self._XMLGen.writeTag("setSpec", self._DataInt.getSetSpec(set))
                            self._XMLGen.closeTag("header")
                            #self.print_record(self._DataInt.idToObj(s), metadataPrefix)



                if sysno:
                    resumptionToken = self.OAIGenResumptionToken()
                    extdate = self.OAIGetResponseDate(self.oai_rt_expire)
                    if extdate:
                        self._XMLGen.writeTag("resumptionToken",resumptionToken, [["expirationDate",extdate]])
                    else:
                        self._XMLGen.writeTag("resumptionToken",resumptionToken)
                    self.OAICacheClean()
                    sysno.append(metadataPrefix)
                    self.OAICacheIn(resumptionToken,sysno)

                self.print_oai_footer("ListIdentifiers")
            """sysnos = self._DataInt.OAIGetItemList(metadataPrefix, set, fromDate, untilDate)

        if len(sysnos) == 0: # noRecordsMatch error
            self.oai_error("noRecordsMatch","no records correspond to the request")
        else:

            self.print_oai_header("ListIdentifiers",{'fromDate':fromDate,"untilDate":untilDate,'set':set,'resumptionToken':resumptionToken})

            i = 0
            for s in sysnos:
                if s:
                    i = i + 1
                    if i > self.nb_identifiers_in_resume:           # cache or write?
                        if i ==  self.nb_identifiers_in_resume + 1: # resumptionToken?
                            resumptionToken = self.OAIGenResumptionToken()
                            extdate = self.OAIGetResponseDate(self.oai_rt_expire)
                            if extdate:
                                self._XMLGen.writeTag("resumptionToken",resumptionToken,[["expirationDate",extdate]])
                            else:
                                self._XMLGen.writeTag("resumptionToken", resumptionToken)
                        sysno.append(s)
                    else:
                        self._XMLGen.openTag("header")
                        self._XMLGen.writeTag("identifier", "oai:" + self._DataInt.namespace + ":" + self._DataInt.getItemId(s)) #id
                        self._XMLGen.writeTag("datestamp", self._DataInt.get_modification_date(s))
                        for set in self._DataInt.getItemSetList(s):
                            self._XMLGen.writeTag("setSpec", self._DataInt.getSetSpec(set))
                        self._XMLGen.closeTag("header")

            if i > self.nb_identifiers_in_resume:
                self.OAICacheClean() # clean cache from expired resumptionTokens
                self.OAICacheIn(resumptionToken,sysno)

            self.print_oai_footer("ListIdentifiers")"""


    def OAIIdentify(self):
        "Generates response to OAIIdentify verb."

        responseDate          = self.OAIGetResponseDate()
        requestURL            = self.OAIGetRequestURL()
        baseURL               = "http://" + self.getHostName() + self.getURI()
        protocolVersion       = "2.0"
        adminEmail            = self._DataInt.supportemail




        self.print_oai_header("Identify",{})

        self._XMLGen.writeTag("repositoryName", self._DataInt.repositoryName)
        self._XMLGen.writeTag("baseURL", baseURL)
        self._XMLGen.writeTag("protocolVersion", protocolVersion)
        self._XMLGen.writeTag("adminEmail", adminEmail)
        self._XMLGen.writeTag("earliestDatestamp", self.get_earliest_datestamp())
        self._XMLGen.writeTag("deletedRecord","persistent")
        self._XMLGen.writeTag("granularity","YYYY-MM-DD")
        #    self._XMLGen.writeTag("compression","")
        self._DataInt.oaiidentifydescription()

        self.print_oai_footer("Identify")

    def OAIGetRequestURL(self):
        "Generates requestURL tag for OAI."

        if os.environ.has_key('SERVER_NAME'):
            server_name = os.environ['SERVER_NAME']
        else:
            server_name = ""
        if os.environ.has_key('QUERY_STRING'):
            query_string = os.environ['QUERY_STRING']
        else:
            query_string = ""
        if os.environ.has_key('SCRIPT_NAME'):
            script_name = os.environ['SCRIPT_NAME']
        else:
            script_name = ""

        requestURL = "http://" + self.getHostName() + self.getURI()

        return requestURL

    def OAIGetResponseDate(self, delay=0):
        "Generates responseDate tag for OAI."

        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + delay))


    def oai_error(self, code, msg):
        "OAI error occured"


        Logger.get('oai').warning('OAI Error returned - %s: %s' % (code, msg))

        self.print_oai_header("",{})
        self._XMLGen.writeTag("error",msg,[["code",code]])
        self.print_oai_footer("")





    def OAIGenResumptionToken(self):
        "Generates unique ID for resumption token management."

        return md5.new(str(time.time())).hexdigest()


    def OAICacheIn(self, resumptionToken, sysnos):
        "Stores or adds sysnos in cache.  Input is a string of sysnos separated by commas."

        filename = "%s/RTdata/%s" % (self.runtimelogdir, resumptionToken)

        fil = open(filename,"w")

        cPickle.dump(sysnos,fil)
        fil.close()
        return 1


    def OAICacheOut(self, resumptionToken):
        "Restores string of comma-separated system numbers from cache."

        sysnos = []

        filename = "%s/RTdata/%s" % (self.runtimelogdir, resumptionToken)

        if self.OAICacheStatus(resumptionToken):
            fil = open(filename,"r")
            sysnos = cPickle.load(fil)
            fil.close()
        else:
            return 0
        return sysnos

    def OAICacheClean(self):
        "Removes cached resumptionTokens older than specified"

        directory = "%s/RTdata" % self.runtimelogdir

        files = os.listdir(directory)

        for f in files:
            filename = directory + "/" + f
            # cache entry expires when not modified during a specified period of time
            if ((time.time() - os.path.getmtime(filename)) > self.oai_rt_expire):
                os.remove(filename)

        return 1

    def OAICacheStatus(self, resumptionToken):
        "Checks cache status.  Returns 0 for empty, 1 for full."

        filename = "%s/RTdata/%s" % (self.runtimelogdir, resumptionToken)

        if os.path.exists(filename):
            if os.path.getsize(filename) > 0:
                return 1
            else:
                return 0
        else:
            return 0

    def get_earliest_datestamp(self):
        "Returns earliest datestamp"
        date = self._DataInt.get_earliest_datestamp()
        if not date:
            tz= HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
            n=nowutc().astimezone(timezone(tz))
            return string.zfill(n.year,4) + "-" + string.zfill(n.month,2) + "-" + string.zfill(n.day,2)
        return date

def oai(verb="Identify", metadataPrefix="", fr="", until="",set="",identifier="",resumptionToken=""):
    #function called by modPython
    start = datetime.now()
    si = dummySystemInt()
    a=OAIResponse(si)
    dict = {}
    if verb:
        dict["verb"] = verb
    if metadataPrefix:
        dict["metadataPrefix"] = metadataPrefix
    if fr:
        dict["from"] = fr
    if until:
        dict["until"] = until
    if set:
        dict["set"] = set
    if identifier:
        dict["identifier"] = identifier
    if resumptionToken:
        dict["resumptionToken"] = resumptionToken

    response = a.oaiResponseMaker(dict)
    stop = datetime.now()
    #fd = open("/home/bourillo/www/oaiLog/oailog","a")
    #fd.write("[%s] from:%s request:%s responseTime:%s\n" %(now().strftime("%Y-%m-%d %H:%M:%S"),req.connection.remote_ip, req.unparsed_uri, (stop-start).strftime("%H:%M:%S")))
    #fd.close()
    print "[%s] responseTime:%s\n"%(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (stop-start).strftime("%H:%M:%S"))
    return response
