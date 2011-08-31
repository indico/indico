/*
 * Manager of participant list in the contribution main tab
 */
type("ParticipantsListManager", ["ListOfUsersManager"], {

    _manageAllConectedUserList: function(method, params) {
        var self = this;
        indicoRequest(
                method, params,
                function(result, error) {
                    if (!error) {
                        if (self.eventType == "conference") {
                            // Update all lists of the page
                            primaryAuthorManager.drawUserList(result[0]);
                            coAuthorManager.drawUserList(result[1]);
                            speakerManager.drawUserList(result[2]);
                        } else {
                            speakerManager.drawUserList(result);
                        }
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

    _personName: function(user) {
        var content = this.ListOfUsersManager.prototype._personName.call(this, user);
        if (!user.showSubmitterCB) {
            content += '<small class="roleSmall"> Submitter </small>';
        }
        return content;
    },

    _drawUserList: function() {
        var self = this;

        var container = $(this.inPlaceListElem.dom).html('');

        this.usersList.each(function(val, idx) {
            var user = val;
            var elemStyle = self.elementClass;
            var row = $('<li/>').attr('class', elemStyle);
            _(self._component_order).each(function(opt, idx){
                if (self.userOptions[opt]) {
                    var comp = self._components[opt].call(self, user, self.userOptions[opt]);
                    row.append(comp);
                }
            });
            if (self.kindOfUser == "prAuthor" || self.kindOfUser == "coAuthor") {
                var spanClass = 'authorMove';
                row.attr('id', 'author_' + user.id);
            } else {
                var spanClass = 'nameLink';
            }
            row.append($('<span class=' + spanClass + ' />').append(
                self._personName(user)));

            container.append(row);
        });
        this._checkEmptyList();
    },

    canDropElement: function(elemId, list) {
        var authorId = elemId.split('_')[1];
        var author = this.getAuthorById(authorId);
        if (author) {
            for (var i=0; i<list.length.get(); i++) {
                if (author.email == list.item(i).email) {
            	    return false;
                }
            }
        }
        return true;
    },

    getAuthorById: function(authorId) {
        for (var i=0; i<this.usersList.length.get(); i++) {
            if (authorId == this.usersList.item(i).id) {
                return this.usersList.item(i);
            }
        }
        return null;
    },

    updateDraggableList: function(complementaryList) {
        var newList = $L();
        for(var i=0; i<this.inPlaceListElem.dom.children.length; i++) {
            var elemId = this.inPlaceListElem.dom.children[i].id.split('_')[1];
            var author = this.getAuthorById(elemId)
            if (author) {
                newList.append(author);
            } else {
            	// the author is in the other list
                author = complementaryList.getAuthorById(elemId);
                if (author) {
                    newList.append(author);
                }
            }
        }
        return newList;
    },

    _getParamsChangeSubmissionRights: function(userId, action) {
	    var params = this.userListParams;
	    params['userId'] = userId;
	    params['action'] = action;
	    params['eventType'] = this.eventType;
        return params;
    },

    _getParamsSendEmail: function(userId) {
        // Same params as remove, so we use the same method
    	return this._getRemoveParams(userId);
    },

    onMenu : function(element, user) {
        var self = this;
        var menuItems = {};

        if (user.showSubmitterCB) {
            menuItems[$T('Grant submission rights')] = function() {
                self._manageAllConectedUserList(self.methods["changeSubmission"], self._getParamsChangeSubmissionRights(user.id, "grant"));
                menu.close();
            };
        } else {
            menuItems[$T('Remove submission rights')] = function() {
            	self._manageAllConectedUserList(self.methods["changeSubmission"], self._getParamsChangeSubmissionRights(user.id, "remove"));
                menu.close();
            };
        }

        menuItems[$T('Send an email')] = function() {
            self._sendEmail(user.id);
            menu.close();
        };

        var menu = new PopupMenu(menuItems, [$E(element)], "popupList");
        var pos = $(element).position();
        menu.open(pos.left - 25, pos.top + 20);
    },

    addManagementMenu: function(){
        var self = this;
        this.inPlaceMenu.observeClick(function(e) {
            var menuItems = {};

            if (self.kindOfUser == 'speaker' && self.eventType == "conference") {
                menuItems[$T('Add from authors')] = function() {
                    self._addFromAuthorsList();
                };
            }

            menuItems[$T('Add existing')] = function() {
                self._addExistingUser($T("Add ")+self.userCaption, true, this.confId, false, true, true, false, true);
            };
            menuItems[$T('Add new')] = function() {
                self._addNonExistingUser();
            };

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList", true);
            var pos = self.inPlaceMenu.getAbsolutePosition();
            menu.open(pos.x + 40, pos.y + 20);
        });
    },

    _sendEmail: function(userId) {
        // request necessary data
        indicoRequest(this.methods["sendEmail"], this._getParamsSendEmail(userId),
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

    _addFromAuthorsList: function() {
        var self = this;
        // Create the popup to add suggested users
        var initialList = this._getAuthorsList();
        // params: (title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
        //          showToggleFavouriteButtons, chooseProcess)
        var chooseUsersPopup = new ChooseUsersPopup($T('Select presenter(s)'), false, this.confId, false, false,
                initialList, false, false,
                function(userList) {self._manageUserList(self.methods["addAuthorAsPresenter"], self._getAddExistingParams(userList));}
        );
        chooseUsersPopup.execute();
    },

    _getAuthorsList: function() {
        return primaryAuthorManager.getUsersList().allItems().concat(coAuthorManager.getUsersList().allItems());
    }

},

    function(confId, params, inPlaceListElem, inPlaceMenu, kindOfUser, userCaption, eventType, elementClass, initialList) {
        this.kindOfUser = kindOfUser;
	    this.eventType = eventType;

        this.methods = {'addNew': 'contribution.participants.addNewParticipant',
                        'addExisting': 'contribution.participants.addExistingParticipant',
                        'remove': 'contribution.participants.removeParticipant',
                        'edit': 'contribution.participants.editParticipantData',
                        'sendEmail': 'contribution.participants.sendEmailData',
                        'changeSubmission': 'contribution.participants.changeSubmissionRights',
                        'addAuthorAsPresenter': 'contribution.participants.addAuthorAsPresenter'};

        this.ListOfUsersManager(confId, this.methods, params, inPlaceListElem, userCaption, elementClass, false,
                {submission: true, management: false, coordination: false},
                {title: false, affiliation: true, email:false},
                {remove: true, edit: true, favorite: false, arrows: false, menu: true}, initialList, true, false, inPlaceMenu);
    }
);



/*
 * Manager of participant list in the subcontribution main tab
 */
type("SubContributionPresenterListManager", ["ListOfUsersManager"], {

    addManagementMenu: function(){
        var self = this;
        this.inPlaceMenu.observeClick(function(e) {
            var menuItems = {};

            if (self.eventType == "conference") {
                menuItems[$T('Add from authors')] = function(){ self._addFromAuthorsList(); };
            }

            menuItems[$T('Add existing')] = function(){ self._addExistingUser($T("Add ") + self.userCaption, true, this.confId, false,
                                                                               true, true, false, true); };
            menuItems[$T('Add new')] = function(){ self._addNonExistingUser(); };

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList", true);
            var pos = self.inPlaceMenu.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
    },

    _addFromAuthorsList: function() {
        var self = this;
        if (this.authorsList.length == 0) {
            // Show warning popup
            var popup = new AlertPopup($T('Warning'), $T('There are no authors available to add as presenters.'));
            popup.open();
        } else {
            var chooseUsersPopup = new ChooseUsersPopup($T('Select presenter(s)'), false, this.confId, false, false,
                    this.authorsList, false, false,
                    function(userList) {self._manageUserList(self.methods["addAuthorAsPresenter"], self._getAddExistingParams(userList));}
            );
            chooseUsersPopup.execute();
        }
    }

},

    function(confId, params, inPlaceListElem, inPlaceMenu, userCaption, initialList, authorsList, eventType) {
        this.methods = {'addNew': 'contribution.participants.subContribution.addNewParticipant',
                        'addExisting': 'contribution.participants.subContribution.addExistingParticipant',
                        'remove': 'contribution.participants.subContribution.removeParticipant',
                        'edit': 'contribution.participants.subContribution.editParticipantData',
                        'addAuthorAsPresenter': 'contribution.participants.subContribution.addAuthorAsPresenter'};
        this.authorsList = authorsList;
        this.eventType = eventType;

        this.ListOfUsersManager(confId, this.methods, params, inPlaceListElem, userCaption, "UIPerson", false,
            {submission: false, management: false, coordination: false},
            {title: false, affiliation: true, email:false},
            {remove: true, edit: true, favorite: false, arrows: false, menu: false}, initialList, true, false, inPlaceMenu);
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

            if (self.eventType == "conference") {
                menuItems[$T('Add from authors')] = function(){ self._addFromAuthorsList(); };
            }

            menuItems[$T('Add existing')] = function(){ self._addExistingUser($T("Add ") + self.userCaption, true, this.confId, false,
                                                                               true, true, false, true); };
            menuItems[$T('Add new')] = function(){ self._addNonExistingUser(); };

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList", true);
            var pos = self.inPlaceMenu.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
    },

    _addFromAuthorsList: function() {
        var self = this;
        if (this.authorsList.length == 0) {
            // Show warning popup
            var popup = new AlertPopup($T('Warning'), $T('There are no authors available to add as presenters.'));
            popup.open();
        } else {
            var chooseUsersPopup = new ChooseUsersPopup($T('Select presenter(s)'), false, this.confId, false, false,
                this.authorsList, false, false,
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
                    self._drawUserList();
                });
            chooseUsersPopup.execute();
        }
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

    function(inPlaceListElem, inPlaceMenu, parentElement, userCaption, authorsList, eventType) {
        this.parentElement = parentElement;
        this.authorsList = authorsList;
        this.eventType = eventType;

        this.ListOfUsersManagerForForm(null, inPlaceListElem, userCaption, "UIPerson", false,
                {submission: false, management: false, coordination: false},
                {title: false, affiliation: true, email:false},
                {remove: true, edit: true, favorite: false, arrows: false, menu: false}, [], true, false, inPlaceMenu);
    }
);


/*
 * Manager of submission control list
 */
type("SubmissionControlListManager", ["ListOfUsersManager"], {

    addExistingUser: function() {
        this._addExistingUser($T('Add submitter'), true, this.confId, true, true, null, false, true);
    },

    _getModifyAsAuthorParams: function(userId, kindOfList) {
        var params = this.userListParams;
        params['userId'] = userId;
        params['kindOfList'] = kindOfList;
        return params;
    },

    _personName: function(user) {
        var content = this.ListOfUsersManager.prototype._personName.call(this, user);
        if (user._type == 'Avatar') {
            var roles = '';
            var counter = 0;
            if (user.isPrAuthor) {
                roles += $T('Primary author');
                counter += 1;
            }
            if (user.isCoAuthor) {
                if (counter > 0)
                    roles += $T(', Co-author');
                else
                    roles += $T('Co-author');
                counter += 1;
            }
            if (user.isSpeaker) {
                if (counter > 0)
                    roles += $T(', ') + this.speakerCaptionCapital;
                else
                    roles += this.speakerCaptionCapital;
                counter += 1;
            }
            if (counter == 0)
                return content;
            else
                return content += '<small class="roleSmall">' + roles +  '</small>';
        } else {
            return content;
        }
    },

    onMenu : function(element, user) {
        var menuItems = {};
        var self = this;

        if (this.eventType == "conference") {
            if (!user.isPrAuthor) {
                menuItems[$T('Add as primary author')] = function() {
                    self._manageUserList(self.methods["addAsAuthor"], self._getModifyAsAuthorParams(user.id, "prAuthor"), false);
                    menu.close();
                };
            } else {
                menuItems[$T('Remove as primary author')] = function() {
                    self._manageUserList(self.methods["removeAsAuthor"], self._getModifyAsAuthorParams(user.id, "prAuthor"), false);
                    menu.close();
                };
            }

            if (!user.isCoAuthor) {
                menuItems[$T('Add as co-author')] = function() {
                    self._manageUserList(self.methods["addAsAuthor"], self._getModifyAsAuthorParams(user.id, "coAuthor"), false);
                    menu.close();
                };
            } else {
                menuItems[$T('Remove as co-author')] = function() {
                    self._manageUserList(self.methods["removeAsAuthor"], self._getModifyAsAuthorParams(user.id, "coAuthor"), false);
                    menu.close();
                };
            }
        }

        if (!user.isSpeaker) {
            menuItems[$T('Add as ') + self.speakerCaption] = function() {
                self._manageUserList(self.methods["addAsAuthor"], self._getModifyAsAuthorParams(user.id, "speaker"), false);
                menu.close();
            };
        } else {
            menuItems[$T('Remove as ') + self.speakerCaption] = function() {
                self._manageUserList(self.methods["removeAsAuthor"], self._getModifyAsAuthorParams(user.id, "speaker"), false);
                menu.close();
            };
        }

        var menu = new PopupMenu(menuItems, [$E(element)], "popupList");
        var pos = $(element).position();
        menu.open(pos.left - 25, pos.top + 20);
    }

},

    function(confId, params, inPlaceListElem, userCaption, eventType, initialList) {
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
                        'addAsAuthor': 'contribution.protection.submissionControl.addAsAuthor',
                        'removeAsAuthor':'contribution.protection.submissionControl.removeAsAuthor'};

        this.ListOfUsersManager(confId, this.methods, params, inPlaceListElem, userCaption, "UIPerson", true, {},
                {title: false, affiliation: false, email:false},
                {remove: true, edit: false, favorite: true, arrows: false, menu: true}, initialList);
    }
);
