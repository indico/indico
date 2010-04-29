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

import os, math, types
import xml.sax.saxutils as saxutils
from HTMLParser import HTMLParser
from reportlab.platypus import SimpleDocTemplate, PageTemplate
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER  
from reportlab import platypus
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus.frames import Frame
from reportlab.lib.pagesizes import landscape, A4, LETTER, A0, A1, A2, A3, A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from MaKaC.i18n import _
from MaKaC.common.utils import isStringHTML
from MaKaC.errors import MaKaCError

ratio = math.sqrt(math.sqrt(2.0))

class PDFSizes:
    
    def __init__(self):
        self.PDFpagesizes = {'Letter' : LETTER,
                    'A0' : A3,
                    'A1' : A3,
                    'A2' : A3,
                    'A3' : A3,
                    'A4' : A4,
                    'A5' : A5
                   }

        self.PDFfontsizes = [_("xxx-small"), _("xx-small"), _("x-small"), _("smaller"), _("small"), _("normal"), _("large"), _("larger")]   

class PDFHTMLParser(HTMLParser):
    _removedTags = ["a", "font"]

    def __init__(self):
        HTMLParser.__init__(self)
        self.text = []
        
    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()
        return "".join(self.text)
        
    def handle_data(self, data):
        self.text.append( saxutils.escape(data) )

    def filterAttrs(self, attrs):
        filteredAttrs = []
        for x, y in attrs:
            if x not in ["target"]:
                filteredAttrs.append((x,y))
        return filteredAttrs

    def handle_entityref(self, name):
        self.text.append( "&%s;"%name )

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.text.append( "<br/>" )
        elif tag in self._removedTags:
            return
        else:
            self.text.append( "<%s%s>" % (tag, " ".join([ ' %s="%s"' % (x,y) for x,y in self.filterAttrs(attrs)])) )

    def handle_startendtag(self, tag, attrs):
        self.text.append( "<%s%s/>" % (tag, " ".join([ ' %s="%s"' % (x,y) for x,y in self.filterAttrs(attrs)])) )
        
    def handle_endtag(self, tag):
        if tag in self._removedTags:
            return
        self.text.append( "</%s>" % tag )
        
def escape(text):
    if text is None: 
        text = ""
    try:
        text = PDFHTMLParser().parse(text)
        if not isStringHTML(text):
            text = text.replace("\r\n"," <br/>")
            text = text.replace("\n"," <br/>")
            text = text.replace("\r"," <br/>")
        return text
    except Exception:
        return saxutils.escape(text)

def modifiedFontSize(fontsize, lowerNormalHigher):
    
    if lowerNormalHigher == _("normal"):
        return fontsize
    elif lowerNormalHigher == _("small"):
        return fontsize / ratio
    elif lowerNormalHigher == _("large"):
        return fontsize * ratio
    elif lowerNormalHigher == _("smaller"):
        return (fontsize / ratio) / ratio
    elif lowerNormalHigher == _("x-small"):
        return ((fontsize / ratio) / ratio) / ratio
    elif lowerNormalHigher == _("xx-small"):
        return (((fontsize / ratio) / ratio) / ratio) / ratio
    elif lowerNormalHigher == _("xxx-small"):
        return ((((fontsize / ratio) / ratio) / ratio) / ratio) / ratio
    elif lowerNormalHigher == _("larger"):
        return fontsize * ratio * ratio
    else:
        return fontsize
    

def setTTFonts():
    # Import fonts from indico.extra (separate package)
    import indico.extra.fonts

    dir=os.path.split(os.path.abspath(indico.extra.fonts.__file__))[0]
    pdfmetrics.registerFont(TTFont('Times-Roman', os.path.join(dir,'LiberationSerif-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Times-Bold', os.path.join(dir, 'LiberationSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('Times-Italic', os.path.join(dir,'LiberationSerif-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('Times-Bold-Italic', os.path.join(dir, 'LiberationSerif-BoldItalic.ttf')))
    pdfmetrics.registerFont(TTFont('Courier', os.path.join(dir, 'LiberationMono-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('Courier-Bold', os.path.join(dir, 'LiberationMono-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('Courier-Italic', os.path.join(dir, 'LiberationMono-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('Courier-Bold-Italic', os.path.join(dir, 'LiberationMono-BoldItalic.ttf')))
    pdfmetrics.registerFont(TTFont('LinuxLibertine', os.path.join(dir, 'LinLibertine_Re-4.4.1.ttf')))
    pdfmetrics.registerFont(TTFont('LinuxLibertine-Bold', os.path.join(dir, 'LinLibertine_Bd-4.1.0.ttf')))
    pdfmetrics.registerFont(TTFont('LinuxLibertine-Italic', os.path.join(dir, 'LinLibertine_It-4.0.6.ttf')))
    pdfmetrics.registerFont(TTFont('LinuxLibertine-Bold-Italic', os.path.join(dir, 'LinLibertine_BI-4.0.5.ttf')))
    pdfmetrics.registerFont(TTFont('Kochi-Mincho', os.path.join(dir, 'kochi-mincho-subst.ttf')))
    pdfmetrics.registerFont(TTFont('Kochi-Gothic', os.path.join(dir, 'kochi-gothic-subst.ttf')))
    pdfmetrics.registerFont(TTFont('Uming-CN', os.path.join(dir, 'uming.ttc')))

class Paragraph(platypus.Paragraph):
    """
    add a part attribute for drawing the name of the current part on the laterPages function
    """
    def __init__(self, test, style, part="", bulletText=None, frags=None, caseSensitive=1):
        platypus.Paragraph.__init__(self, test, style, bulletText, frags, caseSensitive)
        self._part = part
    
    def setPart(self, part):
        self._part = part
    
    def getPart(self):
        return self._part

class Spacer(platypus.Spacer):
    def __init__(self, width, height, part=""):
        platypus.Spacer.__init__(self, width, height)
        self._part = part
    
    def setPart(self, part):
        self._part = part
    
    def getPart(self):
        return self._part

class Image(platypus.Image):
    def __init__(self, filename, part="", width=None, height=None, kind='direct', mask="auto", lazy=1):
        platypus.Image.__init__(self, filename, width=None, height=None, kind='direct', mask="auto", lazy=1)
        self._part = part
    
    def setPart(self, part):
        self._part = part
    
    def getPart(self):
        return self._part


class PageBreak(platypus.PageBreak):
    def __init__(self, part=""):
        self._part = part
    
    def setPart(self, part):
        self._part = part
    
    def getPart(self):
        return self._part

class Preformatted(platypus.Preformatted):
    def __init__(self, text, style, part="", bulletText = None, dedent=0):
        platypus.Preformatted.__init__(self, text, style, bulletText = None, dedent=0)
        self._part = part
    
    def setPart(self, part):
        self._part = part
    
    def getPart(self):
        return self._part


class FileDummy:
    def __init__(self):
        self._data = ""
        self.name = "fileDummy"
    
    def write(self, data):
        self._data += data
    
    def getData(self):
        return self._data
    
    def close(self):
        pass

class CanvasA0(Canvas):
    def __init__(self,filename,
                 pagesize=None,
                 bottomup = 1,
                 pageCompression=None,
                 encoding = None,
                 invariant = None,
                 verbosity=0):
        
        Canvas.__init__(self, filename, pagesize=pagesize, bottomup=bottomup, pageCompression=pageCompression,
                        encoding=encoding, invariant=invariant, verbosity=verbosity)
        self.scale(4.0, 4.0)
        self.setPageSize(A0)

class CanvasA1(Canvas):
    def __init__(self,filename,
                 pagesize=None,
                 bottomup = 1,
                 pageCompression=None,
                 encoding = None,
                 invariant = None,
                 verbosity=0):
        
        Canvas.__init__(self, filename, pagesize=pagesize, bottomup=bottomup, pageCompression=pageCompression,
                        encoding=encoding, invariant=invariant, verbosity=verbosity)
        self.scale(2.0 * math.sqrt(2.0), 2.0 * math.sqrt(2.0))
        self.setPageSize(A1)

class CanvasA2(Canvas):
    def __init__(self,filename,
                 pagesize=None,
                 bottomup = 1,
                 pageCompression=None,
                 encoding = None,
                 invariant = None,
                 verbosity=0):
        
        Canvas.__init__(self, filename, pagesize=pagesize, bottomup=bottomup, pageCompression=pageCompression,
                        encoding=encoding, invariant=invariant, verbosity=verbosity)
        self.scale(2.0, 2.0)
        self.setPageSize(A2)

class CanvasA3(Canvas):
    def __init__(self,filename,
                 pagesize=None,
                 bottomup = 1,
                 pageCompression=None,
                 encoding = None,
                 invariant = None,
                 verbosity=0):
        
        Canvas.__init__(self, filename, pagesize=pagesize, bottomup=bottomup, pageCompression=pageCompression,
                        encoding=encoding, invariant=invariant, verbosity=verbosity)
        self.scale(math.sqrt(2.0), math.sqrt(2.0))
        self.setPageSize(A3)
        
class CanvasA5(Canvas):
    def __init__(self,filename,
                 pagesize=None,
                 bottomup = 1,
                 pageCompression=None,
                 encoding = None,
                 invariant = None,
                 verbosity=0):
        
        Canvas.__init__(self, filename, pagesize=pagesize, bottomup=bottomup, pageCompression=pageCompression,
                        encoding=encoding, invariant=invariant, verbosity=verbosity)
        self.scale(1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0))
        self.setPageSize(A5)

pagesizeNameToCanvas = {'A4': Canvas,
                        'A0': CanvasA0,
                        'A1': CanvasA1,
                        'A2': CanvasA2,
                        'A3': CanvasA3,
                        'A5': CanvasA5,
                        'Letter': Canvas,
                        }

class PDFBase:
    
    def __init__(self, doc=None, story=None, pagesize = 'A4', printLandscape=False):
        
        if doc:
            self._doc = doc
        else:
            #create a new document
            #As the constructor of SimpleDocTemplate can take only a filename or a file object,
            #to keep the PDF data not in a file, we use a dummy file object which save the data in a string
            self._fileDummy = FileDummy()
            if printLandscape:
                self._doc = SimpleDocTemplate(self._fileDummy, pagesize = landscape(PDFSizes().PDFpagesizes[pagesize]))
            else:
                self._doc = SimpleDocTemplate(self._fileDummy, pagesize = PDFSizes().PDFpagesizes[pagesize])
        
        if story is not None:
            self._story = story
        else:
            #create a new story with a spacer which take all the first page
            #then the first page is only drawing by the firstPage method
            self._story = [PageBreak()]
            
        if printLandscape:
            self._PAGE_HEIGHT = landscape(PDFSizes().PDFpagesizes[pagesize])[1]
            self._PAGE_WIDTH = landscape(PDFSizes().PDFpagesizes[pagesize])[0]
        else:
            self._PAGE_HEIGHT = PDFSizes().PDFpagesizes[pagesize][1]
            self._PAGE_WIDTH = PDFSizes().PDFpagesizes[pagesize][0]
            
        self._canv = Canvas
        setTTFonts()
    
    def firstPage(self, c, doc):
        """set the first page of the document
        This function is call by doc.build method for the first page
        """
        pass
    
    
    def laterPages(self, c, doc):
        """set the layout of the page after the first
        This function is call by doc.build method one each page after the first
        """
        pass
    
    
    def getBody(self, story=None):
        if not story:
            story = self._story
        """add the content to the story
        """
        pass
    
    
    def getPDFBin(self):
        #build the pdf in the fileDummy
        self.getBody()
        self._doc.build(self._story, onFirstPage=self.firstPage, onLaterPages=self.laterPages)
        #return the data from the fileDummy
        return self._fileDummy.getData()

    def _drawWrappedString(self, c, text, font='Times-Bold', size=30, color=(0,0,0), \
                                align="center", width=None, height=None, measurement=cm, lineSpacing=1, maximumWidth=None  ):
        if maximumWidth is None:
            maximumWidth = self._PAGE_WIDTH-1*cm
        if width is None:
            width=self._PAGE_WIDTH/2.0
        if height is None:
            height=self._PAGE_HEIGHT-10*measurement
        draw = c.drawCentredString
        if align == "right":
            draw = c.drawRightString
        elif align == "left":
            draw = c.drawString
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        titleWords = text.split()
        line=""
        for word in titleWords:
            lineAux = "%s %s"%(line, word)
            lsize = c.stringWidth(lineAux, font, size)
            if lsize < maximumWidth:
                line = lineAux
            else:
                draw(width,height, escape(line))
                height -= lineSpacing*measurement
                line = word
        if line.strip() != "":
            draw(width, height, escape(line))
        return height
    
    

def _doNothing(canvas, doc):
    "Dummy callback for onPage"
    pass

class DocTemplateWithTOC(SimpleDocTemplate):
    
    def __init__(self, toc, indexedFlowable, filename, firstPageNumber = 1, **kw ):
        """toc is the TableOfContents object
        indexedFlowale is a dictionnary with flowables as key and a dictionnary as value.
            the sub-dictionnary have two key: 
                text: the text which will br print in the table
                level: the level of the entry( modifying the indentation and the police
        """
        
        self._toc = toc
        self._indexedFlowable = indexedFlowable
        self._filename = filename
        self._part = ""
        self._firstPageNumber = firstPageNumber
        SimpleDocTemplate.__init__(self, filename, **kw)
        setTTFonts()
    
    def afterFlowable(self, flowable):
        if flowable in self._indexedFlowable:
            self._toc.addEntry(self._indexedFlowable[flowable]["level"], self._indexedFlowable[flowable]["text"], self.page + (self._firstPageNumber - 1))
        try:
            if flowable.getPart() != "":
                self._part = flowable.getPart()
        except:
            pass
    
    def handle_documentBegin(self):
        self._part = ""
        SimpleDocTemplate.handle_documentBegin(self)
        
    
    
    def multiBuild(self, story, filename=None, canvasMaker=Canvas, maxPasses=10, onFirstPage=_doNothing, onLaterPages=_doNothing):
        self._calc()    #in case we changed margins sizes etc
        frameT = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='normal')
        # we add the function for the later pages to the onPageEnd of the PageTemplate because we must know the part for the page
        self.addPageTemplates([PageTemplate(id='First',frames=frameT, onPage=onFirstPage,pagesize=self.pagesize),
                        PageTemplate(id='Later',frames=frameT, onPageEnd=onLaterPages,pagesize=self.pagesize)])
        if onFirstPage is _doNothing and hasattr(self,'onFirstPage'):
            self.pageTemplates[0].beforeDrawPage = self.onFirstPage
        if onLaterPages is _doNothing and hasattr(self,'onLaterPages'):
            self.pageTemplates[1].beforeDrawPage = self.onLaterPages
        SimpleDocTemplate.multiBuild(self, story, self._filename, canvasMaker, maxPasses)
    
    def getCurrentPart(self):
        return self._part



class PDFWithTOC(PDFBase):
    """
    create a PDF with a Table of Contents
    
    """
    
    def __init__(self, story=None, pagesize = 'A4', fontsize = 'normal', firstPageNumber = 1 ):
        
        
        self._fontsize = fontsize
        self._indexedFlowable = [] #indexedFlowable
        self._toc = TableOfContents()
        self._story=story
        if story is None:
            self._story = []
            self._story.append( PageBreak() )

        self._toc = TableOfContents()
        self._processTOCPage()
        self._indexedFlowable = {}
        self._fileDummy = FileDummy()
        
        self._doc = DocTemplateWithTOC(self._toc, self._indexedFlowable, self._fileDummy, firstPageNumber = firstPageNumber, pagesize=PDFSizes().PDFpagesizes[pagesize])
        
        self._PAGE_HEIGHT = PDFSizes().PDFpagesizes[pagesize][1]
        self._PAGE_WIDTH = PDFSizes().PDFpagesizes[pagesize][0]
        
        setTTFonts()
        
    def _processTOCPage(self):
        style1 = ParagraphStyle({})
        style1.fontName = "Times-Bold"
        style1.fontSize = modifiedFontSize(18, self._fontsize)
        style1.leading = modifiedFontSize(22, self._fontsize)
        style1.alignment = TA_CENTER
        p = Paragraph( _("Table of contents"), style1)
        self._story.append(Spacer(inch, 1*cm))
        self._story.append(p)
        self._story.append(Spacer(inch, 2*cm))
        self._story.append(self._toc)
        self._story.append(PageBreak())
        
    def getBody(self, story=None):
        """add the content to the story
        When you want to put a paragraph p in the toc, add it to the self._indexedFlowable as this:
            self._indexedFlowable[p] = {"text":"my title", "level":1}
        """
        if not story:
            story = self._story
        pass
            
    def getPDFBin(self):
        self.getBody()
        self._doc.multiBuild( self._story, onFirstPage=self.firstPage, onLaterPages=self.laterPages)
        return self._fileDummy.getData()
