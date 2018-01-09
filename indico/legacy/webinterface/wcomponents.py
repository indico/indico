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


class TabControl:

    def __init__( self, parent=None, child=None ):
        self._tabs = []
        self._active = None
        self._default = None
        # Parent element (another tabcontrol),
        # in case there is nesting
        self._parent = parent

        if parent != None:
            parent.setChild(self);
        self._child = child

    def _addTab( self, tab ):
        self._tabs.append( tab )
        if len( self._tabs ) == 1:
            self._default = tab
            self._active = tab

    def newTab( self, id, caption, url, hidden=False, className="" ):
        tab = Tab( self, id, caption, url, hidden=hidden, className=className )
        self._addTab( tab )
        return tab

    def setDefaultTab( self, tab ):
        if tab in self._tabs:
            self._default = tab

    def getDefaultTab( self ):
        return self._default

    def setActiveTab( self, tab ):
        if tab in self._tabs:
            self._active = tab

    def getActiveTab( self ):
        return self._active

    def getTabList( self ):
        return self._tabs

    def getTabById( self, id ):
        for tab in self.getTabList():
            if tab.getId() == id:
                return tab
        return None

    def getParent( self ):
        # retrieve parent TabControl
        return self._parent

    def setChild( self, child ):
        self._child = child

    def getChild( self ):
        # retrieve child TabControl
        return self._child

    def getLevel( self ):
        tmp = self.getParent()
        level = 0
        while tmp:
            level += 1
            tmp = tmp.getParent()
        return level

class Tab:

    def __init__( self, owner, id, caption, URL, hidden = False, className="" ):
        self._owner = owner
        self._id = id.strip()
        self._caption = caption.strip()
        self._url = URL
        self._enabled = True
        self._subtabControl=None
        self._hidden = hidden
        self._className = className

    def __repr__(self):
        return '<Tab(%s, %s, %s, %s)>' % (self._id, self._caption, self._url, int(self.isActive()))

    def getId( self ):
        return self._id

    def getCaption( self ):
        return self._caption

    def setCaption( self, cp):
        self._caption = cp

    def getURL( self ):
        return self._url

    def setDefault( self ):
        self._owner.setDefaultTab( self )

    def isDefault( self ):
        return self._owner.getDefaultTab() == self

    def isActive( self ):
        return self._owner.getActiveTab() == self

    def setActive( self ):
        self._owner.setActiveTab( self )

    def enable( self ):
        self._enabled = True

    def disable( self ):
        self._enabled = False

    def setEnabled(self,value):
        self._enabled=value

    def isEnabled( self ):
        return self._enabled

    def setHidden(self, value):
        self._hidden = value

    def isHidden( self ):
        return self._hidden

    def getSubTabControl(self):
        return self._subtabControl

    def newSubTab( self, id, caption, url ):
        # guarantee that a subtabControl exists
        if not self._subtabControl:
            self._subtabControl = TabControl(parent=self._owner)

        tab=self._subtabControl.newTab( id, caption, url )
        return tab

    def hasChildren(self):
        return self._subtabControl is not None

    def getClassName(self):
        return self._className


class WTabControl(WTemplated):
    def __init__(self, ctrl, **params):
        self._tabCtrl = ctrl

    def _getTabs(self):
        tabs = []
        for tab in self._tabCtrl.getTabList():
            if (not tab.isEnabled() or tab.isHidden()) and not tab.isActive():
                # The active tab may never be skipped. If we skipped it jQuery would consider the first tab active and
                # send an AJAX request to load its contents, which would break the whole page.
                continue
            tabs.append((tab.getCaption(), tab.getURL(), tab.isActive(), tab.getClassName()))
        return tabs

    def _getActiveTabId(self):
        skipped = 0
        for i, tab in enumerate(self._tabCtrl.getTabList()):
            if tab.isActive():
                return i - skipped
            if not tab.isEnabled() or tab.isHidden():
                skipped += 1
        return 0

    def _getActiveTab(self):
        for tab in self._tabCtrl.getTabList():
            if tab.isActive():
                return tab

    def _getBody(self):
        tab = self._getActiveTab()
        if not tab:
            return self._body
        sub = tab.getSubTabControl()
        if not sub:
            return self._body
        return WTabControl(sub).getHTML(self._body)

    def getHTML(self, body):
        self._body = body
        return WTemplated.getHTML(self)

    def getVars( self ):
        vars = WTemplated.getVars(self)
        vars['body'] = self._getBody()
        vars['tabs'] = self._getTabs()
        vars['activeTab'] = self._getActiveTabId()
        vars['tabControlId'] = id(self)

        return vars
