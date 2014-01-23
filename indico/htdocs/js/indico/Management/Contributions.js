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
 * Manager of participant list in the subcontribution main tab
 */
type("SubContributionPresenterListManager", ["ListOfUsersManager"], {

    addManagementMenu: function(){
        var self = this;
        this.inPlaceMenu.observeClick(function(e) {
            var menuItems = {};
            var suggestedAuthors = true;

            if (self.eventType == "conference") {
                suggestedAuthors = self.authorsList;
            }

            menuItems["searchUser"] = {action: function(){ self._addExistingUser($T("Add ") + self.userCaption, true, this.confId, false,
                                                                               true, suggestedAuthors, false, true); }, display: $T('Add Indico User')};
            menuItems["addNew"] =  {action: function(){ self._addNonExistingUser();}, display: $T('Add New')};

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList", true);
            var pos = self.inPlaceMenu.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
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
            var suggestedAuthors = true;

            if (self.eventType == "conference") {
                suggestedAuthors = self.authorsList;
            }

            menuItems["searchUser"] = {action: function(){ self._addExistingUser($T("Add ") + self.userCaption, true, this.confId, false,
                                                                               true, suggestedAuthors, false, true); }, display: $T('Add Indico User')};
            menuItems["addNew"] = {action: function(){ self._addNonExistingUser(); }, display: $T('Add New')};

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList", true);
            var pos = self.inPlaceMenu.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
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
        this._addExistingUser($T('Add submitter'), true, this.confId, this.allowGroups, true, null, false, true);
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
                menuItems["addAsPrimaryAuthor"] = {action: function() {
                    self._manageUserList(self.methods["addAsAuthor"], self._getModifyAsAuthorParams(user.id, "prAuthor"), false);
                    menu.close();
                }, display: $T('Add as primary author')};
            } else {
                menuItems["removeAsPrimaryAuthor"] = {action: function() {
                    self._manageUserList(self.methods["removeAsAuthor"], self._getModifyAsAuthorParams(user.id, "prAuthor"), false);
                    menu.close();
                }, display: $T('Remove as primary author')};
            }

            if (!user.isCoAuthor) {
                menuItems["addAsCoAuthor"] = {action: function() {
                    self._manageUserList(self.methods["addAsAuthor"], self._getModifyAsAuthorParams(user.id, "coAuthor"), false);
                    menu.close();
                }, display: $T('Add as co-author')};
            } else {
                menuItems["removeAsCoAuthor"] = {action: function() {
                    self._manageUserList(self.methods["removeAsAuthor"], self._getModifyAsAuthorParams(user.id, "coAuthor"), false);
                    menu.close();
                }, display: $T('Remove as co-author')};
            }
        }

        if (!user.isSpeaker) {
            menuItems["addAsAuthor"] = {action: function() {
                self._manageUserList(self.methods["addAsAuthor"], self._getModifyAsAuthorParams(user.id, "speaker"), false);
                menu.close();
            }, display: $T('Add as ') + self.speakerCaption};
        } else {
            menuItems["removeAsAuthor"] = {action: function() {
                self._manageUserList(self.methods["removeAsAuthor"], self._getModifyAsAuthorParams(user.id, "speaker"), false);
                menu.close();
            }, display: $T('Remove as ') + self.speakerCaption };
        }

        var menu = new PopupMenu(menuItems, [$E(element)], "popupList");
        var pos = $(element).offset();
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
