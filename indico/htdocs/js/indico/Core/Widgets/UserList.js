



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
 * @param: userOptionsMenu -> Bool, true if we want to show a menu with options for each row
 * @param: kindOfUser -> String, kind of user to show in the texts
 * @param: showGrantManagementCB -> show the checkbox to grant management rights in the AddNew/Edit popup
 */
type("ListOfUsersManager", [], {

    searchChairperson: function(title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
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

    _manageUserList: function(method, params) {
        var self = this;
        var killProgress = IndicoUI.Dialogs.Util.progress();
        indicoRequest(
                method, params,
                function(result, error) {
                    if (!error) {
                        self._updateUserList(result);
                        killProgress();
                    } else {
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

    _updateUserList: function(result) {
        var self = this;
        // update the user list
        this.inPlaceListElem.set('');
        for (var i=0; i<result.length; i++) {
            var userRowElements = [];

            var userFullName = Html.span({className:'nameLink', cssFloat:'left'}, result[i]['fullName']);
            userRowElements.push(userFullName);

            if (this.showEditIcon) {
                // edit icon
                var imageEdit = Html.img({
                    src: imageSrc("edit"),
                    alt: $T('Edit ') + this.kindOfUser,
                    title: $T('Edit this ') + this.kindOfUser,
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
                    alt: $T('Remove ') + this.kindOfUser,
                    title: $T('Remove this ') + this.kindOfUser + $T(' from the list'),
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

            if (this.showFavouritesIcon) {
                // TODO include the star and functionality in the user row
                //userRowElements.push(imageStar);
            }

            if(this.usersOptionsMenu) {
                // TODO include the options menu in the user row
                //userRowElements.push(options menu);
            }

            var row = Html.li({className:'UIPerson', onmouseover: "this.style.backgroundColor = '#ECECEC';",
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
                $T('New ') + self.kindOfUser,
                newUser,
                function(newData) {
                    if (newUserPopup.parameterManager.check()) {
                        self._manageUserList(self.methods["addNew"], self._getAddNewParams(newData));
                        newUserPopup.close();
                    }
                }, false, self.showGrantManagementCB);
        newUserPopup.open();
    },

    _showEditUserPopup: function(userData) {
        var self = this;
        // get the user data
        var user = $O(userData);
        var editUserPopup = new UserDataPopup(
                $T('Edit ') + self.kindOfUser + $T(' data'),
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

    function(confId, methods, userListParams, inPlaceListElem, showRemoveIcon, showEditIcon, showFavouritesIcon,
             userOptionsMenu, kindOfUser, showGrantManagementCB) {
        this.conferenceId = confId;
        this.methods = methods;
        this.userListParams = userListParams;
        this.inPlaceListElem = inPlaceListElem;
        this.showRemoveIcon = showRemoveIcon;
        this.showEditIcon = showEditIcon;
        this.showFavouritesIcon = showFavouritesIcon;
        this.userOptionsMenu = userOptionsMenu;
        this.kindOfUser = kindOfUser;
        this.showGrantManagementCB = showGrantManagementCB;
        var self = this;
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
        this.addManagementMenu();
    }
);
