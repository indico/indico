# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import zipfile
import tempfile
import string
import os


from MaKaC.common.utils import utf8rep
from MaKaC.errors import MaKaCError
from MaKaC import conference
from indico.core.config import Config
from indico.util.i18n import _


class ZIPFileHandler:

    def __init__(self):
        (fh, name) = tempfile.mkstemp(prefix="Indico", dir=Config.getInstance().getTempDir())
        os.fdopen(fh).close()
        try:
            self._file = zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
        except:
            self._file = zipfile.ZipFile(name, "w", allowZip64=True)
        self._name = name

    def _normalisePath(self, path):
        forbiddenChars = string.maketrans(" :()*?<>|\"", "__________")
        path = path.translate(forbiddenChars)
        return path

    def add(self, name, path):
        name = utf8rep(name)
        self._file.write(str(path), self._normalisePath(name))

    def addNewFile(self, name, bytes):
        if not self.hasFile(name):
            name = utf8rep(name)
            self._file.writestr(name, bytes)

    def addDir(self, path):
        normalized_path = os.path.join(self._normalisePath(path), "indico_file.dat")
        if not self.hasFile(normalized_path):
            self.addNewFile(normalized_path, "# Indico File")

    def close(self):
        self._file.close()

    def getPath(self):
        return self._name

    def hasFile(self, fileName):
        for zfile in self._file.infolist():
            if zfile.filename == fileName:
                return True
        return False


class AbstractPacker:
    """
    """

    def __init__(self,conf):
        self._conf=conf

    def _normalisePathItem(self,name):
        return str(name).translate(string.maketrans("",""),"\\/")

    def pack(self,absList,fileHandler):
        if len(absList)<=0:
            raise MaKaCError( _("no abstract to pack"))
        for abstract in absList:
            abstractDirName="abstract-%04d"%(int(abstract.getId()))
            if abstract.getAttachments() is not None :
                for res in abstract.getAttachments().values():
                    fileHandler.add("%s/%s-%s"%(abstractDirName, res.getId(), res.getFileName()), res.getFilePath())
        fileHandler.close()
        return fileHandler.getPath()


class ReviewingPacker:

    """
        Package the reviewing materials for the accepted papers
    """

    def __init__(self, conf):
        self._conf = conf
        self._confDirName = "%s" % self._normalisePathItem(self._conf.getTitle().strip())
        self._items = 0

    def getItems(self):
        return self._items

    def _normalisePathItem(self, name):
        return str(name).translate(string.maketrans("",""),"\\/")

    def pack(self, fileHandler=None):
        for contribution in self._conf.getContributionList():
            reviewingStatus = contribution.getReviewManager().getLastReview().getRefereeJudgement().getJudgement()
            if reviewingStatus == "Accept":
                dirName = "%s" % self._normalisePathItem(contribution.getTitle().strip())
                self._packContribution(contribution, dirName, fileHandler)

        fileHandler.close()
        return fileHandler.getPath()

    def _packContribution(self, contribution, dirName="", fileHandler=None):

        for mat in contribution.getReviewManager().getLastReview().getMaterials():
            for res in mat.getResourceList():
                self._items += 1
                fileHandler.add("%s" % (os.path.join(self._confDirName,
                                                     self._normalisePathItem(contribution.getId()) + "-" + dirName,
                                                     self._normalisePathItem(res.getFileName()))),
                                        res.getFilePath())


class RegistrantPacker:
    """
    """

    def __init__(self,conf):
        self._conf=conf
        self._items=0

    def getItems(self):
        return self._items

    def _normalisePathItem(self,name):
        return str(name).translate(string.maketrans("",""),"\\/")

    def pack(self,regList=[], fileHandler=None):
        if len(regList)<=0:
            raise MaKaCError( _("no registrant to pack"))
        for registrant in regList:
            for attachment in registrant.getAttachmentList():
                if isinstance(attachment,conference.LocalFile):
                    self._items += 1
                    fileHandler.add("%s/%s-%s-%s"%(\
                        self._normalisePathItem(registrant.getId()),
                        self._normalisePathItem(registrant.getId()),
                        self._normalisePathItem(attachment.getId()),
                        self._normalisePathItem(attachment.getFileName())),
                    attachment.getFilePath())
        fileHandler.close()
        return fileHandler.getPath()
