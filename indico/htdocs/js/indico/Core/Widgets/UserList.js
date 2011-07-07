
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

    _manageUserList: function(method, params, progress) {
        var self = this;
        var progress = any(progress, true);
        if (progress)
            var killProgress = IndicoUI.Dialogs.Util.progress();
        indicoRequest(
                method, params,
                function(result, error) {
                    if (!error) {
                        self._updateUserList(result);
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
        this.inPlaceListElem.set('');
        for (var i=0; i<result.length; i++) {
            var userRowElements = [];

            if (this.showAffiliation && result[i]['affiliation'] != '') {
                // Show submitter
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, result[i]['fullName'] + ' ('+ result[i]['affiliation'] + ')');
            } else {
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, result[i]['fullName']);
            }
            userRowElements.push(userText);

            // favourites star
            if (this.showFavouritesIcon && IndicoGlobalVars.isUserAuthenticated &&
                    exists(IndicoGlobalVars['userData']['favorite-user-ids']) && result[i]['_type'] === "Avatar") {
                spanStar = Html.span({style:{padding:'3px', cssFloat:'right'}});
                spanStar.set(new ToggleFavouriteButton(result[i], {}, IndicoGlobalVars['userData']['favorite-user-ids'][result[i]['id']]).draw());
                userRowElements.push(spanStar);
            }

            if (this.showEditIcon) {
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
                    self._getUserData(self.methods["getUserData"], self._getGetUserParams(userId));
                });
                userRowElements.push(imageEdit);
            }

            if (this.showRemoveIcon) {
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
                    self._manageUserList(self.methods["remove"], self._getRemoveParams(userId));
                });
                userRowElements.push(imageRemove);
            }

            if (this.showOrderArrows) {
                // arrow icons
                // up arrow
                var upArrow = Html.img({
                    src: imageSrc("arrow_up"),
                    alt: $T('Up ') + this.userCaption,
                    title: $T('Up this ') + this.userCaption,
                    id: 'up_'+result[i]['id'],
                    style:{paddingTop: '6px', cssFloat:'left', cursor:'pointer'}
                });

                upArrow.observeClick(function(event) {
                    if (event.target) { // Firefox
                        var userId = event.target.id.split('_')[1];
                    } else { // IE
                        var userId = event.srcElement.id.split('_')[1];
                    }
                    self._manageUserList(self.methods["upUser"], self._getUpUserParams(userId));
                });
                userRowElements.push(upArrow);
                // Down arrow
                var downArrow = Html.img({
                    src: imageSrc("arrow_down"),
                    alt: $T('Down ') + this.userCaption,
                    title: $T('Down this ') + this.userCaption,
                    id: 'down_'+result[i]['id'],
                    style:{paddingTop: '6px', cssFloat:'left', cursor:'pointer'}
                });

                downArrow.observeClick(function(event) {
                    if (event.target) { // Firefox
                        var userId = event.target.id.split('_')[1];
                    } else { // IE
                        var userId = event.srcElement.id.split('_')[1];
                    }
                    self._manageUserList(self.methods["downUser"], self._getDownUserParams(userId));
                });
                userRowElements.push(downArrow);

            }

            var elemStyle = this.elementClass;
            if (result[i]['_type'] == 'Group')
                elemStyle = "UIGroup";

            var row = Html.li({className: elemStyle, onmouseover: "this.style.backgroundColor = '#ECECEC';",
                                onmouseout : "this.style.backgroundColor='#ffffff';", style:{cursor:'auto'}});

            for (var j=userRowElements.length-1; j>=0; j--) { // Done the 'for' like this because of IE7
                row.append(userRowElements[j]);
            }

            this.inPlaceListElem.append(row);
        }
    },

    addManagementMenu: function(){
        // To overwrite
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
                }, self.showGrantSubmissionCB, self.showGrantManagementCB);
        newUserPopup.open();
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
                }, false, !userData['canModify']);
        editUserPopup.open();
    }

},

    function(confId, methods, userListParams, inPlaceListElem, showRemoveIcon, showEditIcon, showFavouritesIcon, showOrderArrows,
             kindOfUser, userCaption, elementClass, showGrantSubmissionCB, showGrantManagementCB, showAffiliation) {
        this.conferenceId = confId;
        this.methods = methods;
        this.userListParams = userListParams;
        this.inPlaceListElem = inPlaceListElem;
        this.showRemoveIcon = showRemoveIcon;
        this.showEditIcon = showEditIcon;
        this.showFavouritesIcon = showFavouritesIcon;
        this.showOrderArrows = showOrderArrows;
        this.kindOfUser = kindOfUser;
        this.userCaption = userCaption;
        this.elementClass = elementClass;
        this.showGrantSubmissionCB = showGrantSubmissionCB;
        this.showGrantManagementCB = showGrantManagementCB;
        this.showAffiliation = showAffiliation;
        var self = this;
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
type("ListOfUsersManagerForForm", [], {

	_addExistingUser: function(title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
                               showToggleFavouriteButtons) {
        // Create the popup to add new users
        var self = this;
        // params: (title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
        //          showToggleFavouriteButtons, chooseProcess)
        var chooseUsersPopup = new ChooseUsersPopup(title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers,
                               onlyOne, showToggleFavouriteButtons,
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

        for (var i=0; i<this.usersList.length.get(); i++) {
            var userRowElements = [];

            if (!this.usersList.item(i)['title'] && !this.usersList.item(i)['firstName']) {
                var fullName = this.usersList.item(i)['familyName'].toUpperCase();
            } else if (!this.usersList.item(i)['title'] && this.usersList.item(i)['firstName']) {
                var fullName = this.usersList.item(i)['familyName'].toUpperCase() + ', ' + this.usersList.item(i)['firstName'];
            } else if (this.usersList.item(i)['title'] && !this.usersList.item(i)['firstName']) {
                var fullName = this.usersList.item(i)['title'] + ' ' + this.usersList.item(i)['familyName'].toUpperCase();
            } else {
                var fullName = this.usersList.item(i)['title'] + ' ' + this.usersList.item(i)['familyName'].toUpperCase() + ', ' + this.usersList.item(i)['firstName'];
            }


            if (this.showAffiliation && this.usersList.item(i)['affiliation']) {
                // Show affiliation
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, fullName + ' ('+ this.usersList.item(i)['affiliation'] + ')');
            } else {
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, fullName);
            }
            userRowElements.push(userText);

            // favourites star
            if (this.showFavouritesIcon && IndicoGlobalVars.isUserAuthenticated &&
                    exists(IndicoGlobalVars['userData']['favorite-user-ids']) && this.usersList.item(i)['_type'] === "Avatar") {
                spanStar = Html.span({style:{padding:'3px', cssFloat:'right'}});
                spanStar.set(new ToggleFavouriteButton(this.usersList.item(i), {}, IndicoGlobalVars['userData']['favorite-user-ids'][this.usersList.item(i)['id']]).draw());
                userRowElements.push(spanStar);
            }

            if (this.showEditIcon) {
                // edit icon
                var imageEdit = Html.img({
                    src: imageSrc("edit"),
                    alt: $T('Edit ') + this.userCaption,
                    title: $T('Edit this ') + this.userCaption,
                    className: 'UIRowButton2',
                    id: 'edit_'+i,
                    style:{cssFloat:'right', cursor:'pointer'}
                });

                imageEdit.observeClick(function(event) {
                    if (event.target) { // Firefox
                        var userId = event.target.id.split('_')[1];
                    } else { // IE
                        var userId = event.srcElement.id.split('_')[1];
                    }
                    self._editUser(userId);
                });
                userRowElements.push(imageEdit);
            }

            if (this.showRemoveIcon) {
                // remove icon
                var imageRemove = Html.img({
                    src: imageSrc("remove"),
                    alt: $T('Remove ') + this.userCaption,
                    title: $T('Remove this ') + this.userCaption + $T(' from the list'),
                    className: 'UIRowButton2',
                    id: 'remove_'+i,
                    style:{marginRight:'15px', cssFloat:'right', cursor:'pointer'}
                });

                imageRemove.observeClick(function(event) {
                    if (event.target) { // Firefox
                        var userId = event.target.id.split('_')[1];
                    } else { // IE
                        var userId = event.srcElement.id.split('_')[1];
                    }
                    self._removeUser(userId);
                });
                userRowElements.push(imageRemove);
            }

            if (this.showOrderArrows) {
                // arrow icons
                // up arrow
                var upArrow = Html.img({
                    src: imageSrc("arrow_up"),
                    alt: $T('Up ') + this.userCaption,
                    title: $T('Up this ') + this.userCaption,
                    id: 'up_'+i,
                    style:{paddingTop: '6px', cssFloat:'left', cursor:'pointer'}
                });

                upArrow.observeClick(function(event) {
                    if (event.target) { // Firefox
                        var userId = event.target.id.split('_')[1];
                    } else { // IE
                        var userId = event.srcElement.id.split('_')[1];
                    }
                    self._upUser(userId);
                });
                userRowElements.push(upArrow);
                // Down arrow
                var downArrow = Html.img({
                    src: imageSrc("arrow_down"),
                    alt: $T('Down ') + this.userCaption,
                    title: $T('Down this ') + this.userCaption,
                    id: 'down_'+i,
                    style:{paddingTop: '6px', cssFloat:'left', cursor:'pointer'}
                });

                downArrow.observeClick(function(event) {
                    if (event.target) { // Firefox
                        var userId = event.target.id.split('_')[1];
                    } else { // IE
                        var userId = event.srcElement.id.split('_')[1];
                    }
                    self._downUser(userId);
                });
                userRowElements.push(downArrow);

            }

            var row = Html.li({className: this.elementClass, onmouseover: "this.style.backgroundColor = '#ECECEC';",
                                onmouseout : "this.style.backgroundColor='#ffffff';", style:{cursor:'auto'}});

            for (var j=userRowElements.length-1; j>=0; j--) { // Done the 'for' like this because of IE7
                row.append(userRowElements[j]);
            }

            this.inPlaceListElem.append(row);
        }
        this._checkEmptyList();
    },

    _checkEmptyList: function() {
        // To overwrite
    },

    _removeUser: function(userId) {
        var killProgress = IndicoUI.Dialogs.Util.progress();
        if (this.usersList.item(userId)) {
            this.usersList.remove(this.usersList.item(userId));
            this._updateUserList();
            killProgress();
            return;
        } else {
            killProgress();
            var popup = new AlertPopup($T('Remove ')+this.userCaption, $T('The user you are trying to remove does not exist.'));
            popup.open();
        }
    },

    _editUser: function(userId) {
        var self = this;
        if (this.usersList.item(userId)) {
            var killProgress = IndicoUI.Dialogs.Util.progress();
            var user = $O(this.usersList.item(userId));
            var editUserPopup = new UserDataPopup(
                $T('Edit ') + self.userCaption + $T(' data'),
                user,
                function(newData) {
                    if (editUserPopup.parameterManager.check()) {
                        self._userModifyData(userId, newData);
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

    _userModifyData: function(userId, newData) {
        this.usersList.item(userId)['title'] = any(newData.get('title'), '');
        this.usersList.item(userId)['familyName'] = any(newData.get('familyName'), '');
        this.usersList.item(userId)['firstName'] = any(newData.get('firstName'), '');
        this.usersList.item(userId)['affiliation'] = any(newData.get('affiliation'), '');
        this.usersList.item(userId)['email'] = any(newData.get('email'), '');
        this.usersList.item(userId)['address'] = any(newData.get('address'), '');
        this.usersList.item(userId)['phone'] = any(newData.get('phone'), '');
        this.usersList.item(userId)['fax'] = any(newData.get('fax'), '');
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
type("ModificationControlManager", ["ListOfUsersManager"], {

    _getAddExistingParams: function(userList) {
        var params = this.params;
        params['userList'] = userList;
        return params;
    },

    _getRemoveParams: function(userId) {
        var params = this.params;
        params['userId'] = userId;
        return params;
    },

    addExistingUser: function(){
        this._addExistingUser($T("Add ") + this.userCaption, true, this.confId, true, true, true, false, true);
    },

    _updateUserList: function(result) {
        var self = this;
        // update the user list
        this.inPlaceListElem.set('');
        for (var i=0; i<result.length; i++) {
            var userRowElements = [];

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
                var fullName = $T('Non-registered-user');
                var elementStyle = "UIPerson";
            }
            var userText = Html.span({className:'nameLink', cssFloat:'left'}, fullName, Html.small({},' ('+ result[i]['email'] + ')'));
            userRowElements.push(userText);

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
                id: 'remove_'+result[i]['id'],
                style:{marginRight:'10px', cssFloat:'right', cursor:'pointer'}
            });

            imageRemove.observeClick(function(event) {
                if (event.target) { // Firefox
                    var userId = event.target.id.split('_')[1];
                } else { // IE
                    var userId = event.srcElement.id.split('_')[1];
                }
                    self._manageUserList(self.methods["remove"], self._getRemoveParams(userId), false);
                });
            userRowElements.push(imageRemove);

            var row = Html.li({className: elementStyle, onmouseover: "this.style.backgroundColor = '#ECECEC';",
                                onmouseout : "this.style.backgroundColor='#ffffff';", style:{cursor:'auto'}});

            for (var j=userRowElements.length-1; j>=0; j--) { // Done the 'for' like this because of IE7
                row.append(userRowElements[j]);
            }
            this.inPlaceListElem.append(row);
        }
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
