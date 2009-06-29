import os
from i18nlib import i18nUtil
from shutil import copyfile, copyfileobj
from os.path import exists, join
import re
import sys

re_python_file = re.compile('.py\Z')
re_tpl_file =re.compile('.tpl\Z')

def convertAll(folder, dont_use_default=False, always_ask=False):
    converter = i18nUtil()
    currentfile = None
    filein = None
    fileout = None
    try:
        for root, dirs, files in os.walk(folder):
            if 'CVS' in dirs:
                dirs.remove('CVS')
            if '.svn' in dirs:
                dirs.remove('.svn')
            for file in files:
                currentfile = join(root, file)
                if re.search(re_python_file,file):
                    print ">> Internationalization of '%s' <<" % (currentfile)
                    tmpfile = currentfile + '.bak'
                    if exists(tmpfile):
                        print "\tBackup file found, skipping!"
                    else:
                        copyfile(currentfile, tmpfile)
                        filein = open(tmpfile, 'r')
                        fileout = open(currentfile, 'w')
                        converter.convertPY(filein, fileout, True,False,always_ask,dont_use_default)
                        fileout.close()
                        filein.close()
                elif re.search(re_tpl_file, file):
                    print ">> Internationalization of '%s' <<" % (currentfile)
                    tmpfile = currentfile + '.bak'
                    if exists(tmpfile):
                        print "\tBackup file found, skipping"
                    else:
                        copyfile(currentfile, tmpfile)
                        filein = open(tmpfile, 'r')
                        fileout = open(currentfile, 'w')
                        converter.convertTPL(filein, fileout, True,False, always_ask, dont_use_default)
                        fileout.close()
                        filein.close()
    except KeyboardInterrupt, e:
        if filein:
            filein.close()
        if fileout:
            fileout.close()
        if currentfile != None:
            tmpname = currentfile + '.bak'
            if exists(tmpname):
                tmpfile = open(tmpname,'r')
                torestore = open(currentfile, 'w')
                copyfileobj(tmpfile, torestore)
                tmpfile.close()
                torestore.close()
                os.remove(tmpname)
            
if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "Please specify a folder from where to convert the files"
        print "Usage:"
        print "%s folders... [options]" % os.path.basename(sys.argv[0])
        print "Options:"
        print "-a, --always_ask : Never directly suppose you will say no because you did so in the past"
        print "-n, --no-defaults : Don't propose guessed answers based on previous choices"
    dont_use_default = ('--no-defaults' in sys.argv) or ('-n' in sys.argv)
    always_ask = ('--always-ask' in sys.argv) or ('-a' in sys.argv)
    for arg in sys.argv[1:]:
        if arg[:2] != "--":
            convertAll(arg,dont_use_default, always_ask)
