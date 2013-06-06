import StringIO
import os, sys, re, types

from zope.interface import Interface, interface

import conf

PATH = '../../../indico/'

from MaKaC import common
from indico.core.extpoint import IListener, IContributor


def iterate_sources(dir, exclude=[]):
    """
    iterates through all *.py files inside a dir, recursively
    """
    for dirname, dirnames, filenames in os.walk(dir):
        for filename in filenames:
            relDir = os.path.relpath(dirname, dir)

            cont = False
            for exc in exclude:
                if relDir.startswith(exc):
                    cont = True

            if cont:
                continue

            m = re.match(r'^(.*)\.py$', filename)
            if m:
                name = m.group(1)
                rel = os.path.relpath(dirname, dir).split('/')
                if rel == ['.']:
                    yield 'indico'
                elif name == '__init__':
                    yield '.'.join(['indico'] + rel)
                else:
                    yield '.'.join(['indico'] + rel + [name])


def docsFor(mod, iface, content):
    path = "%s.%s" % (mod, iface.__name__)
    content.write(""".. autointerface:: %s\n""" % path)


def _rst_title(text, char='='):
   return "%s\n%s\n%s\n" % (char * len(text), text, char * len(text))


def gatherInfo(mod, content):

    first = True

    for elem, val in mod.__dict__.iteritems():

        if type(val) == interface.InterfaceClass:
            if val.__module__ == mod.__name__ and \
                   (val.extends(IListener) or val.extends(IContributor)):
                if first:
                    content.write(_rst_title(mod.__name__, char='-'))
                    content.write(""".. automodule:: %s\n""" % mod.__name__)
                    first = False

                if val.extends(IListener):
                    docsFor(mod.__name__, val, content)
                elif val.extends(IContributor):
                    docsFor(mod.__name__, val, content)


def main(fname):
    """
    main function
    """

    content = StringIO.StringIO()

    content.write(_rst_title("Listener/Contributor API"))

    for f in iterate_sources(PATH, exclude=["MaKaC/po"]):
        #        try:
        try:
            mod = __import__(f)
            for pelem in f.split('.')[1:]:
                mod = getattr(mod, pelem)
                gatherInfo(mod, content)
        except ImportError:
            sys.stderr.write("Import of '%s' failed!\n" % f)

    with open(fname, 'w') as fd:
        fd.write(content.getvalue())

    content.close()

if __name__ == '__main__':
    main(sys.argv[1])
