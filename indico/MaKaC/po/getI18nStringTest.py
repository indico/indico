#python -u

import sys
from i18nlib import i18nUtil

i = i18nUtil()
for arg in sys.argv[1:]:
    f = open(arg,'r')
    print i.getI18nStringsPY(f)
    f.close()

if len(sys.argv) == 1:
    print "Please specify at least one file where to look for i18n'ed strings"
