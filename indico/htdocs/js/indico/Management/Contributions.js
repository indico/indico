/*
 * Manager of participant list in the contribution main tab
 */
type("ParticipantsListManager", ["ListOfUsersManager"], {

	_manageUserList: function(method, params, methodKey, progress, highlightUser) {
        var self = this;
        var progress = any(progress, true);
        var highlightUser = any(highlightUser, false);
        if (progress)
            var killProgress = IndicoUI.Dialogs.Util.progress();
        indicoRequest(
            method, params,
            function(result, error) {
                if (!error) {
                    if (self.eventType == "conference") {
                        if (methodKey == 'remove' && self.kindOfUser != 'speaker') {
                            // Update current list and speakers/presenters list
                            self._updateUserList(result[0]);
                            self.complementaryList2.updateUserList(result[1]);
                        } else if (methodKey == 'edit') {
                            if (self.kindOfUser == 'speaker') {
                                // Update all the lists
                                self._updateUserList(result[0]);
                                self.complementaryList1.updateUserList(result[1]);
                                self.complementaryList2.updateUserList(result[2]);
                            } else {
                                // Update current list and speakers/presenters list
                               self._updateUserList(result[0]);
                               self.complementaryList2.updateUserList(result[1]);
                            }
                        } else {
                            self._updateUserList(result);
                        }
                    } else {
                        self._updateUserList(result);
                    }
                    if (highlightUser)
                        IndicoUI.Effect.highLight('fullName_'+params['userId'], 'orange', 3000);
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

    _getAddNewParams: function(userData) {
        var params = {confId: this.confId, userData: userData, contribId: this.contribId, kindOfList: this.kindOfUser};
        return params;
    },

    _getAddExistingParams: function(userList) {
        var params = {confId: this.confId, userList: userList, contribId: this.contribId, kindOfList: this.kindOfUser};
        return params;
    },

    _getEditParams: function(userData) {
        var params = {confId: this.confId, userId: userData.get("id"), userData: userData, contribId: this.contribId,
                      kindOfList: this.kindOfUser, eventType: this.eventType};
        return params;
    },

    _getRemoveParams: function(userId) {
        return this._getParamsWithUserId(userId);
    },

    _getGetUserParams: function(userId) {
        return this._getParamsWithUserId(userId);
    },

    _getDownUserParams: function(userId) {
        return this._getParamsWithUserId(userId);
    },

    _getUpUserParams: function(userId) {
        return this._getParamsWithUserId(userId);
    },

    _getChangeSubmissionRightsParams: function(userId, action) {
        var params = {confId: this.confId, contribId: this.contribId, userId: userId, action: action,
                      kindOfList: this.kindOfUser, eventType: this.eventType};
        return params;
    },

    _getParamsWithUserId: function(userId) {
        var params = {confId: this.confId, contribId: this.contribId, userId: userId, kindOfList: this.kindOfUser};
        return params;
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
                        self._manageUserList(self.methods["edit"], self._getEditParams(newData), "edit");
                        editUserPopup.close();
                    }
                }, userData['showGrantSubmissionRights'], false);
        editUserPopup.open();
    },

    updateUserList: function(result) {
        // this method is implemented to give visibility from outside of the class, keeping the inheritance
        this._updateUserList(result);
    },

    _updateUserList: function(result) {
        var self = this;
        // update the user list
        this.inPlaceListElem.set('');
        for (var i=0; i<result.length; i++) {
            var userRowElements = [];

            if (!result[i]['showGrantSubmissionRights']) {
                // Show submitter
                var userText = Html.span({className:'nameLink', cssFloat:'left', id:'fullName_'+result[i]['id']}, result[i]['fullName'], Html.small({style:{paddingLeft:'5px'}}, $T('(Submitter)')));
            } else {
                var userText = Html.span({className:'nameLink', cssFloat:'left', id:'fullName_'+result[i]['id']}, result[i]['fullName']);
            }
            userRowElements.push(userText);

            // Options menu for each user
            var optionsMenuSpan = Html.span({onmouseover:"this.className = 'mouseover'",
                                        onmouseout:"this.className = ''", style:{cssFloat:'right'}});

            var optionsMenuLink = Html.a({id:'userMenu_' + result[i]['id'], className:'dropDownMenu fakeLink',
                                         style:{marginLeft:'15px', marginRight:'15px'}}, $T('More'));
            this._addParticipantMenu(optionsMenuLink, result[i]['id'], result[i]['showGrantSubmissionRights']);
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
                self._getUserData(self.methods["getUserData"], self._getGetUserParams(userId));
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
                self._manageUserList(self.methods["remove"], self._getRemoveParams(userId), "remove");
            });
            userRowElements.push(imageRemove);

            if (this.kindOfUser != "speaker") {
                // arrow icons
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
                    self._manageUserList(self.methods["downUser"], self._getDownUserParams(userId), "downUser", false, true);
                });
                userRowElements.push(downArrow);

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
                    self._manageUserList(self.methods["upUser"], self._getUpUserParams(userId), "upUser", false, true);
                });
                userRowElements.push(upArrow);
            }
            var row = Html.li({className: this.elementClass, onmouseover: "this.style.backgroundColor = '#ECECEC';",
                onmouseout : "this.style.backgroundColor='#ffffff';", style:{cursor:'auto'}});

            for (var j=userRowElements.length-1; j>=0; j--) { // Done the 'for' like this because of IE7
                row.append(userRowElements[j]);
            }

            this.inPlaceListElem.append(row);
        }
    },

    _addParticipantMenu : function(element, userId, showGrantSubmissionRights) {
        var self = this;

        element.observeClick(function(e) {
            var menuItems = {};
            if (self.kindOfUser == 'prAuthor')
                var opposite = 'co-author';
            else
                var opposite = 'primary author';

            if (self.kindOfUser != 'speaker') {
                menuItems[$T('Move to ') + opposite] = function() {
                    self._changeToOtherList(userId);
                    menu.close();
                };
            }

            if (showGrantSubmissionRights) {
                menuItems[$T('Grant submission rights')] = function() {
                    self._changeSubmissionRights(userId, "grant");
                    menu.close();
                };
            } else {
                menuItems[$T('Remove submission rights')] = function() {
                    self._changeSubmissionRights(userId, "remove");
                    menu.close();
                };
            }

            if (self.kindOfUser != 'speaker') {
                menuItems[$T('Send an email')] = function() {
                    self._sendEmail(userId);
                    menu.close();
                };
            }

            var menu = new PopupMenu(menuItems, [element], "popupList");
            var pos = element.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
    },

    addManagementMenu: function(){
        var self = this;
        this.inPlaceMenu.observeClick(function(e) {
            var menuItems = {};

            if (self.kindOfUser == 'speaker' && self.eventType == "conference") {
                menuItems[$T('Add from authors')] = function(){ self._addFromAuthorsList(); };
            }

            menuItems[$T('Add existing')] = function(){ self._addExistingUser($T("Add ")+self.userCaption, true, this.confId, false,
                                                                               true, true, false, true); };
            menuItems[$T('Add new')] = function(){ self._addNonExistingUser(); };

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList");
            var pos = self.inPlaceMenu.getAbsolutePosition();
            menu.open(pos.x + 40, pos.y + 20);
            return false;
        });
    },

    _changeToOtherList: function(userId) {
        var self = this;
        indicoRequest(
                self.methods["changeToList"], self._getParamsWithUserId(userId),
                function(result, error) {
                    if (!error) {
                        self._updateUserList(result[0]);
                        self.complementaryList1.updateUserList(result[1]);
                        IndicoUI.Effect.highLight('fullName_'+userId, 'orange', 3000);
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

    _sendEmail: function(userId) {
        // request necessary data
        indicoRequest(this.methods["sendEmail"], this._getParamsWithUserId(userId),
               function(result, error) {
                    if (!error) {
                        if (result["email"] == "") {
                            var popup = new AlertPopup($T('Impossible to send an email'), $T('The email of this author is empty, please complete a correct email address before sending the email.'));
                            popup.open();
                        } else {
                            // send the email
                            window.location = 'mailto:'+result["email"]+'?subject=['+result["confTitle"]+'] Contribution '+result["contribId"]+': '+result["contribTitle"];
                        }
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

    _changeSubmissionRights: function(userId, action) {
        var self = this;
        indicoRequest(this.methods["changeSubmission"], this._getChangeSubmissionRightsParams(userId, action),
                function(result, error) {
                    if (!error) {
                        if (self.eventType == "conference") {
                            if (self.kindOfUser != 'speaker') {
                                // Update current list and speakers/presenters list
                                self._updateUserList(result[0]);
                                self.complementaryList2.updateUserList(result[1]);
                                IndicoUI.Effect.highLight('fullName_'+userId, 'orange', 3000);
                            } else {
                                // Update all the lists
                                self._updateUserList(result[0]);
                                self.complementaryList1.updateUserList(result[1]);
                                self.complementaryList2.updateUserList(result[2]);
                           }
                        } else {
                            self._updateUserList(result);
                            IndicoUI.Effect.highLight('fullName_'+userId, 'orange', 3000);
                        }
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

    _addFromAuthorsList: function() {
        var self = this;
        var killProgress = IndicoUI.Dialogs.Util.progress();
        // Get the suggestedUsers
        indicoRequest(this.methods["getAllAuthors"], {confId: this.confId, contribId: this.contribId},
                function(result, error) {
                    if (!error) {
                        killProgress();
                        // Create the popup to add suggested users
                        // params: (title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
                        //          showToggleFavouriteButtons, chooseProcess)
                        var chooseUsersPopup = new ChooseUsersPopup($T('Select presenter(s)'), false, this.confId, false, false,
                                result, false, false,
                                function(userList) {self._manageUserList(self.methods["addAuthorAsPresenter"], self._getAddExistingParams(userList));}
                        );
                        chooseUsersPopup.execute();
                    } else {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

    setComplementariesList: function(complementaryList1, complementaryList2) {
        this.complementaryList1 = complementaryList1;
        this.complementaryList2 = complementaryList2;
    }

},

    function(confId, contribId, inPlaceListElem, inPlaceMenu, kindOfUser, userCaption, eventType, elementClass) {
        var self = this;
        this.confId = confId;
        this.contribId = contribId;
        this.eventType = eventType;

        this.methods = {'addNew': 'contribution.participants.addNewParticipant',
                        'addExisting': 'contribution.participants.addExistingParticipant',
                        'remove': 'contribution.participants.removeParticipant',
                        'edit': 'contribution.participants.editParticipantData',
                        'getUserData': 'contribution.participants.getParticipantData',
                        'getUserList': 'contribution.participants.getParticipantsList',
                        'upUser': 'contribution.participants.upParticipant',
                        'downUser': 'contribution.participants.downParticipant',
                        'changeToList': 'contribution.participants.changeAuthorToOtherList',
                        'sendEmail': 'contribution.participants.sendEmailData',
                        'changeSubmission': 'contribution.participants.changeSubmissionRights',
                        'getAllAuthors': 'contribution.participants.getAllAuthors',
                        'addAuthorAsPresenter': 'contribution.participants.addAuthorAsPresenter'};

        this.inPlaceMenu = inPlaceMenu;

        this.ListOfUsersManager(this.confId, this.methods,
                                {confId: this.confId, contribId: this.contribId, kindOfList: kindOfUser},
                                inPlaceListElem, kindOfUser, userCaption, elementClass, true, false, false, {remove: false, edit: true, favorite: false, arrows: true});
    }
);



/*
 * Manager of participant list in the subcontribution main tab
 */
type("SubContributionPresenterListManager", ["ListOfUsersManager"], {

    _getAddNewParams: function(userData) {
        var params = {confId: this.confId, contribId: this.contribId, subContribId: this.subContribId, userData: userData};
        return params;
    },

    _getAddExistingParams: function(userList) {
        var params = {confId: this.confId, contribId: this.contribId, subContribId: this.subContribId, userList: userList};
        return params;
    },

    _getEditParams: function(userData) {
        var params = {confId: this.confId, contribId: this.contribId, subContribId: this.subContribId, userData: userData};
        return params;
    },

    _getRemoveParams: function(userId) {
        var params = {confId: this.confId, contribId: this.contribId, subContribId: this.subContribId, userId: userId};
        return params;
    },

    _getGetUserParams: function(userId) {
        var params = {confId: this.confId, contribId: this.contribId, subContribId: this.subContribId, userId: userId};
        return params;
    },

    addManagementMenu: function(){
        var self = this;
        this.inPlaceMenu.observeClick(function(e) {
            var menuItems = {};

            menuItems[$T('Add from authors')] = function(){ self._addFromAuthorsList(); };

            menuItems[$T('Add existing')] = function(){ self._addExistingUser($T("Add ") + self.userCaption, true, this.confId, false,
                                                                               true, true, false, true); };
            menuItems[$T('Add new')] = function(){ self._addNonExistingUser(); };

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList");
            var pos = self.inPlaceMenu.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
    },

    _addFromAuthorsList: function() {
        var self = this;
        var killProgress = IndicoUI.Dialogs.Util.progress();
        // Get the suggestedUsers
        indicoRequest(this.methods["getAllAuthors"], {confId: this.confId, contribId: this.contribId},
                function(result, error) {
                    if (!error) {
                        killProgress();
                        // Create the popup to add suggested users
                        // params: (title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
                        //          showToggleFavouriteButtons, chooseProcess)
                        var chooseUsersPopup = new ChooseUsersPopup($T('Select presenter(s)'), false, this.confId, false, false,
                                result, false, false,
                                function(userList) {self._manageUserList(self.methods["addAuthorAsPresenter"], self._getAddExistingParams(userList));}
                        );
                        chooseUsersPopup.execute();
                    } else {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    }

},

    function(confId, contribId, subContribId, inPlaceListElem, inPlaceMenu, userCaption) {
        var self = this;
        this.confId = confId;
        this.contribId = contribId;
        this.subContribId = subContribId;
        this.methods = {'addNew': 'contribution.participants.subContribution.addNewParticipant',
                        'addExisting': 'contribution.participants.subContribution.addExistingParticipant',
                        'remove': 'contribution.participants.subContribution.removeParticipant',
                        'edit': 'contribution.participants.subContribution.editParticipantData',
                        'getUserData': 'contribution.participants.subContribution.getParticipantData',
                        'getUserList': 'contribution.participants.subContribution.getParticipantsList',
                        'getAllAuthors': 'contribution.participants.subContribution.getAllAuthors',
                        'addAuthorAsPresenter': 'contribution.participants.subContribution.addAuthorAsPresenter'};

        this.inPlaceMenu = inPlaceMenu;


        this.ListOfUsersManager(confId, this.methods, {confId: confId, contribId: this.contribId, subContribId: this.subContribId},
                                inPlaceListElem, null, userCaption, "UIPerson", false, false, true, false, {remove: true, edit: true, favorite: false, arrows: false});
    }
);



/*
 * Manager of participant list in creating a new sub contribution
 * The difference between this class and SubContributionPresenterListManager is that this object does not have
 * to send ajax request when a new participant is added/removed or edited.
 */
type("AddSubContributionPresenterListManager", ["ListOfUsersManagerForForm"], {

	addManagementMenu: function() {
        var self = this;
        this.inPlaceMenu.observeClick(function(e) {
            var menuItems = {};

            menuItems[$T('Add from authors')] = function(){ self._addFromAuthorsList(); };

            menuItems[$T('Add existing')] = function(){ self._addExistingUser($T("Add ") + self.userCaption, true, this.confId, false,
                                                                               true, true, false, true); };
            menuItems[$T('Add new')] = function(){ self._addNonExistingUser(); };

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList");
            var pos = self.inPlaceMenu.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
    },

    _addFromAuthorsList: function() {
        var self = this;
        var killProgress = IndicoUI.Dialogs.Util.progress();
        // Get the suggestedUsers
        indicoRequest(this.methods["getAllAuthors"], {confId: this.confId, contribId: this.contribId},
                function(result, error) {
                    if (!error) {
                        killProgress();
                        // Create the popup to add suggested users
                        // params: (title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
                        //          showToggleFavouriteButtons, chooseProcess)
                        var chooseUsersPopup = new ChooseUsersPopup($T('Select presenter(s)'), false, this.confId, false, false,
                                result, false, false,
                                function(userList) {
                                    for (var i=0; i<userList.length; i++) {
                                        if (!self._isAlreadyInList(userList[i]['email'])) {
                                            self.usersList.append(userList[i]);
                                        } else {
                                            var popup = new AlertPopup($T('Add ')+self.userCaption,
                                                            $T('The email address (') + userList[i]['email'] +
                                                            $T(') of a user you are trying to add is already used by another participant or the user is already added to the list.'));
                                            popup.open();
                                        }
                                    }
                                    self._updateUserList();
                                }
                        );
                        chooseUsersPopup.execute();
                    } else {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

    _checkEmptyList: function() {
        if (this.usersList.length.get() == 0) {
            this.parentElement.dom.style.display = 'none';
            this.inPlaceMenu.dom.style.marginLeft = '0px';
        } else {
            this.parentElement.dom.style.display = '';
            this.inPlaceMenu.dom.style.marginLeft = '15px';
        }
    }

},

    function(confId, contribId, inPlaceListElem, inPlaceMenu, parentElement, userCaption) {
        this.contribId = contribId;
        this.inPlaceMenu = inPlaceMenu;
        this.parentElement = parentElement;
        this.userCaption = userCaption;
        this.usersList = $L();
        this.methods = {'getAllAuthors': 'contribution.participants.subContribution.getAllAuthors'};

        this.ListOfUsersManagerForForm(confId, inPlaceListElem, true, true, false, false, userCaption, userCaption,
                                       "UIPerson", false, false, true);
    }
);


/*
 * Manager of submission control list
 */
type("SubmissionControlListManager", ["ListOfUsersManager"], {

    addExistingUser: function() {
        this._addExistingUser($T('Add submitter'), true, this.confId, true, true, null, false, true);
    },

    _getAddExistingParams: function(userList) {
        var params = {confId: this.confId, userList: userList, contribId: this.contribId};
        return params;
    },

    _getRemoveParams: function(userId, kindOfUser) {
        var params = {confId: this.confId, contribId: this.contribId, userId: userId, kindOfUser: kindOfUser};
        return params;
    },

    _getModifyAsAuthorParams: function(userId, kindOfList) {
        var params = {confId: this.confId, contribId: this.contribId, userId: userId, kindOfList: kindOfList};
        return params;
    },

    _getRolesText: function(user) {
        if (user['_type'] == 'Avatar') {
            var text = '(';
            var counter = 0;
            if (user['isPrAuthor']) {
                text += $T('Primary author');
                counter += 1;
            }
            if (user['isCoAuthor']) {
                if (counter > 0)
                    text += $T(', Co-author');
                else
                    text += $T('Co-author');
                counter += 1;
            }
            if (user['isSpeaker']) {
                if (counter > 0)
                    text += $T(', ') + this.speakerCaptionCapital;
                else
                    text += this.speakerCaptionCapital;
                counter += 1;
            }
            if (counter == 0)
                return null;
            else
                return Html.small({style:{paddingLeft:'5px'}}, text + ')');
        } else {
            return null;
        }
    },

    _updateUserList: function(result) {
        var self = this;
        // update the user list
        this.inPlaceListElem.set('');
        for (var i=0; i<result.length; i++) {
            var userRowElements = [];

            if (result[i]["pending"]) {
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, result[i]['name'], Html.small({style:{paddingLeft:'5px'}}, $T('(Pending)')), this._getRolesText(result[i]));
                var kindOfUser = "pending";
                var userIdentifier = result[i]['name'];
            } else {
                var userText = Html.span({className:'nameLink', cssFloat:'left', id:'fullName_'+result[i]['id']}, result[i]['name'], this._getRolesText(result[i]));
                var kindOfUser = "principal";
                var userIdentifier = result[i]['id'];
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
            if (IndicoGlobalVars.isUserAuthenticated &&
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
                style:{cssFloat:'right', cursor:'pointer', marginLeft:'4px', marginRight:'10px'}
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
        this._checkEmptyList(result);
    },

    _addParticipantMenu : function(element, user) {
        var self = this;

        element.observeClick(function(e) {
            var menuItems = {};

            if (self.eventType == "conference") {
                if (!user['isPrAuthor']) {
                    menuItems[$T('Add as primary author')] = function() {
                        self._manageUserList(self.methods["addAsAuthor"], self._getModifyAsAuthorParams(user['id'], "prAuthor"), false, true);
                        menu.close();
                    };
                } else {
                    menuItems[$T('Remove as primary author')] = function() {
                        self._manageUserList(self.methods["removeAsAuthor"], self._getModifyAsAuthorParams(user['id'], "prAuthor"), false, true);
                        menu.close();
                    };
                }

                if (!user['isCoAuthor']) {
                    menuItems[$T('Add as co-author')] = function() {
                        self._manageUserList(self.methods["addAsAuthor"], self._getModifyAsAuthorParams(user['id'], "coAuthor"), false, true);
                        menu.close();
                    };
                } else {
                    menuItems[$T('Remove as co-author')] = function() {
                        self._manageUserList(self.methods["removeAsAuthor"], self._getModifyAsAuthorParams(user['id'], "coAuthor"), false, true);
                        menu.close();
                    };
                }
            }

            if (!user['isSpeaker']) {
                menuItems[$T('Add as ') + self.speakerCaption] = function() {
                    self._manageUserList(self.methods["addAsAuthor"], self._getModifyAsAuthorParams(user['id'], "speaker"), false, true);
                    menu.close();
                };
            } else {
                menuItems[$T('Remove as ') + self.speakerCaption] = function() {
                    self._manageUserList(self.methods["removeAsAuthor"], self._getModifyAsAuthorParams(user['id'], "speaker"), false, true);
                    menu.close();
                };
            }

            var menu = new PopupMenu(menuItems, [element], "popupList");
            var pos = element.getAbsolutePosition();
            menu.open(pos.x-25, pos.y + 20);
            return false;
        });
    },

    _checkEmptyList: function(result) {
        if (result.length == 0)
            this.parentElement.dom.style.display = 'none';
        else
            this.parentElement.dom.style.display = '';
    }

},

    function(confId, contribId, inPlaceListElem, parentElement, userCaption, eventType) {
        this.confId = confId;
	    this.contribId = contribId;
        this.parentElement = parentElement;
        this.userCaption = userCaption;
        this.eventType = eventType;
        if (this.eventType == 'conference') {
            this.speakerCaption = $T('presenter');
            this.speakerCaptionCapital = $T('Presenter');
        }
        else if (this.eventType == 'meeting') {
            this.speakerCaption = $T('speaker');
            this.speakerCaptionCapital = $T('Speaker');
        }

        this.methods = {'addExisting': 'contribution.protection.submissionControl.addExistingSubmitter',
                        'remove': 'contribution.protection.submissionControl.removeSubmitter',
                        'getUserList': 'contribution.protection.submissionControl.getSubmittersList',
                        'addAsAuthor': 'contribution.protection.submissionControl.addAsAuthor',
                        'removeAsAuthor':'contribution.protection.submissionControl.removeAsAuthor'};

        this.ListOfUsersManager(confId, this.methods, {confId: confId, contribId: this.contribId},
                inPlaceListElem, true, true, false, false, null, userCaption, "UIPerson", false, false, true);
    }
);
