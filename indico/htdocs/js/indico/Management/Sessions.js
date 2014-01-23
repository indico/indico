/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

/*
 * Manager for the modification control list of users/groups in session management
 */
type("SessionControlManager", ["ListOfUsersManager"], {

    _manageBothUserList: function(method, params) {
        var self = this;
        indicoRequest(
                method, params,
                function(result, error) {
                    if (!error) {
                        // Update both lists of the page
                        modificationControlManager.drawUserList(result[0]);
                        coordinationControlManager.drawUserList(result[1]);
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

	_getModifyAsConvenerParams: function(userId) {
        var params = this.userListParams;
        params['userId'] = userId;
        return params;
    },

    _personName: function(user) {
        var content = this.ListOfUsersManager.prototype._personName.call(this, user);
        if (user.isConvener) {
            content += '<small class="roleSmall"> Convener </small>';
        }
        return content;
    },

    onMenu: function(element, user) {
        var menuItems = {};
        var self = this;
        if (!user.isConvener) {
            menuItems["addAsConvener"] = {action: function() {
                self._manageBothUserList(self.methods["addAsConvener"], self._getModifyAsConvenerParams(user.id));
                menu.close();
            }, display: $T('Add as convener')};
        } else {
            menuItems["removeAsConvener"] = {action: function() {
                self._manageBothUserList(self.methods["removeAsConvener"], self._getModifyAsConvenerParams(user.id));
                menu.close();
            }, display: $T('Remove as convener')};
        }

        var menu = new PopupMenu(menuItems, [$E(element)], "popupList");
        var pos = $(element).offset();
        menu.open(pos.left, pos.top + 20);
    }

},

    function(confId, methods, params, inPlaceListElem, userCaption, initialList) {
        this.ListOfUsersManager(confId, methods, params, inPlaceListElem, userCaption, "UIPerson", true, {},
                {title: false, affiliation: false, email:true},
                {remove: true, edit: false, favorite: true, arrows: false, menu: true}, initialList);
    }
);
