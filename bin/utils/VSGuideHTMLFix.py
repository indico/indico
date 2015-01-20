# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

""" Simple script to parse and do some corrections HTML exported by the source OpenOffice documents
    used to produce the Video Services guides.

    It assumes you are using it from indico's bin directory in development mode.
    If this isn't right, please change the 'ihelppath' variable and the end of this file.
"""

from HTMLParser import HTMLParser
import htmlentitydefs
import os


class MyHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)

    def process(self, target):
        if not os.path.exists(target):
            print 'Could not find file: ' + target
            return
        self.reset()
        self._inStyleTag = False
        outName = target + '.tmp'
        self._out = file(outName, 'w')
        self.feed(file(target).read())
        self._out.close()
        os.remove(target)
        os.rename(outName, target)
        self.close()

    @classmethod
    def _processAttrs(cls, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == 'img':
            attrs.pop('height','')
            attrs.pop('HEIGHT','')
            attrs.pop('width','')
            attrs.pop('WIDTH','')

            if not 'style' in attrs or attrs['style'].find('text-align: center') == -1:
                attrs['style'] = attrs.pop('style','') + ";text-align: center;"

        if tag.lower() == 'p' and ('align' in attrs and attrs['align'].lower() == 'center' or 'ALIGN' in attrs and attrs['ALIGN'].lower() == 'center'):
            attrs.pop('align','')
            attrs.pop('ALIGN','')
            if not 'style' in attrs or attrs['style'].find('text-align: center') == -1:
                attrs['style'] = attrs.pop('style','') + ";text-align: center;"

        return tag, attrs

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'style':
            self._inStyleTag = True
        tag, attrs = MyHTMLParser._processAttrs(tag, attrs)
        strattrs = "".join([' %s="%s"' % (key, value) for key, value in attrs.iteritems()])
        self._out.write("<%s%s>" % (tag, strattrs))

    def handle_startendtag(self, tag, attrs):
        tag, attrs = MyHTMLParser._processAttrs(tag, attrs)
        strattrs = "".join([' %s="%s"' % (key, value) for key, value in attrs])
        self._out.write("<%s%s />" % (tag, strattrs))

    def handle_endtag(self, tag):
        if tag.lower() == 'style':
            self._inStyleTag = False
        self._out.write("</%s>" % tag)

    def handle_data(self, text):
        if self._inStyleTag:
            iPStyle1 = text.find("P {")
            iPStyle2 = text.find("p {")
            iPStyle3 = text.find("P{")
            iPStyle4 = text.find("p{")
            iPStyle = max(iPStyle1, iPStyle2, iPStyle3, iPStyle4)
            endIPStyle = text.find('}', iPStyle)
            self._out.write(text[:endIPStyle])
            if not text[:endIPStyle].endswith(';margin: 0; padding: 0;'):
                self._out.write(';margin: 0; padding: 0;')
            self._out.write(text[endIPStyle:])
        else:
            self._out.write("%s" % text)

    def handle_comment(self, comment):
        self._out.write("<!-- %s -->\n" % comment)

    def handle_entityref(self, ref):
        self._out.write("&%s" % ref)
        if htmlentitydefs.entitydefs.has_key(ref):
            self._out.write(";")

    def handle_charref(self, ref):
        self._out.write("&#%s;" % ref)

    def handle_pi(self, text):
        self._out.write("<?%s>" % text)

    def handle_decl(self, text):
        self._out.write("<!%s>" % text)


if __name__ == "__main__":
    p = MyHTMLParser()
    ihelpPath = "../../indico/htdocs/ihelp/"
    p.process(ihelpPath + "VideoServices/IndicoUserGuide_VS/index.html")
    p.process(ihelpPath + "VideoServices/EventManagerUserGuide_VS/index.html")
    p.process(ihelpPath + "VideoServices/ServerAdminUserGuide_VS/index.html")
    p.process(ihelpPath + "VideoServices/VSAdminUserGuide_VS/index.html")
