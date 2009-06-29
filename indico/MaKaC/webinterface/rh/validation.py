import new

import MaKaC.webinterface.rh.base as base

try:
    import tidy
    import libxml2
except:
    raise Exception("Can't load tidy or libxml2! If you want HTML validation, install them please.")
    import libxml2

def newFilter(self, res):
    return addToDocument(res)

def addToDocument(html):
                        
    options = dict(output_html=1, 
                   add_xml_decl=1, 
                   indent=1, 
                   tidy_mark=1)
    
    try:
        document = tidy.parseString(html,**options)
        document = addTidyErrors(document)
        
    except libxml2.parserError:
        return textFormatTidyMessages(document.errors)
    
    
    
    return document

def textFormatTidyMessages(messages):

    list = "UNABLE TO GENERATE HTML:\n\n"
    
    for message in messages:
        list += str(message) + '\n'
        
    return list


def formatTidyMessages(nDiv, messages):
        
    list = nDiv.newChild(None,'ul',None)

    for message in messages:
        list.newChild(None,'li',str(message))
        
    return list
    
def addTidyErrors(document):        
        
    doc =  libxml2.htmlParseDoc(str(document),None)      
    
    root = doc.children
    root = root.next.children #<html>
    
    body = root.next # <body>
    
   
    nDiv = body.newChild(None, 'div',None)
    nDiv.newNsProp(None,'class','UITidyDialog')
    
    nDiv.newChild(None,'h1','libtidy Output')
    formatTidyMessages(nDiv, document.errors)
    
    html = str(doc.serialize())
    
    doc.freeDoc()
    
    return html

# Overwrite the method in base.RH

method = new.instancemethod(newFilter, None, base.RH)
setattr(base.RH,'filter',method)
