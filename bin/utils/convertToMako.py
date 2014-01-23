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

"""Script for translating Indico templates to Mako."""

import os
import re
import stat

from indico.core.config import Config

TEMPLATE_DIR = Config.getInstance().getTPLDir()
NEW_TEMPLATE_DIR = "%s/Mako" % TEMPLATE_DIR

def sameElements(a, b):
    """Check if two lists contain the same elements."""
    import copy
    copyA = copy.copy(a)
    copyB = copy.copy(b)
    copyA.sort()
    copyB.sort()
    return copyA == copyB

# This dictionary will be used to collect information about which
# arguments are passed to which templates, so that later we can put
# appropriate <%page directives.
arguments = { }

def translateToMako(tplText):
    """Translate Indico template to Mako."""

    def translateVariables(tplText):
        """Replace <%= expression %> with ${ expression }"""
        pattern = r"""
        <%=(?P<expression>
            (?:(?!<%=|%>).)*  # Matches strings not containing <%= or %>
        )%>
        """
        prog = re.compile(pattern, re.VERBOSE | re.DOTALL)
        def repl(m):
            expr = m.group("expression")
            if expr.find("}") >= 0 or expr.find("{") >= 0:
                raise Exception, "no {, } allowed, " + expr
            return "${%s}" % expr

        return prog.sub(repl, tplText)

    def translateInlineIfs(tplText):
        """ Translate inlined if constructs, e.g.
        class="body clearfix <% if sideMenu: %>bodyWithSideMenu<% end %>"
        to
        class="body clearfix ${bodyWithSideMenu if sideMenu else ''}"
        """
        inlineIf = r"""
        <%\s*if\s+
            (?P<expression>(?:(?!<%|%>).)*)
        :\s*%>
            (?P<true>(?:(?!<%|%>).)*)
        <%\s*end\s*%>
        (
        \s*<%\s*else:\s*%>
            (?P<false>(?:(?!<%|%>).)*)
        <%\s*end\s*%>
        )?
        """
        def fix(expr):
            """Change expressions containing ${} to such form, so
            that they can be used inside of the ${.. if .. else ..}"""
            s = re.split("(\${|})", expr)
            quote = '"' if all(x.find('"') == -1  for x in s) else "'"
            result = []
            putQuotes = True
            for token in s:
                if token in ['${', '}']:
                    putQuotes = not putQuotes
                else:
                    finalToken = token
                    if putQuotes:
                        finalToken = quote + finalToken + quote
                    result.append(finalToken)
            tmp = '+'.join([x for x in result if x not in ['""', "''"]])
            if len(tmp) == 0:
                return '""'
            else:
                return tmp

        def repl(m):
            if m.group(0).strip().find("\n") != -1:
                return m.group(0)
            falseText = m.group("false") if m.group("false") else ""
            p = '${%s if %s else %s}'
            return p % (fix(m.group("true")),
                        m.group("expression"), fix(falseText))

        prog = re.compile(inlineIf, re.VERBOSE)
        return prog.sub(repl, tplText)

    def translateControlStructures(tplText):
        """Translate non-inline if and for sentences, e.g.
        "<% if expr: %>" to "% if expr" and "<% end %>" to "% endif"
        """
        def endsWithColon(expr):
            """Make sure the the expression ends with :"""
            if expr.strip()[-1] != ':':
                raise Exception, "no colon" + expr
            return expr
        result = []
        stack = []
        nr = 1
        lines = tplText.split("\n")
        while lines:
            line = lines[0].replace('<%!', '<%')
            lines = lines[1:]
            p = ("^(?P<indentation>\s*)<%(?P<expression>"
                    + "(?:(?!<%|%>).)*)%>(?P<ending>.*)$")
            m = re.match(p, line)
            if m is not None:
                indentation = m.group("indentation")
                expression = m.group("expression")
                ending = m.group("ending")
                if len(ending.strip()) > 0:
                    lines = [ending] + lines
                firstToken = expression.split()[0]
                if firstToken in ["if", "for"]:
                    line = "%s%%%s" % (indentation, endsWithColon(expression))
                    stack.append(firstToken)
                elif firstToken == "def":
                    m = re.match(r"\s*def\s+(?P<function>.+):",
                                 endsWithColon(expression))
                    line = '<%%def name="%s">' % m.group("function")
                    stack.append(firstToken)
                elif firstToken == "end":
                    try:
                        top = stack.pop()
                    except IndexError, e:
                        raise IndexError, "pop from empty, line %s" % str(nr)
                    top = "</%def>" if top == "def" else "% end" + top
                    line = "%s%s" % (indentation, top)
                # We do startswith() instead of equality because
                # in most places it is used as "<% else: %>"
                elif any(firstToken.startswith(x) for x in ["else", "elif"]):
                    prevLine = result.pop()
                    if prevLine.find("endif") == -1:
                        message = "invalid else, line %s (%s)"
                        raise Exception, message % (prevLine, str(nr))
                    stack.append("if")
                    line = "%s%%%s" % (indentation, endsWithColon(expression))
                else:
                    line = "%s<%%%s%%>" % (indentation, expression)
            result.append(line.rstrip())
            nr += 1
        if len(stack) > 0:
            raise Exception, "stack is not empty: " + str(stack)
        return "\n".join(result)

    def translateIncludeTpls(tplText):
        """Change Indico includeTpls to Mako <%include directives."""
        include = r"""
        (?P<indentation>\s*)
        <%\s*
            includeTpl\s*
            \(\s*
            ["'](?P<tplName>(?:(?!<%|%>|').)*)["']\s*
            (,\s*(?P<parameters>(?:(?!<%|%>).)*)\s*)?
            \)\s*
        %>
        """
        def repl(m):
            global arguments
            indentation = m.group("indentation")
            tplName = "%s.tpl" % m.group("tplName")
            parameters = m.group("parameters")
            if parameters is not None:
                pattern = """%s<%%include file="%s" args="%s"/>"""
                parameters = parameters.replace('"', "'").replace('\\', "")
                line = pattern % (indentation, tplName, parameters)
                splitArgs = parameters.split(",")
                names = [arg.split("=")[0].strip() for arg in splitArgs]
                if tplName not in arguments:
                    # With the checking of `sameElements` commented out,
                    # it is safer to change this to a set() with update,
                    # so that in the end we have all the different argument
                    # names that were passed to the template.
                    arguments[tplName] = names
#                elif not sameElements(arguments[tplName], names):
#                    raise Exception, ("not same args: %s %s"
#                                      % (arguments[tplName], names))
            else:
                line = '%s<%%include file="%s"/>' % (indentation, tplName)
#                if arguments.get(tplName, []) != []:
#                    raise Exception, ("not same args: %s %s"
#                                      % (arguments[tplName], []))
                arguments[tplName] = []
            return line
        prog = re.compile(include, re.VERBOSE | re.DOTALL)
        return prog.sub(repl, tplText)

    def translateContextHelp(tplText):
        """Change calls to the old context help functions
        with a new version."""
        contextHelp = r"""
        <%\s(?P<name>(inlineContextHelp|contextHelp))\s*\(\s*
        (?P<helpTextOrId>
            (?:(?!<%|%>).)* # Matches strings not containing <% or %>
        )
        \s*\)\s*%>
        """
        prog = re.compile(contextHelp, re.VERBOSE)
        return prog.sub(r"${\g<name>(\g<helpTextOrId>)}", tplText)

    def renameSelfVariable(tplText):
        """Name self is reserved in Mako, so we rename it.

        Warning: there is some Javascript code in Indico that uses a
        variable named 'self'. There can be some errors that have to be
        fixed by hand after the script was run (it is also possible
        to rerun the script on .js files with this step commented out."""
        selfVariable = r"""(?P<prev>[^\w])self\."""
        prog = re.compile(selfVariable, re.VERBOSE)
        return prog.sub(r"\g<prev>self_.", tplText)

    tplText = tplText.replace('\\\\', '\\')
    tplText = tplText.replace('\t', ' ' * 4)

    for proc in [translateVariables,
                 translateInlineIfs,
                 translateControlStructures,
                 translateIncludeTpls,
                 translateContextHelp,
                 renameSelfVariable]:
        tplText = proc(tplText)
    return tplText

# Copy pasted from convert-templates.py
def walktree(top='.'):
    names = os.listdir(top)
    yield top, names
    for name in names:
        try:
            st = os.lstat(os.path.join(top, name))
        except os.error:
            continue
        if stat.S_ISDIR(st.st_mode):
            for newtop, children in walktree(os.path.join(top, name)):
                yield newtop, children

def main():
    """Convert Indico templates to Mako template language."""
    succesful, total = 0, 0
    for basepath, children in walktree():
        if basepath.find("htdocs") != -1:
            continue
        if basepath.find("Mako") != -1:
            continue
        for child in children:
            if any(child.endswith(fileType) for fileType in [".tpl", ".js"]):
                total += 1
                newDir = "%s/Mako" % basepath
                if not os.path.isdir(newDir):
                    os.mkdir(newDir)
                indicoTpl = open(os.path.join(basepath, child)).read()
                try:
                    makoTpl = translateToMako(indicoTpl)
                except Exception, e:
                    print "%s failed: %s" % (child, str(e))
                    continue
                succesful += 1
                makoFile = open(os.path.join(newDir, child), 'w')
                makoFile.write(makoTpl)
                makoFile.close()

    # Add <%page directives to Mako templates with the lists
    # of expected arguments. This uses arguments variable
    # and thus must be performed only after translateToMako
    # has been called on all old Indico template files.

    # Assumes that all includes with arguments are in the
    # main tpls directory. This assumption was correct at the
    # time of writing this script
    for tplFilename, args in arguments.items():
        if args == []:
            continue
        tplPath = os.path.join(NEW_TEMPLATE_DIR, tplFilename)
        makoTpl = open(tplPath).read()
        argsDefaultValues = ["%s=None" % x for x in args]
        header = '<%%page args="%s"/>\n' % ", ".join(argsDefaultValues)
        makoFile = open(tplPath, 'w')
        makoFile.write(header + makoTpl)
        makoFile.close()

    print "Translation finished! (%s out of %s)" % (succesful, total)

if __name__ == "__main__":
    main()
