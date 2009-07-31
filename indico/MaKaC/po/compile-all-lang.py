import os, sys

# Accepts --quiet and --basedir somedir

debug = ('--quiet' in sys.argv or '-q' in sys.argv)

if '--basedir' in sys.argv:
    basedir = sys.argv['--basedir']
else:
    basedir = os.getcwd()
    
if debug:
    print "Compiling .po files:"

prevdir = os.getcwd()
    
for root, dir, files in os.walk(basedir):
    if root.endswith("LC_MESSAGES"):
        try:
            os.chdir(root)
            os.system("msgfmt messages.po -o messages.mo")
            if debug:
                print "Compiled " + os.path.join(root,"messages.po")
            
        except Exception, e:
            if debug:
                print "[lang=%s] %s" % (root, e)

os.chdir(prevdir)

if debug:
    print "Finished compiling .po files"
