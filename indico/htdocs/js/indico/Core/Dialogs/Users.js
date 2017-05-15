/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

function userListNothing(data, func) {
    func(true, data);
}

function singleUserNothing(user, func) {
    func(true);
}

function create_favorite_button(user_id) {
    var integerRegex = /^[0-9]+$/;
    if (!integerRegex.test(user_id)) {  // external user
        return $('<span>');
    }
    var active = !!Indico.User.favorite_users[user_id],
        span = $('<span class="favorite-user icon-star">')
            .attr({
                title: active ? $T('Remove from your list of favorite users') : $T('Add to your list of favorite users'),
                'data-id': user_id
            })
            .on('click', function(e) {
                e.stopPropagation();
                $(document).trigger('favorites.' + ($(this).hasClass('active') ? 'remove-user' : 'add-user'), user_id);
            });

    if (active) {
        span.addClass('active');
    }

    return span;
}

$(function() {
    $(document).on('favorites.remove-user', function(e, user_id) {
        $.ajax({
            url: build_url(Indico.Urls.FavoriteUserRemove, {fav_user_id: user_id}),
            method: 'DELETE',
            error: handleAjaxError
        }).done(function() {
            $('.favorite-user[data-id=' + user_id + ']').removeClass('active');
            delete Indico.User.favorite_users[user_id];
        });
    }).on('favorites.add-user', function(e, user_id) {
        $.ajax({
            url: Indico.Urls.FavoriteUserAdd,
            method: 'POST',
            dataType: 'json',
            data: {user_id: [user_id]},
            error: handleAjaxError
        }).done(function(result) {
            $('.favorite-user[data-id=' + user_id + ']').addClass('active');
            Indico.User.favorite_users[user_id] = result.users[0];
        });
    });
});

/**
 * @param {String} style The class name of the <ul> element inside this FoundPeopleList
 *                       If left to null, it will be "user-list"
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
            return Html.div("info", Html.span("name", peopleData.get("name")));
        } else {
            var userName = Html.span("name", peopleData.get("firstName"), ' ', peopleData.get("familyName"));
            var userEmail = Html.span({id: self.id + "_" + pair.key + "_email", className: "email"}, Util.truncate(peopleData.get("email"), 40));
            var affiliation = Html.$($('<span class="affiliation">').text(peopleData.get('affiliation')));
            var html = Html.div("info", userName, userEmail, affiliation);

            var $actionButtons = $('<div>', {'class': 'actions'});
            if (this.showToggleFavouriteButtons && IndicoGlobalVars.isUserAuthenticated && peopleData.get('_type') == "Avatar") {
                var favouritizeButtonDiv = create_favorite_button(peopleData.get('id')).get(0);
                $actionButtons.append(favouritizeButtonDiv);
            }
            if (peopleData.get('_type') == 'EventPerson') {
                var userId = peopleData.get('user_id');
                if (userId) {
                    $actionButtons.append(create_favorite_button(userId));
                }
                $('<span>', {
                    'class': 'event-person',
                    'title': $T("This person exists in the event")
                }).appendTo($actionButtons);
            }

            return [html, new Html.$($actionButtons)];
        }
    }
},

    /**
     * Constructor for FoundPeopleList
     */
    function(style, onlyOne, selectionObserver, showToggleFavouriteButtons, favouriteButtonObserver) {
        if (!exists(style)) {
            style = "user-list";
        }

        this.onlyOne = any(onlyOne,false);
        this.showToggleFavouriteButtons = any(showToggleFavouriteButtons, true);
        this.favouriteButtonObserver = any(favouriteButtonObserver, null);

        /*this.lastTargetListItem = null;*/

        this.SelectableListWidget(selectionObserver, this.onlyOne, style, "selected", "unselected"); //, this.__mouseoverObserver);
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
       if (empty(Indico.Settings.ExtAuthenticators) || !this.allowExternal) {
           return null;
       } else {
            var searchExternalCB = Html.checkbox({});
            $B(searchExternalCB, self.criteria.accessor('search-ext'));
            return [[$T("Users with no Indico account"), searchExternalCB]];
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

       this.foundPeopleListDiv = Html.div("user-search-results", this.foundPeopleList.draw());

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
    function(onlyOne, selectionObserver, showToggleFavouriteButtons, favouriteButtonObserver, submissionRights, grantRights, extraDiv, allowExternal) {

        this.IWidget();
        this.onlyOne = any(onlyOne, false);

        this.criteria = new WatchObject();

        this.foundPeopleList = new FoundPeopleList(null, this.onlyOne, selectionObserver, showToggleFavouriteButtons, favouriteButtonObserver);
        this.foundPeopleList.setMessage($T("You can use the form above to search for users..."));
        this.extraDiv = any(extraDiv, Html.div({}));

        this.searchForm = null;
        this.searchButton = null;
        this.searchButtonDiv = null;
        this.foundPeopleListDiv = null;
        this.container = null;

        this.submissionRights = submissionRights;
        this.grantRights = grantRights;
        this.allowExternal = allowExternal;
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
        var self = this,
            do_search = function() {
                self._searchAction();
                return false;
            };

        this.fields = {
            'surName': new EnterObserverTextBox("text", {style: {width: "100%"}, id:'userSearchFocusField'}, do_search),
            'name': new EnterObserverTextBox("text", {style: {width: "100%"}}, do_search),
            'email': new EnterObserverTextBox("text", {style: {width: "100%"}}, do_search),
            'organisation': new EnterObserverTextBox("text", {style: {width: "100%"}}, do_search),
            'exactMatch': Html.checkbox({})
        };

        var fieldList = [[$T("Family name"), this.fields.surName.draw()],
                         [$T("First name"), this.fields.name.draw()],
                         [$T("E-mail"), this.fields.email.draw()],
                         [$T("Organisation"), this.fields.organisation.draw()],
                         [$T("Exact Match"), this.fields.exactMatch]];

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

        _.each(this.fields, function(widget, key) {
            self.criteria.set(key, widget.get());
        });

        indicoRequest(
            'search.users',
            self.criteria,
            function(result,error) {
                if (!error) {
                    self.foundPeopleList.clearList();
                    if (result.length === 0) {
                        self.foundPeopleList.setMessage($T("No results for this search..."));
                    } else {
                        each(result, function(entry) {
                            if (entry._type === "Avatar") {
                                self.foundPeopleList.set('existingAv' + entry.id, $O(entry));
                            } else if (entry._type === "EventPerson") {
                                self.foundPeopleList.set('existingEventPerson' + entry.id, $O(entry));
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
    function(onlyOne, selectionObserver, conferenceId, showToggleFavouriteButtons, favouriteButtonObserver, submissionRights, grantRights, extraDiv, allowExternal){
        this.SimpleSearchPanel(onlyOne, selectionObserver, showToggleFavouriteButtons, favouriteButtonObserver, submissionRights, grantRights, extraDiv, allowExternal);
        if(exists(conferenceId)) {
            this.criteria.set("conferenceId", conferenceId);
        }
        this.fields = {};
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
        var exactMatch = Html.checkbox({});

        $B(groupName, this.criteria.accessor('group'));
        $B(exactMatch, this.criteria.accessor('exactMatch'));
        this.criteria.set('exactMatch', true);

        var fieldList = [[$T("Group name"), groupName.draw()], [$T("Exact Match"), exactMatch]];
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
        this.tabWidget = new JTabWidget([[$T("Users"), this.userPanel.draw()], [$T("Groups"), this.groupPanel.draw()]]);
        return this.IWidget.prototype.draw.call(this, this.tabWidget.draw());
    }
},

    /**
     * Constructor for UserAndGroupsSearchPanel
     */
    function(onlyOne, selectionObserver, conferenceId, showToggleFavouriteButtons, favouriteButtonObserver, submissionRights, grantRights, extraDiv, allowExternal){
        this.IWidget();
        this.onlyOne = any(onlyOne, false);
        this.parentSelectionObserver = selectionObserver;

        var self = this;

        this.userPanel = new UserSearchPanel(this.onlyOne, function(selectedList){
            self.__selectionObserver("users", selectedList);
        }, conferenceId, showToggleFavouriteButtons, favouriteButtonObserver, submissionRights, grantRights, extraDiv, allowExternal);
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
                                        Html.a({href: Indico.Urls.Favorites}, $T("favourites")),
                                        "?");
            this.suggestedUserList.setMessage(message);
        }

        this.suggestedUserListDiv = Html.div("suggested-users", this.suggestedUserList.draw());

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
            var favorites = _.values(Indico.User.favorite_users).sort(function(a, b) {
                var name1 = '{0} {1}'.format(a.firstName, a.familyName);
                var name2 = '{0} {1}'.format(b.firstName, b.familyName);
                return (name1 == name2) ? 0 : (name1 < name2) ? -1 : 1;
            });
            _.each(favorites, function(user){
                if (!self.suggestedUserList.get('existingAv' + user.id)) {
                    self.suggestedUserList.set('existingAv' + user.id, $O(user));
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

    ],

    __buildSearchPanel: function(container) {
        var self = this;
        if (this.enableGroups) {
            this.searchPanel = new UserAndGroupsSearchPanel(this.onlyOne, function(selectedList){
                self.__selectionObserver("searchUsers", selectedList);
            }, this.conferenceId, this.showToggleFavouriteButtons, function(avatar, action) {
                self.__searchPanelFavouriteButtonObserver(avatar, action);
            }, this.submissionRights, this.grantRights, self.extraDiv, self.allowExternal);
        } else {
            this.searchPanel = new UserSearchPanel(this.onlyOne, function(selectedList) {
                self.__selectionObserver("searchUsers", selectedList);
            }, this.conferenceId, this.showToggleFavouriteButtons, function(avatar, action) {
                self.__searchPanelFavouriteButtonObserver(avatar, action);
            }, this.submissionRights, this.grantRights, self.extraDiv, self.allowExternal);
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
             submissionRights, chooseProcess, extraDiv, allowExternal) {

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
        this.allowExternal = _.isBoolean(allowExternal) ? allowExternal : true;
    }
);


/**
 * Creates a data creation / edit pop-up dialog.
 * @param {String} title The title of the popup.
 * @param {Object} userData A WatchObject that has to have the following keys/attributes:
 *                          id, title, familyName, firstName, affiliation, email, address, telephone, submission.
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
                    self.userData.set('name', '{0} {1}'.format(self.userData.get('firstName'), self.userData.get('familyName')));
                    if (self.parameterManager.check()) {
                        self.action(self.userData);
                        if (self.autoClose) {
                            self.close();
                        }
                    }
                }],
                [$T('Cancel'), function() {
                    self.close();
                }]
            ];
        }
     },
     function(title, userData, action, grantSubmission, grantManagement, grantCoordination, allowEmptyEmail, autoClose) {
         this.userData = userData;
         this.action = action;
         this.grantSubmission = exists(grantSubmission)?grantSubmission:false;
         this.grantManagement = exists(grantManagement)?grantManagement:false;
         this.grantCoordination = exists(grantCoordination)?grantCoordination:false;
         this.allowEmptyEmail = exists(allowEmptyEmail)?allowEmptyEmail:true;
         this.ExclusivePopup(title,  function(){return true;});
         this.autoClose = exists(autoClose) ? autoClose : true;
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
                    $('.icon-shield[data-id="author_'+self.options.userData.get('email')+'"]').trigger('participantProtChange', [{isSubmitter: submissionCheckbox.is(':checked')}]);
                });

                privelegeCheckboxes.push({'checkbox': submissionCheckbox, 'text': $T("Submission rights")});
            }

            // Listen to protection changes
            this.element.on('participantProtChange', function(event, args){
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
        _iteratingElement: function(attrs, item) {
            var className;
            var pairProperties = attrs.pair.get();
            if (pairProperties.get('isGroup')) {
                className = 'item-group';
            } else if (pairProperties.get('_type') === 'IPNetworkGroup') {
                className = 'icon-lan';
            } else if (pairProperties.get('_type') === 'Email') {
                className = 'icon-mail';
            } else {
                className = 'icon-user';
            }
            attrs['className'] = className;
            delete attrs['pair'];
            return this.ListWidget.prototype._iteratingElement.call(this, attrs, item);
        },
        _drawItem: function(user) {
            var self = this;
            var userData = user.get();

            var edit_button = $('<i class="edit-user icon-edit">').click(function() {
                var editPopup = new UserDataPopup(
                    'Change user data',
                    userData.clone(),
                    function(newData) {
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
                    }
                 );
                 editPopup.open();
            });

            var remove_button = $('<i class="remove-user icon-close hide-if-locked">').click(function() {
                var currentUserId = $('body').data('user-id');
                var userId = userData.get('id');
                var confirmed;

                function setResult(result) {
                    if (result) {
                        self.set(user.key, null);
                        self.userListField.inform();
                    }
                }

                if (currentUserId === userId) {
                    confirmed = confirmPrompt($T.gettext('Are you sure you want to remove yourself from the list?'),
                                              $T.gettext('Confirm action'));
                } else {
                    confirmed = $.Deferred().resolve();
                }

                confirmed.then(function() {
                    self.removeProcess(userData, setResult);
                });
            });

            var buttonDiv = Html.div("actions", new Html(remove_button.get(0)));

            if (userData.get('isGroup') || userData.get('_fossil') === 'group') {
                var groupName = $B(Html.span("name"), userData.accessor('name'));
                return [Html.span("info", groupName), buttonDiv];
            } else {
                if (IndicoGlobalVars.isUserAuthenticated & this.showToggleFavouriteButtons && userData.get('_type') === "Avatar") {
                    buttonDiv.append(new Html(create_favorite_button(userData.get('id')).get(0)));
                }
                if (this.allowSetRights) {
                    buttonDiv.append($("<span></span>").shield({userData: userData}).get(0));
                }
                if (this.allowEdit) {
                    buttonDiv.append(new Html(edit_button.get(0)));
                }
                buttonDiv.append(new Html(remove_button.get(0)));

                var userName;
                if (userData.get('_type') == 'Email') {
                    userName = Html.span("info", $B(Html.span("name"), userData.accessor('email')));
                } else {
                    userName = Html.span("info", $B(Html.span("name"), userData.accessor('name')));
                }

                if (userData.get('_type') !== 'Email') {
                    userName.append(Html.span('email', userData.get('email')));
                    userName.append(Html.span('affiliation', userData.get('affiliation')));
                }
                return [userName, buttonDiv];
            }
         }
     },

     function(style, allowSetRights, allowEdit, editProcess, removeProcess, showToggleFavouriteButtons, userListField) {

         this.style = any(style, "user-list");
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
    clear: function() {
        this.userList.clearList();
    },

    privilegesOn: function() {
        return $('#grant-manager').prop("checked") || $('#presenter-grant-submission').prop("checked");
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

    draw: function() {
        var self = this;
        var buttonDiv = Html.div({style: {marginTop: pixels(10)}});

        if (this.allowSearch || this.includeFavourites || exists(this.suggestedUsers)) {
            var chooseUserButton = Html.input("button", {style: {marginRight: pixels(5)},
                                                         className: 'i-button hide-if-locked', type: 'button'},
                                              this.enableGroups ? $T('Add User / Group'): $T('Add user'));
            var chooseIpNetwork = Html.a({href: '#', style: {marginRight: pixels(5)},
                                          className: 'i-button arrow js-dropdown',
                                          'data-toggle': 'dropdown'}, $T('Add IP Network'));
            var ipNetworksContainer = Html.span({className: 'group'});
            var ipNetworksList = Html.ul({className: 'dropdown'});

            _.each(this.ipNetworks, function(network) {
                var li = Html.li();
                li.append(Html.a({href: '#'}, network.name));
                li.observeClick(function() {
                    self.newProcess([network], function(result) {
                        if (result && !self.userList.get(network.identifier)) {
                            var entries = self.userList.getAll();
                            entries[network.identifier] = $O(network);
                            updatePrincipalsList(entries);
                        }
                    });
                });
                ipNetworksList.append(li);
            });

            ipNetworksContainer.append(chooseIpNetwork);
            ipNetworksContainer.append(ipNetworksList);
            var title;
            if (this.includeFavourites || exists(this.suggestedUsers)) {
                title = this.enableGroups ? $T("Add Users and Groups") : $T("Add Users");
            } else {
                title = this.enableGroups ? $T("Search Users and Groups") : $T("Search Users");
            }

            function updatePrincipalsList(entries) {
                var sortedKeys = _.sortBy(_.keys(entries), function(key) {
                    var principal = entries[key].getAll();
                    var weight = (principal._type == 'Avatar') ? 0 : (principal._type == 'Email' ? 1 : (principal.isGroup ? 2 : 3));
                    var name = principal._type !== 'Email' ? principal.name : principal.email;
                    return [weight, name.toLowerCase()];
                });

                self.userList.clearList();
                _.each(sortedKeys, function(key) {
                    self.userList.set(key, $O(entries[key].getAll()));
                });
            }

            var peopleAddedHandler = function(peopleList){
                // newProcess will be passed a list of WatchObjects representing the users.
                self.newProcess(peopleList, function(value, results) {
                    if (value) {
                        each(results, function(person){
                            var key;
                            if (person.isGroup || person._fossil === 'group' || person._type == 'IPNetworkGroup') {
                                key = person.identifier;
                            } else if (person._type === "Avatar") {
                                key = "existingAv" + person.id;
                            } else if (person._type === "EventPerson") {
                                key = "existingEventPerson" + person.id;
                            } else {
                                key = person.id;
                            }
                            if (!self.userList.get(key)) {
                                var entries = self.userList.getAll();
                                entries[key] = $O(person);
                                updatePrincipalsList(entries);
                                $('.icon-shield[data-id="author_' + person.email + '"]')
                                    .trigger('participantProtChange', [{isSubmitter: person.isSubmitter}]);
                            }
                        });
                    }
                });
            };

            chooseUserButton.observeClick(function() {
                var chooseUsersPopup = new ChooseUsersPopup(title, self.allowSearch, self.conferenceId, self.enableGroups,
                        self.includeFavourites, self.suggestedUsers, false, self.showToggleFavouriteButtons, self.allowSetRights, peopleAddedHandler,
                        null, self.allowExternal);
                chooseUsersPopup.execute();
            });

            buttonDiv.append(chooseUserButton);
            if (this.enableIpNetworks) {
                buttonDiv.append(ipNetworksContainer);
            }
        }


        if (this.allowNew) {
            var addNewUserButton = Html.input("button", {className: 'i-button', style:{marginRight: pixels(5)}}, $T('Add New') );
            addNewUserButton.observeClick(function(){
                var newUserId = 'newUser' + self.newUserCounter++;
                var newUser = $O({'id': newUserId});
                var newUserPopup = new UserDataPopup(
                    $T('New user'),
                    newUser,
                    function(newData) {
                        newUser.set('isSubmitter', newUser.get('submission'));
                        self.newProcess([newUser], function(result) {
                            if (result) {
                                self.userList.set(newUserId, newUser);
                                self.check(newUser);
                                $('.icon-shield[data-id="author_'+newUser.get('email')+'"]').trigger('participantProtChange', [{isSubmitter: newUser.get('isSubmitter') || false}]);
                            }
                        });
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
             newProcess, editProcess, removeProcess, allowExternal, enableIpNetworks, ipNetworks) {

        var self = this;
        this.userList = new UserListWidget(userListStyle, allowSetRights, allowEdit, editProcess, removeProcess,
                                           showToggleFavouriteButtons, this);
        self.newUserCounter = 0;
        this.userDivStyle = any(userDivStyle, "user-list");
        this.setUpParameters();

        if (exists(initialUsers)) {
            each(initialUsers, function(user){
                if (any(user._type, null) === 'Avatar') {
                    self.userList.set('existingAv' + user.id, $O(user));
                } else if (user._type === 'EventPerson') {
                    self.userList.set('existingEventPerson' + user.id, $O(user));
                } else if (~['LDAPGroupWrapper', 'LocalGroupWrapper', 'MultipassGroup', 'LocalGroup', 'IPNetworkGroup'].indexOf(user._type)) {
                    self.userList.set(user.identifier, $O(user));
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
        this.enableIpNetworks = any(enableIpNetworks, false);
        this.ipNetworks = any(ipNetworks, []);
        this.conferenceId = any(conferenceId, null);
        this.privileges = any(privileges, {});
        this.selectedPrivileges = new WatchObject();
        this.allowSetRights = allowSetRights;

        this.allowNew = any(allowNew, true);
        this.showToggleFavouriteButtons = any(showToggleFavouriteButtons, true);
        this.newProcess = any(newProcess, userListNothing);
        this.allowExternal = _.isBoolean(allowExternal) ? allowExternal : true;
     }
);
