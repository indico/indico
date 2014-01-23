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

import os
from persistent import Persistent
import tempfile

from indico.util.json import loads
from MaKaC.common.Counter import Counter
from indico.core.config import Config
import conference


class PosterTemplateManager(Persistent):
    """ This class is used to manage the poster templates
        of a given conference.
        An instance of this class contains the list of templates
        of a conference. This conference is called the owner of the manager.
    """

    def __init__(self, conf):
        """ Class constructor
            conf: the conference who owns this manager
        """
        self.__conf = conf
        self.__templates = {}
        self.__counter = Counter(1)
        self.__tempBackgrounds = {}
        self.__tempBackgroundCounters = {}

    def notifyModification(self):
        self._p_changed = 1

    def getTemplateById(self, templateId):
        """
        Returns a PosterTemplate object, given an id
        """
        return self.__templates[templateId]

    def getTemplateData(self, templateId):
        """
        Returns the data (a list with all the information about a template)
        of a template, directly.
        """
        return self.__templates[templateId].getData()

    def getTemplates(self):
        """ Returns a dictionary of (templateId, PosterTemplate) keys and values
        """
        return self.__templates

    def hasTemplate(self, templateId):
        """ Tests if there is a template stored with the given templateId
        """
        return self.__templates.has_key(templateId)

    def getNewTemplateId(self):

        """ Returns a new an unused templateId
        Increments the templateId counter
        """
        return self.__counter.newCount()

    def storeTemplate(self, templateId, templateData):
        """
        Adds a template to the conference.
        templateData is a string produced by converting the object "template" of the save() javascript
        function of WConfModifPosterDesign.tpl into a JSON string.
        The string templateData is a list composed of:
            -The name of the template
            -A dictionary with 2 keys: width and height of the template, in pixels.
            -A number which is the number of pixels per cm. It is defined in WConfModifPosterDesign.tpl. Right now its value is 50.
            -A list of dictionaries. Each dictionary has the attributes of one of the items of the template.
        If the template had any temporary backgrounds, they are archived.
        """
        if self.__templates.has_key(templateId):
            # template already exists
            self.__templates[templateId].setData(loads(templateData))
            self.__templates[templateId].archiveTempBackgrounds(self.__conf)
        else:
            # template does not exist
            self.__templates[templateId] = PosterTemplate(templateId, loads(templateData))
        self.notifyModification()

    def addTemplate(self, templ, templateId):
        if self.__templates.has_key(templateId):
            return None
        else:
            self.__templates[templateId] = templ
            return templ

    def deleteTemplate(self, templateId):
        """ Deletes a template, if it exists (otherwise it does nothing)
        Also deletes its backgrounds.
        """
        if self.__templates.has_key(templateId):
            self.__templates[templateId].deleteBackgrounds()
            del(self.__templates[templateId])
            self.notifyModification()

    def copyTemplate(self, templateId):
        """Duplicates a template"""
        if self.__templates.has_key(templateId):
            srcTempl = self.getTemplateById(templateId)
            destTempl = srcTempl.clone(self)
            tplData = destTempl.getData()
            tplData[0] += " (copy)"
            destTempl.setData(tplData)

    def getOwner(self):
        return self.__conf

def getNewTempFile( ):
    cfg = Config.getInstance()
    tempPath = cfg.getUploadedFilesTempDir()
    tempFileName = tempfile.mkstemp( suffix="IndicoPoster.tmp", dir = tempPath )[1]
    return tempFileName

def saveFileToTemp( fd ):
    fileName = getNewTempFile()
    f = open( fileName, "wb" )
    f.write( fd.read() )
    f.close()
    return fileName

class PosterTemplate (Persistent):
    """ This class represents a poster template, which
        will be used to print posters.
    """

    def __init__(self, id, templateData):
        """ Class Constructor
            templateData is the templateData string used in the method storeTemplate() of the class
            PosterTemplateManager, transformed to a Python object with the function loads().
            IMPORTANT NOTE: loads() builds an objet with unicode objects inside.
                            if these objects are then concatenated to str objects (for example in an Indico HTML template),
                            this can give problems. In those cases transform the unicode object to str with .encode('utf-8')
                            In this class, __cleanData() already does this by calling MaKaC.services.interface.rpc.json.unicodeToUtf8
            Thus, its structure is a list composed of:
                -The name of the template
                -A dictionary with 2 keys: width and height of the template, in pixels.
                -A number which is the number of pixels per cm. It is defined in WConfModifPosterDesign.tpl. Right now its value is 50.
                -The index of the background used in the template, among the several backgrounds of the template. -1 if none
                -A list of dictionaries. Each dictionary has the attributes of one of the items of the template.

        """
        self.__id = id
        self.__templateData = templateData
        self.__cleanData()
        self.__backgroundCounter = Counter() #for the backgrounds (in the future there may be more than 1 background stored per template)
        self.__backgrounds = {} #dictionary with the archived backgrounds(key: id, value: LocalFile object)
        self.__tempBackgroundsFilePaths = {} #dictionary with the temporary, not archived yet backgrounds (key: id, value: filepath string)
        self.__bgPositions = {} #dictionary with the background positioning, for each of them (key: id, value: String ('Center','Stretch'))
        self.notifyModification()

    def clone(self, templMan, templId=None):
        if templId == None:
            templId = templMan.getNewTemplateId()
        templData = self.getData()[:]
        templData[3] = -1
        newTempl = PosterTemplate(templId, templData)
        templMan.addTemplate(newTempl, templId)
        if self.getBackground(self.getUsedBackgroundId())[1] != None:
            templData[3] = 0
            position = self.getBackgroundPosition(self.getUsedBackgroundId())
            fpath = self.getBackground(self.getUsedBackgroundId())[1].getFilePath()
            # make a copy of the original file
            newPath = saveFileToTemp(open(fpath,"r"))
            newTempl.addTempBackgroundFilePath(newPath,position)
            newTempl.archiveTempBackgrounds(templMan.getOwner())
        templMan.notifyModification()
        return newTempl

    def notifyModification(self):
        self._p_changed = 1

    def getData(self):
        """ Returns the list with all the information of the template.
        Useful so that javascript can analyze it on its own.
        """

        # ensure that each item's got a key (in order to avoid
        # using the name as key).
        for item in self.__templateData[4]:
            if not "key" in item:
                item['key'] = item['name']
        ##############################
        return self.__templateData

    def setData(self, templateData):
        """ Sets the data of the template
        """
        self.__templateData = templateData
        self.__cleanData()
        self.notifyModification()

    def getName(self):
        """ Returns the name of the template
        """
        return self.__templateData[0].encode('utf-8')


    def getWidth(self):
        """ Returns the width of the template, in pixels
        """
        return self.__templateData[1]["width"]


    def getHeight(self):
        """ Returns the height of the template, in pixels
        """
        return self.__templateData[1]["height"]


    def getPixelsPerCm(self):
        """ Returns the ratio pixels / cm of the template.
        This ratio is defined in the HTML template. Right now its value should be 50.
        """
        return self.__templateData[2]

    def getItems(self):
        """ Returns a list of object of the class PosterTemplateItem with
            all the items of a template.
        """
        return [PosterTemplateItem(itemData, self) for itemData in self.__templateData[4]]

    def getItem(self, name):
        """ Returns an object of the class PosterTemplateItem
            which corresponds to the item whose name is 'name'
        """
        return PosterTemplateItem(filter(lambda item: item['name'] == name, self.__templateData[4])[0])

    def pixelsToCm(self, length):
        """ Transforms a length in pixels to a length in cm.
        Uses the pixelsPerCm value stored in the template
        """
        return float(length) / self.__templateData[2]

    def getWidthInCm(self):
        """ Returns the width of the template in cm
        """
        return self.pixelsToCm(self.__templateData[1]["width"])

    def getHeightInCm(self):
        """ Returns the height of the template in cm
        """
        return self.pixelsToCm(self.__templateData[1]["height"])

    def getAllBackgrounds(self):
        """ Returns the list of stored background
        Each background is a LocalFile object
        """
        return self.__backgrounds

    def getUsedBackgroundId(self):
        """ Returns the id of the currently used background
        This id corresponds to a stored, archived background
        """
        return int(self.__templateData[3])

    def getBackground(self, backgroundId):
        """ Returns a tuple made of:
        -a boolean
        -a background based on an id
        There are 3 possibilities:
         -the background has already been archived. Then the boolean value is True,
         and the background is a LocalFile object,
         -the background is still temporary and has not been archived yet. Then the
         boolean is False and the background returned is a string with the file path
         to the temporary file.
         -there is no background with such id. Then the method returns (None, None)
        """

        if self.__backgrounds.has_key(backgroundId):
            return True, self.__backgrounds[backgroundId]
        if self.__tempBackgroundsFilePaths.has_key(backgroundId):
            return False, self.__tempBackgroundsFilePaths[backgroundId][0]
        return None, None

    def getBackgroundPosition(self, backgroundId):
        if self.__bgPositions.has_key(backgroundId):
            return self.__bgPositions[backgroundId]
        elif self.__tempBackgroundsFilePaths.has_key(backgroundId):
            return self.__tempBackgroundsFilePaths[backgroundId][1]
        else:
            return None

    def addTempBackgroundFilePath(self, filePath, position):
        """ Adds a filePath of a temporary background to the dictionary of temporary backgrounds
            and registers its positioning.
        """
        backgroundId = int(self.__backgroundCounter.newCount())
        self.__tempBackgroundsFilePaths[backgroundId] = (filePath,position)
        self.notifyModification()
        return backgroundId

    def archiveTempBackgrounds(self, conf):
        """ Archives all the temporary backgrounds of this template.
        This method archives all of the temporary backgrounds of this template, which are
        stored in the form of filepath strings, in the __tempBackgroundsFilePaths dictionary,
        to a dictionary which stores LocalFile objects. The ids are copied, since there is a
        shared id counter for both dictionaries.
        After the archiving, the __tempBackgroundsFilePaths dictionary is reset to {}
        """

        for backgroundId, (filePath, bgPosition) in self.__tempBackgroundsFilePaths.iteritems():
            cfg = Config.getInstance()
            tempPath = cfg.getUploadedFilesSharedTempDir()
            filePath = os.path.join(tempPath, filePath)
            fileName = "background" + str(backgroundId) + "_t" + self.__id + "_c" + conf.id

            file = conference.LocalFile()
            file.setName( fileName )
            file.setDescription( "Background " + str(backgroundId) + " of the template " + self.__id + " of the conference " + conf.id )
            file.setFileName( fileName )
            file.setFilePath( filePath )

            file.setOwner( conf )
            file.setId( fileName )
            file.archive( conf._getRepository() )

            self.__backgrounds[backgroundId] = file
            self.__bgPositions[backgroundId] = bgPosition

        self.notifyModification()
        self.__tempBackgroundsFilePaths = {}

    def deleteTempBackgrounds(self):
        """ Deletes all the temporary backgrounds of this template
        """
        self.__tempBackgroundsFilePaths = {}

    def deleteBackgrounds(self):
        """ Deletes all of the template archived backgrounds.
        To be used when a template is deleted.
        """
        for localFile in self.__backgrounds.values():
            localFile.delete()

    def __cleanData(self):
        """ Private method which cleans the list passed by the javascript in WConfModifPosterDesign.tpl,
        so that it can be properly used later.
        The following actions are taken:
           -When an item is erased while creating or editing a template, the item object is substitued
           by a "False" value. We have to remove these "False" values from the list.
           -When an item is moved, the coordinates of the item are stored for example like this: 'x':'124px', 'y':'45px'.
           We have to remove that 'px' at the end.
        """
        self.__templateData[4] = filter ( lambda item: item != False, self.__templateData[4]) # to remove items that have been deleted
        from MaKaC.services.interface.rpc.json import unicodeToUtf8
        unicodeToUtf8(self.__templateData)
        for item in self.__templateData[4]:
            if isinstance(item['x'],basestring) and item['x'][-2:] == 'px':
                item['x'] = item['x'][0:-2]
            if isinstance(item['y'],basestring) and item['y'][-2:] == 'px':
                item['y'] = item['y'][0:-2]


class PosterTemplateItem:
    """ This class represents one of the items of a poster template
        It is not stored in the database, just used for convenience access methods.
    """

    def __init__(self, itemData, posterTemplate):
        """ Constructor
            -itemData must be a dictionary with the attributes of the item
            Example:
            'fontFamilyIndex': 0, 'styleIndex': 1, 'bold': True, 'key': 'Country', 'fontFamily': 'Arial',
            'color': 'blue', 'selected': false, 'fontSizeIndex': 5, 'id': 0, 'width': 250, 'italic': False,
            'fontSize': 'x-large', 'textAlignIndex': 1, 'y': 40, 'x': 210, 'textAlign': 'Right',
            'colorIndex': 2}
            The several 'index' attributes and the 'selected' attribute can be ignored, they are client-side only.
            -posterTemplate is the posterTemplate which owns this item.
        """
        ###TODO:
        ###    fontFamilyIndex and fontFamily are linked. So, if fontFamily changes, fontFamilyIndex must be changed
        ### as well. This is done in the client. Howerver, it needs to be improved because if we need to change
        ## fontFamily in the server (for example with a script) or we add a new font, the indexes will not be
        ## synchronized anymore.
        self.__itemData = itemData
        self.__posterTemplate = posterTemplate

    def getKey(self):
        """ Returns the key of the item.
        The key of an item idientifies the kind of item it is: "Name", "Country", "Fixed Text"...
        """
        if "key" in self.__itemData:
            return self.__itemData['key']
        else:
            return self.__itemData['name']

    def getFixedText(self):
        """ Returns the text content of a Fixed Text item.
        To be used only on items whose name is "Fixed Text"
        """
        return self.__itemData['text']

    def getX(self):
        """ Returns the x coordinate of the item, in pixels.
        """
        return self.__itemData['x']

    def getXInCm(self):
        """ Returns the x coordinate of the item, in cm.
        """
        return self.__posterTemplate.pixelsToCm(self.getX())

    def getY(self):
        """ Returns the y coordinate of the item, in pixels.
        """
        return self.__itemData['y']

    def getYInCm(self):
        """ Returns the y coordinate of the item, in cm.
        """
        return self.__posterTemplate.pixelsToCm(self.getY())

    def getFont(self):
        """ Returns the name of the font used by this item.
        """
        return self.__itemData['fontFamily']

    def getFontSize(self):
        """ Returns the font size used by this item.
        Actual possible values are: 'xx-small', 'x-small', 'small', 'normal', 'large', 'x-large', 'xx-large'
        They each correspond to one of the 7 HTML sizes.
        """
        return self.__itemData['fontSize']

    def getColor(self):
        """ Returns the color used by the item, as a string.
        """
        return self.__itemData['color']

    def getWidth(self):
        """ Returns the width of the item, in pixels.
        """
        return self.__itemData['width']

    def getWidthInCm(self):
        """ Returns the width of the item, in cm.
        """
        return self.__posterTemplate.pixelsToCm(self.getWidth())

    def isBold(self):
        """ Checks of the item is bold (returns a boolean)
        """
        return self.__itemData['bold']

    def isItalic(self):
        """ Checks of the item is italic (returns a boolean)
        """
        return self.__itemData['italic']

    def getTextAlign(self):
        """ Returns the text alignment of the item, as a string.
        Actual possible values: 'Left', 'Right', 'Center', 'Justified'
        """
        return self.__itemData['textAlign']
