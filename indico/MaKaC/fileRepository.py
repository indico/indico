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

"""
"""
import shutil
import os
import stat
import datetime
import random
import sys
from MaKaC.i18n import _

import ZODB
from persistent import Persistent

from BTrees import OOBTree
from MaKaC.common.Counter import Counter

from MaKaC.common.logger import Logger

class Repository:
    """Generic class for file repositories. A file repository knows where to
        store files (binary, text, ...) and provides services for archiving
        (by uniquely identifyng them inside the repository) and accessing
        them.
       This is a base class that provides a common interface. Any implentation
        should inherit from this one.
    """
    def getInstance( cls ):
        return None
    getInstance = classmethod(getInstance)

    def storeFile( self, newFile ):
        raise Exception( _("not implemented for class %s")%self.__class__.__name__)

    def retireFile( self, file ):
        raise Exception( _("not implemented for class %s")%self.__class__.__name__)


class MaterialLocalRepository(Persistent):
    """File repository keeping the files under a certain path in the local 
        filesystem (machine where the system is installed).
    """
    def __init__(self):
        self.__files = OOBTree.OOBTree()
        #self.__idGen = Counter()

    def __getNewFileId( self ):
        while True:
            id=str(random.randint(0,sys.maxint))
            if not self.__files.has_key(id):
                return id
                
        #due to concurrency problems it will be mandatory to check that the 
        #   directory does not exist, otherwise we'll generate a new id till 
        #   it does not exist
        #concurrency problems could be avoided if we used the file system as 
        #   concurrency control system (creating a dir is an atomic operation)
        #   but this would imply searching for the last id which could be 
        #   very very low in case of having a big directory list
        #while 1:
        #    id = str(self.__idGen.newCount())
        #    destPath = os.path.join( self.__getRepositoryPath(), id )
        #    if not os.access( destPath, os.F_OK ):
        #        return id

    def __getRepositoryPath( self ):
        from MaKaC.common.Configuration import Config
        cfg = Config.getInstance()
        return cfg.getArchiveDir()
    
    def getRepositoryPath( self ):
        return self.__getRepositoryPath()
    
    def getFiles(self):
        return self.__files

    def __getFilePath( self, id ):
        # this os.path.split is to be removed, just to keep compatibility with
        #   old filerepository where the full path was stored
        file = self.__files[id]
        path = os.path.join( self.__getRepositoryPath(), file )
        if os.path.exists(path):
            return path
        #legacy
        elif os.path.exists(path.decode("utf-8",'strict').encode("iso-8859-1",'replace')):
            return path.decode("utf-8",'strict').encode("iso-8859-1",'replace')
        elif os.path.exists(path.decode("utf-8",'replace').encode(sys.getfilesystemencoding(),'replace')):
            return path.decode("utf-8",'replace').encode(sys.getfilesystemencoding(),'replace')
        else:
            return path
    
    def getFilePath( self, id ):
        return self.__getFilePath(id)

    def storeFile( self, newFile, forcedFileId=None ):
        #this id generation can cause concurrency problems as it is not writen
        #   till the transaction is comited which could make that if the copying
        #   of the file to the archive is long two or more clients have the
        #   same id. This will still cause concurrency errors as the two clients
        #   will have modify the counter so the DB will raise a read conflict
        #   for the one who commits later, but at least it will prevent from
        #   having 2 files with the same id

        if forcedFileId:
            id = forcedFileId
        else:
            id = self.__getNewFileId()

        cat = newFile.getCategory()
        #raise "%s"%cat
        if cat:
            interPath = os.path.join("categories", "%s"%cat.getId())
        else:
            
            conf = newFile.getConference()
            
            session = newFile.getSession()
            cont = newFile.getContribution()
            subcont = newFile.getSubContribution()
            try:        
                year = str(conf.getCreationDate().year)
            except:
                year= str(datetime.datetime.now().year)
            interPath = os.path.join(year, "C%s"%conf.getId())
            if cont:
                #the file is in a contribution, then create a directory for the contribution
              
                interPath = os.path.join( interPath, "c%s"%cont.getId())
                
                if subcont:
                    #the file is in a subcontribution, then create a directory for the subcontribution
                    interPath = os.path.join( interPath, "sc%s"%subcont.getId())
            elif session:
                #the file is attach to a session, but not to a contribution. Then create a directory for the session
                interPath = os.path.join( interPath, "s%s"%session.getId())
            else:
                #the file is attach directly to the conference, then don't add directory
                pass
        from MaKaC.common import info
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        volume = minfo.getArchivingVolume()
        destPath = os.path.join( self.__getRepositoryPath(), volume, interPath, id )

        if forcedFileId == None:
            os.makedirs( destPath )

        destPath = os.path.join( destPath, newFile.getFileName() )
        relativePath = os.path.join( volume, interPath, id, newFile.getFileName())

        if forcedFileId == None:
            try:
                shutil.copyfile( newFile.getFilePath(), destPath )
            except IOError, e:
                raise Exception( _("Couldn't archive file %s to %s")%( newFile.getFilePath(), destPath ) )

        self.__files[id] = relativePath
        newFile.setArchivedId( self, id )

        Logger.get('storage').info("stored resource %s (%s) at %s" % (id, newFile.getFileName(), os.path.join(volume, interPath)))

        return id

    def recoverFile(self, recFile):
        ##
        ## TODO: This is NOT working because of the volume (see storeFile)
        ##
        id = recFile.getRepositoryId()
        cat = recFile.getCategory()
        if cat:
            interPath = os.path.join("categories", "%s"%cat.getId())
        else:
            conf = recFile.getConference()
            session = recFile.getSession()
            cont = recFile.getContribution()
            subcont = recFile.getSubContribution()
            year = str(conf.getCreationDate().year)
            interPath = os.path.join(year, "C%s"%conf.getId())
            if cont:
                # The file is in a contribution, then create a directory for the contribution.
                interPath = os.path.join(interPath, "c%s"%cont.getId())
                if subcont:
                    #the file is in a subcontribution, then create a directory for the subcontribution
                    interPath = os.path.join( interPath, "sc%s"%subcont.getId())
            elif session:
                # The file is attached to a session, but not to a contribution. Then create a directory for the session.
                interPath = os.path.join(interPath, "s%s"%session.getId())
            else:
                # The file is attached directly to the conference, then don't add directory.
                pass
        relativePath = os.path.join(interPath, id, recFile.getFileName())
        if not self.__files.has_key(id):
            self.__files[id] = relativePath
        else:
            raise Exception("The id %s is already in use."%id)
        recFile.setArchivedId(self, id)
        return id

    def getFileSize( self, id ):
        filePath = self.__getFilePath( id )
        return int(os.stat(filePath)[stat.ST_SIZE])
        
    def getCreationDate( self, id):
        """
        This method returns the creation date of one file in the repository.
        The file is got with the "id" argument.
        """
        filePath = self.__getFilePath( id )
        return datetime.datetime.fromtimestamp(os.path.getctime(filePath))

    def readFile( self, id ):
        filePath = self.__getFilePath( id )
        f = open(filePath, "rb")
        data = f.read()
        f.close()
        return data

    def replaceContent( self, id, newContent ):
        filePath = self.__getFilePath( id )
        f = open(filePath, "w")
        f.write( newContent )
        f.close()

    def retireFile( self, file ):
        if not self.__files.has_key( file.getRepositoryId() ):
            return
        del self.__files[ file.getRepositoryId() ]


# The following class seems to be not used at all (26.02.2007)
class LocalRepository(Persistent):
    """File repositroy keeping the files under a certain path in the local 
        filesystem (machine where the system is installed).
    """
    def __init__(self):
        self.__files = OOBTree.OOBTree()
        self.__idGen = Counter()

    def __getNewFileId( self ):
        #due to concurrency problems it will be mandatory to check that the 
        #   directory does not exist, otherwise we'll generate a new id till 
        #   it does not exist
        #concurrency problems could be avoided if we used the file system as 
        #   concurrency control system (creating a dir is an atomic operation)
        #   but this would imply searching for the last id which could be 
        #   very very low in case of having a big directory list
        while 1:
            id = str(self.__idGen.newCount())
            destPath = os.path.join( self.__getRepositoryPath(), id )
            if not os.access( destPath, os.F_OK ):
                return id

    def __getRepositoryPath( self ):
        from MaKaC.common.Configuration import Config
        cfg = Config.getInstance()
        return cfg.getArchiveDir()

    def getFilePath( self, id ):
        # this os.path.split is to be removed, just to keep compatibility with
        #   old filerepository where the full path was stored
        return os.path.join( self.__getRepositoryPath(), id, os.path.split(self.__files[id])[1] )
    

    def storeFile( self, newFile, forcedFileId=None ):
        #this id generation can cause concurrency problems as it is not writen
        #   till the transaction is comited which could make that if the copying
        #   of the file to the archive is long two or more clients have the
        #   same id. This will still cause concurrency errors as the two clients
        #   will have modify the counter so the DB will raise a read conflict
        #   for the one who commits later, but at least it will prevent from
        #   having 2 files with the same id
        if forcedFileId:
            id = forcedFileId
        else:
            id = self.__getNewFileId()
        destPath = os.path.join( self.__getRepositoryPath(), id )
        #if not os.access( destPath, os.F_OK ):
        os.makedirs( destPath )
        destPath = os.path.join( destPath, newFile.getFileName() )
        relativePath = os.path.join( id, newFile.getFileName())
        try:
            shutil.copyfile( newFile.getFilePath(), destPath )
            self.__files[id] = relativePath
            newFile.setArchivedId( self, id )
        except IOError, e:
            raise Exception( _("Couldn't archive file %s to %s")%( newFile.getFilePath(), destPath ) )
        return id

    def getFileSize( self, id ):
        filePath = self.getFilePath( id )
        return int(os.stat( filePath )[stat.ST_SIZE])
        
    def getCreationDate( self, id):
        """
        This method returns the creation date of one file in the repository.
        The file is got with the "id" argument.
        """
        filePath = self.__getFilePath( id )
        return datetime.datetime.fromtimestamp(os.path.getctime(filePath))

    def readFile( self, id ):
        filePath = self.getFilePath( id )
        f = open(filePath, "rb")
        data = f.read()
        f.close()
        return data

    def replaceContent( self, id, newContent ):
        filePath = self.getFilePath( id )
        f = open(filePath, "w")
        f.write( newContent )
        f.close()

    def retireFile( self, file ):
        if not self.__files.has_key( file.getRepositoryId() ):
            return
        os.remove( self.__files[ file.getRepositoryId() ] )
        del self.__files[ file.getRepositoryId() ]



class SimpleRepository:
    """File repository keeping the files under a certain path in the local 
        filesystem (machine where the system is installed).
    """

    def getRepositoryPath( self ):
        from MaKaC.common.Configuration import Config
        cfg = Config.getInstance()
        return cfg.getArchiveDir()
        
    def getFullPath( self, relativePath ):
        return os.path.join( self.getRepositoryPath(), relativePath )

    def storeFile( self, relativePath, file ):
        fromPath = file.getFilePath()
        destPath = os.path.join( self.getRepositoryPath(), relativePath )
        #print "fromPath = " + fromPath
        #print "destPath = " + destPath
        os.makedirs( destPath )
        try:
            shutil.copyfile( fromPath, destPath )
        except IOError, e:
            raise Exception("Couldn't archive file %s to %s"%( fromPath, destPath ) )

    def readFile( self, relativePath ):
        fullPath = self.getFullPath( relativePath )
        f = open( fullPath, "rb" )
        data = f.read()
        f.close()
        return data

    def replaceContent( self, id, newContent ):
        pass

    def recoverFile(self, recFile):
        pass

if __name__ == "__main__":
    from MaKaC.common.db import DBMgr
    DBMgr.getInstance().startRequest()
    
    repository = SimpleRepository()
    f = open( r'E:\Indico\code\code\htdocs\abstractsManagment.py', 'r' )
    print repository.storeFile( 'small_rooms/abstractManagement.py', f )
    f.close()
    
    DBMgr.getInstance().endRequest()
