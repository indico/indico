/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
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
                            if (self.kindOfUser == "chairperson") {
                                chairPersonsManager.drawUserList(result);
                            } else {
                                primaryAuthorManager.drawUserList(result[0]);
                                coAuthorManager.drawUserList(result[1]);
                                speakerManager.drawUserList(result[2]);
                            }
                        } else {
                            speakerManager.drawUserList(result);
                        }
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

    removeAuthorById: function(authorId) {
        for (var i=0; i<this.usersList.length.get(); i++) {
            var item = this.usersList.item(i);
            if (authorId == item.id) {
                this.usersList.remove(item);
                break;
            }
        }
        return;
    },

    _personName: function(user) {
        var data = this.ListOfUsersManager.prototype._personName.call(this, user);
        if (!user.showSubmitterCB) {
            data.roles = ['Submitter'];
        }
        return data;
    },

    canDrop: function(authorEmail) {
        var list = this.getUsersList();
        for (var i=0; i<list.length.get(); i++) {
            if (authorEmail == list.item(i).email) {
                return false;
            }
        }
        return true;
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
            menuItems["grantSubmissionRights"] = {action: function() {
                self._manageAllConectedUserList(self.methods["changeSubmission"], self._getParamsChangeSubmissionRights(user.id, "grant"));
                menu.close();
            }, display: $T('Grant submission rights')};
        } else {
            menuItems["removeSubmissionRights"] = {action: function() {
                self._manageAllConectedUserList(self.methods["changeSubmission"], self._getParamsChangeSubmissionRights(user.id, "remove"));
                menu.close();
            }, display: $T('Remove submission rights') };
        }

        menuItems["sendEmail"] = {action: function() {
            self._sendEmail(user.id);
            menu.close();
        }, display: $T('Send an email')};

        var menu = new PopupMenu(menuItems, [$E(element)], "popupList");
        var pos = $(element).offset();
        menu.open(pos.left, pos.top + 20);
    },

    addManagementMenu: function(){
        var self = this;
        this.inPlaceMenu.observeClick(function(e) {
            var menuItems = {};

            menuItems["searchUser"] = {action: function() {
                var privilegesDiv = Html.div({style:{marginTop: pixels(10)}});
                var checkbox = Html.checkbox({style:{verticalAlign:"middle"}}, true);
                checkbox.dom.id = "presenter-grant-submission";
                privilegesDiv.append(Html.span({},checkbox, "Grant all the selected users with submission rights"));
                self._addExistingUser($T("Add ")+self.userCaption, true, this.confId, false, true, self.suggestedAuthors, false, true, {"presenter-grant-submission": function(){return $("#presenter-grant-submission")[0].checked;}}, privilegesDiv);
            }, display: $T('Add Indico User')};
            menuItems["addNew"] = {action: function() {
                self._addNonExistingUser();
            }, display: $T('Add new')} ;

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList", true);
            var pos = $(self.inPlaceMenu.dom).offset();
            menu.open(pos.left, pos.top + 20);
        });
    },

    _sendEmail: function(userId) {
        // request necessary data
        indicoRequest(this.methods["sendEmail"], this._getParamsSendEmail(userId),
               function(result, error) {
                    if (!error) {
                        if (result["email"] == "") {
                            var popup = new AlertPopup($T('Impossible to send an email'), $T('The email of this user is empty, please complete a correct email address before sending the email.'));
                            popup.open();
                        } else {
                            // send the email
                            if (result["contribId"] == undefined) {
                                window.location = 'mailto:'+result["email"]+'?subject=['+result["confTitle"]+']';
                            } else {
                                window.location = 'mailto:'+result["email"]+'?subject=['+result["confTitle"]+'] Contribution '+result["contribId"]+': '+result["contribTitle"];
                            }
                        }
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    }
},

    function(confId, methods, params, inPlaceListElem, inPlaceMenu, kindOfUser, userCaption, eventType, elementClass, initialList, suggestedAuthors) {
        this.kindOfUser = kindOfUser;
        this.eventType = eventType;
        this.suggestedAuthors = suggestedAuthors
        this.rightsToShow = {submission: true, management: false, coordination: false};
        this.nameOptions = {title: false, affiliation: true, email:false};
        if (kindOfUser == "chairperson") {
            this.rightsToShow = {submission: true, management: true, coordination: false};
            this.nameOptions = {title: true, affiliation: false, email:false};
        }
        this.ListOfUsersManager(confId, methods, params, inPlaceListElem, userCaption, elementClass, false,
                this.rightsToShow,
                this.nameOptions,
                {remove: true, edit: true, favorite: false, arrows: false, menu: true}, initialList, true, false, inPlaceMenu);
    }
);
