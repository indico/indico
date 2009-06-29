# -*- coding: utf-8 -*-

"""Contains internationalization subsystem
"""
import re,os.path
import gettext, locale
import operator

# TODO: Use a standard library for this, possibly pycountry
# note that pycountry imports lxml, and libxml2 doesn't seem to like that
languageNames = {
    'en_US': 'English (USA)',
    'fr_FR': 'Français (France)'
    }

r = re.compile(r'_\(\"(.*?)\"\)')
__ = None
Lan= None
LangList = None

def _(txt):
    #f = file("c:/log.log", 'a')
    #txtori = txt
    global __
    if not __:
        install('messages', "en_US", unicode=True)
    res=[]
    deb=""
    l = r.findall(txt)
    if not l:
        #f.write("%s : %s\n"%(txt, Lan.gettext(txt)))
        #f.close()
        return Lan.gettext(txt)
    for i in l:
        deb, txt = txt.split("_(\""+i+"\")",1)
        res.append(deb)
        res.append(Lan.gettext(i))
    res.append(txt)
    #f.write("%s : %s\n"%(txtori, "".join(res)))
    #f.close()
    return "".join(res)

def install(name, lang, unicode, localedir=None):
    global __
    global Lan
    global LanName
    if localedir is None:
        import MaKaC
        localedir=os.path.join(os.path.split(MaKaC.__file__)[0],"po","locale")

    # set date&time too
    try:
        locale.setlocale(locale.LC_TIME, "%s.utf8" % lang)
    except:
        # TODO: look for a fix for this
        # locales in windows have different names
        pass
    
    gettext.install(name, localedir, unicode)
    try:
        Lan = gettext.translation("messages", localedir, languages=[lang])
        LanName = lang
    except Exception, e:
        raise "Can't find the messages.mo for the language ID %s\n%s"%(lang,e)
    Lan.install()
    __ = True

def langList():
    global LangList
#    if LangList is None:
#        localedir=os.path.join(os.path.normpath(os.path.split(MaKaC.__file__)[0]),"po","locale")
#        LangList=os.listdir(localedir)
#        ##to remove the hidden folder CVS (in locale) so that it does not appear in the languages list
#        try:
#            LangList.remove('CVS')
#        except:
#            pass
    # TODO: this is a hack to get just english and french:
    LangList = languageNames.keys()
    restranslated=[]

    #langName = LanName.split('_')[0]

    for language in LangList:       
        restranslated.append((language, languageNames[language]))
    restranslated=sorted(restranslated,key=operator.itemgetter(1))
    return restranslated
