# -*- coding: utf-8 -*-
##
## $Id: TemplateExec.py,v 1.39 2009/05/19 16:53:58 pferreir Exp $
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
from MaKaC.user import Avatar

"""
Part of Room Booking Module (rb_)
Responsible: Piotr Wlodarek
"""

import sys, os, string, StringIO, traceback
import MaKaC
from MaKaC.common.Configuration import Config
from MaKaC.errors import MaKaCError
from MaKaC.common.utils import formatDateTime, formatDate, formatTime
from MaKaC.common import Config
import MaKaC.common.info as info




ERROR_PATH = Config.getInstance().getTempDir()

class TemplateExecException( Exception ):

    def __init__( self, value ):
        self.value = value
        if hasattr(value, 'template_tracebacks'):
            self.template_tracebacks = value.template_tracebacks
        if hasattr(value, 'problematic_templates'):
            self.problematic_templates = value.problematic_templates

    def __str__(self):
        s = str( type(self.value).__name__) + ": " + str(self.value )
        if s[-1] != "}":

            if hasattr(self, 'problematic_templates'):
                s += """ - - - -> {Python code generated from templates is available in %s/%s.tpl.error.py""" % ( ERROR_PATH, self.problematic_templates[0])

                for template_name in self.problematic_templates[1:]:
                    s += ", %s/%s.py"%(ERROR_PATH, template_name)
                s += " file(s)}"

        return s

def declareTemplate(newTemplateStyle=False):

    objDict = globals()['_objDict']
    objDict['newTemplateStyle'] = newTemplateStyle

def includeTpl( tplFileName, *args, **kwargs ):
    """
    Use:
    <% includeTpl( 'TemplateName', paramA = 2, paramB = 3 ) %>
    """

    # Resurrect dictionary from globals - ugly hack.
    # In the recurrent exec, we still need an old dictCopy.
    # This old dictCopy is resurrected from the global scope.
    objDict = globals()['_dictCopy']
    for k, v in kwargs.iteritems():
        objDict[k] = v
    objDict["isIncluded"] = True

    from MaKaC.webinterface import wcomponents
    result = wcomponents.WTemplated(tplFileName).getHTML(objDict)

    globals()['_objDict']["newTemplateStyle"] = True

    print( result.replace('%', '%%') )

def contextHelp( helpId ):
    """
    Allows you to put [?], the context help marker.
    Help content is defined in <div id="helpId"></div>.
    """
    includeTpl( 'ContextHelp', helpId = helpId, imgSrc = Config.getInstance().getSystemIconURL( "help" ) )

def inlineContextHelp( helpContent ):
    """
    Allows you to put [?], the context help marker.
    Help content passed as argument helpContent.
    """
    includeTpl( 'InlineContextHelp', helpContent = helpContent, imgSrc = Config.getInstance().getSystemIconURL( "help" ) )

def escapeAttrVal( s ):
    """
    Just escapes the apostrophes, new lines, etc.
    """
#    if s == None:
#        return None
#    s = s.replace( "'", r"\'" )
#    s = s.strip()
    from xml.sax.saxutils import quoteattr
    s = quoteattr( s )[1:-1]
    s = s.replace( "'", "`" )
    s = s.replace( "\"", "`" )
    s = s.replace( "\n", "" )
    s = s.replace( "\r", "" )
    s = s.replace( "&#13;", " " )
    s = s.replace( "&#10;", " " )
    return s

def verbose( s, default = "" ):
    """
    Purpose: avoid showing "None" to user; show default value instead.
    """
    if isinstance( s, bool ) and s != None:
        if s:
            return "yes"
        else:
            return "no"

    return s or default

def verbose_dt( dt, default = "" ):
    if dt == None:
        return default
    return ( "%s_%2s:%2s" % ( formatDate(dt.date()).replace(' ','_'), dt.hour, dt.minute ) ).replace( ' ', '0' ).replace( '_', ' ' )

def verbose_t( t, default = "" ):
    if t == None:
        return default
    return ( "%2d:%2d" % ( t.hour, t.minute ) ).replace( ' ', '0' )

def escape( s ):
    """HTML escape"""
    from xml.sax.saxutils import escape
    return escape( s )

def jsBoolean ( b ):
    if b:
        return 'true'
    else:
        return 'false'

def quoteattr( s ):
    """quotes escape"""
    from xml.sax.saxutils import quoteattr
    return quoteattr( s )

def roomClass( room ):
    if room.isReservable:
        roomClass = ""
    if not room.isReservable:
        roomClass = "privateRoom"
    if room.isReservable and room.resvsNeedConfirmation:
        roomClass = "moderatedRoom"
    return roomClass

def dequote( s ):
    if ( s.startswith( '"' ) or s.startswith( "'" ) ) and ( s.endswith( '"' ) or s.endswith( "'" ) ):
        return s[1:-1]
    return s

def linkify( s ):
    urlIxStart = s.find( 'http://' )
    if urlIxStart == -1:
        return s
    urlIxEnd = s.find( ' ', urlIxStart + 1 )
    s = s[0:urlIxStart] + '<a href="' + s[urlIxStart:urlIxEnd] + '">' + s[urlIxStart:urlIxEnd] + "</a> " + s[urlIxEnd:]
    return s

def deepstr(obj):
    """ obj is any kind of object
        This method will loop through the object and turn objects into strings through their __str__ method.
        If a list or a dictionary is found during the loop, a recursive call is made.
        However this method does not support objects that are not lists or dictionaries.
        Author: David Martin Clavo
    """

    # stringfy objects inside a list
    if isinstance(obj,list):
        for i in range(0, len(obj)):
            obj[i] = deepstr(obj[i])

    #stringfy objects inside a dictionary
    if isinstance(obj,dict):
        for k,v in obj.items():
            del obj[k] #we delete the old key
            obj[deepstr(k)] = deepstr(v)

    return str(obj)

def beautify(obj, classNames = {"UlClassName": "optionList", "KeyClassName": "optionKey"}, level = 0):
    """ Turns list or dicts into beautiful <ul> HTML lists, recursively.
        -obj: an object that can be a list, a dict, with lists or dicts inside
        -classNames: a dictionary specifying class names. Example:
            {"UlClassName": "optionList", "KeyClassName": "optionKey"}
        supported types are: UlClassName, LiClassName, DivClassName, KeyClassName
        See BeautifulHTMLList.tpl and BeautifulHTMLDict.tpl to see how they are used.
        In the CSS file, you should define classes like: ul.optionList1, ul.optionList2, ul.optionKey1 (the number is the level of recursivity)
        -level: the level of recursivity.
    """
    from MaKaC.webinterface import wcomponents
    if isinstance(obj,list):
        return wcomponents.WBeautifulHTMLList(obj, classNames, level + 1).getHTML()
    elif isinstance(obj,dict):
        return wcomponents.WBeautifulHTMLDict(obj, classNames, level + 1).getHTML()
    elif isinstance(obj, Avatar):
        return obj.getStraightFullName()
    else:
        return str(obj)

def systemIcon( s ):
    return Config.getInstance().getSystemIconURL( s )

def iconFileName( s ):
    return Config.getInstance().getSystemIconFileName(s)

def htmlOutput( s ):
    sys.stdout.write(str(s))

def truncateTitle(title, maxSize=30):
    if len(title) > maxSize:
        return title[:maxSize]+'...'
    else:
        return title

def escapeHTMLForJS(s):
    """ Replaces some restricted characters in JS strings.
        \ -> \\
        ' -> \'
        " -> \"
        & -> \&
        / -> \/
        (line jump) -> \n
        (tab) -> \t
        (carriage return) -> \r
        (backspace) -> \b
        (form feed) -> \f

        TODO: try to optimize this (or check if it's optimum already).
        translate() doesn't work, because we are replacing characters by couples of characters.
        explore use of regular expressions, or maybe split the string and then join it manually, or just replace them by
        looping through the string and using an if...elif... etc.
    """
    res = s.replace("\\", "\\\\").replace("\'", "\\\'").replace("\"", "\\\"").replace("&", "\\&").replace("/", "\\/").replace("\n","\\n").replace("\t","\\t").replace("\r","\\r").replace("\b","\\b").replace("\f","\\f")
    return res


class TemplateExec:
    """
    Enables template execution.

    Template is a string mixing any text (HTML, e-mail, etc.)
    with Python code.

    WARNING: certain restrictions apply. See in the end.

    Every Python expression put between <%= %> will be EVALUATED
    and result will be put in place of expression.

    Every Python statements put between <% %> will be EXECUTED.
    Standard output (stdout) will be put in place of these statements.
    (so you can do <% print %>)

    Every strings put between %()s will be SUBSTITUTED with the
    corresponding value from given dictionary.

    Examples of templates:

    # Example 1:
    <tr><td> <%= 2 + 5 %> </td> </tr>

    # Example 2:
    Hello <%= person.fistName %>!
    Your reservation for <%= period.startDT %> -- <%= period.endDT %> is confirmed.

    # Example 3:
    <html>
    <head>
        <title> %(title)s </title>
    </head>
    <body>
        <h1> <%= room.name.capitalize() %> </h1>

        <% import os %> <!-- Not necessary here - just to show you can do this -->
        Let's skip odd columns.
        <table>
            <% for row in xrange( 0, 2 ): %>
                <tr>
                <% for column in xrange( 0, 6 ): %>
                    <% if column % 2 == 0: %>
                        <td style="background-color:lightgray"> Row = <%= row %>, Column = <%= column %> </td>
                    <% end %>
                <% end %>
                </tr>
            <% end %>  <!-- rows -->
        </table>
        <% include( 'Foot' ) %>  <!-- includes another template -->
    </body>
    </html>

    Template is execution context => objects live through the hole template,
    and not only in their <% %> tag.

    You can include another templates via includeTpl( 'TemplateName' ).
    The child templates inherit execution context, so all parent objects
    are available to it.

    Restrictions:
    1) There must be no ":" in Python code, in any form, except as block start.
       => you CAN NOT use strings like "foo:goo"
       => you CAN NOT initialize dictionaries dic = { a: 2, b: 3 }
       => you can write statements like: for i in xrange( 0, 10 ):
    2) You CAN NOT put blok in the same line as statement:
       => BAD:
          if a == 2: break
          Use instead:
          if a == 2:
              break

    These limitations are consequence of Python syntax-by-indentation rules.
    """

    @staticmethod
    def executeTemplate( tpl, objDict, tplFilename ):
        """
        Behaviour:
        1. Executes <% python code %>
               a) another template may be included
        1. Evaluates <%= python expression %>
        2. Substitutes %(key)s with objDict[key] value

        See class description for more info.

        Returns resulting string.

        tpl - template string
        objDict - context dictionary; insert objects and strings there.
        """
        # IMPLEMENTATION
        # General idea is to convert template into Python code and then execute it.
        # With includeTpl(), these may go recurrent.
        #global recurrenceLevel
        #recurrenceLevel += 1

        pythonCode = "import sys\n"   # Template is converted into Python code
        lastIx = 0        # Index of last Python code in template
        indentLevel = 0   # Indentation level

        # Copy the dictionary, since it will be modified.
        # We do not want to mess up with the oryginal dict.
        dictCopy = objDict.copy()

        TemplateExec.__registerHelpers( dictCopy )

        # Adding dictionary to itself...
        # Justification:
        # In child template, we will also need it.
        # This is the simpliest way to pass it to the child eval.
        #if not globals().has_key( '_dictCopy' ):
        globals()['_dictCopy'] = dictCopy
        globals()['_objDict'] = objDict

        while True:
            ixSt, ixEnd, type, statement = TemplateExec.__nextPythonCode( tpl, lastIx )

            # Human text between Python codes: convert to Python code (print)
            humanText = tpl[lastIx:ixSt]
            if len( humanText.strip() ) > 0:
                humanText = TemplateExec.__neutralizeLastChar( humanText )
                pythonCode += '\n%ssys.stdout.write( """%s""" )' % ( TemplateExec.__indent( indentLevel ), humanText )

            if TemplateExec.__isBlockEnd( statement ):
                indentLevel -= 1

            # Deal with Python code
            if statement == None:
                break

            if type == 'Expression':
                pythonCode += '\n%ssys.stdout.write( str( %s ) )' % ( TemplateExec.__indent( indentLevel ), statement )
            elif type == 'IndentBlock':
                for line in statement.split('\n'):
                    pythonCode += "\n%s%s" % (TemplateExec.__indent( indentLevel ), line)
            elif not TemplateExec.__isBlockEnd( statement ):
                pythonCode += "\n%s%s" % ( TemplateExec.__indent( indentLevel ),  statement )
                # Try to find all trailing ':'  <== OVERSIMPLIFIED
                indentLevel += statement.count( ':' )
            lastIx = ixEnd + 2  # Move after this Python code

        try:
            newTpl = TemplateExec.__executePythonCode( pythonCode, dictCopy, tplFilename )
        except TemplateExecException, e:

            try: open( ERROR_PATH + "/" + tplFilename + ".tpl.py", "w" ).write( pythonCode )
            except: pass
            raise TemplateExecException( e )
        except Exception, e:
            try: open( ERROR_PATH + "/" + tplFilename + ".tpl.error.py", "w" ).write( pythonCode )
            except: pass
            raise TemplateExecException( e )
        #except:
        #    raise pythonCode


        try:
            if (not objDict.has_key( "isIncluded" ) and \
                not (objDict.has_key("newTemplateStyle") and objDict['newTemplateStyle'])):
                # Perform old-style string substitution
                newTpl = newTpl % dictCopy
            else:
                # Substitute %% => %
                newTpl = newTpl.replace( '%%', '%' )

        except Exception, e:
            try: open( ERROR_PATH + "/" + tplFilename + ".tpl.error.py", "w" ).write( pythonCode )
            except: pass
            TemplateExec.__saveDebugInfo(e, tplFilename)

            if e.__class__ == ValueError:
                try:
                    message = str(e)
                    if message.startswith("unsupported format character"):
                        #we add some context information to the error message so that it's easier to see where the unsupported character is
                        problematicIndex = int(message[message.rfind('index')+6:])
                        newMessage = message + ". Context: [[ " + str(newTpl[problematicIndex-20:problematicIndex+20]) + " ]]"
                        e.message = newMessage
                        e.args = (newMessage)
                except Exception:
                    pass
            raise e


        #recurrenceLevel -= 1

        #if recurrenceLevel == 0 and globals().has_key( '_dictCopy' ):
            ## Clean up - we do not want to mess up with global scope
            #global _dictCopy
            #del _dictCopy
            #del recurrenceLevel

        return newTpl

    # PRIVATE ================================================================

    @staticmethod
    def __saveDebugInfo(e, tplFilename):
        if hasattr(e, 'template_tracebacks'):
            e.template_tracebacks.append(traceback.format_tb(sys.exc_info()[2]))
        else:
            e.template_tracebacks = [traceback.format_tb(sys.exc_info()[2])]

        if hasattr(e, 'problematic_templates'):
            e.problematic_templates.append(tplFilename)
        else:
            e.problematic_templates = [tplFilename]

    @staticmethod
    def __executePythonCode( pythonCode, objDict, tplFilename ):
        global recurrenceLevel
        # Execute the pythonCode -------------------------

        # create file-like string to capture output
        codeOut = StringIO.StringIO()
        codeErr = StringIO.StringIO()

        # remember stdout and stderr
        stdoutBackup = sys.stdout
        stderrBackup = sys.stderr

        # capture output and errors
        sys.stdout = codeOut
        #sys.stderr = codeErr
        try:
            exec pythonCode in objDict

        except Exception, e:
            # restore stdout and stderr in case of error
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
#            try: open( ERROR_PATH + "/" + tplFilename + ".tpl.py", "w" ).write( pythonCode )
#            except: pass

            TemplateExec.__saveDebugInfo(e, tplFilename)

            raise e

        sys.stdout = stdoutBackup
        sys.stderr = stderrBackup

        newTpl = ""

        s = codeErr.getvalue()
        if s: newTpl += "<font color='red'>%s</font>" % s

        s = codeOut.getvalue()
        if s: newTpl += s

        codeOut.close()
        codeErr.close()

        return newTpl

    @staticmethod
    def __registerHelpers( objDict ):
        """
        Adds helper methods to the dictionary.
        Does it only if symbol does not exist - backward compatibility.
        """
        if not 'includeTpl' in objDict:
            objDict['includeTpl'] = includeTpl
        if not 'contextHelp' in objDict:
            objDict['contextHelp'] = contextHelp
        if not 'inlineContextHelp' in objDict:
            objDict['inlineContextHelp'] = inlineContextHelp
        if not 'escapeAttrVal' in objDict:
            objDict['escapeAttrVal'] = escapeAttrVal
        if not 'escape' in objDict:
            objDict['escape'] = escape
        if not 'quoteattr' in objDict:
            objDict['quoteattr'] = quoteattr
        if not 'verbose' in objDict:
            objDict['verbose'] = verbose
        if not 'verbose_dt' in objDict:
            objDict['verbose_dt'] = verbose_dt
        if not 'verbose_t' in objDict:
            objDict['verbose_t'] = verbose_t
        if not 'dequote' in objDict:
            objDict['dequote'] = dequote
        if not 'formatTime' in objDict:
            objDict['formatTime'] = formatTime
        if not 'formatDate' in objDict:
            objDict['formatDate'] = formatDate
        if not 'systemIcon' in objDict:
            objDict['systemIcon'] = systemIcon
        if not 'formatDateTime' in objDict:
            objDict['formatDateTime'] = formatDateTime
        if not 'declareTemplate' in objDict:
            objDict['declareTemplate'] = declareTemplate
        if not 'linkify' in objDict:
            objDict['linkify'] = linkify
        if not 'truncateTitle' in objDict:
            objDict['truncateTitle'] = truncateTitle
        if not 'urlHandlers' in objDict:
            objDict['urlHandlers'] = MaKaC.webinterface.urlHandlers
        if not 'Config' in objDict:
            objDict['Config'] = MaKaC.common.Configuration.Config
        if not 'jsBoolean' in objDict:
            objDict['jsBoolean'] = jsBoolean
        if not 'offlineRequest' in objDict:
            from MaKaC.services.interface.rpc.offline import offlineRequest
            objDict['offlineRequest'] = offlineRequest
        if not 'jsonDescriptor' in objDict:
            from MaKaC.services.interface.rpc.offline import jsonDescriptor
            objDict['jsonDescriptor'] = jsonDescriptor
        if not 'jsonDescriptorType' in objDict:
            from MaKaC.services.interface.rpc.offline import jsonDescriptorType
            objDict['jsonDescriptorType'] = jsonDescriptorType
        if not 'jsonEncode' in objDict:
            from MaKaC.services.interface.rpc.json import encode as jsonEncode
            objDict['jsonEncode'] = jsonEncode
        if not 'roomInfo' in objDict:
            from MaKaC.services.interface.rpc.offline import roomInfo
            objDict['roomInfo'] = roomInfo
        if not 'macros' in objDict:
            from MaKaC.webinterface.asyndico import macros
            objDict['macros'] = macros
        if not 'roomBookingActive' in objDict:
            try:
                minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
                objDict['roomBookingActive'] = minfo.getRoomBookingModuleActive()
            except:
                # if the connection to the database is not started, there is no need to set the variable and
                # we avoid an error report.
                # THIS IS NEEDED, when using JSContent. JSContent does not need connection to the database
                # and this is causing an unexpected exception.
                pass
        if not 'user' in objDict:
            if not '__rh__' in objDict or not objDict['__rh__']:
                objDict['user'] = "ERROR: Assign self._rh = rh in your WTemplated.__init__( self, rh ) method."
            else:
                objDict['user'] = objDict['__rh__']._getUser()  # The '__rh__' is set by framework
        if not 'rh' in objDict:
            objDict['rh'] = objDict['__rh__']
        if not roomClass in objDict:
            objDict['roomClass'] = roomClass
        if not 'systemIcon' in objDict:
            objDict['systemIcon'] = systemIcon
        if not 'iconFileName' in objDict:
            objDict['iconFileName'] = iconFileName
        if not 'htmlOutput' in objDict:
            objDict['htmlOutput'] = htmlOutput
        if not 'escapeHTMLForJS' in objDict:
            objDict['escapeHTMLForJS'] = escapeHTMLForJS
        if not 'deepstr' in objDict:
            objDict['deepstr'] = deepstr
        if not 'beautify' in objDict:
            objDict['beautify'] = beautify
        # allow fossilization
        if not 'fossilize' in objDict:
            from MaKaC.common.fossilize import fossilize
            objDict['fossilize'] = fossilize
        #if not 'minfo' in objDict:
        #    objDict['minfo'] = info.HelperMaKaCInfo.getMaKaCInfoInstance()


    @staticmethod
    def __neutralizeLastChar( s ):
        """
        Returns modified s so that it can be printed.
        """
        if s[-1] == '"':
            s = s[0:-1] + chr( 92 ) + s[-1]
        s = s.replace( r'%{', '\%{' )
        return s

    @staticmethod
    def __indent( n ):
        INDENTATION = "    "
        return INDENTATION * n

    @staticmethod
    def __nextPythonCode( tpl, afterIx ):
        """
        Returns a tuple:
        (
            start index,
            end index,
            type,
            string of the statement
        )
        """
        ixSt = tpl.find( "<%", afterIx )
        if ixSt == -1: return ( len( tpl ), None, None, None )

        ixEnd = tpl.find( "%>", afterIx + 1 )
        if ixEnd == -1: return ( len( tpl ), None, None, None )

        isExpression, statement = (None, None)
        if tpl[ixSt + 2] == '=':
            type = 'Expression'
            statement = tpl[ixSt + 3 : ixEnd].strip()
        elif tpl[ixSt + 2] == '!':
            type = 'IndentBlock'
            statement = tpl[ixSt + 3 : ixEnd].strip()
        else:
            type = 'NonIndentBlock'
            statement = tpl[ixSt + 2 : ixEnd].strip()


        return ( ixSt, ixEnd, type, statement )

    @staticmethod
    def __isBlockEnd( statement ):
        if statement == None: return False
        statement = statement.strip().lower()
        return len( statement ) == 0 or statement == 'end'



# ============================================================================
# ================================== TEST ====================================
# ============================================================================


from datetime import datetime
class Test:
    @staticmethod
    def executeTemplate():
        tpl = """
<html>
<head>
    <title> <%= title %> </title>
</head>
<body>
    <% forChild = "TTTTT" %>
    <h1> <%= room.name.capitalize() %> </h1>
    <% includeTpl( 'IncludeMe' ) %>

    <% import os %> <!-- Not necessary here - just to show you can do this -->
    Let's skip odd columns.
    <table>
        <% for row in xrange( 0, 2 ): %>
            <tr>
            <% for column in xrange( 0, 6 ): %>
                <% if column % 2 == 0: %>
                    <td style="background-color:lightgray"> Row = <%= row %>, Column = <%= column %> </td>
                <% end %>
            <% end %>
            </tr>
        <% end %>  <!-- rows -->
    </table>
    <% includeTpl( 'IncludeMe' ) %>
</body>
</html>
"""

        dic = {}
        dic['title'] = "Templating example"
        dic['room'] = Warning()
        dic['room'].name = "Amphitheatre"

        print TemplateExec.executeTemplate( tpl, dic, 'fname' )

if __name__ == '__main__':
    print "Start"
    for i in xrange( 0, 1 ):
        Test.executeTemplate()
    print "End"
