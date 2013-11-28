# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

import sys,os,re
import MySQLdb
import random
from datetime import datetime
from MaKaC import conference
from MaKaC import user,schedule
from MaKaC.webinterface import webFactoryRegistry
import MaKaC.webinterface.displayMgr as displayMgr
from MaKaC.errors import UserError, MaKaCError
from indico.core.config import Config
from MaKaC import domain
from MaKaC.common import db
import MaKaC.common.indexes as indexes
from MaKaC.common.Counter import Counter
from MaKaC.authentication import AuthenticatorMgr

codec = "utf-8"
file_host = "agenda.cern.ch"
agenda = MySQLdb.connect(host='cdsdb', user='agenda', passwd='PMslcqT1.', db='AGE')
hosticonpath = "/soft/httpd/host/agenda/htdocs/images/levelicons"
cf = agenda.cursor()
DBMgr.getInstance().startRequest()
ah = user.AvatarHolder()

getfiles = 0 # do we fetch the files?
max_white_space_in_names = 3


styles = { "standard": "cdsagenda",
    "event": "event",
    "nosession": "cdsagenda",
    "nicecompact": "nicecompact",
    "lecture": "lecture",
    "standard2": "",
    "administrative": "administrative",
    " week": "standard",
    "lcws": "lcws",
    "minutes": "cdsagenda",
    "it": "it" }

def log(msg):
    #logfile = open("c:\\tmp\\mapfinal.log",'a')
    #logfile.write("%s:%s\n" %(now().strftime("%Y-%m-%d %H:%M:%S"),msg))
    print msg
    #logfile.close()
    pass



def getUser(name, email, org, password):
    #If Avatar with this email exists return it
    #else create new Avatar
    org = re.sub("[\r\n\v\t]+"," ",org)
    name = re.sub("[\r\n\v\t]+"," ",name)
    email = re.sub("[\r\n\v\t ]+","",email)
    emailmatch = ah.match({'email':email})
    if emailmatch != None and len(emailmatch) > 0 and emailmatch[0] != '':
        return emailmatch[0] #gets the avatar (if any) that matches the email address
    else:
        return createUser(name, email, org, password)#if user doesn't exist create


def createUser(name, email, org, password):
    #has problem that if no email exists and 2 users with same name will clash
    #perhaps change getUser() to check for same name if no email exist.
    #problem being that more than one person can have same name. Email unique.
    dummy = user.Avatar()
    #sets the user properties
    if name == '':#if there is no username makes the email address appear in it's place
        dummy.setName(email)
    else:
        dummy.setName(name)
    dummy.setEmail(email)
    dummy.setOrganisation(org)
    ah.add(dummy)
    avatar = ah.getById(dummy.id)
    if email != '':#creates the identity and sets the password for chairs etc.
        id = user.LocalIdentity(name, password, avatar)
    else:#user with no email address - identity not created
        return avatar
    try:
        AuthenticatorMgr().add(id)
    except (UserError):
        pass
    avatar.activateAccount()
    return avatar

def setType(style, id):
    if style == 'nicecompact':
        type = ''
    elif style == 'standard' or style == 'tools/printable' or style == 'seminars' or style == 'nosession' or style =='administrative' or style =='standard2' or style == 'minutes':#chooses the 'type' based on 'style' of AGENDA
        type = 'meeting'
    elif style == 'event' or style == 'week' or style == 'lecture':
        type = 'simple_event'
    else:#if stylesheet in AGENDA db is blank
        type = 'meeting'
    if type != '':
        #this if statement is in because if type is equal to nicecompact or lecture then currently no factory is used
        #when a factory type is created to go with these, remove the if statement and unindent the code.
        #instantiate the registry
        wr = webFactoryRegistry.WebFactoryRegistry()
        ch = conference.ConferenceHolder()
        #fetch the conference which type is to be updated
        c = ch.getById(id)
        #get the web factory. Possible values: simple_event, meeting
        fact = wr.getFactoryById(type)
        #register the factory for the conference
        wr.registerFactory(c, fact)
        #get_transaction().commit()

def getAddress(link):#parses the .link and .lnk.html files.  once it gets to http it keeps going till it reaches close quotation mark
    add = ''
    for i in link:
        if add == '':
            if i == 'h':
                add = add + i
        elif add == 'h':
            if i == 't':
                add = add + i
            else:
                add = ''
        elif add == 'ht':
            if i == 't':
                add = add + i
            else:
                add = ''
        elif add == 'htt':
            if i == 'p':
                add = add + i
            else:
                add = ''
        elif add[:4] == 'http' and add[-1:] != '\'' and add[-1:] != '\"':
            add = add + i
    return add[:-1]#returns the address. takes off the close quotation mark at the end

def getCat(Cat, fid, icon):#checks if Category exists, creates if need be, then returns the Category to add Conference to
    if fid != '0': #If level is below root
        cursor = agenda.cursor()
        cursor.execute("select * from LEVEL where uid = \'" + fid + "\'")#gets parent LEVEL
        cp = cursor.fetchone()#gets parent info
        #cp[0]-uid, cp[1]-fid, cp[2]-level, cp[3]-title, cp[4]-cd, cp[5]-md, cp[6]-abstract, cp[7]-icon
        #cp[8]-stitle, cp[9]-visibility, cp[10]-modifyPassword, cp[11]-accessPassword, cp[12]-categorder
        if cp[1] == "delet":
            return None
        newCat = conference.Category()#creates Category with parents properties
        newCat.setName(cp[3])
        newCat.setDescription(cp[6])
        newCat.setOrder(cp[12])
        newCat.setVisibility(cp[9])
        newCat.setId(cp[0])
        catParent = getCat(newCat, cp[1], cp[7])#goes to fetch the parent category
    else:#If at root level get the root category
        catParent = conference.CategoryManager().getRoot()
    catlist = catParent.getSubCategoryList()#get list of subcategories already in category
    for tup in catlist:#checks if the category already exists and returns it
        if tup.name == Cat.name and tup.id == Cat.id:
            return tup
    #if category doesn't exist - create it
    catParent.newSubCategory(Cat)
    if icon != "":
        iconpath = Config.getInstance().getCategoryIconPath(Cat.getId())
        os.system("scp tbaron@%s:%s/%s.gif /tmp/%s.gif" % (file_host,hosticonpath,Cat.getId(),Cat.getId()))
        os.system("convert /tmp/%s.gif %s" % (Cat.getId(),iconpath))
    #get_transaction().commit()
    return Cat


def getFiles(mat, f):#adds the files associated with a conference/session/contribution and adds them
    #f[0]-id, f[1]-format, f[2]-category, f[3]-cd, f[4]-md, f[5]-name, f[6]-path, f[7]-description, f[8]-numPages
    #f[9]-size, f[10]-deleted, f[11]-fileID, f[12]-eventID
    #if file name ends in .link open file, get address, make link
    cf = agenda.cursor()
    cf.execute("select password from FILE_PASSWORD where fileID=" + str(f[0]))
    f = cf.fetchone()
    if f!=None:
        password = f[0]
    else:
        password = ""
    if password!="":
        mat.setAccessKey(password)
        mat.setProtection(True)
    if getfiles!=0:
        error = False
        if f[5][-4:] == 'link' or f[5][-8:] =='lnk.html':
            if f[2] == 'moreinfo' and f[6][-8:] != 'moreinfo':
                path =  f[6].encode(sys.getfilesystemencoding()) + "/moreinfo/" + f[5].encode(sys.getfilesystemencoding())
            else:
                path = f[6].encode(sys.getfilesystemencoding()) + "/" + f[5].encode(sys.getfilesystemencoding())
            log("getFiles:link: path = %s"%path)
            if file_host != "localhost":
                os.system("scp 'tbaron@%s:%s' '/tmp/%s'" % (file_host,re.escape(path), f[5].encode(sys.getfilesystemencoding())))
                path = "/tmp/%s" %  f[5].encode(sys.getfilesystemencoding())
            try:
                f = file(path, 'rb')
                address = f.read()
                address = getAddress(address)
                f.close()
            except IOError,e:
                log("ressource file not found : %s" %path)
                error = True
                address = ''
            res = conference.Link()
            res.setURL(address)
        else:#if not a link
            res = conference.LocalFile()#creates new file and sets the local file path
            res.setFileName(f[5])
            if f[2] == 'moreinfo' and f[6][-8:] != 'moreinfo':
                path = f[6].encode(sys.getfilesystemencoding()) + "/moreinfo/" + f[5].encode(sys.getfilesystemencoding())
            else:
                path = f[6].encode(sys.getfilesystemencoding()) + "/" + f[5].encode(sys.getfilesystemencoding())
            log("getFiles:file: path = %s"%path)
            if file_host != "localhost":
                os.system("scp 'tbaron@%s:%s' '/tmp/%s'" % (file_host,re.escape(path), f[5].encode(sys.getfilesystemencoding())))
                path = "/tmp/%s" %  f[5].encode(sys.getfilesystemencoding())
            try:
                res.setFilePath(path)
            except Exception,e:
                log("ressource file not found : %s" %path)
                error = True
        if error:
            try:
                res.delete()
            except:
                log("cannot delete file")
        else:
            mat.addResource(res) #adds file to the material
        if file_host != "localhost":
            os.remove(path)


def getMinutes(mat, f):#adds the files associated with a conference/session/contribution and adds them
    #f[0]-id, f[1]-format, f[2]-category, f[3]-cd, f[4]-md, f[5]-name, f[6]-path, f[7]-description, f[8]-numPages
    #f[9]-size, f[10]-deleted, f[11]-fileID, f[12]-eventID
    #if file name ends in .link open file, get address, make link
    error = False
    path = f[6].encode(sys.getfilesystemencoding()) + "/" + f[5].encode(sys.getfilesystemencoding())
    log("getMinutes: path = %s"%path)
    if file_host != "localhost":
        os.system("scp tbaron@%s:%s /tmp/%s" % (file_host,path, f[5].encode(sys.getfilesystemencoding())))
        path = "/tmp/%s" %  f[5].encode(sys.getfilesystemencoding())
    try:
        f = open(path,'r')
        text = f.read()
        f.close()
    except Exception,e:
        log("ressource file not found : %s" %path)
        error = True
    if error:
        pass
    else:
        mat.setText(text)



def deleteUsers(start, number):#debug method to delete large number of users, starting with id = start and consecutive 'number' of ids
    ah = user.AvatarHolder()
    for i in range(number):
        x = i + start
        try:
            ah.remove(ah.getById(x))
            #print x
        except IndexError:
            pass

def deleteID():#debug method to delete id in Authenticator.  doesn't delete the 4 id's used by cds members
    au = user.Authenticator()
    for i in au.getList():
        if (i.login != 'hs') and (i.login != 'tb') and (i.login != 'db') and (i.login != 'cf') and (i.login != 'jb'):
            au.remove(i)
    for i in au.getList():
        print i.login


def genPW():#generates a random passord
    #choice has all uppercase, lowercase letters, and digits
    choice = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'Q','W','E','R','T','Y','U','I','O','P','A','S','D','F','G','H','J','K','L','Z','X','C','V','B','N','M','1','2','3','4','5','6','7','8','9','0']
    password = ''
    for i in range(6):#range(n) where n is the length of password wanted
        password = password + (random.choice(choice))
    return password

def getAllSubCategories(cat):
    cs = agenda.cursor()#creates a new cursor to the database
    cs.execute("select uid from LEVEL where fid = '%s'"%cat)
    c = cs.fetchall()#gets the next AGENDA
    subcatlist = map(lambda x: str(x[0]),list(c))
    allsubcatlist = []
    if subcatlist:
        for ic in subcatlist:
            allsubcatlist.extend(getAllSubCategories(ic))
    else:
        allsubcatlist.append(cat)
    return allsubcatlist


def getAgenda():
    print "migrating..."
    log("start getAgenda")
    cc = agenda.cursor()#creates a new cursor to the database
    listcat = getAllSubCategories("171")
    strlistcat = "','".join(listcat)
    #cc.execute("select * from AGENDA where id='a052023'")
    #cc.execute("select * from AGENDA where fid in ('%s') and YEAR(cd)=2004 order by id"%strlistcat)#gets the AGENDAS
    #cc.execute("select * from AGENDA where fid in ('%s') and id>='' order by id"%strlistcat)#gets the AGENDAS
    #cc.execute("select * from AGENDA where fid = '296'")#gets the AGENDAS
    cc.execute("select * from AGENDA where id > 'a015' and id < 'a02' order by id")#gets the AGENDAS
    #cc.execute("select * from AGENDA where id like 'a00%' and cd > '2000-12-01' ")#gets the AGENDAS
    #cc.execute("select * from AGENDA where id like 'a02%' and id >'a021094' order by id")
    #cc.execute("select * from AGENDA where id>='a045146' order by id")
    c = cc.fetchone()#gets the next AGENDA
    cate = agenda.cursor()#creates a cursor to get the LEVEL informaion
    #c[0]-title, c[1]-id, c[2]-stdate, c[3]-endate, c[4]-location, c[5]-nbsession, c[6]-chairman, c[7]-cem
    #c[8]-status, c[9]-an, c[10]-cd, c[11]-md, c[12]-stylesheet, c[13]-format, c[14]-confidentiality
    #c[15]-apassword, c[16]-repno, c[17]-fid, c[18]-acomments, c[19]-keywords, c[20]-visibility
    #c[21]-bld, c[22]-floor, c[23]-room, c[24]-stime, c[25]-etime
    #get CERN domain
    dh = domain.DomainHolder()
    CDom = None
    for dom in dh.getList():
        if dom.getName().upper() == "CERN":
            CDom = dom
    if not CDom:
        CDom = domain.Domain()
        CDom.setName("CERN")
        CDom.setDescription("CERN domain")
        CDom.addFiltersFromStr("128.141;128.142;137.138;192.91;194.12;192.16")
        dh.add( CDom )
        DBMgr.getInstance().commit()
    error = False
    ch = conference.ConferenceHolder()
    while c!=None:
        #DBMgr.getInstance().startRequest()
        try:
            log("add conference : %s" %c[1])
            cate.execute("select * from LEVEL where uid = \'" + c[17] + "\'")#gets the name of the Category the conf belongs in
            catWanted = conference.Category() #creates Category that the AGENDA should belong to
            level = cate.fetchone() #sets the category properties
            catWanted.setName(level[3])
            catWanted.setDescription(level[6])
            catWanted.setOrder(level[12])
            catWanted.setVisibility(level[9])
            catWanted.setId(level[0])
            category = getCat(catWanted, level[1],level[7])#checks to see if this category already exists - if not creates it
            if category == None:#Conference is in a category to delete: don't add
                log("Conference %s not added, it's inside a 'to delete' category"%c[1])
                DBMgr.getInstance().abort()
                c = cc.fetchone()
                continue
            user = getUser('CDS Agenda','cds.support@cern.ch', '', '') #creates a user representing creator
            try:
                cd = datetime(c[10].year, c[10].month, c[10].day)
            except:
                cd = datetime(1999,1,1)
            try:
                md = datetime(c[11].year, c[11].month, c[11].day)
            except:
                md = datetime(1999,1,1)
            try:
                conf = ch.getById(c[1])
            except:
                pass
            conf = category.newConference(user,c[1],cd,md)#creates new Conference to map onto
            # update counter
            #year = c[1][1:3]
            #count = c[1][3:]
            #if count == "":
            #    count = 0
            #counterName = "CONFERENCE%s" % year
            #idxs = ch._getTree("counters")
            #if not idxs.has_key(counterName):
            #    idxs[counterName] = Counter()
            #idxs[counterName].sync(int(count))
            if c[8] == "close":
                conf.setClosed(True)
            conf.setTitle(c[0])
            conf.setDescription(c[18])
            if str(c[20]) == '0' or str(c[20]) == '':
                visibility = 999
            else:
                visibility = int(c[20])
            conf.setVisibility(visibility)
            startDate = datetime(c[2].year, c[2].month, c[2].day, int(c[24].seconds/3600), int((c[24].seconds % 3600) / 60))
            endDate = None
            if c[3] != None:
                endDate = datetime(c[3].year, c[3].month, c[3].day, int(c[25].seconds/3600), int((c[25].seconds % 3600) / 60))
            if not endDate or endDate <= startDate:
                endDate = datetime(c[2].year, c[2].month, c[2].day, int(c[24].seconds/3600), int((c[24].seconds % 3600) / 60))
            conf.setDates(startDate, endDate)
            if c[4] != "0--":
                loc = conference.CustomLocation()
                loc.setName(c[4])
                conf.setLocation(loc)
        except (MaKaCError,AttributeError),e:
            log("Error : %s : conference not added" %e)
            c = cc.fetchone()#gets the next conference
            error = True
        if not error:
            pw = genPW()#generates random password
            if c[6] == None or c[6] == '\xa0':
                username = ''
            else:
                username = c[6]
            if c[7] == None:
                uemail = ''
            else:
                uemail = c[7]
            if uemail == '' or username.count(" ")>=max_white_space_in_names:#if not full user details exist
                if username != '' or uemail != '':
                    if username != '':
                        chairtext = username
                    else:
                        chairtext = uemail
                    if uemail!='':
                        chairtext = "<a href=\"mailto:%s\">%s</a>" % (uemail,chairtext)
                    conf.setChairmanText(chairtext)
            else:
                chair = getUser(username, uemail, '', pw)#creates the chairman user
                conf.addChair(chair)
            setType(c[12], conf.getId())#sets the format of the agenda
            if c[13] == 'olist':#facility to cope with this not in MaKaC
                pass#set the format of talks to ordered list (A,B,C etc) rather than times
            if c[23]!="0--":
                loc = conference.CustomRoom()
                loc.setName(c[23])
                conf.setRoom(loc)
            cf = agenda.cursor()
            #gets the files associated with this conference
            cf.execute("select * from FILE, FILE_EVENT where FILE.id = fileID and eventID = \'" + c[1] +  "\'")
            f = cf.fetchone()#gets the first file form the list
            while f!=None:
                list = conf.getMaterialList()
                type = f[2]
                found = 0
                #if type in list get existing material
                for i in list:
                    if i.getTitle() == type:
                        found = 1
                        mat = i
                if found:
                    getFiles(mat, f)#add resources to material
                else:#if not then create new material with name 'type'
                    mat = conference.Material()
                    mat.setTitle(type)
                    conf.addMaterial(mat)
                    getFiles(mat, f)#add resources to material
                f = cf.fetchone()#get next file/resource
            if c[12] == "nosession":#if there are no sessions look for contributions that go directly onto conference
                addToConf(c, conf)
            else:
                getSessions(c, conf)#gets the sessions belonging to this conference
            confId = conf.getId()
            # ACCESS CONTROL
            if c[14] == 'password':#if conference is password protected creates and access user
                conf.setAccessKey(c[15])#set the access password
                conf.setProtection(1)#makes the conference restricted access
                #conf.grantAccess(colin)#grants access rights to me (for testing reasons)
            elif c[14] == 'cern-only':
                conf.requireDomain(CDom)
                log("added CERN domain")
            # MODIFICATION RIGHTS
            conf.setModifKey(c[9])#add modification key
            log("Conference added : MaKaC ID : %s" %confId)
            # DEFAULT STYLE
            if c[12] in styles.keys():
                displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(conf).setDefaultStyle(styles[c[12]])
            else:
                displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(conf).setDefaultStyle("standard")
            c = cc.fetchone()#gets the next conference
        else:
            error = False
            DBMgr.getInstance().commit()
    log("End adding conferences")
    print "End"




def getSessions(c, conf):
    cs = agenda.cursor()#craetes a cursor and selects all the seesion data for that conference
    cs.execute( "select * from SESSION where ida = \'" + c[1] + "\'")
    s = cs.fetchone()
    #s[0]-ida, s[1]-ids, s[2]-schairman, s[3]-speriod1, s[4]-stime, s[5]-eperiod1, s[6]-etime, s[7]-stitle
    #s[8]-snbtalks, s[9]-slocation, s[10]-scem, s[11]-sstatus, s[12]-bld, s[13]-floor
    #s[14]-room, s[15]-broadcasturl, s[16]-cd, s[17]-md, s[18]-scomment
    while s!=None:#while there are more session
        if c[12]=="nosession" and c[5] == 1:
            ses = conf
        else:
            ses = conference.Session()#add a new seesion to the conference
            slot = conference.SessionSlot(ses)
            if (s[3] == s[5]) and (s[4] == s[6]):#if session has length of 0 set length to 1min so as not to raise exception. Results in sessions of 1min being created during mapping
                min = (s[6].seconds % 3600) / 60
                sd = datetime(s[3].year, s[3].month, s[3].day, s[4].seconds/3600, (s[4].seconds % 3600) / 60)
                ed = datetime(s[5].year, s[5].month, s[5].day, s[6].seconds/3600, min)
                ses.setStartDate(sd,2)#set the session properties
                ses.setEndDate(ed,2)
                slot.setDates(sd,ed,2)
            else:
                try:
                    sd = datetime(s[3].year, s[3].month, s[3].day, int(s[4].seconds/3600), int((s[4].seconds % 3600) / 60))
                    ses.setStartDate(sd,2)#set the session properties
                    if (s[5] != None) and (s[6] != None):
                        ed = datetime(s[5].year, s[5].month, s[5].day, int(s[6].seconds/3600), int((s[6].seconds % 3600) / 60))
                    else:
                        ed = datetime(s[3].year, s[3].month, s[3].day, int(s[4].seconds/3600), int((s[4].seconds % 3600) / 60))
                    ses.setEndDate(ed,2)
                    slot.setDates(sd,ed,2)
                except (Exception,AttributeError,MaKaCError),e:
                    log("error adding session %s:%s, start or end date note found:%s" %(s[0],s[1],e))
                    conf.removeSession(ses)
                    ses = None
                    return
            ses.addSlot(slot)
            ses.setTitle(s[7])
            #get_transaction().commit()
            if s[2] == None:
                username = ''
            else:
                username = s[2]
            if s[10] == None:
                uemail = ''
            else:
                uemail = s[10]
            if username == '' or uemail == '' or username.count(" ")>=max_white_space_in_names:#if not full user details exist
                if username != '' or uemail != '':
                    if username != '':
                        convenertext = username
                    else:
                        convenertext = uemail
                    if uemail!='':
                        convenertext = "<a href=\"mailto:%s\">%s</a>" % (uemail,convenertext)
                    ses.setConvenerText(convenertext)
            else:
                pw = genPW()#generates random password
                convener = getUser(username, uemail,'',  pw)#creates a user representing the convener
                part = conference.SessionChair()
                part.setDataFromAvatar(convener)
                ses.addConvener(part)#and adds the user to the list
            if s[11]=="close":
                ses.setClosed(True)
            if s[9]!="0--":
                loc = conference.CustomLocation()
                loc.setName(s[9])
                ses.setLocation(loc)
            if s[14]!="0--":
                loc = conference.CustomRoom()
                loc.setName(s[14])
                ses.setRoom(loc)
            if s[18]:
                ses.setDescription(s[18])
            conf.addSession(ses,2)
        #gets the files associated with this session
        cf.execute("select * from FILE, FILE_EVENT where FILE.id = fileID and eventID = \'" + s[0] + s[1] +  "\'")
        f = cf.fetchone()
        while f!=None:
            type = f[2]
            if type == "minutes" and not isinstance(ses,conference.Conference):
                mi = ses.getMinutes()
                if not mi:
                    mi = ses.createMinutes()
                if f[5] == s[0] + s[1] + ".txt":
                    getMinutes(mi,f)
                else:
                    getFiles(mi, f)
            else:
                list = ses.getMaterialList()
                found = 0
                #if type in list get existing material
                for i in list:
                    if i.getTitle() == type:
                        found = 1
                        mat = i
                if found:
                    getFiles(mat, f)#add resources to material
                else:#if not then create new material with name 'type'
                    mat = conference.Material()
                    mat.setTitle(type)
                    ses.addMaterial(mat)
                    getFiles(mat, f)#add resources to material
            f = cf.fetchone()#get next file/resource
        addTalksToSession(s, ses, slot)#gets the talks associated with the session
        s = cs.fetchone()#gets the next session



def addToConf(c, conf):#adds talks directly to conference - for simple meetings
    cs = agenda.cursor()#creates a cursor and selects all the seesion data for that conference
    cs.execute( "select * from SESSION where ida = \'" + c[1] + "\'")
    s = cs.fetchone()
    #s[0]-ida, s[1]-ids, s[2]-schairman, s[3]-speriod1, s[4]-stime, s[5]-eperiod1, s[6]-etime, s[7]-stitle
    #s[8]-snbtalks, s[9]-slocation, s[10]-scem, s[11]-sstatus, s[12]-bld, s[13]-floor
    #s[14]-room, s[15]-broadcasturl, s[16]-cd, s[17]-md, s[18]-scomment
    if s!=None:#If there is a session
        addTalksToConference(s, conf)#gets the talks associated with the session and adds directly to the conference


def addTalksToConference(s, ses):
    ct = agenda.cursor()#creates a cursor and gets all the Talks associated with this session
    ct.execute("select * from TALK where ids = \'" + s[1] +"\' and ida = \'" + s[0] + "\'")
    t = ct.fetchone()#selects the first talk from the list
    #t[0]-ida, t[1]-ids, t[2]-idt, t[3]-ttitle, t[4]-tspeaker, t[5]-tday, t[6]-tcomment, t[7]-location
    #t[8]-bld, t[9]-floor, t[10]-room, t[11]-broadcasturl, t[12]-type, t[13]-cd, t[14]-md, t[15]-category
    #t[16]-stime, t[17]-repno, t[18]-affiliation, t[19]-duration, t[20]-email
    while t!=None:#if there is another talk
        if t[12] == 2:#if talk is of type break
            br = schedule.BreakTimeSchEntry()
            br.setTitle(t[3])#sets the break details
            br.setDescription(t[6])
            br.setStartDate(datetime(t[5].year, t[5].month, t[5].day, int(t[16].seconds/3600), int((t[16].seconds % 3600) / 60)))
            try:
                br.setDuration(int(t[19].seconds/3600), int((t[19].seconds % 3600) / 60))
            except Exception,e:
                log("error setting break end time %s-%s-%s: %s" %(t[0],t[1],t[2],e))
                #get_transaction().abort()
            ses.getSchedule().addEntry(br,2)#create a new break
        else:
            talk = ses.newContribution(id="%s%s" % (t[1],t[2]))#adds a contribution to the session
            if t[15] != '':
                title = "<b>%s</b><br>%s" % (t[15],t[3])
            else:
                title = t[3]
            talk.setTitle(title)#sets the contribution details
            talk.setDescription(t[6])
            #talk.setCategory(t[15]) #sets category header for talks.  Mainly used in seminars for the week of.  Not in MaKaC
            if t[7]!="0--":
                loc = conference.CustomLocation()
                loc.setName(t[7])
            #get_transaction().commit()
            if t[4] == None:
                username = ''
            else:
                username = t[4]
            if t[20] == None:
                uemail = ''
            else:
                uemail = t[20]
            if t[18]:
                aff = t[18]
            else:
                aff = ''
            if username == '' or uemail == '' or username.count(" ")>=max_white_space_in_names:#if not full user details exist
                if username != '' or uemail != '':
                    if username != '':
                        speakertext = username
                    else:
                        speakertext = uemail
                    if uemail!='':
                        speakertext = "<a href=\"mailto:%s\">%s</a>" % (uemail,speakertext)
                    if aff != '':
                        speakertext = "%s (%s)" % (speakertext,aff)
                    talk.setSpeakerText(speakertext)
            else:
                pw = genPW()#generates random password
                speaker = getUser(username, uemail, aff,pw)#creates a user representing the speaker
                part = conference.ContributionParticipation()
                part.setDataFromAvatar(speaker)
                talk.addPrimaryAuthor(part)
                talk.addSpeaker(part)#and adds the user to the list
            if t[10]!="0--":
                talk.setLocation(loc)
                loc = conference.CustomRoom()
                loc.setName(t[10])
                talk.setRoom(loc)
            talk.setStartDate(datetime(t[5].year, t[5].month, t[5].day, int(t[16].seconds/3600), int((t[16].seconds % 3600) / 60)))
            talk.setDuration(int(t[19].seconds/3600),int((t[19].seconds % 3600) / 60))
            #gets the files associated with this talk
            cf.execute("select * from FILE, FILE_EVENT where FILE.id = fileID and eventID = \'" + t[0] + t[1] + t[2] + "\'")
            f = cf.fetchone()
            while f!=None:
                type = f[2]
                if type == "minutes":
                    mi = talk.getMinutes()
                    if not mi:
                        mi = talk.createMinutes()
                    if f[5] == t[0] + t[1] + t[2] + ".txt":
                        getMinutes(mi,f)
                    else:
                        getFiles(mi, f)
                else:
                    list = talk.getMaterialList()
                    found = 0
                    #if type in list get existing material
                    for i in list:
                        if i.getTitle() == type:
                            found = 1
                            mat = i
                    if found:
                        getFiles(mat, f)#add resources to material
                    else:#if not then create new material with name 'type'
                        mat = conference.Material()
                        mat.setTitle(type)
                        talk.addMaterial(mat)
                        getFiles(mat, f)#add resources to material
                f = cf.fetchone()#get next file/resource
            getSubTalks(t, talk) #call to the function which would map the subtalks
            ses.getSchedule().addEntry(talk.getSchEntry(),2)
        t = ct.fetchone()


def addTalksToSession(s, ses, slot):
    ct = agenda.cursor()#creates a cursor and gets all the Talks associated with this session
    ct.execute("select * from TALK where ids = \'" + s[1] +"\' and ida = \'" + s[0] + "\'")
    t = ct.fetchone()#selects the first talk from the list
    #t[0]-ida, t[1]-ids, t[2]-idt, t[3]-ttitle, t[4]-tspeaker, t[5]-tday, t[6]-tcomment, t[7]-location
    #t[8]-bld, t[9]-floor, t[10]-room, t[11]-broadcasturl, t[12]-type, t[13]-cd, t[14]-md, t[15]-category
    #t[16]-stime, t[17]-repno, t[18]-affiliation, t[19]-duration, t[20]-email
    while t!=None:#if there is another talk
        if t[5] != None:
            if t[12] == 2:#if talk is of type break
                br = schedule.BreakTimeSchEntry()
                br.setTitle(t[3])#sets the break details
                br.setDescription(t[6])
                br.setColor("#90C0F0")
                br.setStartDate(datetime(t[5].year, t[5].month, t[5].day, int(t[16].seconds/3600), int((t[16].seconds % 3600) / 60),2))
                try:
                    br.setDuration(int(t[19].seconds/3600), int((t[19].seconds % 3600) / 60))
                except Exception,e:
                        log("error setting break end time %s-%s-%s: %s" %(t[0],t[1],t[2],e))
                        #get_transaction().abort()
                slot.getSchedule().addEntry(br,2)#create a new break
                slot.getSchedule().reSchedule()
            else:
                talk = ses.newContribution(id="%s%s" % (t[1],t[2]))#adds a contribution to the session
                if t[15] != '':
                    title = "<b>%s</b><br>%s" % (t[15],t[3])
                else:
                    title = t[3]
                talk.setTitle(title)#sets the contribution details
                talk.setDescription(t[6])
                #talk.setCategory(t[15]) #sets category header for talks.  Mainly used in seminars for the week of.  Not in MaKaC
                if t[7]!="0--":
                    loc = conference.CustomLocation()
                    loc.setName(t[7])
                #get_transaction().commit()
                pw = genPW()#generates random password
                if t[4] == None:
                    username = ''
                else:
                    username = t[4]
                if t[20] == None:
                    uemail = ''
                else:
                    uemail = t[20]
                if t[18]:
                    aff = t[18]
                else:
                    aff = ''
                if username == '' or uemail == '' or username.count(" ")>=max_white_space_in_names:#if not full user details exist
                    if username != '' or uemail != '':
                        if username != '':
                            speakertext = username
                        else:
                            speakertext = uemail
                        if uemail!='':
                            speakertext = "<a href=\"mailto:%s\">%s</a>" % (uemail,speakertext)
                        if aff!='':
                            speakertext = "%s (%s)" % (speakertext,aff)
                        talk.setSpeakerText(speakertext)
                else:
                    speaker = getUser(username, uemail, aff,pw)#creates a user representing the speaker
                    part = conference.ContributionParticipation()
                    part.setDataFromAvatar(speaker)
                    talk.addPrimaryAuthor(part)
                    talk.addSpeaker(part)#and adds the user to the list
                if t[10]!="0--":
                    talk.setLocation(loc)
                    loc = conference.CustomRoom()
                    loc.setName(t[10])
                    talk.setRoom(loc)
                if t[5]!=None:
                    talk.setStartDate(datetime(t[5].year, t[5].month, t[5].day, int(t[16].seconds/3600), int((t[16].seconds % 3600) / 60)),2)
                talk.setDuration(t[19].seconds/3600,(t[19].seconds % 3600) / 60)
                #gets the files associated with this talk
                cf.execute("select * from FILE, FILE_EVENT where FILE.id = fileID and eventID = \'" + t[0] + t[1] + t[2] + "\'")
                f = cf.fetchone()
                while f!=None:
                    type = f[2]
                    if type == "minutes":
                        mi = talk.getMinutes()
                        if not mi:
                            mi = talk.createMinutes()
                        if f[5] == t[0] + t[1] + t[2] + ".txt":
                            getMinutes(mi,f)
                        else:
                            getFiles(mi, f)
                    else:
                        list = talk.getMaterialList()
                        found = 0
                        #if type in list get existing material
                        for i in list:
                            if i.getTitle() == type:
                                found = 1
                                mat = i
                        if found:
                            getFiles(mat, f)#add resources to material
                        else:#if not then create new material with name 'type'
                            mat = conference.Material()
                            mat.setTitle(type)
                            talk.addMaterial(mat)
                            getFiles(mat, f)#add resources to material
                    f = cf.fetchone()#get next file/resource
                getSubTalks(t, talk) #call to the function which would map the subtalks
                sch = slot.getSchedule()
                try:
                    sch.addEntry(talk.getSchEntry(),2)
                except Exception,e:
                    log("%s-%s-%s: %s" %(t[0],t[1],t[2],e))
        t = ct.fetchone()

def getSubTalks(t, talk):#method for mapping subtalks.
    #Program logic is correct so just needs changed to fit the way subtalks are implemented
    cst = agenda.cursor()#creates cursor and gets all the subtalks
    cst.execute("select * from SUBTALK where fidt = \'" + t[2] +"\' and ida = \'" + t[0] + "\' order by stime")
    st = cst.fetchone()#gets the first subtalk on the list
    #st[0]-ida, st[1]-ids, st[2]-idt, st[3]-ttitle, st[4]-tspeaker, st[5]-tday, st[6]-tcomment, st[7]-type
    #st[8]-cd, st[9]-md, st[10]-stime, st[11]-repno, st[12]-affiliation, st[13]-duration, st[14]-fidt, st[15]-email
    while st!=None:#while there are subtalk
        sub = talk.newSubContribution()#add new subtalk to the contribution
        sub.setTitle(st[3])#sets the details
        sub.setDescription(st[6])
        #sub.setStartDate(st[6].year, st[6].month, st[6].day, st[11].seconds/3600, st[11].seconds % 3600) / 60)
        #get_transaction().commit()
        #sub.setEndTime(end.hour, end.minute)
        #sub.setDuration(st[13][0:2],st[13][3:5])X
        sub.setDuration(st[13].seconds/3600,(st[13].seconds % 3600) / 60)
        #SPEAKERS
        if st[4] == None:
            username = ''
        else:
            username = st[4]
        usernames = username.split(";")
        if st[15] == None:
            uemail = ''
        else:
            uemail = st[15].replace(" ","")
        if username == '' or uemail == '' or username.count(" ")>=max_white_space_in_names:#if not full user details exist
            if username != '' or uemail != '':
                if username != '':
                    speakertext = username
                else:
                    speakertext = uemail
                if uemail!='':
                    speakertext = "<a href=\"mailto:%s\">%s</a>" % (uemail,speakertext)
                sub.setSpeakerText(speakertext)
        else:
            for name in usernames:
                pw = genPW()#generates random passwor
                speaker = getUser(name, uemail, st[12], pw)#creates a user representing the speaker
                sub.addSpeaker(speaker)#and adds the user to the list
        #FILES
        cf.execute("select * from FILE, FILE_EVENT where FILE.id = fileID and eventID = \'" + st[0] + st[1] + st[2] + "\'")
        f = cf.fetchone()
        while f!=None:
            type = f[2]
            if type == "minutes":
                mi = sub.getMinutes()
                if not mi:
                    mi = sub.createMinutes()
                if f[5] == t[0] + t[1] + t[2] + ".txt":
                    getMinutes(mi,f)
                else:
                    getFiles(mi, f)
            else:
                list = sub.getMaterialList()
                found = 0
                #if type in list get existing material
                for i in list:
                    if i.getTitle() == type:
                        found = 1
                        mat = i
                if found:
                    getFiles(mat, f)#add resources to material
                else:#if not then create new material with name 'type'
                    mat = conference.Material()
                    mat.setTitle(type)
                    sub.addMaterial(mat)
                    getFiles(mat, f)#add resources to material
            f = cf.fetchone()#get next file/resource
        st = cst.fetchone()

#if __name__ == "__main__":
#    DBMgr.getInstance().startRequest()
#    getAgenda()
#    DBMgr.getInstance().endRequest()

def main():
    return getAgenda()

if __name__ == "__main__":
    main()
    #import profile
    #import pstats
    #profile.run('main()', 'test_speed_prof')
    #p = pstats.Stats('test_speed_prof')
    #p.sort_stats('cumulative').print_stats()

DBMgr.getInstance().endRequest()
