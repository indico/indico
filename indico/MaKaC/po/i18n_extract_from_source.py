##
## This file is part of Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

import sys, re, os, glob, os.path, MaKaC
from MaKaC.common import Config
from i18nlib import i18nUtil
from os import system

#Indicate here top folders that can contain files needing any translation
list_folders_to_translate=[os.path.normpath(os.path.split(MaKaC.__file__)[0]) ]


# To find " _( )" tags, new lines and white spaces
_tag_re = re.compile(r'_\(\"(.*?)\"\)', re.M)
_halftag_re = re.compile(r'_\(\"(.*)')
_nl_re = re.compile('\n')
_ws_re = re.compile('\s+')

def quote(text):
    """Normalize and quote a string for inclusion in the po file."""    
    return text.\
           replace('\\', '\\\\').\
           replace('\n', '\\\\n').\
           replace('\t', '\\\\t').\
           replace('"',  '\\"')


def extract_from_files():
    """Extract translatable strings from the list of files read from
    potfiles_filename.  The files specified there are relative to
    dirname.
    """

    potfilepath = getPotFilePath()
    if os.path.exists(potfilepath):
        choice = chooseOneOf("File: '%s' exists do you want it to be overwritten?" % os.path.basename(potfilepath), ['y','Y','n','N'],False)
        if choice in ['n', 'N']:
            return

    # This list will contain all code files to examine
    file_list=[]
    for root_folder in list_folders_to_translate:
        root_folder.strip()
        if not root_folder or root_folder.startswith('#'):
            continue
        root_folder = root_folder.rstrip('\n')

        #Lists all Python and TPL files in MaKaC directory (given by MaKaCConfig)
        folder=root_folder
        for root, dirs, files, in os.walk(folder):
            # Don't recurse into CVS dirs (nor .svn dirs later perhaps?)
            if 'CVS' in dirs:
                dirs.remove('CVS')
            if '.svn' in dirs:
                dirs.remove('.svn')
            for file in files:
                if file[0] == '#':
                    pass
                elif file[-4:] == '.tpl' or file[-3:] == '.py':
                    file_list.append(os.path.join(root,file))

    # Extract messages from all files and fill db:
    db = {}
    util = i18nUtil()
    cwd = os.getcwd()
    for filename in file_list:
        if len(cwd) < len(filename) and os.path.normcase(cwd) == os.path.normcase(filename[:len(cwd)]):
            shortfilename = filename[len(cwd) + 1:]
        else:
            shortfilename = filename
        print ">> Processing '%s' <<" % (shortfilename)
        file = open(filename, 'r')
        strAndNb = []
        if filename[-3:] == '.py':
            strAndNb = util.getI18nStringsPY(file)
        else:
            strAndNb = util.getI18nStringsTPL(file)
    
        for (string, linenumber) in strAndNb:
            ref = '%s:%d' % (shortfilename, linenumber)

            # Discard withespace, as it is not taken into account later in the po file
            string = _ws_re.sub(' ', string.strip())

            # Format of db: ['word1':[ref1, ref2, ...],'word2':[ref1, ref2, ...],...]
            references = db.setdefault(string, [])
            references.append(ref)

    # Print .po header:
    potfile = open(potfilepath, 'w')
    potfile.write(r'''#
# This file is part of Indico.
# Copyright (C) 2007 CERN.
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
msgid ""
msgstr ""
"Project-Id-Version: Indico 0.7\n"
"POT-Creation-Date: 2005-11-22 11:20+0100\n"
"PO-Revision-Date: 2005-11-22 11:20+0100\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: pygettext.py 1.5\n"
''')

    # Print db content in .po file:
    for original, refs in db.items():
        # Print all references to occurences of this string
        for ref in refs:
            occurence="#: %s" % ref
            potfile.write("\n" + occurence)

        original_message='msgid "%s"' % quote(original)
        potfile.write("\n" + original_message)
        translated_message = 'msgstr ""'
        potfile.write("\n" + translated_message + "\n")

    print "Wrote '%s'" % potfilepath

def getPotFilePath():
    return os.path.join(os.getcwd(),'messages.pot')

def getLocaleDir(): 
    return os.path.join(os.path.dirname(__file__), 'locale')

def getLanguages():
    localedir = getLocaleDir()
    return map(lambda x: os.path.basename(x),glob.glob(os.path.join(localedir,'??_??')))

def chooseOneOf(question, choices, canCancel=True):
    choice = None
    while (not (choice in choices)) and (choice != '' or (not canCancel)):
        print '%s (%s):' % (question,','.join(choices))
        choice = raw_input()
    if choice == '':
        choice = None
    return choice
    
def getPoFileName(language):
    return os.path.join(os.path.join(getLocaleDir(),language),'LC_MESSAGES/messages.po')

def prepareTargetedPotFile(language):
    print "Importing existing strings for target language %s..." % language
    current_po_file = getPoFileName(language) 
    system('msgmerge "%s" messages.pot -o messages_%s.pot' % (current_po_file, language))
    print "Wrote 'messages_%s.pot'" % language

def askForTargetLanguage():
    language = chooseOneOf("There may be already translated strings disponible for your language, please choose a language in the following list, or answer with an empty string if you don't plan to use one of those", getLanguages())
    
    if language == None:
        print "No language choosen from the list"
        return []
    else:
        return [language]

def print_usage():
    print "Usage:"
    print "%s [options]" % os.path.basename(__file__)
    print "Options:"
    print "-h, --help: Display this help"
    print "-a, --all: Do the merge directly for all languages"

if __name__ == "__main__":
    if ('-h' in sys.argv) or ('--help' in sys.argv):
        print_usage()
    else:
        extract_from_files()
        target_languages = None
        if ('-a' in sys.argv) or ('--all' in sys.argv):
            target_languages = getLanguages()
        else:
            target_languages = askForTargetLanguage()
        for language in target_languages:
            prepareTargetedPotFile(language)

    
