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

# For now, disable Pylint
# pylint: disable-all

"""
Contains tests regarding some scenarios related to submission and archiving
of files.
"""

import os
from indico.tests.env import *
from indico.tests.python.unit.util import IndicoTestCase, with_context


class TestMaterialRepository(IndicoTestCase):
    """
    Tests the basic functionalities of the MaterialLocalRepository file
    repository.
    """

    _requires = ["db.DummyUser"]

    def setUp( self ):
        super(TestMaterialRepository, self).setUp()
        self._archivePath = os.path.join( os.getcwd(), "tmpArchive" )
        #create a directory where the archive will be set up
        try:
            os.mkdir( self._archivePath )
        except OSError, e:
            #print e
            pass
        #the MaterialLocalRepository takes the repository base path from
        #   the system configuration so we have to set it up to the new dir
        from indico.core.config import Config
        cfg = Config.getInstance()
        #we overrride the system repository path with the temp one
        cfg._archivePath = self._archivePath

    def tearDown( self ):
        super(TestMaterialRepository, self).tearDown()
        #delete the temporary archive space and all the files below
        #os.removedirs( self._archivePath )
        for root, dirs, files in os.walk(self._archivePath, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        try:
            os.rmdir(os.path.join( os.getcwd(), "tmpArchive" ))
            os.remove(os.path.join( os.getcwd(), "test.txt" ))
        except:
            pass

#this test needs to be executed from root indico dir
#    def testRepositoryPath( self ):
#        """Makes sure it is taking the path from the system configuration
#        """
#        from MaKaC.fileRepository import MaterialLocalRepository
#        fr = MaterialLocalRepository()
#        self.assertEqual( fr.getRepositoryPath(), self._archivePath )

    @with_context('database')
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
