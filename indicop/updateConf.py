'''Modifies the location of indico.conf referenced inside makacconfigpy_path to
point to indico_conf_path'''
import os
import re
fdata = open(os.path.join('indico', 'MaKaC', 'common', 'MaKaCConfig.py')).read()
fdata = re.sub('indico_conf[ ]*=[ ]*[\'"]{1}([^\'"]*)[\'"]{1}', "indico_conf = \"%s\"" % os.path.join('etc', 'indico.conf'), fdata)
open(os.path.join('indico', 'MaKaC', 'common', 'MaKaCConfig.py'), 'w').write(fdata)
