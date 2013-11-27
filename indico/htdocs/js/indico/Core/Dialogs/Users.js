/* This file is part of Indico.
 * Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

function userListNothing(data, func) {
    each(data, function() {
        func(true);
    });
}

function singleUserNothing(user, func) {
    func(true);
}

function arrayToSet(array) {
    var set = {};
    each(array, function(item){
        set[item] = true;
    });
    return set;
}

function userSort(user1, user2) {
    if (user1.familyName > user2.familyName) {
        return 1;
    } else if (user1.familyName == user2.familyName) {
        if (user1.firstName > user2.firstName) {
            return 1;
        } else if (user1.firstName == user2.firstName) {
            return 0;
        } else {
            return -1;
        }
    } else {
        return -1;
    }
}

function updateFavList(favouriteList) {
    IndicoGlobalVars['favorite-user-ids'] = {};
    IndicoGlobalVars['favorite-user-list'] = [];
    each(favouriteList, function(user) {
        IndicoGlobalVars['favorite-user-ids'][user.id] = true;
        IndicoGlobalVars['favorite-user-list'].push(user);
    });
}

/**
 * @param {String} style The class name of the <ul> element inside this FoundPeopleList
 *                       If left to null, it will be "UIPeopleList"
 *
 * @param {Function} selectionObserver A function that will be called when the selection varies. The function will be called without arguments
 *                                     (it can use public methods of FoundPeopleList to get information).
 *
 * @param {Boolean} onlyOne If true, only 1 item can be selected at a time.
 */
type ("FoundPeopleList", ["SelectableListWidget"], {

    _drawItem: function(pair) {
        var self = this;
        var peopleData = pair.get();

        if (peopleData.get('isGroup') || peopleData.get('_type') === 'group') {
            return Html.span({}, peopleData.get("name"));
        } else {

            var userName = Html.span({}, peopleData.get("familyName").toUpperCase(), ', ', peopleData.get("firstName"));
            var userEmail = Html.span({id: self.id + "_" + pair.key + "_email", className: "foundUserEmail"}, Html.br(), Util.truncate(peopleData.get("email"), 40));

            if (this.showToggleFavouriteButtons && IndicoGlobalVars.isUserAuthenticated && peopleData.get('_type') == "Avatar") {
                var favouritizeButton = new ToggleFavouriteButton(peopleData.getAll(), null, null, this.favouriteButtonObserver).draw();
                var favouritizeButtonDiv = Html.div({style: {cssFloat: "right"}}, favouritizeButton);
                return [favouritizeButtonDiv, userName, userEmail];
            } else {
                return [userName, userEmail];
            }

        }
    }
},

    /**
     * Constructor for FoundPeopleList
     */
    function(style, onlyOne, selectionObserver, showToggleFavouriteButtons, favouriteButtonObserver) {

        if (!exists(style)) {
            style = "UIPeopleList";
        }

        this.onlyOne = any(onlyOne,false);
        this.showToggleFavouriteButtons = any(showToggleFavouriteButtons, true);
        this.favouriteButtonObserver = any(favouriteButtonObserver, null);

        /*this.lastTargetListItem = null;*/

        this.SelectableListWidget(selectionObserver, this.onlyOne, style, "selectedUser", "unselectedUser"); //, this.__mouseoverObserver);
    }
);


/**
 * Base class for UserSearchPanel and GroupSearchPanel
 * @param {Boolean} onlyOne If true, only 1 item can be selected at a time.
 * @param {function} selectionObserver Function that will be called when the selected users xor groups change.
 *                                     Will be passed to the inner FoundPeopleList.
 */
type ("SimpleSearchPanel", ["IWidget"], {

   /**
    * Simulates a click in the search button
    */
   _searchAction: function() {
       Dom.Event.dispatch(this.searchButton.dom, 'click');
   },

   /**
    * Form to fill in group search data
    */
   _createSearchForm: function() {
       // To be overloaded by implementing classes
   },

   /**
    * Function to be executed when the search button is pressed
    */
   _search: function() {
       // To be overloaded by implementing classes
   },

   /**
    * Returns the part of the form corresponding to search including external authenticators
    * Should be called by the implementing classes' _createSearchForm method.
    */
   _createAuthenticatorSearch: function() {
       var self = this;

       if (empty(Indico.Settings.ExtAuthenticators)) {
           return null;
       } else {
           var authenticatorList = [];
           each(Indico.Settings.ExtAuthenticators, function(auth) {
               var searchExternalCB = Html.checkbox({});
               $B(searchExternalCB, self.criteria.accessor('searchExternal-' + auth[0]));
               authenticatorList.push(["Search " + auth[1], searchExternalCB]);
           });
           return authenticatorList;
       }
   },

   /**
    * Returns the list of selected users xor groups for this panel
    */
   getSelectedList: function() {
       return this.foundPeopleList.getSelectedList();
   },

   /**
    * Clears the selection
    */
   clearSelection: function() {
       this.foundPeopleList.clearSelection();
   },

   /**
    * Returns the Panel's DOM
    */
   draw: function() {
       var self = this;

       this.searchForm = this._createSearchForm();

       this.searchButton = Html.input("button", {}, $T("Search"));
       this.searchButtonDiv = Html.div("searchUsersButtonDiv",this.searchButton);
       this.searchButton.observeClick(function(){
           self._search();
       });

       this.foundPeopleListDiv = Html.div("UISearchPeopleListDiv", this.foundPeopleList.draw());

       this.container = Html.div({}, this.searchForm.get(), this.searchButtonDiv, this.foundPeopleListDiv, this.extraDiv);

        if (this.submissionRights) {
            var checkbox = Html.checkbox({}, true);
            $B(this.grantRights.accessor('submission'), checkbox);
            var submissionDiv = Html.div({style: {marginTop: pixels(5), marginLeft: pixels(-4)}}, checkbox, $T("Grant all selected users submission rights"));
            this.container.append(submissionDiv);
        }

       return this.IWidget.prototype.draw.call(this, this.container);
   }
},

    /**
     * Constructor for SimpleSearchPanel
     */
    function(onlyOne, selectionObserver, showToggleFavouriteButtons, favouriteButtonObserver, submissionRights, grantRights, extraDiv) {

        this.IWidget();
        this.onlyOne = any(onlyOne, false);

        this.criteria = new WatchObject();

        this.foundPeopleList = new FoundPeopleList(null, this.onlyOne, selectionObserver, showToggleFavouriteButtons, favouriteButtonObserver);
        this.foundPeopleList.setMessage("Fill any of the upper fields and click search...");
        this.extraDiv = any(extraDiv, Html.div({}));

        this.searchForm = null;
        this.searchButton = null;
        this.searchButtonDiv = null;
        this.foundPeopleListDiv = null;
        this.container = null;

        this.submissionRights = submissionRights;
        this.grantRights = grantRights;
   }
);


/**
 * Panel to search for users.
 * @param {Boolean} onlyOne If true, only 1 item can be selected at a time.
 * @param {function} selectionObserver Function that will be called when the selected users xor groups change.
 *                                     Will be passed to the inner FoundPeopleList.
 */
type ("UserSearchPanel", ["SimpleSearchPanel"], {

    /**
     * Form to fill in user search data
     */
    _createSearchForm: function() {
        var self = this;

        var familyName = new EnterObserverTextBox("text",{style:{width:"100%"},id:'userSearchFocusField'}, function() {
            self._searchAction();
            return false;
        });

        var firstName = new EnterObserverTextBox("text",{style:{width:"100%"}}, function() {
            self._searchAction();
            return false;
        });

        var email = new EnterObserverTextBox("text",{style:{width:"100%"}}, function() {
            self._searchAction();
            return false;
        });

        var organisation = new EnterObserverTextBox("text",{style:{width:"100%"}}, function() {
            self._searchAction();
            return false;
        });

        var exactMatch = Html.checkbox({});

        $B(familyName, this.criteria.accessor('surName'));
        $B(firstName, this.criteria.accessor('name'));
        $B(organisation, this.criteria.accessor('organisation'));
        $B(email, this.criteria.accessor('email'));
        $B(exactMatch, this.criteria.accessor('exactMatch'));

        var fieldList = [[$T("Family name"), familyName.draw()],
                         [$T("First name"), firstName.draw()],
                         [$T("E-mail"), email.draw()],
                         [$T("Organisation"), organisation.draw()],
                         [$T("Exact Match"), exactMatch]];

        var authenticatorSearch = this._createAuthenticatorSearch();
        if (exists(authenticatorSearch)) {
            fieldList = concat(fieldList, authenticatorSearch);
        }

        return IndicoUtil.createFormFromMap(fieldList, true);
    },

    /**
     * Function that is called when the Search button is pressed.
     */
    _search: function() {
        var self = this;

        self.searchButton.dom.disabled = true;
        this.foundPeopleList.setMessage(Html.div({style: {paddingTop: '20px'}}, progressIndicator(false, true)));

        indicoRequest(
            'search.users',
            self.criteria,
            function(result,error) {
                if (!error) {
                    self.foundPeopleList.clearList();
                    if (result.length === 0) {
                        self.foundPeopleList.setMessage($T("No results for this search..."));
                    } else {
                        each(result, function(user){
                            if (user._type === "Avatar") {
                                self.foundPeopleList.set('existingAv' + user.id, $O(user));
                            } else if (user._type === "ContributionParticipation") {
                                self.foundPeopleList.set('existingAuthor' + user.id, $O(user));
                            }
                        });
                    }
                    self.searchButton.dom.disabled = false;
                } else {
                    self.foundPeopleList.clearList();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    },
    /**
     * Returns the panel's DOM
     */
    draw: function() {
        return this.SimpleSearchPanel.prototype.draw.call(this);
    }
},

    /**
     * Constructor for UserSearchPanel
     */
    function(onlyOne, selectionObserver, conferenceId, showToggleFavouriteButtons, favouriteButtonObserver, submissionRights, grantRights, extraDiv){
        this.SimpleSearchPanel(onlyOne, selectionObserver, showToggleFavouriteButtons, favouriteButtonObserver, submissionRights, grantRights, extraDiv);
        if(exists(conferenceId)) {
            this.criteria.set("conferenceId", conferenceId);
        }
    }
);


/**
 * Panel to search for groups.
 * @param {Boolean} onlyOne If true, only 1 item can be selected at a time.
 * @param {function} selectionObserver Function that will be called when the selected users xor groups change.
 *                                     Will be passed to the inner FoundPeopleList.
 */
type ("GroupSearchPanel", ["SimpleSearchPanel"], {

    /**
     * Form to fill in group search data
     */
    _createSearchForm: function() {

        var self = this;

        var groupName = new EnterObserverTextBox("text",{style:{width:"100%"}}, function() {
            self._searchAction();
            return false;
        });

        $B(groupName, this.criteria.accessor('group'));

        var fieldList = [[$T("Group name"), groupName.draw()]];

        var authenticatorSearch = this._createAuthenticatorSearch();
        if (exists(authenticatorSearch)) {
            fieldList = concat(fieldList, authenticatorSearch);
        }

        return IndicoUtil.createFormFromMap(fieldList, true);
    },

    /**
     * Function that is called when the Search button is pressed.
     */
    _search: function() {
        var self = this;

        self.searchButton.dom.disabled = true;
        this.foundPeopleList.setMessage(Html.div({style: {paddingTop: '20px'}}, progressIndicator(false, true)));

        indicoRequest(
            'search.groups',
            self.criteria,
            function(result,error) {
                if (!error) {
                    self.foundPeopleList.clearList();
                    if (result.length === 0) {
                        self.foundPeopleList.setMessage($T("No results for this search..."));
                    } else {
                        each(result, function(group){
                            self.foundPeopleList.set(group.name, $O(group));
                        });
                    }
                    self.searchButton.dom.disabled = false;
                } else {
                    self.foundPeopleList.clearList();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    },

    /**
     * Returns the panel's DOM
     */
    draw: function() {
        return this.SimpleSearchPanel.prototype.draw.call(this);
    }
},

    /**
     * Constructor for GroupSearchPanel
     */
    function(onlyOne, selectionObserver, conferenceId, showToggleFavouriteButtons){
        this.SimpleSearchPanel(onlyOne, selectionObserver, conferenceId, showToggleFavouriteButtons);
    }
);


/**
 * Tabbed panel to search either for users or groups
 * @param {Boolean} onlyOne If true, only 1 item can be selected at a time.
 * @param {function} selectionObserver Function that will be called when the selected users xor groups change.
 *                                     Will be passed to the inner FoundPeopleList.
 */
type ("UserAndGroupsSearchPanel", ["IWidget"], {

    /**
     * Function that will be called when the selection changes in either of the panel
     * @param {String} panel 'users' or 'groups', to know which panel's selection changed
     * @param {WatchObject} selectedList a list of selected users.
     */
    __selectionObserver: function(panel, selectedList) {

        if (this.onlyOne) {
            if (panel === "users") {
                this.groupPanel.clearSelection();
            } else {
                this.userPanel.clearSelection();
            }
            this.parentSelectionObserver(selectedList);
        } else {
            var totalSelection = $O();
            totalSelection.update(this.userPanel.getSelectedList().getAll());
            totalSelection.update(this.groupPanel.getSelectedList().getAll());
            this.parentSelectionObserver(totalSelection);
        }
    },

    /**
     * Returns the list of selected users / groups in both panels
     * @return {WatchObject} The list of selected users. Key = user / group id, value = user data
     */
    getSelectedList: function() {
        var totalSelection = $O();

        totalSelection.update(this.userPanel.getSelectedList().getAll());
        totalSelection.update(this.groupPanel.getSelectedList().getAll());

        return totalSelection;
    },

    /**
     * Clears the selection in both panels
     */
    clearSelection: function() {
        this.userPanel.clearSelection();
        this.groupPanel.clearSelection();
    },

    /**
     * Returns the panel's DOM
     */
    draw: function() {
        var self = this;

        this.tabWidget = new JTabWidget([[$T("Users"), this.userPanel.draw()], [$T("Groups"), this.groupPanel.draw()]]);

        return this.IWidget.prototype.draw.call(this, this.tabWidget.draw());
    }
},

    /**
     * Constructor for UserAndGroupsSearchPanel
     */
    function(onlyOne, selectionObserver, conferenceId, showToggleFavouriteButtons, favouriteButtonObserver, submissionRights, grantRights, extraDiv){
        this.IWidget();
        this.onlyOne = any(onlyOne, false);
        this.parentSelectionObserver = selectionObserver;

        var self = this;

        this.userPanel = new UserSearchPanel(this.onlyOne, function(selectedList){
            self.__selectionObserver("users", selectedList);
        }, conferenceId, showToggleFavouriteButtons, favouriteButtonObserver, submissionRights, grantRights, extraDiv);
        this.groupPanel = new GroupSearchPanel(this.onlyOne, function(selectedList){
            self.__selectionObserver("groups", selectedList);
        }, showToggleFavouriteButtons);

        this.tabWidget = null;
    }
);


/**
 * Panel with a list of suggested users.
 * @param {Boolean} onlyOne If true, only 1 item can be selected at a time.
 * @param {Boolean} includeFavourites If True, favourites will appear in the list of suggested users of the ChooseUsersPopup.
 * @param {WatchObject} suggestedUsers A list of users that will be used as list of suggested users.
 *                                     This argument has to be an array or WatchList where the keys are the user ids and the values are fossils/dictionaries with the user data.
 *                                     If null, there will be no suggestedUsers panel.
 * @param {function} selectionObserver Function that will be called when the selected users xor groups change.
 *                                     Will be passed to the inner FoundPeopleList.
 */
type ("SuggestedUsersPanel", ["IWidget"], {

    getSelectedList: function() {
        return this.suggestedUserList.getSelectedList();
    },

    clearSelection: function() {
        this.suggestedUserList.clearSelection();
    },

    draw: function() {
        var self = this;

        this.titleDiv = Html.div("suggestedUsersTitle", Html.span({},$T("Suggested users")));

        if (this.suggestedUserList.isEmpty()) {
            var message = Html.span({}, $T("There are no suggested users for you at the moment. Why not add some "),
                                        Html.a({href: build_url(Indico.Urls.Favourites)}, $T("favourites")),
                                        "?");
            this.suggestedUserList.setMessage(message);
        }

        this.suggestedUserListDiv = Html.div("UISuggestedPeopleListDiv", this.suggestedUserList.draw());

        return this.IWidget.prototype.draw.call(this, Widget.block([this.titleDiv, this.suggestedUserListDiv]));
    }
},

    /**
     * Constructor for SuggestedUsersPanel
     */
    function(onlyOne, includeFavourites, suggestedUsers, selectionObserver, showToggleFavouriteButtons){
        this.IWidget();

        this.onlyOne = any(onlyOne, false);

        includeFavourites = any(includeFavourites, true);

        this.suggestedUserList = new FoundPeopleList(null, this.onlyOne, selectionObserver, showToggleFavouriteButtons);

        var self = this;

        if (exists(suggestedUsers)) {
            each(suggestedUsers, function(user){
                if (any(user._type, null) === "Avatar") {
                    self.suggestedUserList.set('existingAv' + user.id, $O(user));
                } else {
                    self.suggestedUserList.set(user.id, $O(user));
                }
            });
        }

        if (includeFavourites) {
            each(IndicoGlobalVars['favorite-user-list'], function(user){
                var id = user.id;
                if (exists(IndicoGlobalVars['favorite-user-ids'][id]) && IndicoGlobalVars['favorite-user-ids'][id] && !self.suggestedUserList.get('existingAv' + id)) {
                    self.suggestedUserList.set('existingAv' + id, $O(user));
                }
            });
        }

        this.titleDiv = null;
        this.suggestedUserListDiv = null;
    }
);


/**
 * Creates a popup to add users in different ways (search in DB, choose from favourites, add a new one...).
 *
 * @param {String} title The dialog title
 *
 * @param {Boolean} allowSearch If this is true, a search user panel will appear.
 * @param {Integer} conferenceId If allowSearch is true, and if this is different from null, authors from that conference will be included in the search results.
 * @param {Boolean} enableGroups If allowSearch is true, and if this is true, groups will be available for search and add.
 *
 * @param {Boolean} includeFavourites If True, favourites will appear in the list of suggested users of the ChooseUsersPopup.
 * @param {WatchObject} suggestedUsers An array or WatchList of users that will be used as list of suggested users. The users
 *                                     should be fossils / dictionaries with the user data.
 *                                     If null, there will be no suggestedUsers panel.
 *
 * @param {Boolean} onlyOne If true, only 1 user will be able to be chosen in the dialog..
 *
 * @param {Function} process A function that will be called when new users (from new data, or from the search dialog, or from the suggested list) is added to the list.
 *                           The function will be passed a list of WatchObjects representing the users, even when onlyOne is true.
 */
type("ChooseUsersPopup", ["ExclusivePopupWithButtons", "PreLoadHandler"], {

    _preload: [

        function(hook) {
            var self = this;

            if (exists(IndicoGlobalVars['favorite-user-list'])) {
                hook.set(true);
            } else {
                var killProgress = IndicoUI.Dialogs.Util.progress($T("Loading dialog..."));
                indicoRequest('user.favorites.listUsers', {},
                    function(result, error) {
                        if (!error) {
                            updateFavList(result);
                            killProgress();
                            hook.set(true);
                        } else {
                            killProgress();
                            IndicoUI.Dialogs.Util.error(error);
                        }
                    }
                );
            }
        }
    ],

    __buildSearchPanel: function(container) {
        var self = this;
        if (this.enableGroups) {
            this.searchPanel = new UserAndGroupsSearchPanel(this.onlyOne, function(selectedList){
                self.__selectionObserver("searchUsers", selectedList);
            }, this.conferenceId, this.showToggleFavouriteButtons, function(avatar, action) {
                self.__searchPanelFavouriteButtonObserver(avatar, action);
            }, this.submissionRights, this.grantRights, self.extraDiv);
        } else {
            this.searchPanel = new UserSearchPanel(this.onlyOne, function(selectedList) {
                self.__selectionObserver("searchUsers", selectedList);
            }, this.conferenceId, this.showToggleFavouriteButtons, function(avatar, action) {
                self.__searchPanelFavouriteButtonObserver(avatar, action);
            }, this.submissionRights, this.grantRights, self.extraDiv);
        }
        var returnedDom = this.searchPanel.draw();
        container.append(returnedDom);
    },

    __buildSuggestedUsersPanel: function(container) {
        var self = this;

        this.suggestedUsersPanel = new SuggestedUsersPanel(this.onlyOne, this.includeFavourites, this.suggestedUsers, function(selectedList){
            self.__selectionObserver("suggestedUsers", selectedList);
        }, this.showToggleFavouriteButtons);

        container.append(this.suggestedUsersPanel.draw());
    },

    __selectionObserver: function(panel, selectedList) {

        if (this.onlyOne) {
            if (panel === "searchUsers") {
                this.suggestedUsersPanel.clearSelection();
            } else {
                this.searchPanel.clearSelection();
            }
            if (selectedList.isEmpty()) {
                this._toggleSaveButton(false);
            } else {
                this._toggleSaveButton(true);
            }

        } else {

            if (!selectedList.isEmpty()) {
                this._toggleSaveButton(true);
            } else {
                var twoPanels = this.allowSearch && (this.includeFavourites || exists(this.suggestedUsers));
                if (twoPanels) {
                    var otherSelectedList = (panel === "searchUsers") ? this.suggestedUsersPanel.getSelectedList() : this.searchPanel.getSelectedList();
                    if (otherSelectedList.isEmpty()) {
                        this._toggleSaveButton(false);
                    } else {
                        this._toggleSaveButton(true);
                    }
                } else {
                    this._toggleSaveButton(false);
                }
            }
        }
    },

    __save: function() {
        var self = this;
        var totalSelected = $O({});
        if (this.allowSearch) {
            totalSelected.update(this.searchPanel.getSelectedList().getAll());
        }
        if (this.includeFavourites || exists(this.suggestedUsers)) {
            totalSelected.update(this.suggestedUsersPanel.getSelectedList().getAll());
        }
        var returnedList = new List();
        each(totalSelected, function(selectedItem) {
            if (self.submissionRights) {
                selectedItem.set('isSubmitter', self.grantRights.get('submission'));
            }
            returnedList.append(selectedItem.getAll());
        });
        this.chooseProcess(returnedList.allItems());
    },

    __searchPanelFavouriteButtonObserver: function(avatar, addedOrRemoved) {
        if (addedOrRemoved) {
            this.suggestedUsersPanel.suggestedUserList.set('existingAv' + avatar.id, $O(avatar));
        }
    },

    _toggleSaveButton: function(enabled) {
        this.saveButton.disabledButtonWithTooltip(enabled ? 'enable' : 'disable');
    },

    /**
     * Returns the dialog's DOM
     */
    draw: function() {

        var self = this;

        this.saveButton = self.buttons.eq(0);
        this.saveButton.disabledButtonWithTooltip({
            tooltip: $T('Please select at least one item'),
            disabled: true
        });

        var mainContent = Html.tr();
        if (self.allowSearch) {
            this.cellSearch = Html.td("searchUsersGroupsPanel");
            self.__buildSearchPanel(this.cellSearch);
            mainContent.append(this.cellSearch);
        }

        if (this.includeFavourites || exists(this.suggestedUsers)) {
            this.cellSuggested = Html.td("suggestedUsersPanel");
            self.__buildSuggestedUsersPanel(this.cellSuggested);
            mainContent.append(this.cellSuggested);
        }

        mainContent = Html.table({cellpadding: 0, cellPadding: 0, cellspacing: 0, cellSpacing: 0}, Html.tbody({}, mainContent));
        return this.ExclusivePopupWithButtons.prototype.draw.call(this, mainContent,{padding: '0px'});

    },

    _getButtons: function() {
        var self = this;
        return [
            [(self.onlyOne ? $T('Choose') : $T('Add')), function() {
                self.__save();
                self.close();
            }],
            [$T('Cancel'), function() {
                self.close();
            }]
        ];
    },

    postDraw: function() {
        // We have to do this first and not after the super call or it won't work in IE7
        if (this.allowSearch && this.enableGroups) {
            var tabContainer = this.searchPanel.tabWidget.canvas;
            tabContainer.height(tabContainer.height());
        }
        if (this.includeFavourites || exists(this.suggestedUsers)) {
            this.suggestedUsersPanel.suggestedUserListDiv.setStyle('height', pixels(this.cellSuggested.dom.offsetHeight - this.suggestedUsersPanel.titleDiv.dom.offsetHeight - 10));
        }
        this.ExclusivePopupWithButtons.prototype.postDraw.call(this);
        if (this.allowSearch)
            $E('userSearchFocusField').dom.focus();
    }
},
    /**
     * Constructor for ChooseUsersPopup
     */
    function(title,
             allowSearch,
             conferenceId, enableGroups,
             includeFavourites, suggestedUsers,
             onlyOne, showToggleFavouriteButtons,
             submissionRights, chooseProcess, extraDiv) {

        var self = this;

        this.allowSearch = allowSearch;
        this.conferenceId = conferenceId;
        this.enableGroups = enableGroups;

        this.includeFavourites = any(includeFavourites, true);
        this.suggestedUsers = suggestedUsers;

        this.onlyOne = any(onlyOne, false);
        this.showToggleFavouriteButtons = any(showToggleFavouriteButtons, true);
        this.chooseProcess = chooseProcess;
        this.extraDiv = extraDiv;

        // Other attributes that will be set in other methods, listed here for reference
        this.saveButton = null;
        this.suggestedUsersPanel = null;
        this.searchPanel = null;
        this.buttonDiv = null;
        this.cellSearch = null;
        this.cellSuggested = null;

        this.submissionRights = submissionRights;
        this.grantRights = new WatchObject();

        // We build the dialog.
        this.PreLoadHandler(
            self._preload,
            function() {
                self.open();
            });
        this.ExclusivePopupWithButtons(title, positive);
    }
);



/**
 * Creates a form field whose value is a single user
 *
 * @param {Object} initialUser A user that will appear initially. Example: ${ AvatarHolder().getById(1).fossilize(IAvatarFossil) }
 *
 * @param {String} hiddenFieldName The name attribute for the hidden field that will be drawn along with the rest of the widget.
 *                                 This hidden field will have the currently selected user's id.
 *                                 If left to null, there will be no hidden field.
 *
 * @param {Boolean} allowChoose If true, a 'Choose User' dialog will be present when pressing on the "choose" button.
 *
 * @param {Boolean} includeFavourites If True, favourites will appear in the list of suggested users of the ChooseUsersPopup.
 * @param {list} suggestedUsers A list of users that will be offered as options to be added. Example: ${ jsonEncode(fossilize([AvatarHolder().getById(3), AvatarHolder().getById(4)], IAvatarFossil)) }
 *                              If left to null, there will be suggested Users. For an empty list of users, use {}
 *
 * @param {Integer} conferenceId If different from null, authors from that conference will be included in the search results.
 * @param {Boolean} enableGroups If true, choosing groups will be enabled.
 *
 * @param {Boolean} allowNew If true, a 'New User' button will be present.
 *
 * @param {Boolean} allowDelete If true, the user will be able to be deleted from the field.
 *
 * @param {Function} assignProcess A function that will be called when a new user is chosen (from new data, or from the search dialog, or from the suggested list).
 *                                 The function will be passed a WatchObject representing the user, and a callback function.
 *                                 The callback function has to be called with "true" as argument to effectively display the new user.
 * @param {Function} removeProcess A function that will be called when a user is removed.
 *                                 The function will be passed a WatchObject representing the user, and a callback function.
 *                                 The callback function has to be called with "true" as argument to effectively display the new user.
 */
type("SingleUserField", ["IWidget"], {

    /**
     * @return {String} The id of the currently selected user
     */
    get: function() {
        return this.user.getAll();
    },

    set: function(user) {
        this.user.replace(user);
        this.__userChosenObserver();
    },

    /**
     * @return {String} the name of the inner hidden field
     */
    getName: function() {
        return this.hiddenFieldName;
    },

    /**
     * @return {Boolean} Returns if a user has been chosen or not
     */
    isUserChosen: function() {
        return this.userChosen.get();
    },

    __getNotChosenUser: function() {
        return {id: null, name: "Choose a user"};
    },

    /**
     * Updates the buttons to be shown next to the user name after the user changes
     * @param {Object} user a dictionary with the user info.
     */
    __userChosenObserver: function() {
        var user = this.user.getAll();

        this.variableButtonsDiv.clear();
        if (IndicoGlobalVars.isUserAuthenticated && this.userChosen && user._type === "Avatar") {
            var favButtonDiv = Html.div({style:{display:"inline", paddingLeft:pixels(5)}}, new ToggleFavouriteButton(user).draw());
            this.variableButtonsDiv.append(favButtonDiv);
        }

        if (this.allowDelete && this.userChosen) {

            var removeButton = Widget.link(command(function(){
                self.userChosen.set(false);
                var notChosenUser = self.__getNotChosenUser();
                self.user.replace(notChosenUser);
                self.__userChosenObserver();
            }, IndicoUI.Buttons.removeButton()));

            var removeButtonDiv = Html.div({style:{display:"inline"}}, removeButton);
            this.variableButtonsDiv.append(removeButtonDiv);
        }
    },

    /**
     * Returns the DOM of the widget
     */
    draw: function() {
        var self = this;

        var contentDiv = Html.div({style:{display:"inline"}});

        // Draw the hidden field
        if (exists(this.hiddenFieldName)) {
            contentDiv.append($B(Html.input('hidden'), {name: this.hiddenFieldName}, self.user.accessor('id')));
        }

        // Draw the user if there is one
        var userNameDiv = $B(Html.span({style:{verticalAlign:'middle'}}), self.user.accessor('name'));
        contentDiv.append(userNameDiv);

        this.variableButtonsDiv = Html.div({style: {display: 'inline'}});
        this.__userChosenObserver();

        var fixedButtonsDiv = Html.div({style: {display: 'inline'}});
        // Draw the choose button
        if (self.allowChoose) {
            var chooseButton = Html.input("button", {style:{marginLeft: pixels(10), verticalAlign:'middle'}}, $T('Choose'));

            var chooseUserHandler = function(userList) {
                self.assignProcess(userList, function(value) {
                    if (value) { // the assignProcess function returned true
                        var returnedUser = userList[0];
                        self.user.replace(returnedUser);
                        self.__userChosenObserver();
                        self.userChosen.set(true);
                    }
                });
            };

            chooseButton.observeClick(function(){
                var userChoosePopup = new ChooseUsersPopup("Choose user",
                                                           true, self.conferenceId, self.enableGroups,
                                                           self.includeFavourites, self.suggestedUsers,
                                                           true, true, false,
                                                           chooseUserHandler);
                userChoosePopup.execute();
            });

            fixedButtonsDiv.append(chooseButton);
        }

        return Html.div({style: {display: 'inline'}},
                        contentDiv,
                        this.variableButtonsDiv,
                        fixedButtonsDiv);
    }
},
    /**
     * Constructor of SingleUserField
     */
    function(initialUser,
             hiddenFieldName,
             allowChoose,
             includeFavourites, suggestedUsers,
             conferenceId, enableGroups,
             allowNew, allowDelete,
             assignProcess, removeProcess) {

        var self = this;

        // we store the selected user
        this.user = $O(exists(initialUser) ? initialUser : this.__getNotChosenUser());
        this.userChosen = new WatchValue(exists(initialUser));

        this.hiddenFieldName = hiddenFieldName;

        this.allowChoose = any(allowChoose, true);

        this.includeFavourites = any(includeFavourites, true);
        if (exists(suggestedUsers)) {
            if (suggestedUsers.WatchList) {
                this.suggestedUsers = suggestedUsers;
            } else {
                this.suggestedUsers = new WatchList();
                each(suggestedUsers, function(user){
                    self.suggestedUsers.append(user);
                });
            }
        } else {
            this.suggestedUsers = null;
        }

        this.conferenceId = any(conferenceId, null);
        this.enableGroups = any(enableGroups, false);

        // new user dialog configuration
        this.allowNew = any(allowNew, false);

        // widget delete and favouritize buttons configuration
        this.allowDelete = any(allowDelete, true);

        // assign and remove user hook functions
        this.assignProcess = any(assignProcess, singleUserNothing);
        this.removeProcess = any(removeProcess, singleUserNothing);

        // div that will have the remove and favouritize buttons
        this.buttonsDiv = Html.div({style:{display:"inline"}});

    }
);

/**
 * Creates a data creation / edit pop-up dialog.
 * @param {String} title The title of the popup.
 * @param {Object} userData A WatchObject that has to have the following keys/attributes:
 *                          id, title, familyName, firstName, affiliation, email, address, telephone, fax, submission.
 *                          Its information will be displayed as initial values in the dialog.
 * @param {Function} action A callback function that will be called if the user presses ok. The function will be passed
 *                          a WatchObject with the new values.
 */
type("UserDataPopup", ["ExclusivePopupWithButtons"],
    {
        draw: function() {
            var userData = this.userData;
            var self = this;
            self.parameterManager = new IndicoUtil.parameterManager();

            var grantSubmission = [];
            var grantManagement = [];
            var grantCoordination = [];
            var warning = [];
            if (this.grantSubmission) {
                grantSubmission = [$T('Grant submission rights'), $B(Html.checkbox({id: 'submissionCheckbox'}), userData.accessor('submission'))];
                warning = [Html.span({}, Html.span({style:{fontWeight:'bold'}}, $T('Note:')), $T(' If this person does not already have an Indico account, '), Html.br(),
                        $T('he or she will be sent an email asking to register as a user.'), Html.br(),
                        $T(' After the registration the user will automatically be given'), Html.br(),
                        $T(' submission rights.'))];
            }
            if (this.grantManagement) {
                grantManagement = [$T('Give management rights'), $B(Html.checkbox({}), userData.accessor('manager'))];
                warning = [Html.span({}, Html.span({style:{fontWeight:'bold'}}, $T('Note:')), $T(' If this person does not already have an Indico account, '), Html.br(),
                           $T('he or she will be sent an email asking to create an account.'), Html.br(),
                           $T(' After the account creation the user will automatically be'), Html.br(),
                           $T(' given management rights.'))];
            }

            if (this.grantCoordination) {
                grantCoordination = [$T('Give coordination rights'), $B(Html.checkbox({}), userData.accessor('coordinator'))];
                warning = [Html.span({}, Html.span({style:{fontWeight:'bold'}}, $T('Note:')), $T(' If this person does not already have an Indico account, '), Html.br(),
                           $T('he or she will be sent an email asking to create an account.'), Html.br(),
                           $T(' After the account creation the user will automatically be'), Html.br(),
                           $T(' given coordination rights.'))];
            }
            if (this.grantManagement && this.grantCoordination) {
                warning = [Html.span({}, Html.span({style:{fontWeight:'bold'}}, $T('Note:')), $T(' If this person does not already have an Indico account, '), Html.br(),
                        $T('he or she will be sent an email asking to create an account.'), Html.br(),
                        $T(' After the account creation the user will automatically be'), Html.br(),
                        $T(' given the rights.'))];
            }

            var form = IndicoUtil.createFormFromMap([
               [$T('Title'), $B(Html.select({}, Html.option({}, ""), Html.option({value:'Mr.'}, $T("Mr.")), Html.option({value:'Mrs.'}, $T("Mrs.")), Html.option({value:'Ms.'}, $T("Ms.")), Html.option({value:'Dr.'}, $T("Dr.")), Html.option({value:'Prof.'}, $T("Prof."))), userData.accessor('title'))],
               [$T('Family Name'), $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), userData.accessor('familyName'))],
               [$T('First Name'), $B(Html.edit({style: {width: '300px'}}), userData.accessor('firstName'))],
               [$T('Affiliation'), $B(Html.edit({style: {width: '300px'}}), userData.accessor('affiliation'))],
               [$T('Email'),  $B(self.parameterManager.add(Html.edit({id: "email",  style: {width: '300px'}}), 'email', this.allowEmptyEmail), userData.accessor('email'))],
               [$T('Address'), $B(Html.textarea({style:{width:'300px'}}), userData.accessor('address'))],
               [$T('Telephone'), $B(Html.edit({style: {width: '300px'}}), userData.accessor('phone'))],
               [$T('Fax'), $B(Html.edit({style: {width: '300px'}}), userData.accessor('fax'))],
               grantSubmission, grantManagement, grantCoordination, warning]);

             return this.ExclusivePopupWithButtons.prototype.draw.call(this, form);
         },

        _getButtons: function() {
            var self = this;
            return [
                [$T('Save'), function() {
                    if ($('#submissionCheckbox').is(':checked') && $('#email').val() == 0) {
                        var popup = new WarningPopup($T('Warning'), $T("It is not possible to grant submission rights to a participant without an email address. Please set an email address."));
                        popup.open();
                        return;
                    }
                    self.action(self.userData, function() {
                    self.close();
                    });
                }],
                [$T('Cancel'), function() {
                    self.close();
                }]
            ];
        }
     },
     function(title, userData, action, grantSubmission, grantManagement, grantCoordination, allowEmptyEmail) {
         this.userData = userData;
         this.action = action;
         this.grantSubmission = exists(grantSubmission)?grantSubmission:false;
         this.grantManagement = exists(grantManagement)?grantManagement:false;
         this.grantCoordination = exists(grantCoordination)?grantCoordination:false;
         this.allowEmptyEmail = exists(allowEmptyEmail)?allowEmptyEmail:true;
         this.ExclusivePopup(title,  function(){return true;});
     }
    );

/**
 * Creates a data creation / edit pop-up dialog.
 * @param {String} title The title of the popup.
 * @param {Object} userData A WatchObject that has to have the following keys/attributes:
 *                          id, title, familyName, firstName, affiliation, email, telephone.
 *                          Its information will be displayed as initial values in the dialog.
 * @param {Function} action A callback function that will be called if the user presses ok. The function will be passed
 *                          a WatchObject with the new values.
 */
type("AuthorDataPopup", ["ExclusivePopupWithButtons"],
    {
        draw: function() {
            var userData = this.userData;
            var self = this;
            self.parameterManager = new IndicoUtil.parameterManager();

            var form = IndicoUtil.createFormFromMap([
               [$T('Title'), $B(Html.select({}, Html.option({}, ""), Html.option({value:'Mr.'}, $T("Mr.")), Html.option({value:'Mrs.'}, $T("Mrs.")), Html.option({value:'Ms.'}, $T("Ms.")), Html.option({value:'Dr.'}, $T("Dr.")), Html.option({value:'Prof.'}, $T("Prof."))), userData.accessor('title'))],
               [$T('Family Name'), $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), userData.accessor('familyName'))],
               [$T('First Name'), $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), userData.accessor('firstName'))],
               [$T('Affiliation'), $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), userData.accessor('affiliation'))],
               [$T('Email'),  $B(self.parameterManager.add(Html.edit({style: {width: '200px'}}), 'email', false), userData.accessor('email'))],
               [$T('Telephone'), $B(Html.edit({style: {width: '150px'}}), userData.accessor('phone'))]
               ]);


            return this.ExclusivePopupWithButtons.prototype.draw.call(this, form);
         },

        _getButtons: function() {
            var userData = this.userData;
            var self = this;
            return [
                    [$T('Save'), command(curry(this.action, userData, function() {self.close();}))],
                    [$T('Cancel'), function() { self.close();}]
                   ];
         }

     },
     function(title, userData, action) {
         this.userData = userData;
         this.action = action;
         this.ExclusivePopup(title,  function(){return true;});
     }
    );

$(function() {
    // This widget creates a clickable icon-shield that opens a qtip with the different rights that
    // can be granted to a user.
    $.widget("users.shield",{

        options: {
            userData: null,

            // rights
            submission: true
        },

        _qtip: function(rights) {

         // qtip content

            var rightsTooltipText = $("<div></div>")
                                        .append($("<span></span>").text($T("User privileges")).css('fontSize', '13px'))
                                        .append($("<div></div>")
                                                    .css('marginTop', '8px'));
            $.each(rights, function(index, value) {
                rightsTooltipText.append(value.checkbox)
                                 .append($("<span></span>")
                                         .text(value.text)
                                         .css('verticalAlign', 'middle'));
            });

            this.element.qtip({
                style: {
                    classes: 'qtip-rounded qtip-shadow qtip-popup',
                    tip: {
                        corner: true,
                        width: 15,
                        height: 10
                    }
                },
                position: {
                    my: 'top middle',
                    at: 'bottom middle'
                },
                content: {
                    text: rightsTooltipText
                },
                show: {
                    event: 'click',
                    solo: true
                },
                hide: {
                    event: 'unfocus'
                }
                });

        },

        _create: function() {

            var self = this;

            this.element
                // add class and attrs
                .addClass('icon-shield user_list_icon_shield')
                .attr('ariaHidden', true)
                .attr('alt', $T('User rights')).attr('title', $T('User rights'))
                .attr('data-id', 'author_'+this.options.userData.get('email'))
                //css
                .css('color', this.options.userData.get('isSubmitter') ? '#cc4646' : '#aaa');

            // Create privelege checkboxes and events
            var privelegeCheckboxes = [];

            if (this.options.submission) {
                var submissionCheckbox = $("<input type='checkbox'>")
                                            .prop('checked', !!this.options.userData.get('isSubmitter'))
                                            .css('marginRight', '8px').css('verticalAlign', 'middle');

                submissionCheckbox.click(function(){
                    $('.icon-shield[data-id="author_'+self.options.userData.get('email')+'"]').trigger('participantProctChange', [{isSubmitter: submissionCheckbox.is(':checked')}]);
                });

                privelegeCheckboxes.push({'checkbox': submissionCheckbox, 'text': $T("Submission rights")});
            }

            // Listen to protection changes
            this.element.on('participantProctChange', function(event, args){
                if (self.options.submission && 'isSubmitter' in args) {
                    self.element.css('color', args.isSubmitter ? '#cc4646' : '#aaa');
                    self.options.userData.set('isSubmitter', args.isSubmitter);
                    submissionCheckbox.prop('checked',args.isSubmitter);
                }
            });

            this._qtip(privelegeCheckboxes);

        }

    });
});


/**
 * Creates a list of users. Each user can be edited or removed.
 * It inherits from ListWidget who in turn inherits from WatchObject, so the usual WatchObject methods (get, set)
 * can be used on it. For example 'set' can be used to initialize the list.
 * This means that the users are stored with their id's as keys.
 * @param {String} style The class of the ul that will contain the users.
 * @param {Boolean} allowSetRights. If true, each user will have an edit button to change their rights.
 * @param {Boolean} allowEdit. If true, each user will have an edit button to change their data.
 * @param {Function} editProcess. A function that will be called when a user is edited. The function will
 *                                be passed the new data as a WatchObject.
 * @param {Boolean} showToggleFavouriteButtons. false by default. If true, favouritize buttons will not be shown.
 */
type("UserListWidget", ["ListWidget"],
     {
        _drawItem: function(user) {
            var self = this;
            var userData = user.get();

            var editButton = Widget.link(command(function() {
                 var editPopup = new UserDataPopup(
                     'Change user data',
                     userData.clone(),
                     function(newData, suicideHook) {
                         if (editPopup.parameterManager.check()) {
                             //  editProcess will be passed a WatchObject representing the user.
                             self.editProcess(userData, function(result) {
                                 if (result) {
                                     userData.update(newData.getAll());
                                     if (!startsWith('' + userData.get('id'), 'newUser')) {
                                         userData.set('id', 'edited' + userData.get('id'));
                                     }
                                     self.userListField.inform();
                                 }
                             });
                             suicideHook();
                         }
                     }
                 );
                 editPopup.open();
            }, IndicoUI.Buttons.editButton()));

            var removeButton = Widget.link(command(function() {
                             // removeProcess will be passed a WatchObject representing the user.
                             self.removeProcess(userData, function(result) {
                                     if (result) {
                                         self.set(user.key, null);
                                         self.userListField.inform();
                                     }
                                 });
                             }, IndicoUI.Buttons.removeButton()));

            if (userData.get('isGroup') || userData.get('_fossil') === 'group') {
                var removeButtonDiv = Html.div({style: {cssFloat: "right", clear: "both", paddingRight: pixels(10)}}, removeButton);
                var groupName = $B(Html.span(), userData.accessor('name'));
                return Html.span({}, removeButtonDiv, Html.span({style:{fontWeight:'bold'}}, 'Group: '), groupName);
            } else {
                var buttonDiv = Html.div({style: {cssFloat: "right", clear: "both", paddingRight: pixels(10)}});
                if (IndicoGlobalVars.isUserAuthenticated && exists(IndicoGlobalVars['userData']['favorite-user-ids']) && this.showToggleFavouriteButtons && userData.get('_type') === "Avatar") {
                    var favouritizeButton = new ToggleFavouriteButton(userData.getAll(), {}, IndicoGlobalVars['userData']['favorite-user-ids'][userData.get('id')]).draw();
                    buttonDiv.append(favouritizeButton);
                }
                if (this.allowSetRights) {
                    buttonDiv.append($("<span></span>").shield({userData: userData}).get(0));
                }
                if (this.allowEdit) {
                    buttonDiv.append(editButton) ;
                }
                buttonDiv.append(removeButton);

                var userName = Html.span({},
                        $B(Html.span(), userData.accessor('familyName'), function(name){return name.toUpperCase();}),
                        ', ',
                        $B(Html.span(), userData.accessor('firstName')));

                return Html.span({}, buttonDiv, userName);
            }
         }
     },

     function(style, allowSetRights, allowEdit, editProcess, removeProcess, showToggleFavouriteButtons, userListField) {

         this.style = any(style, "UIPeopleList");
         this.allowSetRights = allowSetRights;
         this.allowEdit = allowEdit;
         this.editProcess = any(editProcess, singleUserNothing);
         this.removeProcess = any(removeProcess, singleUserNothing);
         this.showToggleFavouriteButtons = any(showToggleFavouriteButtons, true);
         this.userListField = userListField;
         this.ListWidget(style);
     }
    );




/**
 * Creates a form field with a list of users.
 * Users can be added from an initial list of users, from a 'new user' dialog, or from a "choose user"
 * dialog which will enable both to search users/groups and propose a list of suggested users (favourites and others).
 * The 'id' attribute of the users in the list will depend from their origin.
 * - If it was added from the search dialog, the id will be 'existingAvXX' (where XX corresponds to the avatar id).
 * - It it was added from the 'new user' dialog, the id will be 'newUserXX', where XX is auto-increment starting from 0.
 * - If it was added from the list of suggested users, it will retain the id of the user that was put in the list.
 * - It the user was edited, and the edited user corresponded to an Avatar, the id will be 'editedXX' where XX is the id of the Avatar used initially.
 *
 */
type("UserListField", ["IWidget"], {

    _highlightNewUser: function(userId) {
        IndicoUI.Effect.highLightBackground($E(this.userList.getId() + '_' + userId));
    },

    getUsers: function() {
        return $L(this.userList);
    },

    clear: function() {
        this.userList.clearList();
    },

    privilegesOn: function() {
        return $('#grant-manager').attr("checked") || $('#presenter-grant-submission').attr("checked");
    },

    bothPrivilegesOn: function() {
        return $('#grant-manager').attr("checked") && $('#presenter-grant-submission').attr("checked");
    },

    setUpParameters: function() {
        /* set up basic components : div containers for message , a checkbox list ,
           a list of messages and a warning counter.*/

        this.warning_no_indico = ($T("Please note that you have added a user that does not exist in Indico.\
                                    Non existing users will be asked via email to create an account so\
                                    that they will be able to use the privileges below."));
        this.warning_no_email = ($T("Please note that you have added a user without an email address. Users without \
                                    email will not be able to use the privileges below."));
        this.messageDiv = $("<div/>", {css: {height: '58px',
                                            maxWidth: '420px',
                                            textAlign: 'left',
                                            width: 'auto',
                                            overflow: 'auto',
                                            marginLeft: '5px'
                                        }}).addClass("warningMessage");
        this.messageContainer = $("<div/>", {css: {display: 'inline-block', position: 'absolute'}});
        this.containerDiv = $("<div/>");
        this.warning_flag = false;
    },

    appendMessage: function(message) {
        this.messageDiv.html(message);
        this.messageContainer.append(this.messageDiv);
        this.containerDiv.append(this.messageContainer);
        this.warning_flag = true;
    },

    clearMessages: function() {
        this.messageContainer.html('');
        this.containerDiv.append(this.messageContainer);
        this.warning_flag = false;
    },

    checkList: function(list) {
        var self = this;
        self.clearMessages();
        each(list, function(val,key){
            self.check(self.userList.get(key));
        });
    },

    check: function(user) {
        var self = this;

        if(keys(this.privileges).length>0) {
            if(this.privilegesOn()) {
            if(!user.get('email')) {
                this.appendMessage(this.warning_no_email);
            }
            else {
                indicoRequest('search.users', {email:user.get('email')}, function(result, error) {
                if (!error) {
                    if (result.length == 0) {
                        self.appendMessage(self.warning_no_indico);
                    }
                }});
            }
        }}
    },

    inform: function() {
        if(keys(this.privileges).length>0) {
            if(!this.userList.isEmpty()) {
                this.checkList(this.userList.getAll());
            }
            else{
                this.clearMessages();
            }
        }
    },

    getPrivileges: function() {
        return this.selectedPrivileges;
    },

    draw: function() {
        var self = this;
        var select;
        var buttonDiv = Html.div({style:{marginTop: pixels(10)}});

        if (this.allowSearch || this.includeFavourites || exists(this.suggestedUsers)) {

            var chooseUserButton = Html.input("button", {style:{marginRight: pixels(5)}}, $T('Add Indico User'+(this.enableGroups?" / Group":"")));

            var title = "";
            if (this.includeFavourites || exists(this.suggestedUsers)) {
                title = this.enableGroups ? $T("Add Users and Groups") : $T("Add Users");
            } else {
                title = this.enableGroups ? $T("Search Users and Groups") : $T("Search Users");
            }

            var peopleAddedHandler = function(peopleList){

                // newProcess will be passed a list of WatchObjects representing the users.
                self.newProcess(peopleList, function(value) {
                    if (value) {
                        each(peopleList, function(person){
                            var key;
                            if (person.isGroup || person._fossil === 'group') {
                                key = person.id;
                            } else {
                                key = (person._type === "Avatar") ? "existingAv" + person.id : person.id;
                            }
                            if (person._type === "Avatar" && self.userList.get(key)) {
                                // it is an existing avatar, unchanged, and already exists: we do nothing
                            } else {
                                if (self.userList.get(key)) {
                                    self.userList.set(key, null);
                                }
                                self.userList.set(key, $O(person));
                                $('.icon-shield[data-id="author_'+person.email+'"]').trigger('participantProctChange', [{isSubmitter: person.isSubmitter}]);
                            }
                            //self._highlightNewUser(id);
                        });
                    }
                });
            };

            chooseUserButton.observeClick(function() {
                var chooseUsersPopup = new ChooseUsersPopup(title, self.allowSearch, self.conferenceId, self.enableGroups,
                        self.includeFavourites, self.suggestedUsers, false, self.showToggleFavouriteButtons, self.allowSetRights, peopleAddedHandler);
                chooseUsersPopup.execute();
            });

            buttonDiv.append(chooseUserButton);
        }


        if (this.allowNew) {
            var addNewUserButton = Html.input("button", {style:{marginRight: pixels(5)}}, $T('Add New') );
            addNewUserButton.observeClick(function(){
                var newUserId = 'newUser' + self.newUserCounter++;
                var newUser = $O({'id': newUserId});
                var newUserPopup = new UserDataPopup(
                    $T('New user'),
                    newUser,
                    function(newData, suicideHook) {
                        if (newUserPopup.parameterManager.check()) {
                            newUser.set('isSubmitter', newUser.get('submission'));
                            self.newProcess([newUser], function(result) {
                                if (result) {
                                    self.userList.set(newUserId, newUser);
                                    self.check(newUser);
                                    //self._highlightNewUser(newUserId);
                                    $('.icon-shield[data-id="author_'+newUser.get('email')+'"]').trigger('participantProctChange', [{isSubmitter: newUser.get('isSubmitter') || false}]);
                                }
                            });
                            suicideHook();
                        }
                    }, self.allowSetRights
                );
                newUserPopup.open();
            });
            buttonDiv.append(addNewUserButton);
        }

        // User privileges (submission privilege, etc.)
        var privilegesDiv = $("<span/>").css("marginTop", "10px");
        var keysList = keys(this.privileges);
        if (keysList.length>0) {
            privilegesDiv.append($("<span/>").html($T("Grant all these users with privileges: ")));
        }
        var comma = ", ";
        for (var i=0; i<keysList.length; i++) {
            if (i+1 == keysList.length) {
                comma = "";
            }
            var key = keysList[i];
            var value = this.privileges[key];
            var checkbox = $('<input>', {type:"checkbox" , id: key, name:key}).change(function(){
                if(!self.privilegesOn()){
                    self.clearMessages();
                    return;
                }
                else{
                    if(!self.warning_flag) {
                        self.inform();
                    }
                }
            });
            $B(this.selectedPrivileges.accessor(key), checkbox);
            privilegesDiv.append($("<span/>").append(checkbox).append(value[0] + comma));
        }

        var containsUserListDiv = $("<div/>").css("display", "inline-block");
        containsUserListDiv.append($("<div/>").addClass(this.userDivStyle).html(this.userList.draw().dom));
        this.containerDiv.append(containsUserListDiv);
        return Widget.block([this.containerDiv.get(0), privilegesDiv.get(0), buttonDiv]);

    }
},
    /*
     * @param {String} userDivStyle A CSS class for the div that will sourround the user list.
     * @param {String} userListStyle A CSS class for the user list. It will be passed to the inner UserListWidget.
     *
     * @param {list} initialUsers A list of (fossilized) avatars that will appear initially.
     * @param {Boolean} includeFavourites If True, favourites will appear in the list of suggested users of the ChooseUsersPopup.
     * @param {list} suggestedUsers A list of users that will be offered as options to be added.
     * @param {Boolean} allowSearch If True, the "Choose user" dialog will propose to search.
     * @param {Boolean} enableGroups If True, the "Choose user" dialog will propose to search groups.
     * @param {string} conferenceId for author list search
     * @param {list} privileges dictionary with the privileges that we can set for the users. There is a key and a tuple as vale: (label, default value for checked). E.g. {"grant-manager": ["event modification", false]}
     * @param {Boolean} allowNew If True, a 'New User' button will be present.
     * @param {Boolean} allowSetRights. If True, rights for each user will be able to be edited.
     * @param {Boolean} allowEdit If True, users in the list will be able to be edited.
     * @param {Boolean} showToggleFavouriteButtons. false by default. If true, favouritize buttons will not be shown.
     * @param {Function} newProcess A function that will be called when new users (from new data, or from the search dialog, or from the suggested list) is added to the list.
     * @param {Function} editProcess A function that will be called when a user is edited.
     * @param {Function} removeProcess A function that will be called when a user is removed.
     */
    function(userDivStyle, userListStyle,
             initialUsers, includeFavourites, suggestedUsers,
             allowSearch, enableGroups, conferenceId, privileges,
             allowNew, allowSetRights, allowEdit, showToggleFavouriteButtons,
             newProcess, editProcess, removeProcess) {

        var self = this;
        this.userList = new UserListWidget(userListStyle, allowSetRights, allowEdit, editProcess, removeProcess, showToggleFavouriteButtons,this);
        self.newUserCounter = 0;
        this.userDivStyle = any(userDivStyle, "UIPeopleListDiv");
        this.setUpParameters();

        if (exists(initialUsers)) {
            each(initialUsers, function(user){
                if (any(user._type, null) === 'Avatar') {
                    self.userList.set('existingAv' + user.id, $O(user));
                } else {
                    self.userList.set(user.id, $O(user));
                }
            });
        }

        this.includeFavourites = any(includeFavourites, true);
        if (exists(suggestedUsers)) {
            if (suggestedUsers.WatchList) {
                this.suggestedUsers = suggestedUsers;
            } else {
                this.suggestedUsers = new WatchList();
                each(suggestedUsers, function(user){
                    self.suggestedUsers.append(user);
                });
            }
        } else {
            this.suggestedUsers = null;
        }

        this.allowSearch = any(allowSearch, true);
        this.enableGroups = any(enableGroups, false);
        this.conferenceId = any(conferenceId, null);
        this.privileges = any(privileges, {});
        this.selectedPrivileges = new WatchObject();
        this.allowSetRights = allowSetRights;

        this.allowNew = any(allowNew, true);
        this.showToggleFavouriteButtons = any(showToggleFavouriteButtons, true);
        this.newProcess = any(newProcess, userListNothing);
     }
);


/**
 * Buttons to add or remove a user to the list of the currently
 * logged in user's favourites.
 */
type("ToggleFavouriteButton", ["InlineWidget"], {
    draw: function() {
        var self = this;

        var imageRemove = Html.img({
            src: imageSrc("star"),
            alt: 'Remove from Favorites',
            title: $T('Remove from your list of favorite users'),
            style: this.imageStyle
            });

        var imageAdd = Html.img({
            src: imageSrc("starGrey"),
            alt: 'Add to Favorites',
            title: $T('Add to your list of favorite users'),
            style: this.imageStyle
        });

        var imageLoading = Html.img({
            src: imageSrc("loading"),
            alt: 'Loading',
            title: $T('Communicating with server'),
            style: this.imageStyle
        });

        var starIcon = $B(Html.span(), this.stateWatchValue, function(state){
            if (state) { // user is favourite
                return imageRemove;
            } else { // user is not favourite
                return imageAdd;
            }
        });

        var content = Html.span({}, starIcon);

        imageRemove.observeClick(function(event){
            content.set(imageLoading);
            indicoRequest('user.favorites.removeUser',
                {
                    value: [{id:self.avatar.id}]
                },
                function(result,error){
                    content.set(starIcon);
                    if(!error) {
                        IndicoGlobalVars['favorite-user-ids'][self.avatar.id] = false;
                        self.stateWatchValue.set(false);
                        if (exists(self.observer)) {
                            self.observer(self.avatar, false);
                        }
                    } else {
                        self._error(error); //Implemented in InlineWidget
                    }
                });
            stopPropagation(event);
        });

        imageAdd.observeClick(function(event){
            content.set(imageLoading);
            indicoRequest('user.favorites.addUsers',
                    {
                        value: [{id:self.avatar.id}]
                    },
                    function(result,error){
                        content.set(starIcon);
                        if(!error) {
                            IndicoGlobalVars['favorite-user-ids'][self.avatar.id] = true;
                            if (exists(IndicoGlobalVars['favorite-user-list'])) {
                                IndicoGlobalVars['favorite-user-list'].push(self.avatar);
                                IndicoGlobalVars['favorite-user-list'].sort(userSort);
                            }
                            self.stateWatchValue.set(true);
                            if (exists(self.observer)) {
                                self.observer(self.avatar, true);
                            }
                        } else {
                            self._error(error);  //Implemented in InlineWidget
                        }
                    });

            stopPropagation(event);
        });

        return this.IWidget.prototype.draw.call(this, content);
    }
},
    /**
     * Constructor
     */
    function(avatar, customImgStyle, initialState, observer){
        this.IWidget();

        this.avatar = avatar;

        customImgStyle = any(customImgStyle, {});
        this.imageStyle = merge({verticalAlign:'middle', cursor:'pointer'});

        this.observer = any(observer, null);

        this.stateWatchValue = null;

        if (!exists(IndicoGlobalVars['favorite-user-ids'])) {
            IndicoGlobalVars['favorite-user-ids'] = {};
            /*IndicoGlobalVars['favorite-user-list'] = [];*/
        }
        if (!exists(IndicoGlobalVars.userFavouritesWatchValues)) {
            IndicoGlobalVars.userFavouritesWatchValues = {};
        }

        if(!exists(IndicoGlobalVars.userFavouritesWatchValues[avatar.id])) {
            if(exists(IndicoGlobalVars['favorite-user-ids'][avatar.id])) {
                IndicoGlobalVars.userFavouritesWatchValues[avatar.id] = $V(IndicoGlobalVars['favorite-user-ids'][avatar.id] === true);
            } else {
                if (!exists(IndicoGlobalVars['favorite-user-ids']) && !exists(initialState)) {
                    new AlertPopup($T("Warning"), $T("ToggleFavouriteButton used without IndicoGlobalVars['favorite-user-ids'] variable and without initialState")).open();
                }
                initialState = any(initialState, false);
                IndicoGlobalVars.userFavouritesWatchValues[avatar.id] = $V(initialState);
            }
        }

        this.stateWatchValue = IndicoGlobalVars.userFavouritesWatchValues[avatar.id];
    }
);
