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


class BadgeTemplateManager(Persistent):
    """ This class is used to manage the badge templates
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
        self._PDFOptions = BadgePDFOptions(conf)


    def notifyModification(self):
        self._p_changed = 1

    def getTemplateById(self, templateId):
        """
        Returns a BadgeTemplate object, given an id
        """
        return self.__templates[templateId]

    def getTemplateData(self, templateId):
        """
        Returns the data (a list with all the information about a template)
        of a template, directly.
        """
        return self.__templates[templateId].getData()

    def getTemplates(self):
        """ Returns a dictionary of (templateId, BadgeTemplate) keys and values
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
        function of WConfModifBadgeDesign.tpl into a JSON string.
        The string templateData is a list composed of:
            -The name of the template
            -A dictionary with 2 keys: width and height of the template, in pixels.
            -A number which is the number of pixels per cm. It is defined in WConfModifBadgeDesign.tpl. Right now its value is 50.
            -A list of dictionaries. Each dictionary has the attributes of one of the items of the template.
        If the template had any temporary backgrounds, they are archived.
        """
        if self.__templates.has_key(templateId):
            self.__templates[templateId].setData(loads(templateData))
            self.__templates[templateId].archiveTempBackgrounds(self.__conf)
        else:
            self.__templates[templateId] = BadgeTemplate(templateId, loads(templateData))

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

    def getPDFOptions(self):
        if not hasattr(self, "_PDFOptions"):
            self._PDFOptions = BadgePDFOptions(self.__conf)
        return self._PDFOptions

    def getOwner(self):
        return self.__conf


def getNewTempFile( ):
    cfg = Config.getInstance()
    tempPath = cfg.getUploadedFilesTempDir()
    tempFileName = tempfile.mkstemp( suffix="IndicoBadge.tmp", dir = tempPath )[1]
    return tempFileName

def saveFileToTemp( fd ):
    fileName = getNewTempFile()
    f = open( fileName, "wb" )
    f.write( fd.read() )
    f.close()
    return fileName

class BadgeTemplate (Persistent):
    """ This class represents a badge template, which
        will be used to print badges.
    """

    def __init__(self, id, templateData):
        """ Class Constructor
            templateData is the templateData string used in the method storeTemplate() of the class
            BadgeTemplateManager, transformed to a Python object with the function loads().
            IMPORTANT NOTE: loads() builds an objet with unicode objects inside.
                            if these objects are then concatenated to str objects (for example in an Indico HTML template),
                            this can give problems. In those cases transform the unicode object to str with .encode('utf-8').
                            In this class, __cleanData() already does this by calling MaKaC.services.interface.rpc.json.unicodeToUtf8
            Thus, its structure is a list composed of:
                -The name of the template
                -A dictionary with 2 keys: width and height of the template, in pixels.
                -A number which is the number of pixels per cm. It is defined in ConfModifBadgeDesign.tpl. Right now its value is 50.
                -The index of the background used in the template, among the several backgrounds of the template. -1 if none
                -A list of dictionaries. Each dictionary has the attributes of one of the items of the template.

        """
        self.__id = id
        self.__templateData = templateData
        self.__cleanData()
        self.__backgroundCounter = Counter() #for the backgrounds (in the future there may be more than 1 background stored per template)
        self.__backgrounds = {} #dictionary with the archived backgrounds(key: id, value: LocalFile object)
        self.__tempBackgroundsFilePaths = {} #dictionary with the temporary, not archived yet backgrounds (key: id, value: filepath string)
        self.notifyModification()

    def clone(self, templMan, templId=None):
        if templId == None:
            templId = templMan.getNewTemplateId()
        templData = self.getData()[:]
        templData[3] = -1
        newTempl = BadgeTemplate(templId, templData)
        templMan.addTemplate(newTempl, templId)
        if self.getBackground(self.getUsedBackgroundId())[1] != None:
            templData[3] = 0
            fpath = self.getBackground(self.getUsedBackgroundId())[1].getFilePath()
            # make a copy of the original file
            newPath = saveFileToTemp(open(fpath,"r"))
            newTempl.addTempBackgroundFilePath(newPath)
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
        """ Returns a list of object of the class BadgeTemplateItem with
            all the items of a template.
        """
        return [BadgeTemplateItem(itemData, self) for itemData in self.__templateData[4]]

    def getItem(self, name):
        """ Returns an object of the class BadgeTemplateItem
            which corresponds to the item whose name is 'name'
        """
        return BadgeTemplateItem(filter(lambda item: item['name'] == name, self.__templateData[4])[0])

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
            return False, self.__tempBackgroundsFilePaths[backgroundId]
        return None, None

    def addTempBackgroundFilePath(self, filePath):
        """ Adds a filePath of a temporary background to the dictionary of temporary backgrounds.
        """
        backgroundId = int(self.__backgroundCounter.newCount())
        self.__tempBackgroundsFilePaths[backgroundId] = filePath
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


        for backgroundId, filePath in self.__tempBackgroundsFilePaths.iteritems():
            cfg = Config.getInstance()
            tempPath = cfg.getUploadedFilesSharedTempDir()
            filePath = os.path.join(tempPath, filePath)
            fileName = "background" + str(backgroundId) + "_t" + self.__id + "_c" + conf.id

            from MaKaC.conference import LocalFile
            file = LocalFile()
            file.setName( fileName )
            file.setDescription( "Background " + str(backgroundId) + " of the template " + self.__id + " of the conference " + conf.id )
            file.setFileName( fileName )

            file.setFilePath( filePath )
            file.setOwner( conf )
            file.setId( fileName )
            file.archive( conf._getRepository() )
            self.__backgrounds[backgroundId] = file

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
        """ Private method which cleans the list passed by the javascript in WConfModifBadgeDesign.tpl,
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


class BadgeTemplateItem:
    """ This class represents one of the items of a badge template
        It is not stored in the database, just used for convenience access methods.
    """

    def __init__(self, itemData, badgeTemplate):
        """ Constructor
            -itemData must be a dictionary with the attributes of the item
            Example:
            {'fontFamilyIndex': 0, 'styleIndex': 1, 'bold': True, 'key': 'Country', 'fontFamily': 'Arial',
            'color': 'blue', 'selected': false, 'fontSizeIndex': 5, 'id': 0, 'width': 250, 'italic': False,
            'fontSize': 'x-large', 'textAlignIndex': 1, 'y': 40, 'x': 210, 'textAlign': 'Right',
            'colorIndex': 2}
            The several 'index' attributes and the 'selected' attribute can be ignored, they are client-side only.
            -badgeTemplate is the badgeTemplate which owns this item.
        """
        ###TODO:
        ###    fontFamilyIndex and fontFamily are linked. So, if fontFamily changes, fontFamilyIndex must be changed
        ### as well. This is done in the client. Howerver, it needs to be improved because if we need to change
        ## fontFamily in the server (for example with a script) or we add a new font, the indexes will not be
        ## synchronized anymore.
        self.__itemData = itemData
        self.__badgeTemplate = badgeTemplate

    def getKey(self):
        """ Returns the key of the item (non-translated name).
        The name of an item idientifies the kind of item it is: "Name", "Country", "Fixed Text"...
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
        return self.__badgeTemplate.pixelsToCm(self.getX())

    def getY(self):
        """ Returns the y coordinate of the item, in pixels.
        """
        return self.__itemData['y']

    def getYInCm(self):
        """ Returns the y coordinate of the item, in cm.
        """
        return self.__badgeTemplate.pixelsToCm(self.getY())

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
        return self.__badgeTemplate.pixelsToCm(self.getWidth())

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

class BadgePDFOptions(Persistent):
    """ This class stores the badge PDF options for a conference.
        Badge PDF options include, for now, the page margins and margins between badges.
        The default values are CERN's defaults in cm.
    """

    def __init__(self, conference):
        if conference.getId() == "default":
            #Best values for CERN printing service
            self.__topMargin = 1.6
            self.__bottomMargin = 1.1
            self.__leftMargin = 1.6
            self.__rightMargin = 1.4
            self.__marginColumns = 1.0
            self.__marginRows = 0.0
            self._pageSize = "A4"
            self._landscape = False
            self._drawDashedRectangles = True
        else:
            from MaKaC.conference import CategoryManager
            defaultConferencePDFOptions = CategoryManager().getDefaultConference().getBadgeTemplateManager().getPDFOptions()
            self.__topMargin = defaultConferencePDFOptions.getTopMargin()
            self.__bottomMargin = defaultConferencePDFOptions.getBottomMargin()
            self.__leftMargin = defaultConferencePDFOptions.getLeftMargin()
            self.__rightMargin = defaultConferencePDFOptions.getRightMargin()
            self.__marginColumns = defaultConferencePDFOptions.getMarginColumns()
            self.__marginRows = defaultConferencePDFOptions.getMarginRows()
            self._pageSize = defaultConferencePDFOptions.getPagesize()
            self._landscape = defaultConferencePDFOptions.getLandscape()
            self._drawDashedRectangles = defaultConferencePDFOptions.getDrawDashedRectangles()



    def getTopMargin(self):
        return self.__topMargin

    def getBottomMargin(self):
        return self.__bottomMargin

    def getLeftMargin(self):
        return self.__leftMargin

    def getRightMargin(self):
        return self.__rightMargin

    def getMarginColumns(self):
        return self.__marginColumns

    def getMarginRows(self):
        return self.__marginRows

    def getPagesize(self):
        if not hasattr(self, "_pageSize"):
            self._pageSize = "A4"
        return self._pageSize

    def getDrawDashedRectangles(self):
        """ Returns if we should draw a dashed rectangle around each badge or not.
            Will return a Boolean
        """
        if not hasattr(self, "_drawDashedRectangles"):
            self._drawDashedRectangles = True
        return self._drawDashedRectangles

    def getLandscape(self):
        try:
            return self._landscape
        except AttributeError:
            self._landscape = False
            return False

    def setTopMargin(self, value):
        self.__topMargin = value

    def setBottomMargin(self, value):
        self.__bottomMargin = value

    def setLeftMargin(self, value):
        self.__leftMargin = value

    def setRightMargin(self, value):
        self.__rightMargin = value

    def setMarginColumns(self, value):
        self.__marginColumns = value

    def setMarginRows(self, value):
        self.__marginRows = value

    def setPagesize(self, value):
        self._pageSize = value

    def setDrawDashedRectangles(self, value):
        """ Sets if we should draw a dashed rectangle around each badge or not.
            value must be a Boolean
        """
        self._drawDashedRectangles = value

    def setLandscape(self, value):
        self._landscape = value
