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
            menuItems[$T('Add as convener')] = function() {
                self._manageBothUserList(self.methods["addAsConvener"], self._getModifyAsConvenerParams(user.id));
                menu.close();
            };
        } else {
            menuItems[$T('Remove as convener')] = function() {
                self._manageBothUserList(self.methods["removeAsConvener"], self._getModifyAsConvenerParams(user.id));
                menu.close();
            };
        }
        var menu = new PopupMenu(menuItems, [$E(element)], "popupList");
        var pos = $(element).position();
        menu.open(pos.left, pos.top + 20);
    }

},

    function(confId, methods, params, inPlaceListElem, userCaption, initialList) {
        this.ListOfUsersManager(confId, methods, params, inPlaceListElem, userCaption, "UIPerson", true, {},
                {title: false, affiliation: false, email:true},
                {remove: true, edit: false, favorite: true, arrows: false, menu: true}, initialList);
    }
);


/*
 * Manager for the list of conveners in session management
 */
type("SessionConvenerManager", ["ListOfUsersManager"], {

    _getModifyUserRightsParams: function(userId, kindOfRights) {
	    var params = this.userListParams;
	    params['userId'] = userId;
	    params['kindOfRights'] = kindOfRights;
        return params;
    },


    _personName: function(user) {
        var content = this.ListOfUsersManager.prototype._personName.call(this, user);
        var roles = '';
        var counter = 0;
        if (user.isManager) {
            roles += $T('Session manager');
            counter += 1;
        }
        if (user.isCoordinator) {
            if (counter > 0)
                roles += $T(', Session coordinator');
            else
                roles += $T('Session coordinator');
            counter += 1;
        }
        if (counter == 0)
            return content;
        else
            return content += '<small class="roleSmall">' + roles +  '</small>';
    },

    onMenu: function(element, user) {
        var self = this;
        var menuItems = {};

        if (!user.isManager) {
            menuItems[$T('Give management rights')] = function() {
                self._manageUserList(self.methods["grantRights"], self._getModifyUserRightsParams(user.id, "management"), false);
                menu.close();
            };
        } else {
            menuItems[$T('Remove management rights')] = function() {
                self._manageUserList(self.methods["revokeRights"], self._getModifyUserRightsParams(user.id, "management"), false);
                menu.close();
            };
        }

        if (!user.isCoordinator) {
            menuItems[$T('Give coordination rights')] = function() {
                self._manageUserList(self.methods["grantRights"], self._getModifyUserRightsParams(user.id, "coordination"), false);
                menu.close();
            };
        } else {
            menuItems[$T('Remove coordination rights')] = function() {
                self._manageUserList(self.methods["revokeRights"], self._getModifyUserRightsParams(user.id, "coordination"), false);
                menu.close();
            };
        }

        var menu = new PopupMenu(menuItems, [$E(element)], "popupList");
        var pos = $(element).position();
        menu.open(pos.left, pos.top + 20);
    }

},

function(confId, params, inPlaceListElem, inPlaceMenu, userCaption, initialList) {

    this.methods = {'addNew': 'session.conveners.addNewConvener',
                    'addExisting': 'session.conveners.addExistingConvener',
                    'remove': 'session.conveners.removeConvener',
                    'edit': 'session.conveners.editConvenerData',
                    'grantRights': 'session.conveners.grantRights',
                    'revokeRights': 'session.conveners.revokeRights'
    }

    this.ListOfUsersManager(confId, this.methods, params, inPlaceListElem, userCaption, "UIPerson", false,
            {submission: false, management: true, coordination: true},
            {title: false, affiliation: false, email:false},
            {remove: true, edit: true, favorite: false, arrows: false, menu: true}, initialList, true, false, inPlaceMenu);

});
