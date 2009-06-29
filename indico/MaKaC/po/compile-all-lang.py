import os, sys

compiler="msgfmt"

# If --quiet is set we should not produce any output. This is used in code/setup.py
output = True
if '--quiet' in sys.argv or '-q' in sys.argv:
    output = False
    
if output:
    print "Compiling .po files:"

pwd = os.getcwd()
    
for root, dir, files in os.walk(pwd):
    if root.endswith("LC_MESSAGES"):
        try:
            os.chdir(root)
            os.system("%s messages.po -o messages.mo" % (compiler))
            if output:
                print "Compiled " + os.path.join(root,"messages.po")
            
        except Exception, e:
            if output:
                print "[lang=%s] %s" % (root, e)
        os.chdir(pwd)

if output:
    print "Finished compiling .po files"
