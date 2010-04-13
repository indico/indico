##
## This file is part of Indico.
## Copyright (C) 2008 CERN.
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.


"""
This tool extracts sentences to be translated from source
files.

The sentences to translate are marked with the following tag:

 Blah blah " _("To be translated") " blah.

These tags can span several lines. Extra whitespace is discarded. 
"""

import sys, re, os, glob, os.path, shutil, MaKaC
import MaKaC.common.MaKaCConfig as MaKaCConfig
from i18nlib import i18nUtil
from os import system
from i18n_extract_from_source import *


def install_pot_file(filename):
    print ">> Installing .pot file '%s' <<" % (filename)
    lang = chooseOneOf("Choose target language for '%s'" % filename, getLanguages())
    if lang == None:
        print "No target language choosen"
    else:
        print "Installing '%s', to target language %s" % (filename, lang)
        shutil.copy(filename, getPoFileName(lang))
        print "Done"

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        print "Usage: %s potfile" % (os.path.basename(sys.argv[0]))
    else:
        for arg in args:
            install_pot_file(arg)
   
