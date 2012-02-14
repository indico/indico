# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

"""
String manipulation functions
"""

import unicodedata


def unicodeOrNone(string):
    return None if string == None else string.decode('utf-8')


def remove_accents(text):
    if not isinstance(text, unicode):
        text = text.decode('utf8')
    return ''.join((c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn'))


def remove_non_alpha(text):
    return ''.join(c for c in text if c.isalnum())

def html_line_breaks(text):
    return '<p>' + text.replace('\n\n', '</p><p>').replace('\n', '<br/>') + '</p>'
