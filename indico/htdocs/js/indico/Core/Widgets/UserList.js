
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
 * @param: userOptionsMenu -> Bool, true if we want to show a menu with options for each row
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

            if (this.showFavouritesIcon) {
                // TODO include the star and functionality in the user row
                //userRowElements.push(imageStar);
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

            var row = Html.li({className: this.elementClass, onmouseover: "this.style.backgroundColor = '#ECECEC';",
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
