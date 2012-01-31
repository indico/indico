# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

## WARNING: THE FOLLOWING LINE WILL BE OVERWRITTEN AT INSTALLATION TIME
indico_conf = "" # path to indico.conf
##

import os

if indico_conf == '': # we may be in development mode or in installation mode
    indico_conf = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'etc', 'indico.conf')
    if not os.path.exists(indico_conf):
        # eggmode
        indico_conf = os.path.join(os.path.dirname(__file__), '..', '..', 'etc', 'indico.conf.sample')
    if not os.path.exists(indico_conf):
        indico_conf = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'etc', 'indico.conf.sample')

print indico_conf

execfile(indico_conf)

FileTypes = {"DOC":  ["Ms Word","application/msword","word_big.png"],
             "DOCX":  ["Ms Word","application/vnd.openxmlformats-officedocument.wordprocessingml.document","word.png"],
             "WAV":  ["Audio","audio/x-pn-wav",""],
             "XLS":  ["MS Excel","application/vnd.ms-excel","xls.png"],
             "XLSX":  ["MS Excel","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","xls.png"],
             "PS":   ["PostScript","application/postscript","ps.png"],
             "SXC":  ["Open Office Calc","application/vnd.sun.xml.calc","calc.png"],
             "TAR":  ["Tar File","application/tar","zip.png"],
             "ODP":  ["Open Documents Presentation","application/vnd.sun.xml.impress","impress.png"],
             "SXI":  ["Open Office Impress","application/vnd.sun.xml.impress","impress.png"],
             "ODS":  ["Open Office Spreadsheet","application/vnd.sun.xml.calc","calc.png"],
             "ODT":  ["Open Document Text","application/vnd.sun.xml.writer","writer.png"],
             "HTML": ["HTML","text/html",""],
             "PPT":  ["Ms Powerpoint","application/vnd.ms-powerpoint","powerpoint.png"],
             "PPTX":  ["Ms Powerpoint","application/vnd.openxmlformats-officedocument.presentationml.presentation","powerpoint.png"],
             "RM":   ["Real Video","application/vnd.rn-realmedia",""],
             "TXT":  ["Plain Text","text/plain","txt.png"],
             "XML":  ["XML","text/xml",""],
             "ZIP":  ["ZIP","application/zip",""],
             "SXW":  ["Open Office Writer","application/vnd.sun.xml.writer","writer.png"],
             "GZ":   ["Zipped File","application/zip","zip.png"],
             "ICAL": ["ICAL","text/calendar",""],
             "PDF":  ["Portable Document Format","application/pdf","pdf_small.png"],
             "CSV":  ["Ms Excel","application/vnd.ms-excel","excel.png"],
             "HTM":  ["HTML","text/html",""],
             "OGV":  ["Ogg/Theora Video","application/ogg",""],
             "MOV":  ["Quicktime Video","video/quicktime",""],
             "RTF":  ["RTF","application/rtf",""],
             "OGG":  ["Ogg/Theora Video","application/ogg",""],
             "RSS":  ["RSS","application/xhtml+xml",""],
             "MHT":  ["MHT", " message/rfc822", ""],
             "JPG":  ["JPEG Image","image/jpeg",""],
             "PNG":  ["PNG Image","image/png",""],
             "GIF":  ["GIF Image","image/gif",""],
             "TIFF":  ["TIFF Image","image/gif",""],
             "ATOM": ['Atom', "application/atom+xml", ""]
             }
