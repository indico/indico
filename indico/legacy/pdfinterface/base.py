# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
from importlib.resources import as_file, files
from xml.sax import saxutils  # noqa: S406

from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from indico.util.string import sanitize_for_platypus


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


_reportlab_fonts_initialized = False


def init_reportlab_fonts():
    global _reportlab_fonts_initialized  # noqa: PLW0603
    if _reportlab_fonts_initialized:
        return
    _reportlab_fonts_initialized = True
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
