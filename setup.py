# -*- coding: utf-8 -*-
##
## $Id: setup.py,v 1.122 2009/06/17 15:27:43 jose Exp $
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

from subprocess import Popen, PIPE
import xml.sax, sys, os, shutil, string, fileinput, commands
from distutils.sysconfig import get_python_lib
from optparse import OptionParser, OptionGroup
from distutils.command.sdist import sdist as _sdist
from distutils.cmd import Command

try:
    from etc import confmerge
except ImportError,e:
    import confmerge

#variables will change dependant on the function called
class vars:
    packageDir='None'
    tplDir='None'
    tplJSDir='None'
    tplCHelpDir='None'
    htdocsDir='None'
    helpDir ='None'
    imageDir='None'
    confdef='None'
    docDir='None'
    versionVal = 'None'
    ssDir='None'
    currdbDir='None'
    dbbackDir='None'
    toolsDir='None'
    accessuser = 'None'
    accessgroup='None'
    logDir='None'
    develop = 1 #Development =0, user installation=1
    cernDistDir=None
    logDir='None'
    tmpDir='None'

x=vars()

def makeConf(reconfiguring=False):
    if reconfiguring:
        confdir = 'config.xml'
    else:
        confdir = os.path.join('etc','config.xml')
    cm=confmerge.ConfigFile(confdir)
    cm.getXmlFile()
    cm.getAllAsDicts()
    
    #Taking the information needed from config.xml
    paths = cm.pathdict
    db_params = cm.dbdict
    ac_params = cm.acdict
    smtp = cm.smtpdict
    isearch = cm.isearchdict
    footer = cm.footertextdict
    
    url_base = cm.urldict
    login_url = cm.logurldict
    reg_url = cm.regurldict
    shortevent_url = cm.shorteventurldict
    shortcateg_url = cm.shortcategurldict
    support = cm.supportdict
    supp_email = cm.emaildict
    OAI = cm.oaidict
    fileConv = cm.fcdict
    
    reportNumberSystems=cm.repnumsysdict
    worker=cm.worker
    types = cm.filedict
    authlist = cm.authlistdict
    niceConfig = cm.niceCfgDict
    sanitaryLevel = cm.sanitaryLevelValue
    
    #Default Paths if user leaves blank
    platform = sys.platform
    
    DefaultPaths =\
             { "win32": {"htdocs": "C:\\Program Files\\Apache Group\\Apache2\\htdocs\\MaKaC",\
                         "archive": "C:\\indico\\archive",\
                         "uploadedFiles": "C:\\indico\\temp",\
                         "dbCache": "C:\\indico\\db_cache",
                         "logDir": "C:\\indico\\log"},\
               "linux2":{"htdocs" : "/opt/indico/www/htdocs",\
                         "archive" : "/opt/indico/archive", \
                         "uploadedFiles": "/opt/indico/tmp",\
                         "dbCache": "/opt/indico/db_cache", \
                         "logDir": "/opt/indico/log"}
             }
    platdef=DefaultPaths.get(platform)

    pkgdef=os.path.join(get_python_lib())

    #Assigns correct path names to directories to be used in the program

    if x.develop==0:
        pkg = raw_input("Please enter the directory where your indico module is located\nFor example C:\development\indico or /opt/indico/, or type 'cancel' to exit.\n\n")
        if pkg =="cancel":
            sys.exit()
        x.packageDir = pkg
    elif paths['pkgdirectory'].strip()=="":
        x.packageDir=pkgdef
    else:
        x.packageDir=paths['pkgdirectory'].encode('utf-8').strip()

    if x.develop ==0:
        tpldef = os.path.join(x.packageDir, "indico", "MaKaC", "webinterface" ,"tpls")
    else:
        tpldef = os.path.join(x.packageDir, "MaKaC","webinterface","tpls")

    if x.develop==0:
        ssdef =  os.path.join(x.packageDir, "indico","MaKaC","webinterface","stylesheets")
    else:
        ssdef =  os.path.join(x.packageDir, "MaKaC","webinterface","stls")

    x.confdef = os.path.join(x.packageDir,"MaKaC","common")
    x.docDir = os.path.join(x.packageDir,"MaKaC","doc")
    x.toolsDir = os.path.join(x.packageDir,"MaKaC","scripts")
    
    if x.develop==0:
        x.htdocsDir = os.path.join(x.packageDir,"indico","htdocs")
    elif paths['htdocs'].strip()=="":
        x.htdocsDir = platdef.get("htdocs","")
    else:
        x.htdocsDir=paths['htdocs'].encode('utf-8').strip()

    if x.develop==0:
        x.XMLCacheDir = os.path.join(x.packageDir, "cache")
    elif paths['XMLCacheDir'].strip()=="":
        x.XMLCacheDir = platdef.get("XMLCacheDir","")
    else:
        x.XMLCacheDir=paths['XMLCacheDir'].encode('utf-8').strip()
    
    x.imageDir = os.path.join(x.htdocsDir,"images")

    if x.develop ==0:
        TempDir = os.path.join(x.packageDir, "temp")
    elif paths['temp'].strip()=="":
        TempDir = platdef.get("uploadedFiles","")
        if os.path.exists(TempDir) is False:
            os.makedirs(TempDir)
    else:
        TempDir=paths['temp'].encode('utf-8').strip()
    x.tmpDir=TempDir
        
    if x.develop ==0:
        ArchiveDir = os.path.join(x.packageDir, "archive")
    elif paths['archive'].strip()=="":
        ArchiveDir = platdef.get("archive","")
        if os.path.exists(ArchiveDir) is False:
            os.makedirs(ArchiveDir)
    else:
        ArchiveDir=paths['archive'].encode('utf-8').strip()

    if x.develop ==0:
        x.logDir = os.path.join(x.packageDir, "log")
    elif paths['logDir'].strip()=="":
        x.logDir = platdef.get("logDir")
    else:
        x.logDir = paths['logDir'].encode('utf-8').strip()

    if paths['tpls'].strip()=="":
        x.tplDir= tpldef
    else:
        x.tplDir=paths['tpls'].encode('utf-8').strip()

    x.tplJSDir= x.tplDir + "/js"
    x.tplCHelpDir= x.tplDir + "/chelp"

    if paths['ssheets'].strip()=="":
        x.ssDir= ssdef
    else:
        x.ssDir=paths['ssheets'].encode('utf-8').strip()

    if x.develop==0:
        commonDir = os.path.join(x.packageDir,"indico","MaKaC","common","MaKaCConfig.py")
       
    #Variables holding the datatbase and access parameters,url base, loginurl, email support and smtp Server
    if x.develop==0:
        dbhost = raw_input("\n\nPlease enter your database host\nFor example pcdh24.cern.ch\n\n")
    else:
        dbhost =db_params["host"]
    if x.develop==0:
        dbport = raw_input("\n\nPlease enter your database port\nFor example 9675\n\n")
    else:
        dbport =db_params["port"]
    if x.develop==0:
        dbusername=""
        dbpassword=""
        dbrealm=""
    else:
        dbusername=db_params["username"]
        dbpassword=db_params["password"]
        dbrealm=db_params["realm"]
    if x.develop==0:
        url_base = raw_input("\n\nPlease enter your url base\nFor example http://pcdh24.cern.ch/indico\n\n")
    else:
        url_base= url_base["url"]
    url_base_secure = url_base.replace("http://", "https://")
    if x.develop==0:
        fileConvServer = raw_input("\n\n[Automatic conversion] Please enter conversion server URL [OPTIONAL]\nFor example http://pcuds01.cern.ch/getSegFile.py\n\n")
    else:
        fileConvServer = fileConv.get("conversion_server","")
    fileConvResponse = fileConv.get("response_url","")
    if x.develop==0:
        x.currdbDir = raw_input("\n\nPlease enter the path to the directory that will contain the database files [OPTIONAL]\n\n")
    else:
        x.currdbDir =paths["currentdb"]
    if x.develop==0:
        x.dbbackDir = raw_input("\n\nPlease enter the path to the directory that will contain the database backups [OPTIONAL]\n\n")
    else:
        x.dbbackDir =paths["dbbackups"]
    login_url = login_url["loginurl"]
    reg_url = reg_url["registrationurl"]
    shortevent_url = shortevent_url["shorteventurl"]
    shortcateg_url = shortcateg_url["shortcategurl"]
    supportEmail = supp_email["email"]
    publicSupportAddress = support["support"]
    smtpServer = smtp["SMTPServer"]
    smtpLogin = smtp["SMTPLogin"]
    smtpPassword = smtp["SMTPPassword"]
    smtpUseTLS = smtp["SMTPUseTLS"]
    isearchServer = isearch["searchServer"]
    isearchClass = isearch["searchClass"]
    footerText = footer["footer_text"]

    auth_list =[]
    listrange = range(len(authlist))
    for a in listrange:
        auth_list.append(authlist[a].encode())
    
    if ac_params["user"].strip()!="":
        x.accessuser = ac_params["user"]
    if ac_params["group"].strip()!="":
        x.accessgroup = ac_params["group"]


    #Variables holding OAI information
    oaiLog=OAI['logfile']
    nb_recs=OAI['nb_record']
    nb_id=OAI['nb_ids']
    oai_exp=OAI['oai_rt_exp']
    oains=OAI['namespace']
    iconfNs=OAI['iconfNS']
    iconfXSD=OAI['iconfXSD']
    reposName=OAI['reposName']
    reposId=OAI['reposId']

#Generates the MaKaCConfig.py configuration script
    
    #Parameters not changed by user but need to be in the config file.
    if x.develop==0:
        if os.path.exists(commonDir) is True:
            note = raw_input("You are about to overwrite your existing MaKaCConfig.py file,\nType 'y' to continue, or 'n' to cancel\n\n")
            if note != "y":
                print ("Cancelled")
                sys.exit()               
        fh=open(commonDir,"w")
    else:
        fh=open("MaKaCConfig.py","w")
    fh.write("""from pytz import common_timezones
             \nTimezones=common_timezones
             \n\"\"\"This file contains parameters, path names and other configurations\"\"\"  \
             \n#Parameters not configured by user\n#****************************************************************************         \
             \n\n#Template files (if not using default ones)\nTPL_files={}\
             \n\n#Templates, user defined variables\n""")
    fh.write("""TPL_vars={"MaKaCHomeURL":"%s/index.py"} """%url_base)
    fh.write("""\n#The image Url Base\nImagesBaseURL="%s/images" """%url_base)
    fh.write("""\n#The image Url Base for HTTPS\nImagesBaseSecureURL="%s/images" """%url_base_secure)
    fh.write("""\n\n#MaKaC stylesheet\ncssStylesheetName="indico.css"\n """)
    fh.write("""\n#Public Folder\npublicFolder="results"\n """)

    fh.write("""\n\n#Parameters copied from setup\n#*****************************************************************************\n""")
    fh.write("""\nsanitaryLevel="%s" """%sanitaryLevel)
    #Parameters copied from xml file.
    fh.write("""\nworker="%s" """%worker)
    fh.write("""\nDB_params=("%s",%s)"""%(dbhost,dbport))
    fh.write("""\nDBUserName = "%s" """%(dbusername))
    fh.write("""\nDBPassword = "%s" """%(dbpassword))
    fh.write("""\nDBRealm = "%s" """%(dbrealm))
    fh.write("""\n\nURL_base="%s" """%url_base)
    fh.write("""\n\nSecure_URL_base="%s" """%url_base_secure)
    fh.write("""\n\nloginURL="%s" """%login_url)
    fh.write("""\n\nregURL="%s" """%reg_url)
    fh.write("""\n\nshortEventURL="%s" """%shortevent_url)
    fh.write("""\n\nshortCategURL="%s" """%shortcateg_url)
    fh.write("""\n\nsupportEmail="%s" """%supportEmail)
    fh.write("""\n\npublicSupportAddress="%s" """%publicSupportAddress)
    fh.write("""\n\nauthenticatorList=%s """%auth_list)
    fh.write("""\n\nNiceLogin="%s" """%niceConfig["NiceLogin"])
    fh.write("""\nNicePassword="%s" """%niceConfig["NicePassword"])
    #Paths
    fh.write("""\n\nTPL_dir=\t\t"%s" """%x.tplDir.replace("\\","\\\\"))
    fh.write("""\nhtdocsDir=\t\t"%s" """%x.htdocsDir.replace("\\","\\\\"))
    fh.write("""\nImagesDir=\t\t"%s" """%x.imageDir.replace("\\","\\\\"))
    fh.write("""\nUploadedFilesTempDir=\t"%s" """%TempDir.replace("\\","\\\\"))
    fh.write("""\nArchivePath=\t\t"%s" """%ArchiveDir.replace("\\","\\\\"))
    fh.write("""\nStylesheetPath=\t\t"%s" """%x.ssDir.replace("\\","\\\\"))
    fh.write("""\nCurrentDBPath=\t\t"%s" """%x.currdbDir.replace("\\","\\\\"))
    fh.write("""\nDBBackupsPath=\t\t"%s" """%x.dbbackDir.replace("\\","\\\\"))
    fh.write("""\nXMLCacheDir=\t\t"%s" """%x.XMLCacheDir.replace("\\","\\\\"))

    fh.write("""\nlogDir=\t\t"%s" """%x.logDir.replace("\\","\\\\"))

    #file conversion server

    fh.write("""\nlogDir=\t\t"%s" """%x.logDir.replace("\\","\\\\"))
    
    fh.write("""\n\nfileConverter={"conversion_server":"%s", "response_url":%s}"""%(fileConvServer,fileConvResponse))
    #filetypes
    fh.write("""\n\nReportNumberSystems=""")
    ft=['"%s":{"name":"%s","url":"%s"}'%(type,desc['name'],desc['url']) for (type,desc) in reportNumberSystems.items()]
    fh.write("{%s}"%",\n".join(ft))
    #filetypes
    fh.write("""\n\nFileTypes=""")
    ft=['"%s":["%s","%s","%s"]'%(type,desc['name'],desc['loc'],desc['img']) for (type,desc) in types.items()]
    fh.write("{%s}"%",\n".join(ft))
    #OAI, smtp server
    fh.write("""\n\n#OAI Parameters\nOAILogFile=\t\t"%s" """%oaiLog)
    fh.write("""\nnb_records_in_resume=\t%s"""%nb_recs)
    fh.write("""\nnb_identifiers_in_resume=%s"""%nb_id)
    fh.write("""\noai_rt_expire=\t\t%s\nnamespace=\t\t"%s" """%(oai_exp,oains))
    fh.write("""\niconfNamespace=\t\t%s\niconfXSD=\t\t%s"""%(iconfNs,iconfXSD))
    fh.write("""\nrepositoryName=\t\t"%s"\nrepositoryIdentifier=\t"%s" """%(reposName, reposId))
    fh.write("""\nSMTPServer=\t\t"%s" """%smtpServer)
    fh.write("""\nSMTPLogin=\t\t"%s" """%smtpLogin)
    fh.write("""\nSMTPPassword=\t\t"%s" """%smtpPassword)
    fh.write("""\nSMTPUseTLS=\t\t"%s" """%smtpUseTLS)
    # Search
    fh.write("""\n\n#Indico search URL""")
    fh.write("""\nindicoSearchServer=\t\t"%s" """%isearchServer)
    fh.write("""\nindicoSearchClass=\t\t"%s" """%isearchClass)
    # Template set
    fh.write("""\n\n#Template Set""")
    # Footer
    fh.write("""\n\n#Indico footer""")
    fh.write("""\nindicoFooter=\t\t"%s" """%footerText)
    fh.write("""\n\n#Version\n""")
    fh.write("""\nversion = "%s"\n\n"""%x.versionVal)    
     

#Command used to run reconfigure script
if len(sys.argv)>1 and sys.argv[1] =='run':
    makeConf(reconfiguring=True)



"^^&"
#reconfigure tag, Everything other than the vars class, reconfigure command and the makeConf function goes under this tag,



#Used for sdist and install ********************************************************

#Puts the files in correct directories
def TPLFileList():
    tplFiles=[]
    for file in os.listdir('indico/MaKaC/webinterface/tpls'):
        if os.path.isfile("indico/MaKaC/webinterface/tpls/%s"%file):
            tplFiles.append("indico/MaKaC/webinterface/tpls/%s"%file)
    return tplFiles

def TPLCHelpFileList():
    tplFiles=[]
    for file in os.listdir('indico/MaKaC/webinterface/tpls/chelp'):
        if os.path.isfile("indico/MaKaC/webinterface/tpls/chelp/%s"%file):
            tplFiles.append("indico/MaKaC/webinterface/tpls/chelp/%s"%file)
    return tplFiles


def TPLJSFileList():
    tplFiles=[]
    for file in os.listdir('indico/MaKaC/webinterface/tpls/js'):
        if os.path.isfile("indico/MaKaC/webinterface/tpls/js/%s"%file):
            tplFiles.append("indico/MaKaC/webinterface/tpls/js/%s"%file)
    return tplFiles

def HTDOCFileList():
    htdocFiles=[]
    for file in os.listdir('indico/htdocs'):
        if os.path.isfile("indico/htdocs/%s"%file):
            htdocFiles.append("indico/htdocs/%s"%file)
    return htdocFiles

def addFileFromPath(path, recursive=False):
    files=[]
    for file in os.listdir(path):
        if os.path.isfile("%s/%s" % (path,file)):
            files.append("%s/%s" % (path,file))
        elif recursive:
            files.extend(addFileFromPath(os.path.join(path,file), recursive=True))
    return files

def addDataFilesFromPath(list, destPkg, origDir, recursive=True):
    tmpList = []
    for file in os.listdir(origDir):
        if os.path.isfile("%s/%s" % (origDir,file)):
            tmpList.append("%s/%s" % (origDir,file))
        elif recursive:
            addDataFilesFromPath(list, os.path.join(destPkg,file), os.path.join(origDir,file), recursive=True)
    list.append((destPkg, tmpList))

def HelpFileList():
    helpFiles=[]
    for file in os.listdir('indico/htdocs/help/docs'):
        if os.path.isfile("indico/htdocs/help/docs/%s"%file):
            helpFiles.append("indico/htdocs/help/docs/%s"%file)
    return helpFiles

def QspicsList():
    QspicsFiles=[]
    for file in os.listdir('indico/htdocs/help/docs/QSPics'):
        if os.path.isfile("indico/htdocs/help/docs/QSPics/%s"%file):
            QspicsFiles.append("indico/htdocs/help/docs/QSPics/%s"%file)
    return QspicsFiles

def AdminGList():
    AdminGFiles=[]
    for file in os.listdir('indico/htdocs/help/docs/AdminUserGuide'):
        if os.path.isfile("indico/htdocs/help/docs/AdminUserGuide/%s"%file):
            AdminGFiles.append("indico/htdocs/help/docs/AdminUserGuide/%s"%file)
    return AdminGFiles

def AdminpicsList():
    AdminpicsFiles=[]
    for file in os.listdir('indico/htdocs/help/docs/AdminUserGuide/AdminUserGuidePics'):
        if os.path.isfile("indico/htdocs/help/docs/AdminUserGuide/AdminUserGuidePics/%s"%file):
            AdminpicsFiles.append("indico/htdocs/help/docs/AdminUserGuide/AdminUserGuidePics/%s"%file)
    return AdminpicsFiles

def MainGList():
    MainGFiles=[]
    for file in os.listdir('indico/htdocs/help/docs/MainUserGuide'):
        if os.path.isfile("indico/htdocs/help/docs/MainUserGuide/%s"%file):
            MainGFiles.append("indico/htdocs/help/docs/MainUserGuide/%s"%file)
    return MainGFiles

def UgpicsList():
    UgpicsFiles=[]
    for file in os.listdir('indico/htdocs/help/docs/MainUserGuide/UserGuidePics'):
        if os.path.isfile("indico/htdocs/help/docs/MainUserGuide/UserGuidePics/%s"%file):
            UgpicsFiles.append("indico/htdocs/help/docs/MainUserGuide/UserGuidePics/%s"%file)
    return UgpicsFiles

def IMGFileList():
    imgFiles=[]
    for file in os.listdir('indico/htdocs/images'):
        if os.path.isfile("indico/htdocs/images/%s"%file):
            imgFiles.append("indico/htdocs/images/%s"%file)
    return imgFiles

## CERN Specific

def LargeRoomsIMGFileList():
    files=[]
    rootDir = 'indico/htdocs/images/rooms/large_photos'
    for file in os.listdir(rootDir):
        if os.path.isfile(os.path.join(rootDir, file)):
            files.append(os.path.join(rootDir, file))
    return files

def SmallRoomsIMGFileList():
    files=[]
    rootDir = 'indico/htdocs/images/rooms/small_photos'
    for file in os.listdir(rootDir):
        if os.path.isfile(os.path.join(rootDir, file)):
            files.append(os.path.join(rootDir, file))
    return files

def FoundationSyncList():
    files=[]
    rootDir = 'indico/MaKaC/common/FoundationSync'
    for file in os.listdir(rootDir):
        if os.path.isfile(os.path.join(rootDir, file)):
            files.append(os.path.join(rootDir, file))
    return files

def CERNYellowPayList():
    files=[]
    rootDir = os.path.join(x.cernDistDir, 'plugins/epayment/CERNYellowPay')
    for file in os.listdir(rootDir):
        if os.path.isfile(os.path.join(rootDir, file)):
            files.append(os.path.join(rootDir, file))
    return files

####

def SSFileList():
    ssFiles=[]
    for file in os.listdir('indico/MaKaC/webinterface/stylesheets'):
        if os.path.isfile("indico/MaKaC/webinterface/stylesheets/%s"%file):
            ssFiles.append("indico/MaKaC/webinterface/stylesheets/%s"%file)
    return ssFiles

def SSIncFileList():
    ssincFiles=[]
    for file in os.listdir('indico/MaKaC/webinterface/stylesheets/include'):
        if os.path.isfile("indico/MaKaC/webinterface/stylesheets/include/%s"%file):
            ssincFiles.append("indico/MaKaC/webinterface/stylesheets/include/%s"%file)
    return ssincFiles

def ToolsList():
    tplFiles=[]
    for file in os.listdir('scripts'):
        if os.path.isfile("scripts/%s"%file):
            tplFiles.append("scripts/%s"%file)
    return tplFiles

def HtdocsToolsList():
    tl=[]
    for file in os.listdir('indico/htdocs/tools'):
        if os.path.isfile("indico/htdocs/tools/%s"%file):
            tl.append("indico/htdocs/tools/%s"%file)
    return tl


def HtdocsJavascriptsCalendarList():
    js=[]
    for file in os.listdir('indico/htdocs/js/calendar'):
        if os.path.isfile("indico/htdocs/js/calendar/%s"%file):
            js.append("indico/htdocs/js/calendar/%s"%file)
    return js

def HtdocsJavascriptsLightboxList():
    js=[]
    for file in os.listdir('indico/htdocs/js/lightbox'):
        if os.path.isfile("indico/htdocs/js/lightbox/%s"%file):
            js.append("indico/htdocs/js/lightbox/%s"%file)
    return js

def HtdocsJavascriptsPrototypeList():
    js=[]
    for file in os.listdir('indico/htdocs/js/prototype'):
        if os.path.isfile("indico/htdocs/js/prototype/%s"%file):
            js.append("indico/htdocs/js/prototype/%s"%file)
    return js

def HtdocsJavascriptsScriptaculousList():
    js=[]
    for file in os.listdir('indico/htdocs/js/scriptaculous'):
        if os.path.isfile("indico/htdocs/js/scriptaculous/%s"%file):
            js.append("indico/htdocs/js/scriptaculous/%s"%file)
    return js

def HtdocsJavascriptsTooltipList():
    js=[]
    for file in os.listdir('indico/htdocs/js/tooltip'):
        if os.path.isfile("indico/htdocs/js/tooltip/%s"%file):
            js.append("indico/htdocs/js/tooltip/%s"%file)
    return js

def RecoveryToolsList():
    tplFiles=[]
    for file in os.listdir('scripts/recovery'):
        if os.path.isfile("scripts/recovery/%s"%file):
            tplFiles.append("scripts/recovery/%s"%file)
    return tplFiles

def IndexesToolsList():
    tplFiles=[]
    for file in os.listdir('scripts/indexes'):
        if os.path.isfile("scripts/indexes/%s"%file):
            tplFiles.append("scripts/indexes/%s"%file)
    return tplFiles

def TTFontsList():
    ttfFiles=[]
    for file in os.listdir('indico/MaKaC/PDFinterface/ttfonts'):
        if os.path.isfile("indico/MaKaC/PDFinterface/ttfonts/%s"%file):
            ttfFiles.append("indico/MaKaC/PDFinterface/ttfonts/%s"%file)
    return ttfFiles

#Generates the reconfiguration script
def reconf():
    file=open('setup.py').read()
    found = string.find(file,"\"^^&")
    file=open('setup.py','r')
    confpart=file.read(found)
    open('reconfigure.py','w').write(confpart)
    file.close()
    #fh = open('reconfigure.py','r').readlines()
    #fh[0]="""import confmerge \n"""
    #open('reconfigure.py','w').writelines(fh)
  
#Checks if the distrubition will be for CERN or not
def checkDistType():
    try:
        cmd=sys.argv.index("--cern-package")
        x.cernDistDir = sys.argv[cmd+1]
        f = open('.cerndist', 'w')
        f.close()
    except ValueError:
        pass
    while True:
        try:
            idx=sys.argv.index("--cern-package")
        except ValueError:
             break
        del sys.argv[idx+1]
        del sys.argv[idx]

def checkDistTypeForInstall():
    if os.path.isfile('.cerndist'):
        x.cernDistDir = True

#Accepts the version number as a command option if not supplied asks user
def versionVal():
    try:
        cmd=sys.argv.index("--version")
        x.versionVal = sys.argv[cmd+1]
    except ValueError:
        pass
    while True:
        try:
            idx=sys.argv.index("--version")
        except ValueError:
             break
        del sys.argv[idx+1]
        del sys.argv[idx]
    
  
#Puts the version number in the __init__ file inside code directory
def versioninit():
    if x.versionVal == None or x.versionVal == '0' :
        x.versionVal = raw_input('\nNo version given please enter version number\n')
    else:
        fh = open('indico/MaKaC/__init__.py','r').readlines()
        i=0
        while i<len(fh):
            line=fh[i]
            if line.strip().startswith("__version__"):
                del fh[i]
            else:
                i+=1
        fh.append("""__version__="%s" """%x.versionVal)
        open('indico/MaKaC/__init__.py','w').writelines(fh)

#Gets the version number from the __init__ file inside code directory
def getVersioninit():
    fh = open('indico/MaKaC/__init__.py','r').readlines()
    for line in fh:
        if line.strip().startswith("__version__"):
            line=line.strip()
            if line.find("=")!=-1:
                x.versionVal=line[line.find("=")+2:-1]
                break

#Obtains the current settings for an upgrade

def upgmsgok():
    print '\nPlease open the config.xml file to check parameters are correct\n\
To continue - type \'setup.py install\'\n\n\
If not correct\nplease edit the config.xml in a text editor,\n\
save and close the file and continue with \'setup.py install\'\n'
def upgmsgcst():
     print '\nNo current configurations can be found, please check the path\nname is correct and that \
you have a version already installed\n'
def upgmsgbad():
     print '\nNo current configurations can be found in the default directory,\nplease check that \
you have a version already installed\n'


def upgrade():
        cusdef=raw_input("\nPlease enter the package directory of the makac installation\n\
or type 'default' if you ran a default installation originally\n\n")
        currentFile = os.path.join('etc', 'config.xml')
        if cusdef == 'default':
            siteDir=get_python_lib()
            defltconfxml= os.path.join(siteDir,'MaKaC','common','config.xml')
            if os.path.isfile(defltconfxml) is True:
                confmerge.MergeFiles(defltconfxml,currentFile,currentFile)
                upgmsgok()
            else:
                upgmsgbad()
        else:
            customconfxml=os.path.join(cusdef,'MaKaC','common','config.xml')
            if os.path.isfile(customconfxml) is True:
                confmerge.MergeFiles(customconfxml,currentFile,currentFile)
                upgmsgok()
            else:
                upgmsgcst()

def copyconffiles():
    confdir = os.path.join('etc','config.xml')
    distConf = confmerge.ConfigFile(confdir)
    distConf.getXmlFile()
    distConf.generateXml('config.xml')

def copyCERNSpecificFiles():

    if not os.path.isdir('indico/htdocs/images/rooms'):
        os.mkdir('indico/htdocs/images/rooms/')

    shutil.copytree(os.path.join(x.cernDistDir, 'images/rooms/large_photos'),
                'indico/htdocs/images/rooms/large_photos')
    shutil.copytree(os.path.join(x.cernDistDir, 'images/rooms/small_photos'),
                'indico/htdocs/images/rooms/small_photos')
    shutil.copytree(os.path.join(x.cernDistDir, 'scripts/FoundationSync'),
                'indico/MaKaC/common/FoundationSync')
    shutil.copytree(os.path.join(x.cernDistDir, 'plugins/epayment/CERNYellowPay'),
                'indico/MaKaC/plugins/EPayment/CERNYellowPay')

def removeCERNSpecificFiles():
    shutil.rmtree('indico/htdocs/images/rooms', True)
    shutil.rmtree('indico/MaKaC/common/FoundationSync', True)
    shutil.rmtree('indico/MaKaC/plugins/EPayment/CERNYellowPay', True)

def compileAllLanguages():
    # Compile all .po files to .mo files
    pwd = os.getcwd()
    os.chdir('./indico/MaKaC/po')
    os.system('%s compile-all-lang.py --quiet' % sys.executable)
    os.chdir(pwd)

def clean():
    varstmp=os.path.join(x.tmpDir, "vars.js.tpl.tmp")
    if os.path.exists(varstmp):
        os.remove(varstmp)

def pkgdirfile():
    fh = open('setup.cfg','w')
    fh.write("""[install]\ninstall-purelib=%s"""%x.packageDir)
    fh.close()
    
def convertdoc():
    commands.getoutput('docbook2html --nochunks doc/docbook_src/INSTALL.xml > INSTALL.html')
    commands.getoutput('docbook2pdf doc/docbook_src/INSTALL.xml')
    commands.getoutput('w3m INSTALL.html > INSTALL')
    commands.getoutput('rm INSTALL.html')

def createFolders():
    resultspath = os.path.join(x.htdocsDir , "results")
    if os.path.exists(resultspath) is False:
            os.makedirs(resultspath)
    toolspath = os.path.join(x.htdocsDir , "tools")
    if os.path.exists(toolspath) is False:
            os.makedirs(toolspath)
    if sys.platform == "linux2":
        if x.accessuser =="None" and x.accessgroup=="None":
            x.accessuser = raw_input("\nTo allow the correct access for the Public Folder:\n\nYou need to:\n\nEnter the name of the user:\n\n")
            x.accessgroup = raw_input("\n\nEnter the group name:\n\n")
        string = "chown "+x.accessuser+":"+x.accessgroup+" "+resultspath 
        commands.getoutput(string)
        
    x.helpDir  = os.path.join(x.htdocsDir , "ihelp")
    if os.path.exists(x.helpDir) is False:
            os.makedirs(x.helpDir)

    qspics = os.path.join(x.helpDir , "QSPics")
    if os.path.exists(qspics) is False:
            os.makedirs(qspics)

    adming = os.path.join(x.helpDir , "AdminUserGuide")
    if os.path.exists(adming) is False:
            os.makedirs(adming)

    admingpics = os.path.join(x.helpDir , "AdminUserGuide","AdminUserGuidePics")
    if os.path.exists(admingpics) is False:
            os.makedirs(admingpics)

    ug = os.path.join(x.helpDir , "MainUserGuide")
    if os.path.exists(ug) is False:
            os.makedirs(ug)

    ugpics = os.path.join(x.helpDir , "MainUserGuide","UserGuidePics")
    if os.path.exists(ugpics) is False:
            os.makedirs(ugpics)

#Determines which functions to call dependant on command
if len(sys.argv)>1 and sys.argv[1] =='develop':
    x.develop = 0
    compileAllLanguages()
    makeConf()
    sys.exit()   
  
if len(sys.argv)>1 and sys.argv[1] =='install':
    getVersioninit()
    compileAllLanguages()
    checkDistTypeForInstall()
    makeConf()
    clean()
    pkgdirfile()
    reconf()
    shutil.copyfile("MaKaCConfig.py", "indico/MaKaC/common/MaKaCConfig.py")
    createFolders()
    
if len(sys.argv)>1 and sys.argv[1] =='upgrade':
    compileAllLanguages()
    upgrade()
    sys.exit()

if len(sys.argv)>1 and sys.argv[1] =='sdist':
    removeCERNSpecificFiles()
    checkDistType()
    if x.cernDistDir:
        copyCERNSpecificFiles()
    versionVal()
    versioninit()
    convertdoc()
    copyconffiles()
    
    
# Packaging all the files together to build the package when sdist is run
from distutils.core import setup
#get all directory in the plugins
pwd = os.getcwd()
os.chdir("./indico")

p = [] #package dir
d = [] #datadir

#old plugin stuff
#for root, dir, files in os.walk("MaKaC/plugins"):
#    if not root[-3:] == "CVS":
#        if root[-4:] == "tpls":
#            f = []
#            for fi in files:
#                f.append(os.path.join("code", root, fi))
#            d.append((os.path.join(x.packageDir, root), f))
#        else:
#            p.append(root)
 
#new plugin stuff           
for root, dir, files in os.walk("MaKaC/plugins"):
    if not root[-3:] == ".git":
        p.append(root)
    f = []
    for fi in files:
        if fi.endswith('.tpl') or fi.endswith('.wohl') or fi.endswith('.css') or fi.endswith('.js') or fi.endswith('.xsl'):
            f.append(os.path.join("indico", root, fi))
    if f:
        d.append((os.path.join(x.packageDir, root), f))

os.chdir(pwd)


packages=['MaKaC',
          'MaKaC.authentication',
          'MaKaC.common',
          'MaKaC.export',
          'MaKaC.webinterface',
          'MaKaC.webinterface.pages',
          'MaKaC.webinterface.rh',       
          'MaKaC.webinterface.session',
          'MaKaC.webinterface.common',
          'MaKaC.PDFinterface',
          'MaKaC.search',
          'MaKaC.ICALinterface',
          'MaKaC.RSSinterface',
          'MaKaC.services',
          'MaKaC.services.implementation',
          'MaKaC.services.interface',
          'MaKaC.services.interface.rpc',
          'MaKaC.po',
          'MaKaC.modules']

#transform dir path to module path and add to packages
for path in p:
    packages.append(path.replace("/",".").replace("\\", ".")) 

if x.cernDistDir:
    packages.append('MaKaC.common.FoundationSync')

dataFiles=[(x.tplDir, TPLFileList()),\
                  (x.tplJSDir, TPLJSFileList()),\
                  (x.tplCHelpDir, TPLCHelpFileList()),\
                  (x.htdocsDir, HTDOCFileList()),\
                  (x.ssDir, SSFileList()),\
                  (os.path.join(x.ssDir,"include"), SSIncFileList()),\
                  (x.imageDir, IMGFileList()),\
                  (x.docDir,['doc/UserGuide.pdf','doc/AdminUserGuide.pdf']),\
                  (x.toolsDir,ToolsList()),\
                  (os.path.join(x.toolsDir,"recovery"),RecoveryToolsList()),\
                  (os.path.join(x.toolsDir,"indexes"),IndexesToolsList()),\
                  (os.path.join(x.packageDir,"MaKaC/PDFinterface/ttfonts"),TTFontsList()),\
                  (x.confdef,['etc/config.xml','etc/config.xsd','reconfigure.py', 'etc/confmerge.py']),\
                  (os.path.join(x.htdocsDir, "scripts"),HtdocsToolsList()),\
                  (os.path.join(x.htdocsDir, "services"),[]),\
                  (os.path.join(x.htdocsDir, "modules"),[]),\
                  (os.path.join(x.htdocsDir, "js"),addFileFromPath('indico/htdocs/js')),\
                  (os.path.join(x.htdocsDir, "js/calendar"),HtdocsJavascriptsCalendarList()),\
                  (os.path.join(x.htdocsDir, "js/indico"),addFileFromPath('indico/htdocs/js/indico')),\
                  (os.path.join(x.htdocsDir, "js/indico/pack"),addFileFromPath('indico/htdocs/js/indico/pack')),\
                  (os.path.join(x.htdocsDir, "js/indico/Core"),addFileFromPath('indico/htdocs/js/indico/Core')),\
                  (os.path.join(x.htdocsDir, "js/indico/Management"),addFileFromPath('indico/htdocs/js/indico/Management')),\
                  (os.path.join(x.htdocsDir, "js/indico/Common"),addFileFromPath('indico/htdocs/js/indico/Common')),\
                  (os.path.join(x.htdocsDir, "js/indico/Admin"),addFileFromPath('indico/htdocs/js/indico/Admin')),\
                  (os.path.join(x.htdocsDir, "js/indico/Collaboration"),addFileFromPath('indico/htdocs/js/indico/Collaboration')),\
                  (os.path.join(x.htdocsDir, "js/indico/i18n"),addFileFromPath('indico/htdocs/js/indico/i18n')),\
                  (os.path.join(x.htdocsDir, "js/indico/MaterialEditor"),addFileFromPath('indico/htdocs/js/indico/MaterialEditor')),\
                  (os.path.join(x.htdocsDir, "js/indico/Display"),addFileFromPath('indico/htdocs/js/indico/Display')),\
                  (os.path.join(x.htdocsDir, "js/indico/Legacy"),addFileFromPath('indico/htdocs/js/indico/Legacy')),\
                  (os.path.join(x.htdocsDir, "js/indico/Core/Dialogs"),addFileFromPath('indico/htdocs/js/indico/Core/Dialogs')),\
                  (os.path.join(x.htdocsDir, "js/indico/Core/Widgets"),addFileFromPath('indico/htdocs/js/indico/Core/Widgets')),\
                  (os.path.join(x.htdocsDir, "js/indico/Timetable"),addFileFromPath('indico/htdocs/js/indico/Timetable')),\
                  (os.path.join(x.htdocsDir, "js/indico/Core/Interaction"),addFileFromPath('indico/htdocs/js/indico/Core/Interaction')),\
                  (os.path.join(x.htdocsDir, "js/lightbox"),HtdocsJavascriptsLightboxList()),\
                  (os.path.join(x.htdocsDir, "js/prototype"),HtdocsJavascriptsPrototypeList()),\
                  (os.path.join(x.htdocsDir, "js/scriptaculous"),HtdocsJavascriptsScriptaculousList()),\
                  (os.path.join(x.htdocsDir, "js/tooltip"),HtdocsJavascriptsTooltipList()),\
                  (os.path.join(x.htdocsDir, "js/presentation"),addFileFromPath('indico/htdocs/js/presentation')),\
                  (os.path.join(x.htdocsDir, "js/presentation/pack"),addFileFromPath('indico/htdocs/js/presentation/pack')),\
                  (os.path.join(x.htdocsDir, "js/presentation/Core"),addFileFromPath('indico/htdocs/js/presentation/Core')),\
                  (os.path.join(x.htdocsDir, "js/presentation/Data"),addFileFromPath('indico/htdocs/js/presentation/Data')),\
                  (os.path.join(x.htdocsDir, "js/presentation/Ui"),addFileFromPath('indico/htdocs/js/presentation/Ui')),\
                  (os.path.join(x.htdocsDir, "js/presentation/Ui/Styles"),addFileFromPath('indico/htdocs/js/presentation/Ui/Styles')),\
                  (os.path.join(x.htdocsDir, "js/presentation/Ui/Widgets"),addFileFromPath('indico/htdocs/js/presentation/Ui/Widgets')),\
                  (os.path.join(x.htdocsDir, "js/presentation/Ui/Extensions"),addFileFromPath('indico/htdocs/js/presentation/Ui/Extensions')),\
                  (x.helpDir,HelpFileList()), \
                  (os.path.join(x.helpDir , "QSPics"),QspicsList()),\
                  (os.path.join(x.helpDir,"AdminUserGuide"),AdminGList()),\
                  (os.path.join(x.helpDir,"MainUserGuide"),MainGList()),\
                  (os.path.join(x.helpDir,"AdminUserGuide","AdminUserGuidePics"),AdminpicsList()),\
                  (os.path.join(x.helpDir,"MainUserGuide","UserGuidePics"),UgpicsList())\
                  ]

addDataFilesFromPath(dataFiles, os.path.join(x.htdocsDir, "css"), 'indico/htdocs/css', recursive=True)
addDataFilesFromPath(dataFiles, os.path.join(x.htdocsDir, "js/fckeditor"), 'indico/htdocs/js/fckeditor', recursive=True)
addDataFilesFromPath(dataFiles, os.path.join(x.imageDir, "conf"), 'indico/htdocs/images/conf', recursive=True)


if x.cernDistDir:
    try:
        dataFiles.append((os.path.join(x.imageDir,"rooms/large_photos"), LargeRoomsIMGFileList()))
        dataFiles.append((os.path.join(x.imageDir,"rooms/small_photos"), SmallRoomsIMGFileList()))
        dataFiles.append((os.path.join(x.packageDir,"MaKaC/common/FoundationSync"), FoundationSyncList()))
        dataFiles.append((os.path.join(x.packageDir,"MaKaC/plugins/EPayment/CERNYellowPay"), CERNYellowPayList()))

    except Exception, e:
        print "CERN Resources were not found: %s" % e

###############add plugins data files###########################
for df in d:
    dataFiles.append(df)
################################################################

############add po locale files#################################
pwd = os.getcwd()
os.chdir("./indico")

p = [] #package dir
d = [] #datadir
for root, dir, files in os.walk("MaKaC/po"):
    if not root.endswith(".git"):
        if root.endswith("LC_MESSAGES"):
            f = []
            for fi in files:
                f.append(os.path.join("indico", root, fi))
            dataFiles.append((os.path.join(x.packageDir, root), f))
   
os.chdir(pwd)
#############################################################################


def jsCompress():
    jsbuildPath = os.path.join(sys.exec_prefix, 'bin', 'jsbuild')
    print "Compressing JavaScript... "
    os.chdir('./etc/js')
    os.system('%s -o ../../indico/htdocs/js/indico/pack -v indico.cfg' % jsbuildPath)
    os.system('%s -o ../../indico/htdocs/js/presentation/pack -v presentation.cfg' % jsbuildPath )
    os.chdir('../..')
    print "Done!"

class jsbuild(Command):
    description = "compresses javascript"
    user_options = []
    boolean_options = []
    
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass
    
    def run(self):
        jsCompress()

class sdist(_sdist):
    def run(self):
        jsCompress()
        _sdist.run(self)


class tests_indico(Command):
    description = "run the test suite"
    user_options = []
    boolean_options = []
        
    def initialize_options(self): pass

    def finalize_options(self): pass
    
    def run(self):
        p = Popen("python2.4 tests/__init__.py", shell=True, stdout=PIPE, stderr=PIPE)
        out = string.join(p.stdout.readlines() )
        outerr = string.join(p.stderr.readlines() )
        print out, outerr

        
setup(name = "cds-indico",
      cmdclass={'sdist': sdist,
                'jsbuild': jsbuild,
                'tests': tests_indico},
      version = "%s"%x.versionVal,
      description = "Integrated Digital Conferences",
      author = "AVC Section@CERN-IT",
      author_email= "indico-project@cern.ch",
      url = "http://cern.ch/indico",
      platforms = ["any"],
      long_description = "Integrated Digital Conferences",
      license = "http://www.gnu.org/licenses/gpl-2.0.txt",
      package_dir={ '':'indico' },
      packages = packages,
      data_files = dataFiles
      )
if len(sys.argv)>1 and sys.argv[1] =='install':
    print "\n\nPlease do not forget to start the 'taskDaemon' in order to use alarms, creation of off-line websites, reminders, etc. You can find it in './tools/taskDaemon.py'\n\n"
            














