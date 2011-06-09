from MaKaC.common.db import DBMgr
from MaKaC.conference import ConferenceHolder
from indico.util.console import conferenceHolderIterator

dbi = DBMgr.getInstance()
dbi.startRequest()

ENCODINGS = ['Windows-1252', 'iso-8859-1', 'latin1']

def fix(getter, setter):
    txt = getter()
    print "fixing... ",
    for encoding in ENCODINGS:
        try:
            utxt = txt.decode(encoding)
            print encoding
            setter(utxt.encode('utf-8'))
            return
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
    print "error! %s" % repr(txt)

with dbi.transaction() as conn:
    i = 0
    for level, conf in conferenceHolderIterator(ConferenceHolder(), deepness='event', verbose=False):
        try:
            conf.getTitle().decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            print '\r%s title' % conf
            fix(conf.getTitle, conf.setTitle)

        try:
            conf.getDescription().decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            print '\r%s description' % conf
            fix(conf.getDescription, conf.setDescription)

        if i % 999 == 0:
            dbi.commit()
        i += 1
