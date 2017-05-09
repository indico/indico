# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import cgi
import math
import os
import subprocess
import tempfile
import xml.sax.saxutils as saxutils

import markdown
import pkg_resources
from PIL import Image as PILImage
from reportlab import platypus
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import landscape, A4, LETTER, A0, A1, A2, A3, A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, PageTemplate
from reportlab.platypus.frames import Frame

from indico.core.config import Config
from indico.core.logger import Logger
from indico.util import mdx_latex
from indico.util.i18n import _
from indico.util.string import render_markdown, sanitize_for_platypus, to_unicode
from indico.legacy.common.TemplateExec import render as tpl_render
from indico.legacy.common.utils import isStringHTML


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


def escape(text):
    if text is None:
        text = ""
    try:
        if isStringHTML(text):
            text = sanitize_for_platypus(text)
        else:
            text = cgi.escape(text)
            text = text.replace("\r\n", " <br/>")
            text = text.replace("\n", " <br/>")
            text = text.replace("\r", " <br/>")
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

alreadyRegistered = False


def setTTFonts():
    global alreadyRegistered
    if not alreadyRegistered:
        distribution = pkg_resources.get_distribution('indico-fonts')
        font_dir = os.path.join(distribution.location, 'indico_fonts')
        pdfmetrics.registerFont(TTFont('Times-Roman', os.path.join(font_dir, 'LiberationSerif-Regular.ttf')))
        pdfmetrics.registerFont(TTFont('Times-Bold', os.path.join(font_dir, 'LiberationSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('Times-Italic', os.path.join(font_dir, 'LiberationSerif-Italic.ttf')))
        pdfmetrics.registerFont(TTFont('Times-Bold-Italic', os.path.join(font_dir, 'LiberationSerif-BoldItalic.ttf')))
        addMapping('Times-Roman', 0, 0, 'Times-Roman')
        addMapping('Times-Roman', 1, 0, 'Times-Bold')
        addMapping('Times-Roman', 0, 1, 'Times-Italic')
        addMapping('Times-Roman', 1, 1, 'Times-Bold-Italic')
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(font_dir, 'LiberationSans-Regular.ttf')))
        pdfmetrics.registerFont(TTFont('Sans-Bold', os.path.join(font_dir, 'LiberationSans-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('Sans-Italic', os.path.join(font_dir, 'LiberationSans-Italic.ttf')))
        pdfmetrics.registerFont(TTFont('Sans-Bold-Italic', os.path.join(font_dir, 'LiberationSans-BoldItalic.ttf')))
        addMapping('Sans', 0, 0, 'Sans')
        addMapping('Sans', 1, 0, 'Sans-Bold')
        addMapping('Sans', 0, 1, 'Sans-Italic')
        addMapping('Sans', 1, 1, 'Sans-Bold-Italic')
        pdfmetrics.registerFont(TTFont('Courier', os.path.join(font_dir, 'LiberationMono-Regular.ttf')))
        pdfmetrics.registerFont(TTFont('Courier-Bold', os.path.join(font_dir, 'LiberationMono-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('Courier-Italic', os.path.join(font_dir, 'LiberationMono-Italic.ttf')))
        pdfmetrics.registerFont(TTFont('Courier-Bold-Italic', os.path.join(font_dir, 'LiberationMono-BoldItalic.ttf')))
        addMapping('Courier', 0, 0, 'Courier')
        addMapping('Courier', 1, 0, 'Courier-Bold')
        addMapping('Courier', 0, 1, 'Courier-Italic')
        addMapping('Courier', 1, 1, 'Courier-Bold-Italic')
        pdfmetrics.registerFont(TTFont('LinuxLibertine', os.path.join(font_dir, 'LinLibertine_Rah.ttf')))
        pdfmetrics.registerFont(TTFont('LinuxLibertine-Bold', os.path.join(font_dir, 'LinLibertine_RBah.ttf')))
        pdfmetrics.registerFont(TTFont('LinuxLibertine-Italic', os.path.join(font_dir, 'LinLibertine_RIah.ttf')))
        pdfmetrics.registerFont(TTFont('LinuxLibertine-Bold-Italic', os.path.join(font_dir, 'LinLibertine_RBIah.ttf')))
        addMapping('LinuxLibertine', 0, 0, 'LinuxLibertine')
        addMapping('LinuxLibertine', 1, 0, 'LinuxLibertine-Bold')
        addMapping('LinuxLibertine', 0, 1, 'LinuxLibertine-Italic')
        addMapping('LinuxLibertine', 1, 1, 'LinuxLibertine-Bold-Italic')
        pdfmetrics.registerFont(TTFont('Kochi-Mincho', os.path.join(font_dir, 'kochi-mincho-subst.ttf')))
        pdfmetrics.registerFont(TTFont('Kochi-Gothic', os.path.join(font_dir, 'kochi-gothic-subst.ttf')))
        alreadyRegistered = True


class Int2Romans:

    def int_to_roman(input):
        """
        Convert an integer to Roman numerals.
        """
        if type(input) != type(1):
            raise TypeError, _("expected integer, got %s") % type(input)
        if not 0 < input < 4000:
            raise MaKaCError( _("Int to Roman Error: Argument must be between 1 and 3999"))
        ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
        nums = ('m',  'cm', 'd', 'cd','c', 'xc','l','xl','x','ix','v','iv','i')
        result = ""
        for i in range(len(ints)):
            count = int(input / ints[i])
            result += nums[i] * count
            input -= ints[i] * count
        return result
    int_to_roman = staticmethod(int_to_roman)

class Paragraph(platypus.Paragraph):
    """
    add a part attribute for drawing the name of the current part on the laterPages function
    """
    def __init__(self, text, style, part="", bulletText=None, frags=None, caseSensitive=1):
        platypus.Paragraph.__init__(self, to_unicode(text), style, bulletText, frags, caseSensitive)
        self._part = part

    def setPart(self, part):
        self._part = part

    def getPart(self):
        return self._part

class SimpleParagraph(platypus.Flowable):
    """  Simple and fast paragraph.

    WARNING! This paragraph cannot break the line and doesn't have almost any formatting methods.
             It's used only to increase PDF performance in places where normal paragraph is not needed.
    """
    def __init__(self, text, fontSize = 10, indent = 0, spaceAfter = 2):
        platypus.Flowable.__init__(self)
        self.text = text
        self.height = fontSize + spaceAfter
        self.fontSize = fontSize
        self.spaceAfter = spaceAfter
        self.indent = indent

    def __repr__(self):
        return ""

    def draw(self):
        #centre the text
        self.canv.setFont('Times-Roman',self.fontSize)
        self.canv.drawString(self.indent, self.spaceAfter, self.text)

class TableOfContentsEntry(Paragraph):
    """
        Class used to create table of contents entry with its number.
        Much faster than table of table of contents from platypus lib
    """
    def __init__(self, text, pageNumber, style, part="", bulletText=None, frags=None, caseSensitive=1):
        Paragraph.__init__(self, to_unicode(text), style, part, bulletText, frags, caseSensitive)
        self._part = part
        self._pageNumber = pageNumber

    def _drawDots(self):
        """
        Draws row of dots from the end of the abstract title to the page number.
        """
        try:
            freeSpace = int(self.blPara.lines[-1][0])
        except AttributeError:
            # Sometimes we get an ABag instead of a tuple.. in this case we use the extraSpace attribute
            # as it seems to contain just what we need.
            freeSpace = int(self.blPara.lines[-1].extraSpace)
        while( freeSpace > 10 ):
            dot = self.beginText(self.width + 10 - freeSpace, self.style.leading - self.style.fontSize)
            dot.textLine(".")
            self.canv.drawText(dot)
            freeSpace -= 3

    def draw(self):
        platypus.Paragraph.draw(self)
        tx = self.beginText(self.width + 10, self.style.leading - self.style.fontSize)
        tx.setFont(self.style.fontName, self.style.fontSize, 0)
        tx.textLine(str(self._pageNumber))
        self.canv.drawText(tx)
        self._drawDots()

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
        platypus.PageBreak.__init__(self)
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

    def __init__(self, doc=None, story=None, pagesize = 'A4', printLandscape=False, title=None):

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

        if title is not None:
            self._doc.title = title

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
                draw(width,height, line)
                height -= lineSpacing*measurement
                line = word
        if line.strip() != "":
            draw(width, height, line)
        return height

    def _drawLogo(self, c, drawTitle = True):
        from indico.modules.events.util import create_event_logo_tmp_file
        logo = self._conf.as_event.logo
        imagePath = ""
        if logo:
            imagePath = create_event_logo_tmp_file(self._conf.as_event).name
        if imagePath:
            try:
                img = PILImage.open(imagePath)
                width, height = img.size

                # resize in case too big for page
                if width > self._PAGE_WIDTH / 2:
                    ratio =  float(height)/width
                    width = self._PAGE_WIDTH / 2
                    height = width * ratio
                startHeight = self._PAGE_HEIGHT

                if drawTitle:
                    startHeight = self._drawWrappedString(c, escape(self._conf.as_event.title.encode('utf-8')),
                                                          height=self._PAGE_HEIGHT - inch)

                # lower edge of the image
                startHeight = startHeight - inch / 2 - height

                # draw horizontally centered, with recalculated width and height
                c.drawImage(imagePath, self._PAGE_WIDTH/2.0 - width/2, startHeight, width, height, mask="auto")
                return startHeight
            except IOError:
                if drawTitle:
                    self._drawWrappedString(c, escape(self._conf.as_event.title.encode('utf-8')),
                                            height=self._PAGE_HEIGHT - inch)
        return 0


def _doNothing(canvas, doc):
    "Dummy callback for onPage"
    pass

class DocTemplateWithTOC(SimpleDocTemplate):

    def __init__(self, indexedFlowable, filename, firstPageNumber = 1, **kw ):
        """toc is the TableOfContents object
        indexedFlowale is a dictionnary with flowables as key and a dictionnary as value.
            the sub-dictionnary have two key:
                text: the text which will br print in the table
                level: the level of the entry( modifying the indentation and the police
        """
        self._toc = []
        self._tocStory = []
        self._indexedFlowable = indexedFlowable
        self._filename = filename
        self._part = ""
        self._firstPageNumber = firstPageNumber
        SimpleDocTemplate.__init__(self, filename, **kw)
        setTTFonts()
        self._PAGE_HEIGHT = self.pagesize[1]
        self._PAGE_WIDTH = self.pagesize[0]

    def afterFlowable(self, flowable):
        if flowable in self._indexedFlowable:
            self._toc.append((self._indexedFlowable[flowable]["level"],self._indexedFlowable[flowable]["text"], self.page + self._firstPageNumber - 1))
        try:
            if flowable.getPart() != "":
                self._part = flowable.getPart()
        except:
            pass

    def handle_documentBegin(self):
        self._part = ""
        SimpleDocTemplate.handle_documentBegin(self)

    def _prepareTOC(self):
        headerStyle = ParagraphStyle({})
        headerStyle.fontName = "LinuxLibertine-Bold"
        headerStyle.fontSize = modifiedFontSize(18, 18)
        headerStyle.leading = modifiedFontSize(22, 22)
        headerStyle.alignment = TA_CENTER
        entryStyle = ParagraphStyle({})
        entryStyle.fontName = "LinuxLibertine"
        entryStyle.spaceBefore = 8
        self._tocStory.append(PageBreak())
        self._tocStory.append(Spacer(inch, 1*cm))
        self._tocStory.append(Paragraph( _("Table of contents"), headerStyle))
        self._tocStory.append(Spacer(inch, 2*cm))
        for entry in self._toc:
            self._tocStory.append(TableOfContentsEntry("<para leftIndent=%s" % ((entry[0] - 1) * 50) + ">" + entry[1] + "</para>", str(entry[2]),entryStyle))
            #self._tocStory.append(SimpleParagraph(entry[1]))
        #self._tocStory.append(PageBreak())

    def laterPages(self,c,doc):
        c.saveState()
        c.setFont('Times-Roman',9)
        c.setFillColorRGB(0.5,0.5,0.5)
        c.drawCentredString(self._PAGE_WIDTH/2.0,0.5*cm,"%s "%Int2Romans.int_to_roman(doc.page-1))
        c.restoreState()

    def multiBuild(self, story, filename=None, canvasMaker=Canvas, maxPasses=10, onFirstPage=_doNothing, onLaterPages=_doNothing):
        self._calc()    #in case we changed margins sizes etc
        frameT = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='normal')
        self.addPageTemplates([PageTemplate(id='Later',frames=frameT, onPageEnd=onLaterPages,pagesize=self.pagesize)])
        if onLaterPages is _doNothing and hasattr(self,'onLaterPages'):
            self.pageTemplates[0].beforeDrawPage = self.onLaterPages
        SimpleDocTemplate.multiBuild(self, story, maxPasses, canvasmaker=canvasMaker)
        self._prepareTOC()
        contentFile = self.filename
        self.filename = FileDummy()
        self.pageTemplates = []
        self.addPageTemplates([PageTemplate(id='First',frames=frameT, onPage=onFirstPage,pagesize=self.pagesize)])
        if onFirstPage is _doNothing and hasattr(self,'onFirstPage'):
            self.pageTemplates[0].beforeDrawPage = self.onFirstPage
        self.addPageTemplates([PageTemplate(id='Later',frames=frameT, onPageEnd=self.laterPages,pagesize=self.pagesize)])
        if onLaterPages is _doNothing and hasattr(self,'onLaterPages'):
            self.pageTemplates[1].beforeDrawPage = self.onLaterPages
        SimpleDocTemplate.multiBuild(self, self._tocStory, maxPasses, canvasmaker=canvasMaker)
        self.mergePDFs(self.filename, contentFile)

    def mergePDFs(self, pdf1, pdf2):
        from pyPdf import PdfFileWriter, PdfFileReader
        import cStringIO
        outputStream = cStringIO.StringIO()
        pdf1Stream = cStringIO.StringIO()
        pdf2Stream = cStringIO.StringIO()
        pdf1Stream.write(pdf1.getData())
        pdf2Stream.write(pdf2.getData())
        output = PdfFileWriter()
        background_pages = PdfFileReader(pdf1Stream)
        foreground_pages = PdfFileReader(pdf2Stream)
        for page in background_pages.pages:
            output.addPage(page)
        for page in foreground_pages.pages:
            output.addPage(page)
        output.write(outputStream)
        pdf2._data = outputStream.getvalue()
        outputStream.close()

    def getCurrentPart(self):
        return self._part


class PDFWithTOC(PDFBase):
    """
    create a PDF with a Table of Contents

    """

    def __init__(self, story=None, pagesize='A4', fontsize='normal', firstPageNumber=1):

        self._fontsize = fontsize
        self._story = story
        if story is None:
            self._story = []
            # without this blank spacer first abstract isn't displayed. why?
            self._story.append(Spacer(inch, 0*cm))

        self._indexedFlowable = {}
        self._fileDummy = FileDummy()

        self._doc = DocTemplateWithTOC(self._indexedFlowable, self._fileDummy, firstPageNumber=firstPageNumber,
                                       pagesize=PDFSizes().PDFpagesizes[pagesize])

        self._PAGE_HEIGHT = PDFSizes().PDFpagesizes[pagesize][1]
        self._PAGE_WIDTH = PDFSizes().PDFpagesizes[pagesize][0]

        setTTFonts()

    def _processTOCPage(self):
        """ Generates page with table of contents.

        Not used, because table of contents is generated automatically inside DocTemplateWithTOC class
        """
        style1 = ParagraphStyle({})
        style1.fontName = "Times-Bold"
        style1.fontSize = modifiedFontSize(18, self._fontsize)
        style1.leading = modifiedFontSize(22, self._fontsize)
        style1.alignment = TA_CENTER
        p = Paragraph(_("Table of contents"), style1)
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
        self._doc.multiBuild(self._story, onFirstPage=self.firstPage, onLaterPages=self.laterPages)
        return self._fileDummy.getData()


class PDFLaTeXBase(object):

    _table_of_contents = False

    def __init__(self):
        # Markdown -> LaTeX renderer
        # safe_mode - strip out all HTML
        md = markdown.Markdown(safe_mode='remove')
        latex_mdx = mdx_latex.LaTeXExtension()
        latex_mdx.extendMarkdown(md, markdown.__dict__)

        def _escape_latex_math(string):
            return mdx_latex.latex_escape(string, ignore_math=True)

        def _convert_markdown(text):
            return render_markdown(text, md=md.convert, escape_latex_math=_escape_latex_math)

        self._args = {
            'md_convert': _convert_markdown
        }

    def generate(self):
        latex = LatexRunner(has_toc=self._table_of_contents)
        pdffile = latex.run(self._tpl_filename, **self._args)
        return pdffile


class LaTeXRuntimeException(Exception):
    def __init__(self, source_file, log_file):
        super(LaTeXRuntimeException, self).__init__('LaTeX compilation of {} failed'.format(source_file))
        self.source_file = source_file
        self.log_file = log_file

    @property
    def message(self):
        return "Impossible to compile '{0}'. Read '{1}' for details".format(self.source_file, self.log_file)


class LatexRunner(object):
    """
    Handles the PDF generation from a chosen LaTeX template
    """

    def __init__(self, has_toc=False):
        self.has_toc = has_toc

    def run_latex(self, source_file, log_file=None):
        pdflatex_cmd = [Config.getInstance().getPDFLatexProgram(),
                        '-no-shell-escape',
                        '-interaction', 'nonstopmode',
                        '-output-directory', self._dir,
                        source_file]

        try:
            subprocess.check_call(pdflatex_cmd, stdout=log_file)
            Logger.get('pdflatex').debug("PDF created successfully!")

        except subprocess.CalledProcessError:
            Logger.get('pdflatex').warning('PDF creation possibly failed (non-zero exit code)!')
            # Only fail if we are in strict mode
            if Config.getInstance().getStrictLatex():
                # flush log, go to beginning and read it
                if log_file:
                    log_file.flush()
                raise

    def run(self, template_name, **kwargs):
        template_dir = os.path.join(Config.getInstance().getTPLDir(), 'latex')
        template = tpl_render(os.path.join(template_dir, template_name), kwargs)

        self._dir = tempfile.mkdtemp(prefix="indico-texgen-", dir=Config.getInstance().getTempDir())
        source_filename = os.path.join(self._dir, template_name + '.tex')
        target_filename = os.path.join(self._dir, template_name + '.pdf')
        log_filename = os.path.join(self._dir, 'output.log')
        log_file = open(log_filename, 'a+')

        with open(source_filename, 'w') as f:
            f.write(template)

        try:
            self.run_latex(source_filename, log_file)
            if self.has_toc:
                self.run_latex(source_filename, log_file)
        finally:
            log_file.close()

            if not os.path.exists(target_filename):
                # something went terribly wrong, no LaTeX file was produced
                raise LaTeXRuntimeException(source_filename, log_filename)

        return target_filename
