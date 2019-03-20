# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from xml.sax.saxutils import escape

from flask import g, render_template
from speaklater import _LazyString

from indico.legacy.common.TemplateExec import render as render_mako
from indico.web.menu import build_menu_structure


def render_header(category=None, protected_object=None, local_tz=None, force_local_tz=False):
    top_menu_items = build_menu_structure('top-menu')
    rv = render_template('header.html',
                         category=category,
                         top_menu_items=top_menu_items,
                         protected_object=protected_object,
                         local_tz=local_tz,
                         force_local_tz=force_local_tz)
    return rv.encode('utf-8')


class WTemplated:
    """This class provides a basic implementation of a web component (an
       object which generates HTML related to a certain feature or
       functionality) which relies in a template file for generating the
       HTML it's in charge of.
       By templating file we mean that there will be a file in the file
       system (uniquely identified) which will contain HTML code plus some
       "variables" (dynamic values). The class will take care of opening
       this file, parsing the HTML and replacing the variables by the
       corresponding values.
    """
    tplId = None

    def __init__(self, tpl_name=None):
        if tpl_name is not None:
            self.tplId = tpl_name

        self._rh = g.get('rh')

    def getVars( self ):
        """Returns a dictionary containing the TPL variables that will
            be passed at the TPL formating time. For this class, it will
            return the configuration user defined variables.
           Classes inheriting from this one will have to take care of adding
            their variables to the ones returned by this method.
        """
        self._rh = g.get('rh')
        return dict(self.__params)

    def getHTML( self, params=None ):
        """Returns the HTML resulting of formating the text contained in
            the corresponding TPL file with the variables returned by the
            getVars method.
            Params:
                params -- additional paramters received from the caller
        """

        self._rh = g.get('rh')
        if self.tplId == None:
            self.tplId = self.__class__.__name__[1:]
        self.tplFile = '{}.tpl'.format(self.tplId)
        self.__params = {}
        if params != None:
            self.__params = params

        vars = self.getVars()
        vars['__rh__'] = self._rh
        vars['self_'] = self
        return render_mako(self.tplFile, vars)

    @staticmethod
    def htmlText(param):
        if not param:
            return ''
        if not isinstance(param, (basestring, _LazyString)):
            param = repr(param)
        if isinstance(param, unicode):
            param = param.encode('utf-8')
        return escape(param)

    @staticmethod
    def textToHTML(param):
        if param != "":
            if param.lower().find("<br>") == -1 and param.lower().find("<p>") == -1 and param.lower().find("<li>") == -1 and param.lower().find("<table") == -1:
                param=param.replace("\r\n", "<br>")
                param=param.replace("\n","<br>")
            return param
        return "&nbsp;"
