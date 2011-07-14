/*
 * Manager for the modification control list of users/groups in session management
 */
type("SessionControlManager", ["SimpleListControlManager"], {

    _manageBothUserList: function(method, params) {
        var self = this;
        indicoRequest(
                method, params,
                function(result, error) {
                    if (!error) {
                        // Update both lists of the page
                        modificationControlManager.updateUserList(result[0]);
                        coordinationControlManager.updateUserList(result[1]);
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

	_getModifyAsConvenerParams: function(userId) {
        var params = this.params;
        params['userId'] = userId;
        return params;
    },

    _getRemoveParams: function(userId, kindOfUser) {
        var params = this.params;
        params['userId'] = userId;
        params['kindOfUser'] = kindOfUser;
        return params;
    },

    updateUserList: function(result) {
        this._updateUserList(result)
    },

	_updateUserList: function(result) {
        var self = this;
        // update the user list
        this.inPlaceListElem.set('');
        for (var i=0; i<result.length; i++) {
            var userRowElements = [];

            var kindOfUser = "principal";
            var userIdentifier = result[i]['id'];
            if (result[i]['_type'] == "Avatar") {
                if (!result[i]['firstName']) {
                    var fullName = result[i]['familyName'].toUpperCase();
                } else {
                    var fullName = result[i]['familyName'].toUpperCase() + ', ' + result[i]['firstName'];
                }
                var elementStyle = "UIPerson";
            } else if (result[i]['_type'] == "Group") {
                var fullName = result[i]['name'];
                var elementStyle = "UIGroup";
            } else if (result[i]['pending']) {
                kindOfUser = "pending";
                userIdentifier = result[i]['email'];
                var fullName = $T('Non-registered-user');
                var elementStyle = "UIPerson";
            }
            if (result[i]['isConvener']) {
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, fullName,
                        Html.small({},' ('+ result[i]['email'] + ')'),
                        Html.small({style:{fontWeight:'bold', paddingLeft:'5px'}},' Convener'));
            } else {
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, fullName, Html.small({},' ('+ result[i]['email'] + ')'));
            }
            userRowElements.push(userText);

            if (result[i]['_type'] == 'Avatar') {
                // Options menu for each user
                var optionsMenuSpan = Html.span({onmouseover:"this.className = 'mouseover'",
                                            onmouseout:"this.className = ''", style:{cssFloat:'right'}});

                var optionsMenuLink = Html.a({id:'userMenu_' + result[i]['id'], className:'dropDownMenu fakeLink',
                                         style:{marginLeft:'15px', marginRight:'15px'}}, $T('More'));
                this._addParticipantMenu(optionsMenuLink, result[i]);
                optionsMenuSpan.append(optionsMenuLink);
                userRowElements.push(optionsMenuSpan);
            }

            // favourites star
            if (this.showFavouritesIcon && IndicoGlobalVars.isUserAuthenticated &&
                    exists(IndicoGlobalVars['userData']['favorite-user-ids']) && result[i]['_type'] === "Avatar") {
                spanStar = Html.span({style:{padding:'3px', cssFloat:'right'}});
                spanStar.set(new ToggleFavouriteButton(result[i], {}, IndicoGlobalVars['userData']['favorite-user-ids'][result[i]['id']]).draw());
                userRowElements.push(spanStar);
            }

            // remove icon
            var imageRemove = Html.img({
                src: imageSrc("remove"),
                alt: $T('Remove ') + this.userCaption,
                title: $T('Remove this ') + this.userCaption + $T(' from the list'),
                className: 'UIRowButton2',
                id: 'r_' + kindOfUser + '_' + userIdentifier,
                style:{marginRight:'10px', cssFloat:'right', cursor:'pointer'}
            });

            imageRemove.observeClick(function(event) {
                if (event.target) { // Firefox
                    var kindOfUser = event.target.id.split('_')[1];
                    var userId = event.target.id.split('r_'+kindOfUser+'_')[1];
                } else { // IE
                    var kindOfUser = event.srcElement.id.split('_')[1];
                    var userId = event.srcElement.id.split('r_'+kindOfUser+'_')[1];
                }
                self._manageUserList(self.methods["remove"], self._getRemoveParams(userId, kindOfUser), false);
                });
            userRowElements.push(imageRemove);

            var row = Html.li({className: elementStyle, onmouseover: "this.style.backgroundColor = '#ECECEC';",
                                onmouseout : "this.style.backgroundColor='#ffffff';", style:{cursor:'auto'}});

            for (var j=userRowElements.length-1; j>=0; j--) { // Done the 'for' like this because of IE7
                row.append(userRowElements[j]);
            }
            this.inPlaceListElem.append(row);
        }
    },

    _addParticipantMenu: function(element, user) {
        var self = this;

        element.observeClick(function(e) {
            var menuItems = {};

            if (!user['isConvener']) {
                menuItems[$T('Add as convener')] = function() {
                    self._manageBothUserList(self.methods["addAsConvener"], self._getModifyAsConvenerParams(user['id']));
                    menu.close();
                };
            } else {
                menuItems[$T('Remove as convener')] = function() {
                    self._manageBothUserList(self.methods["removeAsConvener"], self._getModifyAsConvenerParams(user['id']));
                    menu.close();
                };
            }

            var menu = new PopupMenu(menuItems, [element], "popupList");
            var pos = element.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
    }

},

    function(confId, methods, params, inPlaceListElem, userCaption) {
        this.SimpleListControlManager(confId, methods, params, inPlaceListElem, userCaption);
    }
);


/*
 * Manager for the list of conveners in session management
 */
type("SessionConvenerManager", ["ListOfUsersManager"], {

    _getAddExistingParams: function(userList) {
        var params = {confId: this.confId, sessionId: this.sessionId, userList: userList};
        return params;
    },

    _getAddNewParams: function(userData) {
        var params = {confId: this.confId, sessionId: this.sessionId, userData: userData};
        return params;
    },

    _getEditParams: function(userData) {
        var params = {confId: this.confId, sessionId: this.sessionId, userData: userData, userId: userData.get('id')};
        return params;
    },

    _getUserParams: function(userId) {
        var params = {confId: this.confId, sessionId: this.sessionId, userId: userId};
        return params;
    },

    _getModifyUserRightsParams: function(userId, kindOfRights) {
        var params = {confId: this.confId, sessionId: this.sessionId, userId: userId, kindOfRights: kindOfRights};
        return params;
    },

    _getRolesText: function(user) {
        var text = '(';
        var counter = 0;
        if (user['isManager']) {
            text += $T('Session manager');
            counter += 1;
        }
        if (user['isCoordinator']) {
            if (counter > 0)
                text += $T(', Session coordinator');
            else
                text += $T('Session coordinator');
            counter += 1;
        }
        if (counter == 0)
            return null;
        else
            return Html.small({style:{paddingLeft:'5px'}}, text + ')');
    },

    _updateUserList: function(result) {
        var self = this;
        // update the user list
        this.inPlaceListElem.set('');
        for (var i=0; i<result.length; i++) {
            var userRowElements = [];

            var userText = Html.span({className:'nameLink', cssFloat:'left'}, result[i]['fullName'], this._getRolesText(result[i]));

            userRowElements.push(userText);

            // Options menu for each user
            var optionsMenuSpan = Html.span({onmouseover:"this.className = 'mouseover'",
                                        onmouseout:"this.className = ''", style:{cssFloat:'right'}});

            var optionsMenuLink = Html.a({id:'userMenu_' + result[i]['id'], className:'dropDownMenu fakeLink',
                                     style:{marginLeft:'15px', marginRight:'15px'}}, $T('More'));
            this._addParticipantMenu(optionsMenuLink, result[i]);
            optionsMenuSpan.append(optionsMenuLink);
            userRowElements.push(optionsMenuSpan);

            // edit icon
            var imageEdit = Html.img({
                src: imageSrc("edit"),
                alt: $T('Edit ') + this.userCaption,
                title: $T('Edit this ') + this.userCaption,
                className: 'UIRowButton2',
                id: 'edit_'+result[i]['id'],
                style:{cssFloat:'right', cursor:'pointer'}
            });

            imageEdit.observeClick(function(event) {
                if (event.target) { // Firefox
                    var userId = event.target.id.split('_')[1];
                } else { // IE
                    var userId = event.srcElement.id.split('_')[1];
                }
                self._getUserData(self.methods["getUserData"], self._getUserParams(userId));
            });
            userRowElements.push(imageEdit);

            // remove icon
            var imageRemove = Html.img({
                src: imageSrc("remove"),
                alt: $T('Remove ') + this.userCaption,
                title: $T('Remove this ') + this.userCaption + $T(' from the list'),
                className: 'UIRowButton2',
                id: 'remove_'+result[i]['id'],
                style:{marginRight:'15px', cssFloat:'right', cursor:'pointer'}
            });

            imageRemove.observeClick(function(event) {
                if (event.target) { // Firefox
                    var userId = event.target.id.split('_')[1];
                } else { // IE
                    var userId = event.srcElement.id.split('_')[1];
                }
                self._manageUserList(self.methods["remove"], self._getUserParams(userId), false);
            });
            userRowElements.push(imageRemove);

            var row = Html.li({className: this.elementClass, onmouseover: "this.style.backgroundColor = '#ECECEC';",
                                onmouseout : "this.style.backgroundColor='#ffffff';", style:{cursor:'auto'}});

            for (var j=userRowElements.length-1; j>=0; j--) { // Done the 'for' like this because of IE7
                row.append(userRowElements[j]);
            }

            this.inPlaceListElem.append(row);
        }
    },

    _showEditUserPopup: function(userData) {
        var self = this;
        // get the user data
        var user = $O(userData);
        var editUserPopup = new UserDataPopup(
                $T('Edit ') + self.userCaption + $T(' data'),
                user,
                function(newData) {
                    if (editUserPopup.parameterManager.check()) {
                        self._manageUserList(self.methods["edit"], self._getEditParams(newData));
                        editUserPopup.close();
                    }
                }, false, !userData['isManager'], !userData['isCoordinator'], true);
        editUserPopup.open();
    },

	addManagementMenu: function(){
        var self = this;
        this.inPlaceMenu.observeClick(function(e) {
            var menuItems = {};

            menuItems[$T('Add existing')] = function(){ self._addExistingUser($T("Add ") + self.userCaption, true, this.confId, false,
                                                                           true, true, false, true); };
            menuItems[$T('Add new')] = function(){ self._addNonExistingUser(); };

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList");
            var pos = self.inPlaceMenu.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
    },

    _addParticipantMenu: function(element, user) {
        var self = this;

        element.observeClick(function(e) {
            var menuItems = {};

            if (!user['isManager']) {
                menuItems[$T('Give management rights')] = function() {
                    self._manageUserList(self.methods["grantRights"], self._getModifyUserRightsParams(user['id'], "management"), false);
                    menu.close();
                };
            } else {
                menuItems[$T('Remove management rights')] = function() {
                    self._manageUserList(self.methods["revokeRights"], self._getModifyUserRightsParams(user['id'], "management"), false);
                    menu.close();
                };
            }

            if (!user['isCoordinator']) {
                menuItems[$T('Give coordination rights')] = function() {
                    self._manageUserList(self.methods["grantRights"], self._getModifyUserRightsParams(user['id'], "coordination"), false);
                    menu.close();
                };
            } else {
                menuItems[$T('Remove coordination rights')] = function() {
                    self._manageUserList(self.methods["revokeRights"], self._getModifyUserRightsParams(user['id'], "coordination"), false);
                    menu.close();
                };
            }

            var menu = new PopupMenu(menuItems, [element], "popupList");
            var pos = element.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
    }

},

    function(confId, sessionId, inPlaceListElem, inPlaceMenu, userCaption) {
	var self = this;
    this.confId = confId;
    this.sessionId = sessionId;
    this.methods = {'addNew': 'session.conveners.addNewConvener',
                    'addExisting': 'session.conveners.addExistingConvener',
                    'remove': 'session.conveners.removeConvener',
                    'edit': 'session.conveners.editConvenerData',
                    'getUserData': 'session.conveners.getConvenerData',
                    'getUserList': 'session.conveners.getConvenerList',
                    'grantRights': 'session.conveners.grantRights',
                    'revokeRights': 'session.conveners.revokeRights'
    }

    this.inPlaceMenu = inPlaceMenu;


    // params: (confId, methods, userListParams, inPlaceListElem, showRemoveIcon, showEditIcon, showFavouritesIcon, showOrderArrows,
    // kindOfUser, userCaption, elementClass, showGrantSubmissionCB, showGrantManagementCB, showAffiliation, showGrantCoordiantionCB)
    this.ListOfUsersManager(confId, this.methods, {confId: confId, sessionId: this.sessionId}, inPlaceListElem, true, true,
                            false, false, null, userCaption, "UIPerson", false, true, false, true);
    }
);
