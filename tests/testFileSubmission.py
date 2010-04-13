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

"""Contains tests regarding some scenarios related to submission and archiving
of files.
"""

import unittest
import os


class TestMaterialRepository(unittest.TestCase):
    """Tests the basic functionalities of the MaterialLocalRepository file 
        repository.
    """

    def setUp( self ):
        self._archivePath = os.path.join( os.getcwd(), "tmpArchive" )
        #create a directory where the archive will be set up
        try:
            os.mkdir( self._archivePath )
        except OSError, e:
            #print e
            pass
        #the MaterialLocalRepository takes the repository base path from
        #   the system configuration so we have to set it up to the new dir
        from MaKaC.common import Config
        cfg = Config.getInstance()
        #we overrride the system repository path with the temp one
        cfg._archivePath = self._archivePath

    def tearDown( self ):
        #delete the temporary archive space and all the files below
        #os.removedirs( self._archivePath )
        for root, dirs, files in os.walk(self._archivePath, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        

    def testRepositoryPath( self ):
        """Makes sure it is taking the path from the system configuration
        """
        from MaKaC.fileRepository import MaterialLocalRepository
        fr = MaterialLocalRepository()
        self.assertEqual( fr.getRepositoryPath(), self._archivePath )

    def testArchiveConferenceFile( self ):
        """Makes sure a file wich is attached to a conference gets stored in 
            the right path: basePath/year/C0/0/test.txt
        """
        #first we create a dummy user which will be the conf creator
        from MaKaC.user import Avatar
        av = Avatar()
        #Now we create a dummy conference and set its id to 0
        from MaKaC.conference import Conference
        c = Conference( av )
        c.setId( "0" )
        #Now we create the material (id=0) and attach it to the conference
        from MaKaC.conference import Material
        m = Material()
        c.addMaterial( m )
        #Now we create a dummy file and attach it to the material
        filePath = os.path.join( os.getcwd(), "test.txt" )
        fh = open(filePath, "w")
        fh.write("hola")
        fh.close()
        from MaKaC.conference import LocalFile
        f = LocalFile()
        f.setFilePath( filePath )
        f.setFileName( "test.txt" )
        m.addResource( f )


def testsuite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite(TestMaterialRepository) )
    return suite
