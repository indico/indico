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

import tempfile, os, getopt, sys, base64, socket
import httplib, mimetypes, urlparse, simplejson
from MaKaC.common.Configuration import Config
from MaKaC import conference

#URL_RESPONSE = "http://pcdh20.cern.ch/indico/getConvertedFile.py"
#SERVER = 'http://pcdh20.cern.ch/getSegFile.py'#'http://pcuds01.cern.ch/getSegFile.py'

SEGMENT_SIZE = 500000
DEFAUTL_ENCODING = "utf-8"

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def writeLog(m):
    ERROR_LOG_FOLDER="c:/tmp"
    if os.path.isdir(ERROR_LOG_FOLDER):
        l=open(os.path.join(ERROR_LOG_FOLDER, "FILE-CONVERTER-ERROR.log"),"a")
        l.write("%s\n"%m)
        l.close()


class FileConverter:

    def convert(filepath, converter, uid):
        pass
    convert=staticmethod(convert)

    def storeConvertedFile(params):
        pass
    storeConvertedFile=staticmethod(storeConvertedFile)

    def hasAvailableConversionsFor(ext):
        pass    
    hasAvailableConversionsFor=staticmethod(hasAvailableConversionsFor)

class CDSConvFileConverter(FileConverter):

    _availableExt=[".ppt", ".doc", ".pptx", ".docx", ".odp", ".sxi" ]
    
    def convert(filepath, converter, material):
        # Material UID
        materialUID="%s"%material.getLocator()
        # Getting variables
        responseURL = Config.getInstance().getFileConverterResponseURL()
        serverURL = Config.getInstance().getFileConverterServerURL()
        up = urlparse.urlparse(serverURL)
        if up[0] == "":
            #writeLog("Wrong conversion server URL")
            return
        host = up[1]
        selector = up[2]        
        # Checking the file
        localFile = filepath.strip()
        localFile = localFile.replace("\\", "/")
        filename = localFile.split("/")[-1]
        if not os.access(localFile, os.F_OK):
            #writeLog("Local file to upload invalid")
            return False
        fic=open(localFile, "rb")
        segnum=0
        segsize = SEGMENT_SIZE
        filekey = 'segfile'
        i = 0
        
        try :
            h = httplib.HTTP(host)
        except Exception, e:
            #writeLog("Error : Can't connect to host:%s"%host)
            return False
            
        while 1:

            temp = fic.read(segsize)

            segnum = segnum + 1
            BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
            CRLF = '\r\n'
            L = []
                    
            if len(temp) < segsize:
                lastseg = 1
                
                L.append('--' + BOUNDARY)
                L.append('Content-Disposition: form-data; name="dirresponse"')
                L.append('')
                L.append(materialUID)

                L.append('--' + BOUNDARY)
                L.append('Content-Disposition: form-data; name="urlresponse"')
                L.append('')
                L.append(responseURL)

                L.append('--' + BOUNDARY)
                L.append('Content-Disposition: form-data; name="converter"')
                L.append('')
                L.append(converter)
            else:
                lastseg = 0
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="filename"')
            L.append('')
            L.append(filename)

            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="segnum"')
            L.append('')
            L.append('%i' % segnum)

            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="lastseg"')
            L.append('')
            L.append('%i' % lastseg)

            """
            add the segment
            """

            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (filekey, filename))
            L.append('Content-Type: %s' % get_content_type(filename))
            L.append('')
            L.append(temp)

            L.append('--' + BOUNDARY + '--')
            L.append('')
            body = CRLF.join(L)
            content_type = 'multipart/form-data; boundary=%s' % BOUNDARY

            try:
                h.putrequest('POST', selector)
                h.putheader('content-type', content_type)
                h.putheader('content-length', str(len(body)))
                h.endheaders()
                h.send(body)
            except:
                #writeLog("Exception while sending file to the CDSconv server")
                pass
            try:
                errcode, errmsg, headers = h.getreply()
            except Exception, e:
                #writeLog(e)
                pass
            i = i + 1
            if lastseg == 1 :
                #print "\n%s\n"%(h.getfile().read())
                break
        fic.close()
        #writeLog("File uploaded")
    convert=staticmethod(convert)

    def _getMaterialObj(owner, id):
        if id=="video":
            return owner.getVideo()
        elif id=="paper":
            return owner.getPaper()
        elif id=="slides":
            return owner.getSlides()
        elif id=="poster":
            return owner.getPoster()
        elif id=="minutes":
            return owner.getMinutes()
        else:
            try:
                return owner.getMaterialById(id)
            except KeyError, e:
                pass
        return None
    _getMaterialObj=staticmethod(_getMaterialObj)

    def _getMaterial(locator):
        ch=conference.ConferenceHolder()
        if locator.has_key("confId") and locator.has_key("materialId"):
            c=ch.getById(locator["confId"])
            # ---------- Conference ----------
            if c is not None:
                # ---------- Session ----------
                if locator.has_key("sessionId"):
                    s=c.getSessionById(locator["sessionId"])
                    if s is not None:
                        # ---------- Contribution ----------
                        if locator.has_key("contribId"):
                            contrib=c.getContributionById(locator["contribId"])
                            if contrib is not None:
                                # ---------- Subcontribution ----------
                                if locator.has_key("subContId"):
                                    subContrib=contrib.getSubContributionById(locator["subContId"])
                                    if subContrib is not None:
                                        return CDSConvFileConverter._getMaterialObj(subContrib, locator["materialId"])
                                else:
                                    return CDSConvFileConverter._getMaterialObj(contrib, locator["materialId"])
                        else:
                            return CDSConvFileConverter._getMaterialObj(s, locator["materialId"])
                # ---------- Contribution ----------
                elif locator.has_key("contribId"):
                    contrib=c.getContributionById(locator["contribId"])
                    if contrib is not None:
                        # ---------- Subcontribution ----------
                        if locator.has_key("subContId"):
                            subContrib=contrib.getSubContributionById(locator["subContId"])
                            if subContrib is not None:
                                return CDSConvFileConverter._getMaterialObj(subContrib, locator["materialId"])
                        else:
                            return CDSConvFileConverter._getMaterialObj(contrib, locator["materialId"])
                else:
                    return CDSConvFileConverter._getMaterialObj(c, locator["materialId"])
                
        return None
    _getMaterial=staticmethod(_getMaterial)

    def _getNewTempFile():
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="Indico.tmp", dir = tempPath )[1]
        return tempFileName
    _getNewTempFile=staticmethod(_getNewTempFile)

    def _saveFileToTemp( params ):
        fileName = CDSConvFileConverter._getNewTempFile()
        f = open( fileName, "wb" )
        f.write( base64.decodestring(params["content"]) )
        f.close()
        return fileName
    _saveFileToTemp=staticmethod(_saveFileToTemp)

    def storeConvertedFile(requestIP, params):

        """ returns the path to the temp file used in the process
        so that it can be deleted at a later stage """

        # extract the server name from the url
        serverURL = Config.getInstance().getFileConverterServerURL()
        up = urlparse.urlparse(serverURL)

        # check that the request comes from the conversion server
        if socket.gethostbyname(up[1]) != requestIP:
            return

        if params["status"] == '1':
            locator={}
            # python dicts come with ' instead of " by default
            # using a json encoder on the server side would help...
            locator = simplejson.loads(params["directory"].replace('\'','"'))

            mat=CDSConvFileConverter._getMaterial(locator)
            if mat is not None:
                filePath = CDSConvFileConverter._saveFileToTemp( params )
                fileName = params["filename"]
                if not mat.hasFile(fileName):
                    f = conference.LocalFile()
                    f.setName(fileName)
                    f.setFileName( fileName )
                    f.setFilePath( filePath )
                    mat.addResource( f )
                return filePath
            else:
                #writeLog("Locator does not exist for file \"%s\": \n-locator:%s\nmessage:%s"%(params["filename"], params["directory"], params["error_message"]))
                pass
        else:
            #Here it should be processed the received error from the conversion server.
            #writeLog("Error converting file \"%s\": \n-locator:%s\nmessage:%s"%(params["filename"], params["directory"], params["error_message"])) 
            pass
    storeConvertedFile=staticmethod(storeConvertedFile)

    def hasAvailableConversionsFor(ext):
        if ext in CDSConvFileConverter._availableExt:
            return True
        return False
    hasAvailableConversionsFor=staticmethod(hasAvailableConversionsFor)
