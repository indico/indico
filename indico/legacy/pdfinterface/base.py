# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# ruff: noqa: N802, N803, N806

import math
import os
from importlib.resources import as_file, files
from io import BytesIO
from xml.sax import saxutils  # noqa: S406

from PIL import Image as PILImage
from reportlab import platypus
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import A3, A4, A5, A6, LETTER, landscape
from reportlab.lib.units import cm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate

from indico.util.string import sanitize_for_platypus


ratio = math.sqrt(math.sqrt(2.0))


class PDFSizes:
    def __init__(self):
        self.PDFpagesizes = {
            'Letter': LETTER,
            'A0': A3,
            'A1': A3,
            'A2': A3,
            'A3': A3,
            'A4': A4,
            'A5': A5,
            'A6': A6
        }


def _is_string_html(s):
    # yeah, this function is pretty ugly. it's legacy and should eventually be replaced :)
    if not isinstance(s, str):
        return False
    s = s.lower()
    return any(tag in s for tag in ('<p>', '<p ', '<br', '<li>'))


def escape(text):
    if text is None:
        return ''
    if _is_string_html(text):
        return sanitize_for_platypus(text)
    else:
        return saxutils.escape(text)


def modifiedFontSize(fontsize, lowerNormalHigher):
    if lowerNormalHigher == 'normal':
        return fontsize
    elif lowerNormalHigher == 'small':
        return fontsize / ratio
    elif lowerNormalHigher == 'large':
        return fontsize * ratio
    elif lowerNormalHigher == 'smaller':
        return (fontsize / ratio) / ratio
    elif lowerNormalHigher == 'x-small':
        return ((fontsize / ratio) / ratio) / ratio
    elif lowerNormalHigher == 'xx-small':
        return (((fontsize / ratio) / ratio) / ratio) / ratio
    elif lowerNormalHigher == 'xxx-small':
        return ((((fontsize / ratio) / ratio) / ratio) / ratio) / ratio
    elif lowerNormalHigher == 'larger':
        return fontsize * ratio * ratio
    else:
        return fontsize


already_registered = False


def setTTFonts():
    global already_registered  # noqa: PLW0603
    if already_registered:
        return
    already_registered = True
    with as_file(files('indico_fonts')) as font_dir:
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


class Paragraph(platypus.Paragraph):
    """
    Add a part attribute for drawing the name of the current part
    on the laterPages function.
    """

    def __init__(self, text, style, part='', bulletText=None, frags=None, caseSensitive=1):
        platypus.Paragraph.__init__(self, str(text), style, bulletText, frags, caseSensitive)
        self._part = part

    def setPart(self, part):
        self._part = part

    def getPart(self):
        return self._part


class Spacer(platypus.Spacer):
    def __init__(self, width, height, part=''):
        platypus.Spacer.__init__(self, width, height)
        self._part = part

    def setPart(self, part):
        self._part = part

    def getPart(self):
        return self._part


class PageBreak(platypus.PageBreak):
    def __init__(self, part=''):
        platypus.PageBreak.__init__(self)
        self._part = part

    def setPart(self, part):
        self._part = part

    def getPart(self):
        return self._part


class PDFBase:
    def __init__(self, doc=None, story=None, pagesize='A4', printLandscape=False, title=None):
        if doc:
            self._doc = doc
        else:
            # create a new document
            # As the constructor of SimpleDocTemplate can take only a filename or a file object,
            # to keep the PDF data not in a file, we use a dummy file object which save the data in a string
            self._fileDummy = BytesIO()
            if printLandscape:
                self._doc = SimpleDocTemplate(self._fileDummy, pagesize=landscape(PDFSizes().PDFpagesizes[pagesize]))
            else:
                self._doc = SimpleDocTemplate(self._fileDummy, pagesize=PDFSizes().PDFpagesizes[pagesize])

        if title is not None:
            self._doc.title = title

        if story is not None:
            self._story = story
        else:
            # create a new story with a spacer which take all the first page
            # then the first page is only drawing by the firstPage method
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
        """Set the first page of the document.

        This function is called by doc.build method for the first page.
        """

    def laterPages(self, c, doc):
        """Set the layout of the page after the first.

        This function is called by doc.build method one each page after the first.
        """

    def getBody(self, story=None):
        """Add the content to the story."""

    def getPDFBin(self):
        # build the pdf in the fileDummy
        self.getBody()
        self._doc.build(self._story, onFirstPage=self.firstPage, onLaterPages=self.laterPages)
        # return the data from the fileDummy
        return self._fileDummy.getvalue()

    def _drawWrappedString(self, c, text, font='Times-Bold', size=30, color=(0, 0, 0), align='center', width=None,
                           height=None, measurement=cm, lineSpacing=1, maximumWidth=None):
        if maximumWidth is None:
            maximumWidth = self._PAGE_WIDTH-1*cm
        if width is None:
            width = self._PAGE_WIDTH/2.0
        if height is None:
            height = self._PAGE_HEIGHT-10*measurement
        draw = c.drawCentredString
        if align == 'right':
            draw = c.drawRightString
        elif align == 'left':
            draw = c.drawString
        c.setFont(font, size)
        c.setFillColorRGB(*color)
        titleWords = text.split()
        line = ''
        for word in titleWords:
            lineAux = f'{line} {word}'
            lsize = c.stringWidth(lineAux, font, size)
            if lsize < maximumWidth:
                line = lineAux
            else:
                draw(width, height, line)
                height -= lineSpacing*measurement
                line = word
        if line.strip():
            draw(width, height, line)
        return height

    def _drawLogo(self, c, drawTitle=True):
        from indico.modules.events.util import create_event_logo_tmp_file
        logo = self.event.logo
        imagePath = ''
        if logo:
            imagePath = create_event_logo_tmp_file(self.event)
        if imagePath:
            try:
                img = PILImage.open(imagePath)
                width, height = img.size

                # resize in case too big for page
                if width > self._PAGE_WIDTH / 2:
                    ratio = float(height)/width
                    width = self._PAGE_WIDTH / 2
                    height = width * ratio
                startHeight = self._PAGE_HEIGHT

                if drawTitle:
                    startHeight = self._drawWrappedString(c, escape(self.event.title), height=self._PAGE_HEIGHT - inch)

                # lower edge of the image
                startHeight = startHeight - inch / 2 - height

                # draw horizontally centered, with recalculated width and height
                c.drawImage(imagePath, self._PAGE_WIDTH/2.0 - width/2, startHeight, width, height, mask='auto')
                return startHeight
            except OSError:
                if drawTitle:
                    self._drawWrappedString(c, escape(self.event.title), height=self._PAGE_HEIGHT - inch)
        return 0
