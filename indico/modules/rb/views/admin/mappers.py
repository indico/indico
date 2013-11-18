# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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


class WPRoomMapperBase(WPRoomsBase):

    def __init__(self, rh):
        super(WPRoomMapperBase, self).__init__(rh)

    def _setActiveTab(self):
        self._subTabRoomMappers.setActive()


class WPRoomMapperList(WPRoomMapperBase):

    def __init__(self, rh, params):
        super(WPRoomMapperList, self).__init__(rh)
        self._params = params

    def _getTabContent(self, params):
        criteria = {}
        if filter(lambda x: self._params[x], self._params):
            criteria["name"] = self._params.get("sName","")
        comp = WRoomMapperList(criteria)
        pars = {"roomMapperDetailsURLGen": urlHandlers.UHRoomMapperDetails.getURL }
        return comp.getHTML(pars)


class WRoomMapperList(WTemplated):

    def __init__(self, criteria):
        self._criteria = criteria

    def _performSearch(self, criteria):
        rmh = roomMapping.RoomMapperHolder()
        res = rmh.match(criteria)
        return res

    def getVars(self):
        wvars = super(WRoomMapperList, self).getVars()
        wvars["createRoomMapperURL"] = urlHandlers.UHNewRoomMapper.getURL()
        wvars["searchRoomMappersURL"] = urlHandlers.UHRoomMappers.getURL()
        wvars["roomMappers"] = ""
        if self._criteria:
            wvars["roomMappers"] = """<tr>
                              <td>
                    <br>
                <table width="100%%" align="left" style="border-top: 1px solid #777777; padding-top:10px">"""
            roomMapperList = self._performSearch(self._criteria)
            ul = []
            color="white"
            ul = []
            for rm in roomMapperList:
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                url = wvars["roomMapperDetailsURLGen"]( rm )
                ul.append("""<tr>
                                <td bgcolor="%s"><a href="%s">%s</a></td>
                            </tr>"""%(color, url, rm.getName() ) )
            if ul:
                wvars["roomMappers"] += "".join( ul )
            else:
                wvars["roomMappers"] += i18nformat("""<tr>
                            <td><br><span class="blacktext">&nbsp;&nbsp;&nbsp; _("No room mappers for this search")</span></td></tr>""")
            wvars["roomMappers"] += """    </table>
                      </td>
                </tr>"""
        return wvars


class WPRoomMapperDetails(WPRoomMapperBase):

    def __init__(self, rh, roomMapper):
        super(WPRoomMapperDetails, self).__init__(rh)
        self._roomMapper = roomMapper

    def _getTabContent(self, params):
        comp = WRoomMapperDetails( self._roomMapper )
        pars = {"modifyURL": urlHandlers.UHRoomMapperModification.getURL( self._roomMapper ) }
        return comp.getHTML( pars )


class WRoomMapperDetails(WTemplated):

    def __init__( self, rm):
        self._roomMapper = rm

    def getVars( self ):
        wvars = super(WRoomMapperDetails, self).getVars()
        wvars["name"] = self._roomMapper.getName()
        wvars["description"] = self._roomMapper.getDescription()
        wvars["url"] = self._roomMapper.getBaseMapURL()
        wvars["placeName"] = self._roomMapper.getPlaceName()
        wvars["regexps"] = self._roomMapper.getRegularExpressions()
        return wvars


class WPRoomMapperCreation(WPRoomMapperBase):

    def _getTabContent(self, params):
        comp = WRoomMapperEdit()
        pars = {"postURL": urlHandlers.UHRoomMapperPerformCreation.getURL()}
        return comp.getHTML( pars )


class WPRoomMapperModification(WPRoomMapperBase):

    def __init__(self, rh, domain):
        super(WPRoomMapperModification, self).__init__(rh)
        self._domain = domain

    def _getTabContent( self, params ):
        comp = WRoomMapperEdit( self._domain )
        pars = {"postURL": urlHandlers.UHRoomMapperPerformModification.getURL(self._domain)}
        return comp.getHTML( pars )


class WRoomMapperEdit(WTemplated):

    def __init__(self, rm=None):
        self._roomMapper = rm

    def getVars(self):
        wvars = super(WRoomMapperEdit, self).getVars()
        wvars["name"] = ""
        wvars["description"] = ""
        wvars["url"] = ""
        wvars["placeName"] = ""
        wvars["regexps"] = ""
        wvars["locator"] = ""
        if self._roomMapper:
            wvars["name"] = self._roomMapper.getName()
            wvars["description"] = self._roomMapper.getDescription()
            wvars["url"] = self._roomMapper.getBaseMapURL()
            wvars["placeName"] = self._roomMapper.getPlaceName()
            wvars["regexps"] = "\r\n".join(self._roomMapper.getRegularExpressions())
            wvars["locator"] = self._roomMapper.getLocator().getWebForm()
        return wvars
