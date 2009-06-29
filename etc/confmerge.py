# -*- coding: utf-8 -*-
##
## $Id: confmerge.py,v 1.40 2008/08/13 13:31:37 jose Exp $
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

import sys, xml
from xml import sax

class Parsing(sax.ContentHandler):

    def __init__ (self):
        self.item=None     #used for many
        self.key=None
        #paths
        self.pathlist = PathsSet()
        self.inpthname=0
        #url
        self.url = UrlField()
        #worker
        self.worker = WorkerField()
        #email
        self.email = EmailField()
        #support
        self.support = SupportField()
        #smtp
        self.smtp = SmtpField()
        #indico search
        self.isearch = IndicoSearchField()
        #indico footer
        self.footer = FooterField()
        #DB Param
        self.db = DbField()
        #Access params
        self.ac = AcField()
        #File conversion server
        self.fileConv = FileConverterField()
        #Login URL
        self.logurl = LogUrlField()
        #Registration URL
        self.regurl = LogUrlField()
        #Short event URL
        self.shorteventurl = ShortEventUrlField()
        #Short categ URL
        self.shortcategurl = ShortCategUrlField()
        #Authenticator List
        self.authlist = AuthList() #[]
        #Nice config
        self.niceConfig = NiceConfig()
        #OAI
        self.oai = OaiField()
        #FileTypes
        self.repNumSyslist = ReportNumberSystemSet()
        self.inrepid=0
        #FileTypes
        self.filelist = FileSet()
        self.intype =0
        self.sanitaryLevel = Sanitary()
   


    def startElement(self, name, atts):
        self.buffer=""
        self.item=name
        if name =='pathname':
            self.inpthname=1
        if name =='type':
            self.intype=1
        if name =='rns_id':
            self.inrepid=1


    def characters(self, data):
       if self.inpthname:
           self.key=data
       if self.intype:
           self.key=data
       if self.inrepid:
           self.key=data
       if self.item is not None:
            self.buffer+=data

    def endElement(self, name):
        if name =='pathname':
            self.inpthname=0
        if name =='pathdir':
            path = PathField()
            path.setId(self.key)
            path.setValue(self.buffer)
            self.pathlist.add(path)
        if name in ['host','port', 'username', 'password', 'realm']:
            self.db.setId(self.item)
            self.db.setValue(self.buffer)
            self.db.add(self.db.getId(),self.db.getValue())
        if name in ['user','group']:
            self.ac.setId(self.item)
            self.ac.setValue(self.buffer)
            self.ac.add(self.ac.getId(),self.ac.getValue())
        if name =='rns_id':
            self.inrepid=0
            self.repnumsys = ReportNumberSystemField()
            self.repnumsys.setId(self.key)
            self.repNumSyslist.add(self.repnumsys)
        if name =='rns_name':
            self.repnumsys.setName(self.buffer)
        if name =='rns_url':
            self.repnumsys.setURL(self.buffer)
        if name =='type':
            self.intype=0
            self.file = FileField()
            self.file.setId(self.key)
            self.filelist.add(self.file)
        if name =='name':
               self.file.setName(self.buffer)
        if name =='loc':
               self.file.setLoc(self.buffer)
        if name =='img':
               self.file.setImg(self.buffer)
        if name =='url':
            self.url.setId(self.item)
            self.url.setValue(self.buffer)
        if name =='worker':
            self.worker.setId(self.item)
            self.worker.setValue(self.buffer)
        if name=='loginurl':
            self.logurl.setId(self.item)
            self.logurl.setValue(self.buffer)
        if name=='registrationurl':
            self.regurl.setId(self.item)
            self.regurl.setValue(self.buffer)
        if name=='shorteventurl':
            self.shorteventurl.setId(self.item)
            self.shorteventurl.setValue(self.buffer)
        if name=='shortcategurl':
            self.shortcategurl.setId(self.item)
            self.shortcategurl.setValue(self.buffer)
        if name =='email':
            self.email.setId(self.item)
            self.email.setValue(self.buffer)
        if name =='support':
            self.support.setId(self.item)
            self.support.setValue(self.buffer)
        #if name =='smtp':
        if name in ['SMTPServer','SMTPLogin', 'SMTPPassword', 'SMTPUseTLS', 'smtp']:
            self.smtp.setId(self.item)
            self.smtp.setValue(self.buffer)
            self.smtp.add(self.smtp.getId(),self.smtp.getValue())
        if name in ['searchServer','searchClass','indico_search']:
            self.isearch.setId(self.item)
            self.isearch.setValue(self.buffer)
            self.isearch.add(self.isearch.getId(),self.isearch.getValue())
        if name =='footer_text':
            self.footer.setId(self.item)
            self.footer.setValue(self.buffer)
        if name in["logfile","nb_record","nb_ids","oai_rt_exp",\
                   "namespace","iconfNS","iconfXSD","reposName","reposId"]:
            self.oai.setId(self.item)
            self.oai.setValue(self.buffer)
            self.oai.add(self.oai.getId(),self.oai.getValue())
        if name in["conversion_server","response_url"]:
            self.fileConv.setId(self.item)
            self.fileConv.setValue(self.buffer)
            self.fileConv.add(self.fileConv.getId(),self.fileConv.getValue())
        if name == 'authenticator':
            self.authlist.add(self.buffer)
        if name in ["NiceLogin", "NicePassword"]:
            self.niceConfig.setId(self.item)
            self.niceConfig.setValue(self.buffer)
            self.niceConfig.add(self.niceConfig.getId(),self.niceConfig.getValue())
        if name == 'sanitaryLevel':
            self.sanitaryLevel.setId(self.item)
            self.sanitaryLevel.setValue(self.buffer)


#################### CONFIG FILE #################################

class ConfigFile:
    
    def __init__(self,filename):
        self.filename = filename
        self.paths = None
        self.db = None
        self.ac = None
        self.url = None
        self.worker = None
        self.logurl = None
        self.regurl = None
        self.shorteventurl = None
        self.shortcategurl = None
        self.email = None
        self.support = None
        self.smtp = None
        self.isearch = None
        self.footer = None
        self.oai = None 
        self.fileConv=None
        self.reportNumberSystems=None
        self.files = None
        self.authlist = None
        self.sanitaryLevel = None
        self.pathdict={}
        self.dbdict=None
        self.acdict=None
        self.smtpdict={}
        self.isearchdict={}
        self.footertextdict={}
        self.urldict={}
        self.worker=None
        self.logurldict={}
        self.regurldict={}
        self.shorteventurldict={}
        self.shortcategurldict={}
        self.emaildict={}
        self.supportdict={}
        self.oaidict=None
        self.fcdict={}
        self.repnumsysdict={}
        self.filedict={}
        self.sysdict={}
        self.authlistdict=[]
        self.niceCfgDict = {}
        self.sanitaryLevelValue = "1"
        
    def getXmlFile(self):
        parser=xml.sax.make_parser()
        handler = Parsing()
        parser.setContentHandler(handler)
        parser.parse(self.filename)
        self.paths = handler.pathlist
        self.db = handler.db
        self.ac = handler.ac
        self.url = handler.url
        self.worker = handler.worker
        self.logurl = handler.logurl
        self.regurl = handler.regurl
        self.shorteventurl = handler.shorteventurl
        self.shortcategurl = handler.shortcategurl
        self.authlist = handler.authlist
        self.NiceConfig = handler.niceConfig
        self.email = handler.email
        self.support = handler.support
        self.smtp = handler.smtp
        self.isearch = handler.isearch
        self.footer = handler.footer
        self.oai = handler.oai 
        self.fileConv=handler.fileConv
        self.reportNumberSystems=handler.repNumSyslist
        self.files = handler.filelist
        self.sanitaryLevel = handler.sanitaryLevel
        

    def getAllAsDicts(self):
        #Paths
        for a in self.paths.getDict().keys():
            self.pathdict[a]=self.paths.getDict()[a].getValue()
        #Db
        self.dbdict = self.db.getDict()
        #Access
        self.acdict = self.ac.getDict()
        self.smtpdict=self.smtp.getDict()
        self.isearchdict=self.isearch.getDict()
        self.footertextdict[self.footer.getId()]=self.footer.getValue()
        self.urldict[self.url.getId()]=self.url.getValue()
        self.worker=self.worker.getValue()
        self.emaildict[self.email.getId()]=self.email.getValue()
        self.supportdict[self.support.getId()]=self.support.getValue()
        self.logurldict[self.logurl.getId()]=self.logurl.getValue()
        self.regurldict[self.regurl.getId()]=self.regurl.getValue()
        self.shorteventurldict[self.shorteventurl.getId()]=self.shorteventurl.getValue()
        self.shortcategurldict[self.shortcategurl.getId()]=self.shortcategurl.getValue()
        #OAI
        self.oaidict =self.oai.getDict()
        #File Converter
        self.fcdict =self.fileConv.getDict()
        #Report Number Systems
        for s in self.reportNumberSystems.getDict().keys():
            self.repnumsysdict[s] = {u'id':self.reportNumberSystems.getDict()[s].getId(),\
                                     u'name':self.reportNumberSystems.getDict()[s].getName(),\
                                     u'url':self.reportNumberSystems.getDict()[s].getURL()\
                                     }
        #FileTypes
        for a in self.files.getDict().keys():
            self.filedict[a] = {u'name':self.files.getDict()[a].getName(),\
                                u'loc':self.files.getDict()[a].getLoc(),\
                                u'img':self.files.getDict()[a].getImg()\
                                }
        #Auth list
        self.authlistdict = self.authlist.getDict()
        self.niceCfgDict = self.NiceConfig.getDict()
        self.sanitaryLevelValue = self.sanitaryLevel.getValue()
        

    def generateXml(self,newfile):
        fh = open(newfile,'w')
        fh.write( """<?xml version ="1.0"?>\n""")
        fh.write("""\n<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\nxsi:noNamespaceSchemaLocation="schema.xsd">\n""")
        #Paths
        fh.write("\n\n<!--Enter Path names in between the pathdir tags, e.g.<pathdir>c:\\tmp</pathdir> or leave blank for default-->\n")
        for a in self.paths.getDict().keys():
            fh.write(self.paths.getDict()[a].getXml())
        fh.write("\n<!-- htdocs needs to be the same directory as where you set the modpython handler (or blank)-->\n\n")
        #DBParams
        fh.write("\n\n\n<!--Enter database parameters in between tags, e.g. <port>1234</port> or leave as they are for default-->\n")
        fh.write("\t<db_param>\n")
        for a in self.db.getDict().keys():
            fh.write(self.db.getXml(a))
        fh.write("\t</db_param>\n")
        #Access Params
        fh.write("\n\n\n<!--Enter user and group for Public Folder access privaledges, (only applicable in linux installations)-->\n")
        fh.write("\t<access>\n")
        for a in self.ac.getDict().keys():
            fh.write(self.ac.getXml(a))
        fh.write("\t</access>\n")        
        #Url
        fh.write("\n\n\n<!--Enter url base in between tags, e.g. <url>http://localhost/MaKaC</url> or leave as it is for default-->\n")
        fh.write(self.url.getXml())     
        #Worker
        fh.write("\n\n\n<!--Name of the local worker (empty if no load balancing)-->\n")
        fh.write(self.worker.getXml())
        #Login Url
        fh.write("\n\n\n<!--Enter your login Url or leave as it is for default-->\n")
        fh.write(self.logurl.getXml())
        #Registration Url
        fh.write("\n\n\n<!--Enter your registration Url or leave as it is for default-->\n")
        fh.write(self.regurl.getXml())
        #Short Event Url
        fh.write("\n\n\n<!--Enter a short Url to events (if a redirection is configured in httpd) or leave as it is for default-->\n")
        fh.write(self.shorteventurl.getXml())
        #Short Categ Url
        fh.write("\n\n\n<!--Enter a short Url to categories (if a redirection is configured in httpd) or leave as it is for default-->\n")
        fh.write(self.shortcategurl.getXml())
        #Auth List
        fh.write("\n\n\n<!--Add any authenticators to the list below eg. <authenticator>Nice</authenticator> or leave as it is for default-->\n")
        fh.write("\t<Authlist>\n")
        for x in range(len(self.authlist.getDict())):
            fh.write(self.authlist.getXml(x))
        fh.write("\t</Authlist>\n")
        #Nice config
        fh.write("\t<NiceAccount>\n")
        fh.write(self.NiceConfig.getXml())
        fh.write("\t</NiceAccount>\n")
        #Support
        fh.write("\n\n\n<!--Enter support email in between tags, e.g. <support>indico-support@cern.ch</support> or leave for default. This address will be displayed in all Indico pages footers-->\n")
        fh.write(self.support.getXml())
        #Email
        fh.write("\n\n\n<!--Enter support email in between tags, e.g. <email>indico-project@cern.ch</email> or leave for default. this address will be used to send information or error warnings to the administrators of the server-->\n")
        fh.write(self.email.getXml())
        #Smtp
        fh.write("\n\n\n<!--Enter SMTP Server to send Email or leave for default-->\n")
        #fh.write(self.smtp.getXml())
        fh.write("\t<smtpConfig>\n")
        for a in self.smtp.getDict().keys():
            fh.write(self.smtp.getXml(a))
        fh.write("\t</smtpConfig>\n")
        #Indico search
        fh.write("\n\n\n<!--Enter Search Server URL or leave empty by default-->\n")
        fh.write("\t<indicoSearch>\n")
        for a in self.isearch.getDict().keys():
            print a
            fh.write(self.isearch.getXml(a))
        fh.write("\t</indicoSearch>\n")
        #Footer
        fh.write("\n\n\n<!--Footer String-->\n")
        fh.write(self.footer.getXml())
        #OAI
        fh.write("\n\n\n<!--OAI Parameters, leave for default-->\n")
        fh.write("\t<OAI>\n")
        for a in self.oai.getDict().keys():
            fh.write( self.oai.getXml(a))
        fh.write("\t</OAI>\n")
        #File converter
        fh.write("""\n\n\n<!--Conversion service allow to convert files to PDF
        - conversion server: URL which we'll to order the conversion
        - response URL: URL which will received the converted file. It isn't recommendable to modify it.-->\n""")
        fh.write("\t<FileConversion>\n")
        for a in self.fileConv.getDict().keys():
            fh.write( self.fileConv.getXml(a))
        fh.write("\t</FileConversion>\n")
        #ReportNumberSystems
        fh.write("""\n\n\n<!--Report number systems
        - id: id of the report number system, it is mandatory.
        - name: name of the report number system, it is mandatory.
        - url: URL for the report number system.
    <ReportNumberSystem>
        <rns_id></rns_id>
        <rns_name></rns_name>
        <rns_url></rns_url>
    </ReportNumberSystem>
    -->\n""")
        for s in self.reportNumberSystems.getDict().keys():
            fh.write(self.reportNumberSystems.getDict()[s].getXml())
        #FileTypes
        fh.write("\n\n\n<!--Known file types-->\n")
        for a in self.files.getDict().keys():
            fh.write(self.files.getDict()[a].getXml())
        fh.write("\n\n\n<!--Enter sanitary level -->\n")
        fh.write("    <!--0: All html tag are escaped -->\n")
        fh.write("    <!--1: Raise an error if some javascript or style is submitted  -->\n")
        fh.write("    <!--2: Raise an error if some javascript is submitted but style is allowed -->\n")
        fh.write("    <!--3: Accept all -->\n")
        fh.write(self.sanitaryLevel.getXml())

        fh.write("\n</config>")


    def merge(self, oldCF):
        if self.paths != None:
            self.paths.merge(oldCF.paths)
        if self.db !=None:
            self.db.merge(oldCF.db)
        if self.ac !=None:
            self.ac.merge(oldCF.ac)
        if self.url !=None:
            self.url.merge(oldCF.url)
        if self.worker !=None:
            self.worker.merge(oldCF.worker)
        if self.logurl !=None:
            self.logurl.merge(oldCF.logurl)
        if self.regurl !=None:
            self.regurl.merge(oldCF.regurl)
        if self.shorteventurl !=None:
            self.shorteventurl.merge(oldCF.shorteventurl)
        if self.shortcategurl !=None:
            self.shortcategurl.merge(oldCF.shortcategurl)
        if self.authlist !=None:
            self.authlist.merge(oldCF.authlist)
        if self.email !=None:
            self.email.merge(oldCF.email)
        if self.support !=None:
            self.support.merge(oldCF.support)
        if self.smtp !=None:
            self.smtp.merge(oldCF.smtp)
        if self.isearch !=None:
            self.isearch.merge(oldCF.isearch)
        if self.footer !=None:
            self.footer.merge(oldCF.footer)
        if self.oai !=None:
            self.oai.merge(oldCF.oai)
        if self.fileConv !=None:
            self.fileConv.merge(oldCF.fileConv)
        if self.reportNumberSystems != None:
           self.reportNumberSystems.merge(oldCF.reportNumberSystems)
        if self.files != None:
            self.files.merge(oldCF.files)
        if self.NiceConfig != None:
            self.NiceConfig.merge(oldCF.NiceConfig)
        if self.sanitaryLevel != None:
            self.sanitaryLevel.merge(oldCF.sanitaryLevel)

############# FIELDS ##############################################

class Field:
    def __init__(self):
        self.id = ""
    def setId(self, idvalue):
        self.id = idvalue
    def getId(self):
        return self.id

       
class PathField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext="\n\t<paths>\n\t\t<pathname>%s</pathname>\n\t\t<pathdir>%s</pathdir>\n\t</paths>\n"%(self.getId(),self.getValue())
        return xmltext
    def merge(self, oldPathField):
      self.setValue(oldPathField.getValue())
            


class DbField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
        self.dbpdict={}
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def add(self,name,value):
        self.dbpdict[name]=value
    def getDict(self):
        return self.dbpdict
    def getXml(self,key):
        xmltext= "\t\t<%s>%s</%s>\n" %(key,self.dbpdict[key],key)
        return xmltext
    def merge(self,oldDb):
        for key in self.dbpdict.keys():
            if oldDb.dbpdict.has_key(key):
                self.dbpdict[key]=oldDb.dbpdict[key]


class AuthList(Field):
    def __init__(self):
        Field.__init__(self)
        self.value=""
        self.authlist=[]
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def add(self,value):
        self.authlist.append(value)
    def getDict(self):
        return self.authlist
    def getXml(self,x):
        xmltext ="\t\t<authenticator>%s</authenticator>\n"%(self.authlist[x])
        return xmltext
    def merge(self,oldAuthlist):
        if oldAuthlist.getDict() != []:
            self.authlist = oldAuthlist.getDict()


class NiceConfig(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
        self.NiceDict = {"NiceLogin":"", "NicePassword":""}
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def setLogin(self,value):
        self.NiceDict["NiceLogin"] = value
    def getLogin(self):
        return self.NiceDict["NiceLogin"]
    def setPassword(self,value):
        self.NiceDict["NicePassword"] = value
    def getPassword(self):
        return self.NiceDict["NicePassword"]
    def add(self,name,value):
        self.NiceDict[name]=value
    def getDict(self):
        return self.NiceDict
    def getXml(self):
        return "\t\t<NiceLogin>%s</NiceLogin>\n\t\t<NicePassword>%s</NicePassword>\n"%(self.NiceDict["NiceLogin"], self.NiceDict["NicePassword"])
    def merge(self,oldNiceConfig):
        if oldNiceConfig.getDict() != {}:
            self.NiceDict["NiceLogin"] = oldNiceConfig.getDict()["NiceLogin"]
            self.NiceDict["NicePassword"] = oldNiceConfig.getDict()["NicePassword"]
    

class AcField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
        self.acpdict={}
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def add(self,name,value):
        self.acpdict[name]=value
    def getDict(self):
        return self.acpdict
    def getXml(self,key):
        xmltext= "\t\t<%s>%s</%s>\n" %(key,self.acpdict[key],key)
        return xmltext
    def merge(self,oldAc):
        for key in self.acpdict.keys():
            if oldAc.acpdict.has_key(key):
                self.acpdict[key]=oldAc.acpdict[key]

class FileConverterField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value=""
        self.fcdict={}
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def add(self,name,value):
        self.fcdict[name]=value
    def getDict(self):
        return self.fcdict
    def getXml(self,key):
        xmltext= "\t\t<%s>%s</%s>\n""" %(key,self.fcdict[key],key)
        return xmltext
    def merge(self, oldFc):
        for key in self.fcdict.keys():
            if oldFc.fcdict.has_key(key):
                self.fcdict[key]=oldFc.fcdict[key]
    

class UrlField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext= "\n\t<%s>%s</%s>\n"%(self.getId(),self.getValue(),self.getId())
        return xmltext
    def merge(self,oldUrl):
        if self.getId() != oldUrl.getId():
            self.setId(oldUrl.getId())
        if self.getValue() != oldUrl.getValue():
            self.setValue(oldUrl.getValue())

class WorkerField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext= "\n\t<worker>%s</worker>\n" % self.getValue()
        return xmltext
    def merge(self,oldItem):
        if self.getId() != oldItem.getId():
            self.setId(oldItem.getId())
        if self.getValue() != oldItem.getValue():
            self.setValue(oldItem.getValue())

class LogUrlField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value=""
    def setValue(self,value):
        self.value=value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext="\n\t<%s>%s</%s>\n"%(self.getId(),self.getValue(),self.getId())
        return xmltext
    def merge (self,oldLogurl):
        if oldLogurl.getId().strip() != "":
            if self.getId() != oldLogurl.getId():
                self.setId(oldLogurl.getId())
            if self.getValue() != oldLogurl.getValue():
                self.setValue(oldLogurl.getValue())  

class RegUrlField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value=""
    def setValue(self,value):
        self.value=value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext="\n\t<%s>%s</%s>\n"%(self.getId(),self.getValue(),self.getId())
        return xmltext
    def merge (self,oldRegurl):
        if oldRegurl.getId().strip() != "":
            if self.getId() != oldRegurl.getId():
                self.setId(oldRegurl.getId())
            if self.getValue() != oldRegurl.getValue():
                self.setValue(oldRegurl.getValue())  

class Sanitary(Field):
    def __init__(self):
        Field.__init__(self)
        self.value=""
        self.setId("sanitaryLevel")
    def setValue(self,value):
        self.value=value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext="\n\t<%s>%s</%s>\n"%(self.getId(),self.getValue(),self.getId())
        return xmltext
    def merge (self,oldLogurl):
        if oldLogurl.getId().strip() != "":
            if self.getId() != oldLogurl.getId():
                self.setId(oldLogurl.getId())
            if self.getValue() != oldLogurl.getValue():
                self.setValue(oldLogurl.getValue())  
        if self.getValue() == "":
            self.setValue("1")

class ShortEventUrlField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value=""
    def setValue(self,value):
        self.value=value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext="\n\t<%s>%s</%s>\n"%(self.getId(),self.getValue(),self.getId())
        return xmltext
    def merge (self,oldShortEventurl):
        if oldShortEventurl.getId().strip() != "":
            if self.getId() != oldShortEventurl.getId():
                self.setId(oldShortEventurl.getId())
            if self.getValue() != oldShortEventurl.getValue():
                self.setValue(oldShortEventurl.getValue())

class ShortCategUrlField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value=""
    def setValue(self,value):
        self.value=value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext="\n\t<%s>%s</%s>\n"%(self.getId(),self.getValue(),self.getId())
        return xmltext
    def merge (self,oldShortCategurl):
        if oldShortCategurl.getId().strip() != "":
            if self.getId() != oldShortCategurl.getId():
                self.setId(oldShortCategurl.getId())
            if self.getValue() != oldShortCategurl.getValue():
                self.setValue(oldShortCategurl.getValue())

class SupportField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext= "\n\t<support>%s</support>\n"%self.getValue()
        return xmltext
    def merge(self,oldEmail):
        if self.getId() != oldEmail.getId():
            self.setId(oldEmail.getId())
        if oldEmail.getValue() != "":
            self.setValue(oldEmail.getValue())

class EmailField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext= "\n\t<%s>%s</%s>\n"%(self.getId(),self.getValue(),self.getId())
        return xmltext
    def merge(self,oldEmail):
        if self.getId() != oldEmail.getId():
            self.setId(oldEmail.getId())
        if self.getValue() != oldEmail.getValue():
            self.setValue(oldEmail.getValue())

class SmtpField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
        self.smtpValues = {}
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def add(self,name,value):
        self.smtpValues[name]=value
    def getDict(self):
        return self.smtpValues
    def getXml(self,key):
        xmltext= "\t\t<%s>%s</%s>\n" %(key,self.smtpValues[key],key)
        return xmltext
    def merge(self,oldSmtp):
        for key in self.smtpValues.keys():
            if oldSmtp.smtpValues.has_key(key):
                self.smtpValues[key]=oldSmtp.smtpValues[key].strip()
            #merge from old format:
            elif key == "SMTPServer":
                if oldSmtp.smtpValues.has_key("smtp"):
                    self.smtpValues["SMTPServer"]=oldSmtp.smtpValues["smtp"].strip()
##        if self.getId() != oldSmtp.getId():
##            self.setId(oldSmtp.getId())
##        if self.getValue() != oldSmtp.getValue():
##            self.setValue(oldSmtp.getValue())

class IndicoSearchField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
        self.sfValues = {}
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def add(self,name,value):        
        self.sfValues[name]=value
    def getDict(self):
        return self.sfValues
    def getXml(self,key):
        xmltext= "\t\t<%s>%s</%s>\n" %(key,self.sfValues[key],key)
        return xmltext
    def merge(self,oldISearch):
        for key in self.sfValues.keys():
            if oldISearch.sfValues.has_key(key):
                self.sfValues[key]=oldISearch.sfValues[key].strip()
            #merge from old format:
            elif key == "searchServer":
                if oldISearch.sfValues.has_key("indico_search"):
                    self.sfValues["searchServer"]=oldISearch.sfValues["indico_search"].strip()

class FooterField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value = ""
        self.setId("footer_text")
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def getXml(self):
        xmltext= "\n\t<%s>%s</%s>\n"%(self.getId(),sax.saxutils.escape(self.getValue()),self.getId())
        return xmltext
    def merge(self,oldField):
        if self.getId() != oldField.getId():
            self.setId(oldField.getId())
        if oldField.getValue() != "" and self.getValue() != oldField.getValue():
            self.setValue(oldField.getValue())


class OaiField(Field):
    def __init__(self):
        Field.__init__(self)
        self.value=""
        self.oaidict={}
    def setValue(self,value):
        self.value = value
    def getValue(self):
        return self.value
    def add(self,name,value):
        self.oaidict[name]=value
    def getDict(self):
        return self.oaidict
    def getXml(self,key):
        xmltext= "\t\t<%s>%s</%s>\n""" %(key,self.oaidict[key],key)
        return xmltext
    def merge(self, oldOai):
        for key in self.oaidict.keys():
            if oldOai.oaidict.has_key(key):
                self.oaidict[key]=oldOai.oaidict[key]

class ReportNumberSystemField(Field):
    def __init__(self):
        Field.__init__(self)
        self.name =""
        self.url=""
    def setName(self,name):
        self.name = name
    def getName(self):
        return self.name
    def setURL(self,url):
        self.url = url
    def getURL(self):
        return self.url
    def getXml(self):
        xmltext= """\n\t<ReportNumberSystem>\n\t\t<rns_id>%s</rns_id>\n\t\t<rns_name>%s</rns_name>\n\t\t<rns_url>%s</rns_url>\n\t</ReportNumberSystem>\n"""%(self.getId(),self.getName(),self.getURL())
        return xmltext
    def merge(self, oldSys):
        if self.getName() != oldSys.getName():
              self.setName(oldSys.getName())
        if self.getURL() != oldSys.getURL():
              self.setURL(oldSys.getURL())

class FileField(Field):
    def __init__(self):
        Field.__init__(self)
        self.name =""
        self.loc = ""
        self.img = ""
    def setName(self,name):
        self.name = name
    def getName(self):
        return self.name
    def setLoc(self,loc):
        self.loc = loc
    def getLoc(self):
        return self.loc
    def setImg(self,img):
        self.img = img
    def getImg(self):
        return self.img
    def getXml(self):
        xmltext= """\n\t<FileType>\n\t\t<type>%s</type>\n\t\t<name>%s</name>\n\t\t<loc>%s</loc>\n\t\t<img>%s</img>\n\t</FileType>\n"""%(self.getId(),self.getName(),self.getLoc(),self.getImg())
        return xmltext
    def merge(self, oldFile):
        if self.getName() != oldFile.getName():
              self.setName(oldFile.getName())
        if self.getLoc() != oldFile.getLoc():
              self.setLoc(oldFile.getLoc())
        if self.getImg() != oldFile.getImg():
              self.setImg(oldFile.getImg())

    
####################### SETS ######################################
              
class PathsSet:
    def __init__ (self):
        self.paths= {}
    def add(self,new):
        self.paths[new.getId()]=new
    def getDict(self):
        return self.paths
    def merge(self, oldPathsSet):
        for key in self.paths.keys():
            newPath = self.paths[key]
            if oldPathsSet.paths.has_key(key):
                oldPath = oldPathsSet.paths[key]
                newPath.merge(oldPath)


class ReportNumberSystemSet:
    def __init__(self):
        self.rnsys={}
    def add(self,new):
        self.rnsys[new.getId()]=new
    def getDict(self):
        return self.rnsys
    def merge(self,oldReportNumberSystemSet):
        for key in self.rnsys.keys():
            newR = self.rnsys[key]
            if oldReportNumberSystemSet.rnsys.has_key(key):
                oldR = oldReportNumberSystemSet.rnsys[key]
                newR.merge(oldR)
        for key in oldReportNumberSystemSet.rnsys.keys():
            if not self.rnsys.has_key(key):
                self.rnsys[key]=oldReportNumberSystemSet.rnsys[key]
                
class FileSet:
    def __init__(self):
        self.files={}
    def add(self,new):
        self.files[new.getId()]=new
    def getDict(self):
        return self.files
    def genXml(self):
        print FileField.getXml()
    def merge(self,oldFileSet):
        return

def MergeFiles(file1,file2,newfile):
    oldCF = ConfigFile(file1)
    oldCF.getXmlFile()
    mergeCF =ConfigFile(file2)
    mergeCF.getXmlFile()
    mergeCF.merge(oldCF)
    mergeCF.generateXml(newfile)




