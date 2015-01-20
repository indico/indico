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
 * List of users: This component manage a list of users, you can search and add users to the list, remove and edit them.
 * You can also add your own options
 * @param: confId -> Id of the conference (if needed)
 * @param: methods -> json object with the methods for the indicoRequests, the methods have to be:
 *    addExisting, addNew, edit, remove, upUser, downUser (for these functionalities, then you can add your own ones)
 * @param: userListParams -> common params for all the indicoRequests for the component (ex. confId, contribId)
 * @param: inPlaceListElem -> element of the webpage where the list will be.
 * @param: userCaption -> String to show in the texts
 * @param: elementClass -> Class for the <li> elements in the list
 * @param: allowGroups -> Bool, true if to have groups in the list is allowed
 * @param: rightsToShow -> dictionary object, It shows the rights that the added users will be able to have. These values has to be:
 *         {submission: bool, management: bool, coordination: bool}
 * @param: nameOptions -> json object, Options for the user's name in the list. The options are:
 *         {'affiliation': bool, 'email': bool, 'title': bool}
 * @param: userOptions -> dictionary object: Options that can be performanced for each user. The allowed values are:
 *         {remove: bool, edit: bool, favorite: bool, arrows: bool, menu: bool}
 * @param: initialList -> List, It contains the initial users to add when the component is loaded the first time
 * @param: allowEmptyEmail -> Bool, true if it is allowed to have an empty email when we add a non existing user
 * @param: blockOnRemove -> Bool, true if it is necessary to block the page when an user is removed
 * @param: inPlaceMenu -> element where the menu with the options to add users will be placed
 */
type("ListOfUsersManager", [], {

    _addExistingUser: function(title, allowSearch, confId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
                                showToggleFavouriteButtons, extraParams, extraDiv) {
        // Create the popup to add new users
        var self = this;
        // params: (title, allowSearch, confId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
        //          showToggleFavouriteButtons, chooseProcess)
        var chooseUsersPopup = new ChooseUsersPopup(title, allowSearch, confId, enableGroups, includeFavourites, suggestedUsers,
                                                    onlyOne, showToggleFavouriteButtons, false,
                function(userList) {self._manageUserList(self.methods["addExisting"], self._getAddExistingParams(userList, extraParams));}, extraDiv);
        chooseUsersPopup.execute();
    },

    _manageUserList: function(method, params, progress) {
        var self = this;
        var progress = any(progress, true);
        if (progress)
            var killProgress = IndicoUI.Dialogs.Util.progress();
        indicoRequest(
                method, params,
                function(result, error) {
                    if (!error) {
                        self._updateUsersList(result);
                        self._drawUserList();
                        if (progress)
                            killProgress();
                    } else {
                        if (progress)
                            killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

    _manageAllConectedUserList: function() {
        // To overwrite
    	// You have to use this method if you have more than one ListOfUsersManager in the same page and
    	// the elements of one list depend on the actions over the other list
    },

    _personName: function(user) {
        if (user._type && user._type.indexOf("Group") != -1) {
            var fullName = user.name;
        } else {
            if (user.pending) {
                var fullName = $T('Non-registered user');
            } else {
                var fullName = user.familyName.toUpperCase() + (user.firstName?(', ' + user.firstName):'');
            }
        }
        if (this.nameOptions['title'] && user.title) {
            fullName = user.title + ' ' + fullName;
        }
        if (this.nameOptions['affiliation'] && user.affiliation) {
            fullName += " (" + user.affiliation + ")";
        }
        if ((this.nameOptions['email'] || user.pending) && user.email) {
            fullName += '<small> (' + user.email + ')</small>';
        }
        return fullName;
    },

    _component_order: ['remove', 'edit', 'favorite', 'menu', 'arrows'],

    _components: {

        menu: function(user) {
            var self = this;
            if (!user.pending && user._type.indexOf("Group") == -1) {
                var optionsMenuSpan = $('<span/>').css('float', 'right');
                var optionsMenuLink = $('<a/>').attr({
                    id: user.id,
                    'class': 'dropDownMenu fakeLink',
                    style: 'margin-left:15px; margin-right:15px'
                }).append($T('More')).click(function(event) {
                    self.userOptions.onMenu.call(self, this, user);
                });
                optionsMenuSpan.append(optionsMenuLink);
                return optionsMenuSpan;
            }
        },

        favorite: function(user) {
            if (user._type == "Avatar") {
                return $('<span/>').css({'float':'right'}).
                    html(new ToggleFavouriteButton(user, {}, IndicoGlobalVars['userData']['favorite-user-ids'][user.id]).draw().dom);
            }
        },

        remove: function(user) {
            var self = this;
            // remove icon
            return $('<img/>').attr({
                src: imageSrc("remove"), alt: $T('Remove ') + self.userCaption,
                title: $T('Remove this ') + self.userCaption + $T(' from the list'),
                'class': 'UIRowButton2',
                style: "margin-right:10px; float:right; cursor:pointer;"
            }).click(function(event) {
                self.userOptions.onRemove.call(self, user);
            });
        },


        edit: function(user, callback) {
            var self = this;
            return $('<img />').attr({
                src: imageSrc("edit"),
                alt: $T('Edit ') + this.userCaption,
                title: $T('Edit this ') + this.userCaption,
                'class': 'UIRowButton2',
                style:'float: right; cursor: pointer;'
            }).click(function(event) {
                self.userOptions.onEdit.call(self, user);
            });
        },

        arrows: function(user, callback_up, callback_down){
            var self = this;
            var arrow = function(direction, title) {
                return $('<img/>').attr({
                    src: imageSrc("arrow_" + direction),
                    'alt': title,
                    'title': title,
                    style: 'padding-top: 6px; float: left; cursor: pointer'
                });
            };

            return $('<div/>').append(
                arrow('up', $T('Move up')).click(function(event) {
                    self.userOptions.onArrowUp.call(self, user);
                }),
                arrow('down', $T('Move down')).click(function(event) {
                    self.userOptions.onArrowDown.call(self, user);
                }));
        }
    },

    onEdit: function(userData, all) {
        var self = this;
        // get the user data
        var user = $O(userData);
        var editUserPopup = new UserDataPopup(
                $T('Edit ') + self.userCaption + $T(' data'),
                user,
                function(newData) {
                    if (editUserPopup.parameterManager.check()) {
                    	if (!all)
                            self._manageUserList(self.methods["edit"], self._getEditParams(newData));
                    	else
                    	    self._manageAllConectedUserList(self.methods["edit"], self._getEditParams(newData));
                        editUserPopup.close();
                    }
                }, user.get('showSubmitterCB'), user.get('showManagerCB'), user.get('showCoordinatorCB'), self.allowEmptyEmail);
        editUserPopup.open();
    },

    onRemove: function(user) {
        if (user.pending) {
            var kindOfUser = "pending";
            this._manageUserList(this.methods["remove"], this._getRemoveParams(user.email, kindOfUser), this.blockOnRemove);
        } else {
            this._manageUserList(this.methods["remove"], this._getRemoveParams(user.id), this.blockOnRemove);
        }
    },

    onArrowUp: function(user) {
        self._manageUserList(this.methods["upUser"], this._getUpUserParams(user.id), false);
    },

    onArrowDown: function(user) {
        self._manageUserList(this.methods["downUser"], this._getDownUserParams(user.id), false);
    },

    onMenu: function(element, user) {
        // to overwrite with the menu options for each case
    },

    _getAddNewParams: function(userData) {
        var params = this.userListParams;
        params['userData'] = userData;
        return params;
    },

    _getAddExistingParams: function(userList, extraParams) {
        var params = this.userListParams;
        params['userList'] = userList;
        extraParams = any(extraParams, {});
        for(var param in extraParams){
            params[param] = extraParams[param]();
        }
        return params;
    },

    _getEditParams: function(userData) {
        var params = this.userListParams;
        params['userId'] = userData.get("id");
        params['userData'] = userData;
        return params;
    },

    _getRemoveParams: function(userId, kindOfUser) {
        var params = this.userListParams;
        params['userId'] = userId;
        if (kindOfUser)
            params['kindOfUser'] = kindOfUser;
        else
            params['kindOfUser'] = null;
        return params;
    },


    _getDownUserParams: function() {
        // To overwrite
    },

    _getUpUserParams: function() {
        // To overwrite
    },

    addExistingUser: function(){
        this._addExistingUser($T("Add ") + this.userCaption, true, this.confId, this.allowGroups, true, true, false, true);
    },

    drawUserList: function(result) {
        if (result != undefined)
            this._updateUsersList(result);
        this._drawUserList();
    },

    _drawUserList: function() {
        var self = this;

        var container = $(this.inPlaceListElem.dom).html('');

        this.usersList.each(function(val, idx) {
            var user = val;
            var elemStyle = self.elementClass;
            if (user._type == 'Group')
                elemStyle = "UIGroup";

            var row = $('<li/>').attr('class', elemStyle);

            _(self._component_order).each(function(opt, idx) {
                if (self.userOptions[opt]) {
                    var comp = self._components[opt].call(self, user, self.userOptions[opt]);
                    row.append(comp);
                }
            });
            row.append($('<span class="nameLink" />').append(
                    self._personName(user)));
            container.append(row);
        });
        this._checkEmptyList();
    },

    addManagementMenu: function() {
        var self = this;
        if (this.inPlaceMenu) {
            this.inPlaceMenu.observeClick(function(e) {
                var menuItems = {
                    'add_existing': {
                        action: function() {
                            self._addExistingUser($T("Add ") + self.userCaption, true, this.confId, false, true, true, false, true);
                        },
                        display: $T('Add Indico User')
                    },
                    'add_new': {
                        action: function() {
                            self._addNonExistingUser();
                        },
                        display: $T('Add new')
                    }
                };

                var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList", true);
                var pos = $(self.inPlaceMenu.dom).offset();
                menu.open(pos.left, pos.top + 15);
                //return false;
            });
        }
    },

    _addNonExistingUser: function() {
        var self = this;
        var newUser = $O();
        var newUserPopup = new UserDataPopup(
                $T('New ') + self.userCaption,
                newUser,
                function(newData) {
                    if (newUserPopup.parameterManager.check()) {
                        self._manageUserList(self.methods["addNew"], self._getAddNewParams(newData));
                        newUserPopup.close();
                    }
                }, self.rightsToShow.submission, self.rightsToShow.management, self.rightsToShow.coordination, self.allowEmptyEmail);
        newUserPopup.open();
    },

    getUsersList: function() {
        return this.usersList;
    },

    setUsersList: function(list) {
        this.usersList = list;
    },

    _checkEmptyList: function() {
        // To overwrite
    },

    _isAlreadyInList: function(email) {
        // It checks if there is any user with the same email
        for (var i=0; i<this.usersList.length.get(); i++) {
            if (email && email == this.usersList.item(i)['email']) {
                return true;
            }
        }
        return false;
    },

    _updateUsersList: function(list) {
        var self = this;
        this.usersList.clear();
        $.each(list, function(idx, val) {
            self.usersList.append(val);
        });
    }
},

    function(confId, methods, userListParams, inPlaceListElem, userCaption, elementClass, allowGroups,
             rightsToShow, nameOptions, userOptions, initialList, allowEmptyEmail, blockOnRemove, inPlaceMenu) {
	    var self = this;
        this.confId = confId;
        this.methods = methods;
        this.userListParams = userListParams;
        this.inPlaceListElem = inPlaceListElem;
        this.userCaption = userCaption;
        this.elementClass = elementClass;
        this.allowGroups = allowGroups;
        this.rightsToShow = rightsToShow;
        /*this.rightsToShow = {
            submission: false,
            management: false,
            coordination: false
        };*/
        this.nameOptions = nameOptions;
        /*this.nameOptions = {
            'affiliation': false,
            'email': false,
            'title': false
        };*/
        this.userOptions = userOptions;
        this.usersList = $L();
        this._updateUsersList(initialList);
        this.allowEmptyEmail = allowEmptyEmail;
        this.blockOnRemove = any(blockOnRemove, false);
        this.inPlaceMenu = inPlaceMenu;

        /*this.userOptions = {
            remove: true,
            edit: true,
            favorite: true,
            menu: true,
            arrows: true
        };*/
        _(['onRemove', 'onEdit', 'onArrowUp', 'onArrowDown', 'onMenu']).
            each(function(val){
                self.userOptions[val] = self[val];
            });
        _(this.userOptions).extend(userOptions);

        if (this.usersList.length.get()) {
            self._drawUserList();
        }

        this.addManagementMenu();
    }
);


/*
 * Manager of participant list for the cases that it is necessary to keep the information until the form submission and
 * not send any request.
 * The difference between this class and ListOfUsersManager is that this object does not have
 * to send ajax request when a new participant is added/removed or edited.
 *
 * @param: confId -> Id of the conference (if needed)
 * @param: inPlaceListElem -> element of the webpage where the list will be.
 * @param: userCaption -> String to show in the texts
 * @param: elementClass -> Class for the <li> elements in the list
 * @param: allowGroups -> Bool, true if to have groups in the list is allowed
 * @param: rightsToShow -> dictionary object, It shows the rights that the added users will be able to have. These values has to be:
 *         {submission: bool, management: bool, coordination: bool}
 * @param: nameOptions -> json object, Options for the user's name in the list. The options are:
 *         {'affiliation': bool, 'email': bool, 'title': bool}
 * @param: userOptions -> dictionary object: Options that can be performanced for each user. The allowed values are:
 *         {remove: bool, edit: bool, favorite: bool, arrows: bool, menu: bool}
 * @param: initialList -> List, It contains the initial users to add when the component is loaded the first time
 * @param: allowEmptyEmail -> Bool, true if it is allowed to have an empty email when we add a non existing user
 * @param: blockOnRemove -> Bool, true if it is necessary to block the page when an user is removed
 * @param: inPlaceMenu -> element where the menu with the options to add users will be placed
 */
type("ListOfUsersManagerForForm", ["ListOfUsersManager"], {

	_addExistingUser: function(title, allowSearch, confId, enableGroups,
                                   includeFavourites, suggestedUsers, onlyOne,
                                   showToggleFavouriteButtons) {
        var self = this;
        // Create the popup to add new users
        var chooseUsersPopup = new ChooseUsersPopup(
            title, allowSearch, confId, enableGroups, includeFavourites,
            suggestedUsers, onlyOne, showToggleFavouriteButtons, false,
            function(userList) {
                for (var i=0; i<userList.length; i++) {
                    if (!self._isAlreadyInList(userList[i]['email'])) {
                        userList[i]['existing'] = true;
                        if (!userList[i]['address'])
                            userList[i]['address'] = '';
                        if (!userList[i]['fax'])
                            userList[i]['fax'] = '';
                        self.usersList.append(userList[i]);
                    } else {
                        var popup = new AlertPopup($T('Add ')+self.userCaption,
                                                   $T('The email address (') + userList[i]['email'] +
                                                   $T(') of a user you are trying to add is already used by another participant or the user is already added to the list.'));
                        popup.open();
                    }
                }
                self._drawUserList();
            });
            chooseUsersPopup.execute();
        },

    _addNonExistingUser: function() {
        var self = this;
        var newUser = $O();
        var newUserPopup = new UserDataPopup(
                $T('New ') + self.userCaption,
                newUser,
                function(newData) {
                    var newUserData = {'title': any(newData.get('title'), ''),
                                       'firstName': any(newData.get('firstName'), ''),
                                       'familyName': any(newData.get('familyName'), ''),
                                       'affiliation': any(newData.get('affiliation'), ''),
                                       'email': any(newData.get('email'), ''),
                                       'address': any(newData.get('address'), ''),
                                       'phone': any(newData.get('phone'), ''),
                                       'fax': any(newData.get('fax'), '')
                                      };
                    if (newUserPopup.parameterManager.check()) {
                        if (!self._isAlreadyInList(newUserData['email'])) {
                            newUserPopup.close();
                            self.usersList.append(newUserData);
                            self._drawUserList();
                        } else {
                            var popup = new AlertPopup($T('Add ')+self.userCaption,
                                    $T('The email address (') + newUserData['email'] +
                                    $T(') is already used by another participant. Please modify email field value.'));
                            popup.open();
                        }
                    }
                }, self.rightsToShow.submission, self.rightsToShow.management, self.rightsToShowCoordination, self.allowEmptyEmail);
        newUserPopup.open();
    },

    onEdit: function(user) {
        var self = this;
        if (user) {
            var killProgress = IndicoUI.Dialogs.Util.progress();
            var userData = $O(user);
            var editUserPopup = new UserDataPopup(
                $T('Edit ') + self.userCaption + $T(' data'),
                userData,
                function(newData) {
                    if (editUserPopup.parameterManager.check()) {
                        self._userModifyData(user, newData);
                        self._drawUserList();
                        editUserPopup.close();
                    }
                }, false, false);
            editUserPopup.open();
            killProgress();
        } else {
            killProgress();
            var popup = new AlertPopup($T('Edit')+this.userCaption, $T('The user you are trying to edit does not exist.'));
            popup.open();
        }
    },

    onRemove: function(user) {
        if (user) {
            this.usersList.remove(user);
            this._drawUserList();
            return;
        } else {
            var popup = new AlertPopup($T('Remove ')+this.userCaption, $T('The user you are trying to remove does not exist.'));
            popup.open();
        }
    },

    onArrowUp: function(user) {
        // to overwrite
    },

    onArrowDown: function(user) {
        // to overwrite
    },

    onMenu: function(element, user) {
        // to overwrite with the menu options for each case
    },


    _userModifyData: function(user, newData) {
        user.title = any(newData.get('title'), '');
        user.familyName = any(newData.get('familyName'), '');
        user.firstName = any(newData.get('firstName'), '');
        user.affiliation = any(newData.get('affiliation'), '');
        user.email = any(newData.get('email'), '');
        user.address = any(newData.get('address'), '');
        user.phone = any(newData.get('phone'), '');
        user.fax = any(newData.get('fax'), '');
    }

},

    function(confId, inPlaceListElem, userCaption, elementClass, allowGroups, rightsToShow, nameOptions, userOptions,
             initialList, allowEmptyEmail, blockOnRemove, inPlaceMenu) {

        this.ListOfUsersManager(confId, {}, {}, inPlaceListElem, userCaption, elementClass, allowGroups,
                rightsToShow, nameOptions, userOptions, initialList, allowEmptyEmail, blockOnRemove, inPlaceMenu);
    }
);

/*
 * List of users: The difference with ListOfUsersManager is that a checkbox to send mail to the current managers is shown
 * You can also add your own options
 * @param: confId -> Id of the conference (if needed)
 * @param: methods -> json object with the methods for the indicoRequests, the methods have to be:
 *    addExisting, addNew, edit, remove, upUser, downUser (for these functionalities, then you can add your own ones)
 * @param: userListParams -> common params for all the indicoRequests for the component (ex. confId, contribId)
 * @param: inPlaceListElem -> element of the webpage where the list will be.
 * @param: userCaption -> String to show in the texts
 * @param: elementClass -> Class for the <li> elements in the list
 * @param: allowGroups -> Bool, true if to have groups in the list is allowed
 * @param: rightsToShow -> dictionary object, It shows the rights that the added users will be able to have. These values has to be:
 *         {submission: bool, management: bool, coordination: bool}
 * @param: nameOptions -> json object, Options for the user's name in the list. The options are:
 *         {'affiliation': bool, 'email': bool, 'title': bool}
 * @param: userOptions -> dictionary object: Options that can be performanced for each user. The allowed values are:
 *         {remove: bool, edit: bool, favorite: bool, arrows: bool, menu: bool}
 * @param: initialList -> List, It contains the initial users to add when the component is loaded the first time
 * @param: allowEmptyEmail -> Bool, true if it is allowed to have an empty email when we add a non existing user
 * @param: blockOnRemove -> Bool, true if it is necessary to block the page when an user is removed
 * @param: inPlaceMenu -> element where the menu with the options to add users will be placed
 * @param: showEmailCheckbox -> Bool, true if we want to activate the notification
 */
type("ListOfUsersManagerProtection", ["ListOfUsersManager"], {

    addExistingUser: function(){
        if(this.showEmailCheckbox){
            var sendEmailDiv = Html.div({className:"informationUserList", style:{marginTop: pixels(10)}});
            var checkbox = Html.checkbox({style:{verticalAlign:"middle"}}, true);
            checkbox.dom.id = "send-email-managers";
            sendEmailDiv.append(Html.span({},checkbox, $T("Send email notification to the current category managers")));
            this._addExistingUser($T("Add ") + this.userCaption, true, this.confId, this.allowGroups, true, true, false, true,{"sendEmailManagers": function(){return $("#send-email-managers")[0].checked;}}, sendEmailDiv);
        }else {
            this._addExistingUser($T("Add ") + this.userCaption, true, this.confId, this.allowGroups, true, true, false, true);
        }
    }
},

    function(confId, methods, userListParams, inPlaceListElem, userCaption, elementClass, allowGroups,
             rightsToShow, nameOptions, userOptions, initialList, allowEmptyEmail, blockOnRemove, inPlaceMenu, showEmailCheckbox) {
        this.showEmailCheckbox = showEmailCheckbox;
        this.ListOfUsersManager(confId, methods, userListParams, inPlaceListElem, userCaption, elementClass, allowGroups,
                rightsToShow, nameOptions, userOptions, initialList, allowEmptyEmail, blockOnRemove, inPlaceMenu);
    }
);
