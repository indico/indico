#<inheritanceGraph.py>

"""
Draw inheritance hierarchies via Dot (http://www.graphviz.org/)
Author: Michele Simionato
E-mail: mis6@pitt.edu
Modified by: David Martin Clavo
Date: August 2003
License: Python-like
Requires: Python 2.3, dot, standard Unix tools
"""

"""
INSTRUCTIONS ON HOW TO USE THIS SCRIPT:
-go to the 'test hierarchy' method and modify the 'classList' variable.
You can add the classes one by one or make a method that appends a subset of classes
(like loadRHClasses, loadServiceClasses that are done already; they are a good example).
-play with the parameters in the 'if __name__=="__main__":' part to change the filename
where the diagram is exported (can be .ps or .png), colors, etc.
"""

import os,itertools,types

PSVIEWER='gnome-open'     # you may change these with
PNGVIEWER='gnome-open' # your preferred viewers
PSFONT='Times'    # you may change these too
PNGFONT='Courier' # on my system PNGFONT=Times does not work

def if_(cond,e1,e2=''):
    "Ternary operator would be"
    if cond: return e1
    else: return e2

def MRO(cls):
    "Returns the MRO of cls as a text"
    out=["MRO of %s:" % cls.__name__]
    for counter,c in enumerate(mro_old_classes(cls)):
        name=c.__name__
        bases=','.join([b.__name__ for b in c.__bases__])
        s="  %s - %s(%s)" % (counter,name,bases)
        if type(c) is not type: s+="[%s]" % type(c).__name__
        out.append(s)
    return '\n'.join(out)

def merge(seqs):
    #print '\n\nCPL[%s]=%s' % (seqs[0][0],seqs),
    res = []; i=0
    while 1:
        nonemptyseqs=[seq for seq in seqs if seq]
        if not nonemptyseqs: return res
        i+=1; #print '\n',i,'round: candidates...',
        for seq in nonemptyseqs: # find merge candidates among seq heads
            cand = seq[0]; #print ' ',cand,
            nothead=[s for s in nonemptyseqs if cand in s[1:]]
            if nothead: cand=None #reject candidate
            else: break
        if not cand: raise "Inconsistent hierarchy"
        res.append(cand)
        for seq in nonemptyseqs: # remove cand
            if seq[0] == cand: del seq[0]


def mro_old_classes(C):
    "Compute the class precedence list (mro) according to C3"
    return merge([[C]]+map(mro_old_classes,C.__bases__)+[list(C.__bases__)])


class MROgraph(object):
    def __init__(self,classes,**options):
        "Generates the MRO graph of a set of given classes."
        if not classes: raise "Missing class argument!"
        filename=options.get('filename',"MRO_of_%s.ps" % classes[0].__name__)
        self.labels=options.get('labels',2)
        caption=options.get('caption',False)
        setup=options.get('setup','')
        name,dotformat=os.path.splitext(filename)
        format=dotformat[1:]
        fontopt="fontname="+if_(format=='ps',PSFONT,PNGFONT)
        nodeopt=' node [%s];\n' % fontopt
        edgeopt=' edge [%s];\n' % fontopt
        viewer=if_(format=='ps',PSVIEWER,PNGVIEWER)
        self.textrepr='\n'.join([MRO(cls) for cls in classes])
        caption=if_(caption,
                   'caption [shape=box,label="%s\n",fontsize=9];'
                   % self.textrepr).replace('\n','\\l')
        setupcode=nodeopt+edgeopt+caption+'\n'+setup+'\n'
        codeiter=itertools.chain(*[self.genMROcode(cls) for cls in classes])
        codeiter=list(set(codeiter))
        self.dotcode='digraph %s{\n%s%s}' % (
            name,setupcode,'\n'.join(codeiter))
        os.system("echo '%s' | dot -T%s > %s; %s %s&" %
              (self.dotcode,format,filename,viewer,filename))
    def genMROcode(self,cls):
        "Generates the dot code for the MRO of a given class"
        for mroindex,c in enumerate(mro_old_classes(cls)):
            name=c.__name__
            manyparents=len(c.__bases__) > 1
            if c.__bases__:
                yield ''.join([
                    ' edge [style=solid]; %s -> %s %s;\n' % (
                    b.__name__,name,if_(manyparents and self.labels==2,
                                        '[label="%s"]' % (i+1)))
                    for i,b in enumerate(c.__bases__)])
            if manyparents:
                yield " {rank=same; %s}\n" % ''.join([
                    '"%s"; ' % b.__name__ for b in c.__bases__])
            number=if_(self.labels,"%s-" % mroindex)
            label='label="%s"' % (number+name)
            option=if_(issubclass(cls,type), # if cls is a metaclass
                       '[%s]' % label,
                       '[shape=box,%s]' % label)
            yield(' %s %s;\n' % (name,option))
            #if type(c) is not type: # c has a custom metaclass
            #    metaname=type(c).__name__
            #    yield ' edge [style=dashed]; %s -> %s;' % (metaname,name)
    def __repr__(self):
        "Returns the Dot representation of the graph"
        return self.dotcode
    def __str__(self):
        "Returns a text representation of the MRO"
        return self.textrepr

def loadClasses(module, filter, classList):
    for className in module.__dict__.keys():
        if filter(className):
            classList.append(module.__dict__[className])

def loadRHClasses(classList):
    import MaKaC.webinterface.rh.base as base
    loadClasses(base, lambda className : className.startswith("RH"), classList)

    import MaKaC.webinterface.rh.conferenceBase as conferenceBase
    loadClasses(conferenceBase, lambda className : className.startswith("RH"), classList)

    import MaKaC.webinterface.rh.conferenceDisplay as conferenceDisplay
    loadClasses(conferenceDisplay, lambda className : className.startswith("RH") and className.count("Base"), classList)

    import MaKaC.webinterface.rh.conferenceModif as conferenceModif
    loadClasses(conferenceModif, lambda className : className.startswith("RH") and className.count("Base"), classList)

    import MaKaC.webinterface.rh.reviewingModif as reviewingModif
    loadClasses(reviewingModif, lambda className : className.startswith("RH") and className.count("Base"), classList)

    import MaKaC.webinterface.rh.contribMod as contribMod
    loadClasses(contribMod, lambda className : className.startswith("RH") and className.count("Base"), classList)

    import MaKaC.webinterface.rh.contribReviewingModif as contribReviewingModif
    loadClasses(contribReviewingModif, lambda className : className.startswith("RH") and className.count("Base"), classList)

def isClass(obj):
    return type(obj) == type or type(obj) == types.ClassType

def loadServiceClasses(classList):
    import MaKaC.services.interface.rpc.common as common
    loadClasses(common, lambda className : isClass(common.__dict__[className]) and
                (className.count("Base") or className.count("Service")), classList)

    import MaKaC.services.implementation.conference as conference
    loadClasses(conference, lambda className : isClass(conference.__dict__[className]) and
                (className.count("Base") or className.count("Service")), classList)

def testHierarchy(**options):
    from MaKaC.services.implementation.conference import ConferenceTitleModification
    from MaKaC.services.implementation.reviewing import ContributionReviewingDueDateModification
    from MaKaC.services.implementation.schedule import ConferenceSetSessionSlots
    classList = [ConferenceTitleModification, ContributionReviewingDueDateModification, ConferenceSetSessionSlots]

    loadServiceClasses(classList)

    return MROgraph(classList,**options)

if __name__=="__main__":
    colors='edge [color=blue]; node [color=red];'
    g=testHierarchy(filename='A.ps',caption=False,\
        setup='size="6,4"; ratio=0.7; '+colors)

#</inheritanceGraph.py>