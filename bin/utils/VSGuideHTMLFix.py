from HTMLParser import HTMLParser
import htmlentitydefs
import os


class MyHTMLParser(HTMLParser):
    
    def __init__(self):
        HTMLParser.__init__(self)
        
    def process(self, target):
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
        
            attrs['style'] = attrs.pop('style','') + ";text-align: center;"
            
        if tag.lower() == 'p' and ('align' in attrs and attrs['align'].lower() == 'center' or 'ALIGN' in attrs and attrs['ALIGN'].lower() == 'center'):
            attrs.pop('align','')
            attrs.pop('ALIGN','')
            attrs['style'] = attrs.pop('style','') + ";text-align: center;"
        
        return tag, attrs
        
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'style':
            self._inStyleTag = True
        tag, attrs = MyHTMLParser._processAttrs(tag, attrs)
        strattrs = "".join([' %s="%s"' % (key, value) for key, value in attrs.iteritems()])
        self._out.write("<%s%s>\n" % (tag, strattrs))
        
    def handle_startendtag(self, tag, attrs):
        tag, attrs = MyHTMLParser._processAttrs(tag, attrs)
        strattrs = "".join([' %s="%s"' % (key, value) for key, value in attrs])
        self._out.write("<%s%s />\n" % (tag, strattrs))
        
    def handle_endtag(self, tag):
        if tag.lower() == 'style':
            self._inStyleTag = False
        self._out.write("</%s>\n" % tag)
        
    def handle_data(self, text):
        if self._inStyleTag:
            iPStyle1 = text.find("P {")
            iPStyle2 = text.find("p {")
            iPStyle3 = text.find("P{")
            iPStyle4 = text.find("p{")
            iPStyle = max(iPStyle1, iPStyle2, iPStyle3, iPStyle4)
            endIPStyle = text.find('}', iPStyle)
            self._out.write(text[:endIPStyle])
            self._out.write(';margin: 0; padding: 0;')
            self._out.write(text[endIPStyle:])
        else:
            self._out.write("%s" % text)
        
    def handle_comment(self, comment):
        import pydevd;pydevd.settrace()
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
    p.process("/home/dmartinc/Dropbox/PFC/video services user guide/export/Indico VS Guide - Normal User/Indico VS Guide - Normal User.html")
    p.process("/home/dmartinc/Dropbox/PFC/video services user guide/export/Indico VS Guide - Event Manager/Indico VS Guide - Event Manager.html")
    p.process("/home/dmartinc/Dropbox/PFC/video services user guide/export/Indico VS Guide - VS Admin/Indico VS Guide - VS Admin.html")
    p.process("/home/dmartinc/Dropbox/PFC/video services user guide/export/Indico VS Guide - Server Admin/Indico VS Guide - Server Admin.html")