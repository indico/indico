
/*
 * List of users: This component manage a listo of users, you can search and add users to the list, remove and edit them.
 * You can also add your own options
 * @param: confId -> Id of the conference (if needed)
 * @param: methods -> json object with the methods for the indicoRequests, the methods have to be:
 *    addExisting, addNew, edit, remove, getUserData, getUserList
 * @param: userListParams -> params of the indicoRequest for getUserList method
 * @param: inPlaceListElem -> element of the webpage where the list will be.
 * @param: showRemoveIcon -> Bool, true if we want to show the remove icon in each row
 * @param: showEditIcon -> Bool, true if we want to show the edit icon in each row
 * @param: showFavouritesIcon -> Bool, true if we want to show the favourites star
 * @param: showOrderArrows -> Bool, true if we want to have the order options
 * @param: kindOfUser -> String, kind of user identifier
 * @param: userCaption -> String to show in the texts
 * @param: elementClass -> String, css class of the elements in the list
 * @param: showGrantManagementCB -> Bool, show the checkbox to grant management rights in the AddNew/Edit popup
 * @param: showGrantSubmissionCB -> Bool, show the checkbox to grant submission rights in the AddNew/Edit popup
 * @param: showAffiliation -> Bool, show the affiliation of the user
 * @param: showGrantCoordinationCB -> Bool, show the checkbox to grant coordination rights in the AddNew/Edit popup
 */
type("ListOfUsersManager", [], {

    _addExistingUser: function(title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
                                showToggleFavouriteButtons) {
        // Create the popup to add new users
        var self = this;
        // params: (title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
        //          showToggleFavouriteButtons, chooseProcess)
        var chooseUsersPopup = new ChooseUsersPopup(title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers,
                                                    onlyOne, showToggleFavouriteButtons,
                function(userList) {self._manageUserList(self.methods["addExisting"], self._getAddExistingParams(userList));});
        chooseUsersPopup.execute();
    },

    _manageUserList: function(method, params, progress, highlight) {
        var self = this;
        var progress = any(progress, true);
        var highlight = any(highlight, false);
        if (progress)
            var killProgress = IndicoUI.Dialogs.Util.progress();
        indicoRequest(
                method, params,
                function(result, error) {
                    if (!error) {
                        self._updateUserList(result);
                        if (progress)
                            killProgress();
                        if (highlight)
                            IndicoUI.Effect.highLight('fullName_'+params['userId'], 'orange', 3000);
                    } else {
                        if (progress)
                            killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

    _personName: function(user, showAffiliation) {
        var fullName = user.familyName.toUpperCase() + (user.firstName?(', ' + user.firstName):'');
        if (user.title) {
            fullName = user.title + ' ' + fullName;
        }
        if (showAffiliation && user.affiliation) {
            fullName += " (" + user.affiliation + ")";
        }
        return fullName
    },

    _component_order: ['favorite',  'remove', 'edit', 'arrows'],

    _components: {

        favorite: function(user) {
            return $('<span/>').css({padding:'3px', 'float':'right'}).
                html(new ToggleFavouriteButton(this, {}, IndicoGlobalVars['userData']['favorite-user-ids'][user.id]).draw().dom);

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
                self.options.onRemove.call(self, user);
            })
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
                self.options.onEdit.call(self, user);
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
                    self.options.onArrowUp.call(self, user);
                }),
                arrow('down', $T('Move down')).click(function(event) {
                    self.options.onArrowDown.call(self, user);
                }));
        }
    },

    onEdit: function(user) {
        this._getUserData(this.methods["getUserData"], this._getGetUserParams(user.id));
    },

    onRemove: function(user) {
        this._manageUserList(this.methods["remove"], this._getRemoveParams(user.id));
    },

    onArrowUp: function(user) {
        self._manageUserList(this.methods["upUser"], this._getUpUserParams(user.id));
    },

    onArrowDown: function(user){
        self._manageUserList(this.methods["downUser"], this._getDownUserParams(user.id));
    },

    _getUserData: function(method, params) {
        var self = this;
        var killProgress = IndicoUI.Dialogs.Util.progress();
        indicoRequest(
                method, params,
                function(result,error) {
                    if (!error) {
                        self._showEditUserPopup(result);
                        killProgress();
                    } else {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

    _getAddNewParams: function() {
        // To overwrite
    },

    _getAddExistingParams: function() {
        // To overwrite
    },

    _getEditParams: function() {
        // To overwrite
    },

    _getRemoveParams: function() {
        // To overwrite
    },

    _getGetUserParams: function() {
        // To overwrite
    },

    _getDownUserParams: function() {
        // To overwrite
    },

    _getUpUserParams: function() {
        // To overwrite
    },

    _updateUserList: function(result) {
        var self = this;
        // update the user list

        var container = $(this.inPlaceListElem.dom).html('');

        $.each(result, function(idx) {
            var user = this;
            var elemStyle = self.elementClass;
            if (this._type == 'Group')
                elemStyle = "UIGroup";

            var row = $('<li/>').attr('class', elemStyle).
                append($('<span class="nameLink" />').append(
                    self._personName(this, self.showAffiliation)));

            _(self._component_order).each(function(opt, idx){
                if (self.options[opt]) {
                    var comp = self._components[opt].call(self, user, self.options[opt]);
                    row.append(comp);
                }
            });
            container.append(row);
        });
    },

    addManagementMenu: function(){
        // To overwrite
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
                }, self.showGrantManagementCB, self.showGrantSubmissionCB);
        editUserPopup.open();
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
                }, self.showGrantSubmissionCB, self.showGrantManagementCB, self.showGrantCoordinationCB);
        newUserPopup.open();
    }
},

    function(confId, methods, userListParams, inPlaceListElem,
             kindOfUser, userCaption, elementClass, showGrantSubmissionCB, showGrantManagementCB, showAffiliation, showGrantCoordinationCB, options) {
        var self = this;
        this.conferenceId = confId;
        this.methods = methods;
        this.userListParams = userListParams;
        this.inPlaceListElem = inPlaceListElem;
        this.kindOfUser = kindOfUser;
        this.userCaption = userCaption;
        this.elementClass = elementClass;
        this.showGrantSubmissionCB = showGrantSubmissionCB;
        this.showGrantManagementCB = showGrantManagementCB;
        this.showAffiliation = showAffiliation;
        this.showGrantCoordinationCB = showGrantCoordinationCB;

        var self = this;

        this.options = {
            remove: true,
            edit: true,
            favorite: true,
            arrows: true,
        };

        _(['onRemove', 'onEdit', 'onArrowUp', 'onArrowDown']).
            each(function(val){
                self.options[val] = self[val];
            });
        _(this.options).extend(options)

        this.inPlaceListElem.set(progressIndicator(true, true));

        if (userListParams) {
            indicoRequest(
                    self.methods["getUserList"], self.userListParams,
                    function(result, error) {
                        if (!error) {
                            self._updateUserList(result);
                        } else {
                            IndicoUtil.errorReport(error);
                        }
                    }
            );
        }
        this.addManagementMenu();
    }
);


/*
 * Manager of participant list for the cases we want to keep the information until the form submission.
 * The difference between this class and ListOfUsersManager is that this object does not have
 * to send ajax request when a new participant is added/removed or edited.
 *
 * @param: confId -> Id of the conference (if needed)
 * @param: userListParams -> params of the indicoRequest for getUserList method
 * @param: inPlaceListElem -> element of the webpage where the list will be.
 * @param: showRemoveIcon -> Bool, true if we want to show the remove icon in each row
 * @param: showEditIcon -> Bool, true if we want to show the edit icon in each row
 * @param: showFavouritesIcon -> Bool, true if we want to show the favourites star
 * @param: showOrderArrows -> Bool, true if we want to have the order options
 * @param: userCaption -> String to show in the texts
 * @param: elementClass -> String, css class of the elements in the list
 * @param: showGrantManagementCB -> Bool, show the checkbox to grant management rights in the AddNew/Edit popup
 * @param: showGrantSubmissionCB -> Bool, show the checkbox to grant submission rights in the AddNew/Edit popup
 * @param: showAffiliation -> Bool, show the affiliation of the user
 */
type("ListOfUsersManagerForForm", ["ListOfUsersManager"], {

	_addExistingUser: function(title, allowSearch, conferenceId, enableGroups,
                                   includeFavourites, suggestedUsers, onlyOne,
                                   showToggleFavouriteButtons) {
        var self = this;
        // Create the popup to add new users
        var chooseUsersPopup = new ChooseUsersPopup(
            title, allowSearch, conferenceId, enableGroups, includeFavourites,
            suggestedUsers, onlyOne, showToggleFavouriteButtons,
            function(userList) {
                for (var i=0; i<userList.length; i++) {
                    if (!self._isAlreadyInList(userList[i]['email'])) {
                        userList[i]['existing'] = true;
                        self.usersList.append(userList[i]);
                    } else {
                        var popup = new AlertPopup($T('Add ')+self.userCaption,
                                                   $T('The email address (') + userList[i]['email'] +
                                                   $T(') of a user you are trying to add is already used by another participant or the user is already added to the list.'));
                        popup.open();
                    }
                }
                self._updateUserList();
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
                            self._updateUserList();
                        } else {
                            var popup = new AlertPopup($T('Add ')+self.userCaption,
                                    $T('The email address (') + newUserData['email'] +
                                    $T(') is already used by another participant. Please modify email field value.'));
                            popup.open();
                        }
                    }
                }, self.showGrantSubmissionCB, self.showGrantManagementCB);
        newUserPopup.open();
    },

    _updateUserList: function() {
        // Update the users in the interface
        var self = this;
        this.inPlaceListElem.set('');

        $.each(result, function(idx) {
            var user = this;
            var row = $('<li class="UIPerson"/>');

            var userText = $('<span class="nameLink" />').append(
                self._personName(this, self.showAffiliation));
            var star = self._favoriteStar(this);

            if (this.showEditIcon) {
                var edit = self._editIcon(this, function(user) {
                    self._editUser(user);
                });
            }
            var removeImage = self._removeIcon(
                this,
                function(){
                    self._removeUser(user);
                });

            if (this.showOrderArrows) {
                var arrows = self._arrowIcons(
                    this,
                    function(user){
                        self._upUser(user.id);
                    },
                    function(user){
                        self._downUser(user.id);
                    });
            }

            row.append(userText, star, edit, removeImage, arrows);
        });

        this._checkEmptyList();
    },

    _checkEmptyList: function() {
        // To overwrite
    },

    _removeUser: function(user) {
        var killProgress = IndicoUI.Dialogs.Util.progress();
        if (user) {
            this.usersList.remove(user);
            this._updateUserList();
            killProgress();
            return;
        } else {
            killProgress();
            var popup = new AlertPopup($T('Remove ')+this.userCaption, $T('The user you are trying to remove does not exist.'));
            popup.open();
        }
    },

    _editUser: function(user) {
        var self = this;
        if (user) {
            var killProgress = IndicoUI.Dialogs.Util.progress();
            var user = $O(user);
            var editUserPopup = new UserDataPopup(
                $T('Edit ') + self.userCaption + $T(' data'),
                user,
                function(newData) {
                    if (editUserPopup.parameterManager.check()) {
                        self._userModifyData(newData);
                        self._updateUserList();
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

    _userModifyData: function(user) {
        this.usersList.item(user.id)['title'] = any(user.get('title'), '');
        this.usersList.item(user.id)['familyName'] = any(user.get('familyName'), '');
        this.usersList.item(user.id)['firstName'] = any(user.get('firstName'), '');
        this.usersList.item(user.id)['affiliation'] = any(user.get('affiliation'), '');
        this.usersList.item(user.id)['email'] = any(user.get('email'), '');
        this.usersList.item(user.id)['address'] = any(user.get('address'), '');
        this.usersList.item(user.id)['phone'] = any(user.get('phone'), '');
        this.usersList.item(user.id)['fax'] = any(user.get('fax'), '');
    },

    addManagementMenu: function() {
        // To overwrite
    },

    _upUser: function(userId) {
        // To overwrite
    },

    _downUser: function(userId) {
        // To overwrite
    },
    getUsersList: function() {
        return this.usersList;
    },

    _isAlreadyInList: function(email) {
        // It checks if there is any user with the same email
        for (var i=0; i<this.usersList.length.get(); i++) {
            if (email && email == this.usersList.item(i)['email']) {
                return true;
            }
        }
        return false;
    }

},

    function(confId, inPlaceListElem, showRemoveIcon, showEditIcon, showFavouritesIcon, showOrderArrows,
             userCaption, userCaption, elementClass, showGrantSubmissionCB, showGrantManagementCB, showAffiliation) {

        this.confId = confId;
        this.inPlaceListElem = inPlaceListElem;
        this.showRemoveIcon = showRemoveIcon;
        this.showEditIcon = showEditIcon;
        this.showFavouritesIcon = showFavouritesIcon;
        this.showOrderArrows = showOrderArrows;
        this.userCaption = userCaption;
        this.elementClass = elementClass;
        this.showGrantSubmissionCB = showGrantSubmissionCB;
        this.showGrantManagementCB = showGrantManagementCB;
        this.showAffiliation = showAffiliation;
        this.usersList = $L();
    }
);


/*
 * Manager for the list of users/groups with modification rights
 *
 * @param: confId -> Id of the conference (if needed),
 * @param: methods -> Supported methods,
 * @param: params -> Common params for all the methods,
 * @param: inPlaceListElem -> Element of the webpage where the list will be.
 * @param: userCaption -> String to show in the texts
 */
type("SimpleListControlManager", ["ListOfUsersManager"], {

    _getAddExistingParams: function(userList) {
        var params = this.params;
        params['userList'] = userList;
        return params;
    },

    _getRemoveParams: function(userId, kindOfUser) {
        var params = this.params;
        params['userId'] = userId;
        params['kindOfUser'] = kindOfUser;
        return params;
    },

    addExistingUser: function(){
        this._addExistingUser($T("Add ") + this.userCaption, true, this.confId, true, true, true, false, true);
    },

    _updateUserList: function(result) {
        var self = this;
        // update the user list

        var container = $(this.inPlaceListElem.dom).html('');
        $.each(result, function(idx) {
            var kindOfUser = "principal";
            var userIdentifier = this.id;

            if (this._type == "Avatar") {
                var fullName = self._personName(this);
                var elementStyle = "UIPerson";
            } else if (this._type == "Group") {
                var fullName = this.name;
                var elementStyle = "UIGroup";
            } else if (this.pending) {
                kindOfUser = "pending";
                userIdentifier = this.email;
                var fullName = $T('Non-registered user');
                var elementStyle = "UIPerson";
            }

            var row = $('<li/>').attr({'class': elementStyle});

            var userText = $('<span class="nameLink" />').
                append(fullName, $('<small/>').append(' (' + this.email + ')'));

            row.append(self._removeIcon(
                this,
                function(){
                    self._manageUserList(self.methods.remove, self._getRemoveParams(userIdentifier, kindOfUser), false);
                }));

            // favourites star
            if (self.showFavouritesIcon && IndicoGlobalVars.isUserAuthenticated &&
                exists(IndicoGlobalVars.userData['favorite-user-ids']) && this._type == "Avatar") {
                row.append(self._favoriteStar(this))
            }

            row.append(userText);
            container.append(row);
        });
    }

},
     function(confId, methods, params, inPlaceListElem, userCaption) {
         this.confId = confId;
         this.methods = methods;
         this.params = params;
         // params: confId, methods, userListParams, inPlaceListElem, showRemoveIcon, showEditIcon, showFavouritesIcon, showOrderArrows,
         // kindOfUser, userCaption, elementClass, showGrantSubmissionCB, showGrantManagementCB, showAffiliation
         this.ListOfUsersManager(this.confId, this.methods, params, inPlaceListElem, true,
                                 false, true, false, userCaption, userCaption, null, false, false, false);
     }
);
