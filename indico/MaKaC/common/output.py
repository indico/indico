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
from collections import defaultdict
from datetime import datetime
from flask import request
from hashlib import md5
from indico.modules.groups import GroupProxy
from pytz import timezone
from sqlalchemy.orm import joinedload, load_only

import string
import StringIO

from lxml import etree

import MaKaC.webinterface.urlHandlers as urlHandlers
from xmlGen import XMLGen
from MaKaC.i18n import _
from MaKaC.common.utils import getHierarchicalId, resolveHierarchicalId
from MaKaC.common.cache import MultiLevelCache, MultiLevelCacheEntry
from MaKaC.common.TemplateExec import escapeHTMLForJS

from indico.core.config import Config
from indico.modules.attachments.models.attachments import AttachmentType, Attachment
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.events.legacy import XMLEventSerializer
from indico.modules.users.legacy import AvatarUserWrapper
from indico.modules.users import User
from indico.modules.groups.legacy import LDAPGroupWrapper
from indico.util.event import uniqueId, unify_event_args
from indico.web.flask.util import url_for


def get_map_url(item):
    return item.room.map_url if item.room else None


class XSLTransformer:

    def __init__(self, stylesheet):
        # instanciate stylesheet object
        styledoc = etree.parse(stylesheet)
        self.__style = etree.XSLT(styledoc)

    def process (self, xml):

        doc = etree.parse(StringIO.StringIO(xml))
        # compute the transformation
        result = self.__style(doc)

        return str(result)


class outputGenerator(object):
    """
    this class generates the application standard XML (getBasicXML)
    and also provides a method to format it using an XSLt stylesheet
    (getFormattedOutput method)
    """

    def __init__(self, aw, XG = None):
        self.__aw = aw
        if XG != None:
            self._XMLGen = XG
        else:
            self._XMLGen = XMLGen()
        self._config = Config.getInstance()
        self.text = ""
        self.time_XML = 0
        self.time_HTML = 0
        self.cache = XMLCache()

    def _getRecordCollection(self, obj):
        if obj.is_protected:
            return "INDICOSEARCH.PRIVATE"
        else:
            return "INDICOSEARCH.PUBLIC"

    def getOutput(self, conf, stylesheet, vars=None, includeSession=1, includeContribution=1, includeSubContribution=1, includeMaterial=1, showSession="all", showDate="all", showContribution="all"):
        # get xml conference
        xml = self._getBasicXML(conf, vars, includeSession,includeContribution,includeSubContribution,includeMaterial,showSession,showDate,showContribution)
        if not os.path.exists(stylesheet):
            self.text = _("Cannot find stylesheet")
        if os.path.basename(stylesheet) == 'XML.xsl':
            self.text = xml
        else:
            # instantiate the XSL tool
            parser = XSLTransformer(stylesheet)
            self.text = parser.process(xml)
        return self.text

    def getFormattedOutput(self, rh, conf, stylesheet, vars=None, includeSession=1,includeContribution=1,includeSubContribution=1,includeMaterial=1,showSession="all",showDate="all",showContribution="all"):
        """
        conf: conference object
        stylesheet: path to the xsl file
        """
        self.getOutput(conf, stylesheet, vars, includeSession, includeContribution, includeSubContribution, includeMaterial, showSession, showDate, showContribution)
        html = self.text
        if request.is_secure:
            baseURL = Config.getInstance().getBaseURL()
            baseSecureURL = urlHandlers.setSSLPort(Config.getInstance().getBaseSecureURL())
            html = html.replace(baseURL, baseSecureURL)
            html = html.replace(escapeHTMLForJS(baseURL), escapeHTMLForJS(baseSecureURL))
        return html

    def _getBasicXML(self, conf, vars, includeSession, includeContribution, includeSubContribution, includeMaterial, showSession="all", showDate="all", showContribution="all", showSubContribution="all", out=None):
        serializer = XMLEventSerializer(conf.as_event, include_timetable=includeContribution, event_tag_name='iconf')
        return serializer.serialize_event()

    def _userToXML(self, obj, user, out):
        out.openTag("user")
        out.writeTag("title", user.getTitle())
        out.writeTag("name", "", [["first", user.getFirstName()], ["middle", ""], ["last", user.getFamilyName()]])
        out.writeTag("organization", user.getAffiliation())

        if obj.canModify(self.__aw):
            out.writeTag("email", user.getEmail())

        out.writeTag("emailHash", md5(user.getEmail()).hexdigest())

        try:
            out.writeTag("userid",user.id)
        except:
            pass
        out.closeTag("user")

    def _generateLinkField(self, url, obj, text, out):
        out.openTag("datafield", [["tag", "856"], ["ind1", "4"], ["ind2", " "]])
        out.writeTag("subfield", str(url.getURL(obj)), [["code", "u"]])
        out.writeTag("subfield", text, [["code", "y"]])
        out.closeTag("datafield")

    def _generateACLDatafield(self, eType, memberList, objId, out):
        """
        Generates a specific MARCXML 506 field containing the ACL
        """
        if eType:
            out.openTag("datafield", [["tag", "506"],
                                      ["ind1", "1"], ["ind2", " "]])
            for memberId in memberList:
                out.writeTag("subfield", memberId, [["code", "d"]])
            out.writeTag("subfield", eType, [["code", "f"]])

        else:
            out.openTag("datafield", [["tag", "506"], ["ind1", "0"],
                                      ["ind2", " "]])

        # define which part of the record the list concerns
        if objId is not None:
            out.writeTag("subfield", "INDICO.%s" % \
                         objId, [["code", "3"]])

        out.closeTag("datafield")

    def _generateAccessList(self, obj=None, out=None, acl=None, objId=None):
        """
        Generate a comprehensive access list showing all users and e-groups who
        may access this object, taking into account the permissions and access
        lists of its owners.
        obj could be a Conference, Session, Contribution, Material, Resource
        or SubContribution object.
        """

        if acl is None:
            acl = obj.get_access_list()

        # Populate two lists holding email/group strings instead of
        # Avatar/Group objects
        allowed_logins = set()
        allowed_groups = []

        for user_obj in acl:
            if isinstance(user_obj, (User, AvatarUserWrapper)):
                if isinstance(user_obj, AvatarUserWrapper):
                    user_obj = user_obj.user
                # user names for all non-local accounts
                for provider, identifier in user_obj.iter_identifiers():
                    if provider != 'indico':
                        allowed_logins.add(identifier)
            elif isinstance(user_obj, LDAPGroupWrapper):
                allowed_groups.append(user_obj.getId())
            elif isinstance(user_obj, GroupProxy) and not user_obj.is_local:
                allowed_groups.append(user_obj.name)

        if len(allowed_groups) + len(allowed_logins) > 0:
            # Create XML list of groups
            if len(allowed_groups) > 0:
                self._generateACLDatafield('group', allowed_groups, objId, out)

            # Create XML list of emails
            if len(allowed_logins) > 0:
                self._generateACLDatafield('username', allowed_logins, objId, out)
        else:
            # public record
            self._generateACLDatafield(None, None, objId, out)

    @unify_event_args
    def confToXMLMarc21(self,event,includeSession=1,includeContribution=1,includeMaterial=1,out=None, overrideCache=False):

        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "MARC21_ses-%s_cont-%s_mat-%s"%(includeSession,includeContribution,includeMaterial)
        obj = None
        if not overrideCache:
            obj = self.cache.loadObject(version, event.as_legacy)
        if obj:
            xml = obj.getContent()
        else:
            # No cache, build the XML
            temp = XMLGen(init=False)
            self._event_to_xml_marc_21(event, includeSession, includeContribution, includeMaterial, out=temp)
            xml = temp.getXml()
            # save XML in cache
            self.cache.cacheObject(version, xml, event.as_legacy)
        out.writeXML(xml)

    def _generate_category_path(self, event, out):
        path = [unicode(c.id) for c in event.category.chain_query.options(load_only('id'))]
        out.openTag("datafield", [["tag", "650"], ["ind1", " "], ["ind2", "7"]])
        out.writeTag("subfield", ":".join(path), [["code", "a"]])
        out.closeTag("datafield")

    def _event_to_xml_marc_21(self, event, includeSession=1, includeContribution=1, includeMaterial=1, out=None):
        if not out:
            out = self._XMLGen

        out.openTag("datafield",[["tag","245"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", event.title, [["code", "a"]])
        out.closeTag("datafield")

        out.writeTag("leader", "00000nmm  2200000uu 4500")
        out.openTag("datafield",[["tag","111"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", event.title, [["code", "a"]])
        event_location_info = []
        if event.venue_name:
            event_location_info.append(event.venue_name)
        if event.address:
            event_location_info.append(event.address)
        event_room = event.get_room_name(full=False)
        if event_room:
            event_location_info.append(event_room)
        out.writeTag("subfield", ', '.join(event_location_info), [["code", "c"]])

        sd = event.start_dt
        ed = event.end_dt
        out.writeTag("subfield","%d-%s-%sT%s:%s:00Z" %(sd.year, string.zfill(sd.month,2), string.zfill(sd.day,2), string.zfill(sd.hour,2), string.zfill(sd.minute,2)),[["code","9"]])
        out.writeTag("subfield","%d-%s-%sT%s:%s:00Z" %(ed.year, string.zfill(ed.month,2), string.zfill(ed.day,2), string.zfill(ed.hour,2), string.zfill(ed.minute,2)),[["code","z"]])

        out.writeTag("subfield", uniqueId(event), [["code", "g"]])
        out.closeTag("datafield")

        self._generate_category_path(event, out)

        sd = event.start_dt
        if sd is not None:
            out.openTag("datafield",[["tag","518"],["ind1"," "],["ind2"," "]])
            out.writeTag("subfield","%d-%s-%sT%s:%s:00Z" %(sd.year, string.zfill(sd.month,2), string.zfill(sd.day,2), string.zfill(sd.hour,2), string.zfill(sd.minute,2)),[["code","d"]])
            out.closeTag("datafield")

        out.openTag("datafield",[["tag","520"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", event.description, [["code", "a"]])
        out.closeTag("datafield")

        self._generate_references(event, out)

        out.openTag("datafield",[["tag","653"],["ind1","1"],["ind2"," "]])
        for keyword in event.keywords:
            out.writeTag("subfield",keyword,[["code","a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","650"],["ind1","2"],["ind2","7"]])
        out.writeTag("subfield", event.type.capitalize(), [["code", "a"]])
        out.closeTag("datafield")
        #### t o d o

        #out.openTag("datafield",[["tag","650"],["ind1","3"],["ind2","7"]])
        #out.writeTag("subfield",,[["code","a"]])
        #out.closeTag("datafield")


        # tag 700 chair name
        for chair in event.person_links:
            out.openTag("datafield",[["tag","906"],["ind1"," "],["ind2"," "]])
            full_name = chair.get_full_name(last_name_first=True, last_name_upper=False, abbrev_first_name=False)
            out.writeTag("subfield", full_name, [["code", "p"]])
            out.writeTag("subfield", chair.affiliation, [["code", "u"]])
            out.closeTag("datafield")


        #out.openTag("datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
        if includeMaterial:
            self.materialToXMLMarc21(event, out=out)
        #out.closeTag("datafield")

        if event.note:
            self.noteToXMLMarc21(event.note, out=out)

        #if respEmail != "":
        #    out.openTag("datafield",[["tag","859"],["ind1"," "],["ind2"," "]])
        #   out.writeTag("subfield",respEmail,[["code","f"]])
        #   out.closeTag("datafield")
        # tag 859 email
        for chair in event.person_links:
            out.openTag("datafield", [["tag", "859"], ["ind1", " "], ["ind2", " "]])
            out.writeTag("subfield", chair.person.email, [["code", "f"]])
            out.closeTag("datafield")

        out.openTag("datafield", [["tag", "961"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", event.created_dt.strftime('%Y-%m-%dT'), [["code", "x"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "961"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", datetime.now().strftime('%Y-%m-%dT'), [["code", "c"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","980"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", self._getRecordCollection(event), [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","970"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", "INDICO." + str(uniqueId(event)), [["code", "a"]])
        out.closeTag("datafield")

        self._generate_link_field(url_for('event.conferenceDisplay', confId=event.id, _external=True), 'Event details',
                                  out)

        self._generateAccessList(event, out, objId=uniqueId(event))

    def contribToXMLMarc21(self, contrib, includeMaterial=1, out=None, overrideCache=False):
        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "MARC21_mat-%s"%(includeMaterial)
        obj = None
        if not overrideCache:
            obj = self.cache.loadObject(version, contrib)
        if obj:
            xml = obj.getContent()
        else:
            # No cache, build the XML
            temp = XMLGen(init=False)
            self._contrib_to_marc_xml_21(contrib, includeMaterial, out=temp)
            xml = temp.getXml()
            # save XML in cache
            self.cache.cacheObject(version, xml, contrib)
        out.writeXML(xml)

    def _contrib_to_marc_xml_21(self, contrib, include_material=1, out=None):
        if not out:
            out = self._XMLGen

        out.writeTag("leader", "00000nmm  2200000uu 4500")
        out.openTag("datafield", [["tag", "035"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", "INDICO.%s" % uniqueId(contrib), [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "035"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", uniqueId(contrib), [["code", "a"]])
        out.writeTag("subfield", "Indico", [["code", "9"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "245"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", contrib.title, [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "300"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", contrib.duration, [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "111"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", uniqueId(contrib.event_new), [["code", "g"]])
        out.closeTag("datafield")

        # TODO: Adapt modification date once in the model
        out.openTag("datafield", [["tag", "961"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", datetime.now().strftime('%Y-%m-%dT'), [["code", "c"]])
        out.closeTag("datafield")

        self._generate_category_path(contrib.event_new, out)

        self._generate_contrib_location_and_time(contrib, out)

        out.openTag("datafield", [["tag", "520"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", contrib.description, [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "611"], ["ind1", "2"], ["ind2", "4"]])
        out.writeTag("subfield", contrib.event_new.title, [["code", "a"]])
        out.closeTag("datafield")

        self._generate_references(contrib, out)

        out.openTag("datafield", [["tag", "653"], ["ind1", "1"], ["ind2", " "]])
        for keyword in contrib.keywords:
            out.writeTag("subfield", keyword, [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","650"],["ind1","1"],["ind2","7"]])
        out.writeTag("subfield","SzGeCERN",[["code","2"]])
        if contrib.track:
            out.writeTag("subfield", contrib.track.title, [["code", "a"]])
        out.closeTag("datafield")

        self._generate_contrib_people(contrib=contrib, out=out)

        if include_material:
            self.materialToXMLMarc21(contrib, out=out)

        if contrib.note:
            self.noteToXMLMarc21(contrib.note, out=out)

        out.openTag("datafield",[["tag","962"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", 'INDICO.{}'.format(uniqueId(contrib.event_new)), [["code", "b"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","970"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", 'INDICO.{}'.format(uniqueId(contrib)), [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","980"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", self._getRecordCollection(contrib), [["code","a"]])
        out.closeTag("datafield")

        self._generate_link_field(url_for('contributions.display_contribution', contrib, _external=True),
                                  'Contribution details', out)

        self._generate_link_field(url_for('event.conferenceDisplay', contrib.event_new, _external=True),
                                  'Event details', out)

        self._generateAccessList(contrib, out, objId=uniqueId(contrib))
    ####
    #fb

    def _generate_link_field(self, url, caption, out):
        out.openTag('datafield', [['tag', '856'], ['ind1', '4'], ['ind2', ' ']])
        out.writeTag('subfield', url, [['code', 'u']])
        out.writeTag('subfield', caption, [['code', 'y']])
        out.closeTag('datafield')

    def _generate_references(self, obj, out):
        if obj.references:
            out.openTag('datafield', [['tag', '088'], ['ind1', ' '], ['ind2', ' ']])
            for reference in obj.references:
                out.writeTag('subfield', reference.value, [['code', 'a']])
            out.closeTag('datafield')

    def _generate_contrib_location_and_time(self, contrib, out):
        if contrib.venue_name or contrib.start_dt:
            out.openTag('datafield', [['tag', '518'], ['ind1', ' '], ['ind2', ' ']])
            if contrib.venue_name:
                out.writeTag('subfield', contrib.venue_name, [['code', 'r']])
            if contrib.start_dt is not None:
                out.writeTag('subfield', contrib.start_dt.strftime('%Y-%m-%dT%H:%M:00Z'), [['code', 'd']])
                out.writeTag('subfield', contrib.end_dt.strftime('%Y-%m-%dT%H:%M:00Z'), [['code', 'h']])
            out.closeTag('datafield')

    def _generate_contrib_people(self, contrib, out, subcontrib=None):
        sList = list(subcontrib.person_links) if subcontrib else list(contrib.speakers)
        users = defaultdict(list)
        for primary_author in contrib.primary_authors:
            users[primary_author] = ['Primary Author']
        for user in contrib.secondary_authors:
            users[user].append('Author')
        for user in sList:
            users[user].append('Speaker')
        for user, roles in users.iteritems():
            tag = '100' if user in contrib.primary_authors else '700'
            out.openTag('datafield', [['tag', tag], ['ind1', ' '], ['ind2', ' ']])
            out.writeTag('subfield', u'{} {}'.format(user.last_name, user.first_name), [['code', 'a']])
            for role in roles:
                out.writeTag('subfield', role, [['code', 'e']])
            out.writeTag('subfield', user.affiliation, [['code', 'u']])
            out.closeTag('datafield')

    def subContribToXMLMarc21(self,subCont,includeMaterial=1, out=None, overrideCache=False):
        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "MARC21_mat-%s"%(includeMaterial)
        obj = None
        if not overrideCache:
            obj = self.cache.loadObject(version, subCont)
        if obj:
            xml = obj.getContent()
        else:
            # No cache, build the XML
            temp = XMLGen(init=False)
            self._subcontrib_to_marc_xml_21(subCont,includeMaterial, out=temp)
            xml = temp.getXml()
            # save XML in cache
            self.cache.cacheObject(version, xml, subCont)
        out.writeXML(xml)

    def _subcontrib_to_marc_xml_21(self, subcontrib, includeMaterial=1, out=None):
        if not out:
            out = self._XMLGen

        out.writeTag("leader", "00000nmm  2200000uu 4500")
        out.openTag("datafield",[["tag","035"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", 'INDICO.{}'.format(uniqueId(subcontrib)), [["code", "a"]])
        out.closeTag("datafield")
    #
        out.openTag("datafield",[["tag","035"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", uniqueId(subcontrib), [["code", "a"]])
        out.writeTag("subfield","Indico",[["code","9"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","245"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", subcontrib.title, [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","300"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", subcontrib.duration, [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","111"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", uniqueId(subcontrib.event_new), [["code", "g"]])
        out.closeTag("datafield")

        self._generate_references(subcontrib, out)
        self._generate_category_path(subcontrib.event_new, out)
        self._generate_contrib_location_and_time(subcontrib.contribution, out)
    #
        out.openTag("datafield",[["tag","520"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", subcontrib.description, [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","611"],["ind1","2"],["ind2","4"]])
        out.writeTag("subfield", subcontrib.event_new.title, [["code", "a"]])
        out.closeTag("datafield")
    #
        out.openTag("datafield",[["tag","650"],["ind1","1"],["ind2","7"]])
        out.writeTag("subfield","SzGeCERN",[["code","2"]])
        if subcontrib.contribution.track:
            out.writeTag("subfield", subcontrib.contribution.track.title, [["code", "a"]])
        out.closeTag("datafield")

        self._generate_contrib_people(contrib=subcontrib.contribution, out=out, subcontrib=subcontrib)

        if includeMaterial:
            self.materialToXMLMarc21(subcontrib, out=out)

        if subcontrib.note:
            self.noteToXMLMarc21(subcontrib.note, out=out)

        out.openTag("datafield",[["tag","962"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", 'INDICO.{}'.format(uniqueId(subcontrib.event_new)), [["code", "b"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","970"],["ind1"," "],["ind2"," "]])
        confcont = 'INDICO.{}'.format(uniqueId(subcontrib))
        out.writeTag("subfield",confcont,[["code","a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","980"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", self._getRecordCollection(subcontrib), [["code", "a"]])
        out.closeTag("datafield")

        self._generate_link_field(url_for('contributions.display_contribution', subcontrib.contribution,
                                          _external=True), 'Contribution details', out)

        self._generate_link_field(url_for('event.conferenceDisplay', subcontrib.event_new, _external=True),
                                  'Event details', out)

        self._generateAccessList(subcontrib.contribution, out, objId=uniqueId(subcontrib))

    def materialToXMLMarc21(self, obj, out=None):
        if not out:
            out = self._XMLGen
        for attachment in (Attachment.find(~AttachmentFolder.is_deleted, AttachmentFolder.object == obj,
                                           is_deleted=False, _join=AttachmentFolder)
                                     .options(joinedload(Attachment.legacy_mapping))):
            if attachment.can_access(self.__aw.getUser().user):
                self.resourceToXMLMarc21(attachment, out)
                self._generateAccessList(acl=self._attachment_access_list(attachment), out=out,
                                         objId=self._attachment_unique_id(attachment, add_prefix=False))

    def resourceToXMLMarc21(self, res, out=None):
        if not out:
            out = self._XMLGen
        if res.type == AttachmentType.file:
            self.resourceFileToXMLMarc21(res, out=out)
        else:
            self.resourceLinkToXMLMarc21(res, out=out)

    def _attachment_unique_id(self, attachment, add_prefix=True):
        if attachment.legacy_mapping:
            unique_id = 'm{}.{}'.format(attachment.legacy_mapping.material_id, attachment.legacy_mapping.resource_id)
        else:
            unique_id = 'a{}'.format(attachment.id)
        unique_id = '{}{}'.format(uniqueId(attachment.folder.object), unique_id)
        return 'INDICO.{}'.format(unique_id) if add_prefix else unique_id

    def _attachment_access_list(self, attachment):
        linked_object = attachment.folder.object
        manager_list = set(linked_object.get_manager_list(recursive=True))

        if attachment.is_self_protected:
            return {e for e in attachment.acl} | manager_list
        if attachment.is_inheriting and attachment.folder.is_self_protected:
            return {e for e in attachment.folder.acl} | manager_list
        else:
            return linked_object.get_access_list()

    def resourceLinkToXMLMarc21(self, attachment, out=None):
        if not out:
            out = self._XMLGen

        out.openTag("datafield", [["tag", "856"], ["ind1", "4"], ["ind2", " "]])
        out.writeTag("subfield", attachment.description, [["code", "a"]])
        out.writeTag("subfield", attachment.absolute_download_url, [["code", "u"]])
        out.writeTag("subfield", self._attachment_unique_id(attachment), [["code", "3"]])
        out.writeTag("subfield", "resource", [["code", "x"]])
        out.writeTag("subfield", "external", [["code", "z"]])
        out.writeTag("subfield", attachment.title, [["code", "y"]])
        out.closeTag("datafield")

    def resourceFileToXMLMarc21(self, attachment, out=None):
        if not out:
            out = self._XMLGen

        out.openTag("datafield", [["tag", "856"], ["ind1", "4"], ["ind2", " "]])
        out.writeTag("subfield", attachment.description, [["code", "a"]])
        out.writeTag("subfield", attachment.file.size, [["code", "s"]])

        out.writeTag("subfield", attachment.absolute_download_url, [["code", "u"]])
        out.writeTag("subfield", self._attachment_unique_id(attachment), [["code", "3"]])
        out.writeTag("subfield", attachment.title, [["code", "y"]])
        out.writeTag("subfield", "stored", [["code", "z"]])
        out.writeTag("subfield", "resource", [["code", "x"]])
        out.closeTag("datafield")

    def noteToXMLMarc21(self, note, out=None):
        if not out:
            out = self._XMLGen
        out.openTag('datafield', [['tag', '856'], ['ind1', '4'], ['ind2', ' ']])
        out.writeTag('subfield', url_for('event_notes.view', note, _external=True), [['code', 'u']])
        out.writeTag('subfield', u'{} - Minutes'.format(note.object.title), [['code', 'y']])
        out.writeTag('subfield', 'INDICO.{}'.format(uniqueId(note)), [['code', '3']])
        out.writeTag('subfield', 'resource', [['code', 'x']])
        out.closeTag('datafield')


class XMLCacheEntry(MultiLevelCacheEntry):
    def __init__(self, objId):
        MultiLevelCacheEntry.__init__(self)
        self.id = objId

    def getId(self):
        return self.id

    @classmethod
    def create(cls, content, obj):
        entry = cls(getHierarchicalId(obj))
        entry.setContent(content)
        return entry


class XMLCache(MultiLevelCache):

    _entryFactory = XMLCacheEntry

    def __init__(self):
        MultiLevelCache.__init__(self, 'xml')


    def isDirty(self, mtime, object):
        modDate = resolveHierarchicalId(object.getId())._modificationDS
        fileModDate = timezone("UTC").localize(
            datetime.utcfromtimestamp(mtime))

        # check file system date vs. event date
        return (modDate > fileModDate)

    def _generatePath(self, entry):
        """
        Generate the actual hierarchical location
        """

        # a205.0 -> /cachedir/a/a2/a205/0

        tree = entry.getId().split('.')
        return [tree[0][0], tree[0][0:2]] + tree
