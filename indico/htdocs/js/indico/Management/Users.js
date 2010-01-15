function userListNothing(data, func) {
    each(data, function() {
        func(true);
    });
}

/**
 * Creates a user search pop-up dialog that queries the user
 * database.
 * @param {Function} process Callback method that is invoked
 *                   in order to process the users that are selected
 *                   from the list.
 * @param {Function} suicideHook A callback method that is passed by
 *                   the exclusivePopup method, and is called by the
 *                   function when the dialog needs to be destroyed.
 */
type ("UserSearchPopup", ["ExclusivePopup"], {

    _clickSearchAction: function(){
        Dom.Event.dispatch( this.searchButton.dom, 'click');
    },

    _drawUsers: function() {
        var self = this;
        // Form to input user data
        var criteria = this.criteria;

        var famName = new EnterObserverTextBox("text",{}, function() {
            self._clickSearchAction();
            });
        var firstName = new EnterObserverTextBox("text",{}, function() {
            self._clickSearchAction();
        });
        var email = new EnterObserverTextBox("text",{}, function() {
            self._clickSearchAction();
        });
        var org = new EnterObserverTextBox("text",{}, function() {
            self._clickSearchAction();
        });
        var exactMatch = Html.checkbox({});

        $B(famName, criteria.accessor('surName'));
        $B(firstName, criteria.accessor('name'));
        $B(org, criteria.accessor('organisation'));
        $B(email, criteria.accessor('email'));
        $B(exactMatch, criteria.accessor('exactMatch'));

        return IndicoUtil.createFormFromMap([[$T("Family name"), famName.draw()], [$T("First name"), firstName.draw()], [$T("E-mail"), email.draw()], [$T("Organisation"), org.draw()], [$T("Exact Match"), exactMatch]]);
    },

    _drawGroups: function() {
        var self = this;
        var criteria = this.criteria;

        return IndicoUtil.createFormFromMap([
            ["Group name",
             $B( new EnterObserverTextBox("text",{}, function() {
                 self._clickSearchAction();
             }).draw(), criteria.accessor('group'))]]);
    },

    _clearSelections: function(selectedList, selectedDiv) {
        selectedList.clear();
        each(selectedDiv, function(elem) {
            elem.dom.className = 'unselectedUser';
        });
    },

    draw: function () {

        var selectedUserList = new WatchList();
        var selectedGroupList = new WatchList();

        selectedUserList.length.observe(function(){
            if (selectedUserList.length.get() > 0) {
                addButton.enable();
            }else {
                addButton.disable();
            }
        });

        selectedGroupList.length.observe(function(){
            if (selectedGroupList.length.get() > 0) {
                addButton.enable();
            }else {
                addButton.disable();
            }
        });

        var self = this;

        var selectedDiv;


        /**
         * if we want to allow the search in many DB we should do something like this
         *
        var authList = [];
        each(Indico.Settings.ExtAuthenticators, function(auth) {
                var searchExt = Html.checkbox({});
                $B(searchExt, this.criteria.accessor('searchExt'));
                authList.append(["Search "+auth, searchExt])
        });
        */
        var searchExtForm = null;
        if (!empty(Indico.Settings.ExtAuthenticators)){
            var searchExt = Html.checkbox({});
            $B(searchExt, this.criteria.accessor('searchExt'));
            /*
             * TODO: TO IMPROVE THIS (related with upper comment).
             * Current search service does not support to search in specific authenticators. But you
             * can search in all of them by activating the flag "searchExt".
             * For CERN, we want to display NICE instead of "Search external authenticator", that's
             * why we use Indico.Settings.ExtAuthenticators[0] because we suppose that there will be
             * just one external authenticator.
             */
            searchExtForm = IndicoUtil.createFormFromMap([["Search "+Indico.Settings.ExtAuthenticators[0], searchExt]]);
        }

        var source = null;
        this.searchButton = Html.input("button", {}, $T("Search"));
        var parametersArea = this.searchGroups?
        this.parametersWidget.draw():this.parametersWidget;

        var formPart = Html.div({}, parametersArea, searchExtForm, Html.div({style:{textAlign:"center"}},this.searchButton));
        this.searchButton.observeClick(function(){
            if (!source) {
                source = indicoSource('search.usersGroups', self.criteria);
                bind.element(peopleList, $L($V(source, "people")), template('user'));
                bind.element(groupList, $L($V(source, "groups")), template('group'));
                source.state.observe(function(state) {
                    if (state == SourceState.Loaded) {
                        userList.set(selectedDiv);
                        self.searchButton.dom.disabled = false;
                        if ( (!self.searchGroups && empty($L($V(source, "people")))) ||
                             (self.searchGroups && self.parametersWidget.selected.get() == 'Users' && empty($L($V(source, "people")))) ||
                            (self.searchGroups && self.parametersWidget.selected.get() == 'Groups' && empty($L($V(source, "groups"))))) {
                            userList.append(Html.br());
                            userList.append(Html.em({style:{padding: pixels(10)}}, $T("No results for this search...") ));
                        }
                    }
                });
            }else {
                source.refresh();
            }
            selectedUserList.clear();
            selectedGroupList.clear();
            userList.set(Html.div({style: {paddingTop: '20px'}}, progressIndicator(false, true)));
            self.searchButton.dom.disabled = true;
        });


        // List of found users
        var template = function(userOrGroup) {
            return function(value){
                var liElem = value.isGroup?Html.li({}, value.name):
                Html.li({}, value.familyName.toUpperCase() + ', ' + value.firstName, Html.em({},' (' + value.email + ')'));
                liElem.observeClick(function() {
                    toggle(userOrGroup, value, liElem);
                });
                return liElem;
            };
        };

        var toggle = function(userOrGroup, object, element){
            var selectedList = userOrGroup=='user'?
                selectedUserList:selectedGroupList;

            if (!search(selectedList, match(object))) {
                if (self.onlyOne) {
                    self._clearSelections(selectedList, selectedDiv);
                }
                selectedList.insert(object);
                element.dom.className = 'selectedUser';
            }
            else {
                selectedList.remove(object);
                element.dom.className = 'unselectedUser';
            }
        };

        var peopleList = Html.ul("UIPeopleList");
        var groupList = Html.ul("UIPeopleList");

        var userList = Html.div({className:'UISearchPeopleListDiv'}, peopleList);
        selectedDiv = peopleList;

        var tooltipListEmpty = Html.em({style:{padding: pixels(10)}}, $T("Fill any of the upper fields and click search...") );
        userList.append(Html.br());
        userList.append(tooltipListEmpty);

        if (this.searchGroups) {
            this.parametersWidget.selected.observe(function(option) {
                if (option == 'Users') {
                    selectedDiv = peopleList;
                } else {
                    selectedDiv = groupList;
                }
                userList.set(selectedDiv);
                if (!selectedDiv.get()) {
                    userList.append(Html.br());
                    userList.append(tooltipListEmpty);
                }
            });

            this.parametersWidget.selected.set('Users');
        }

        var addButton = new DisabledButton(Html.input("button", {disabled:true}, $T("Add") ));
        var cancelButton = Html.input("button", {style:{marginLeft: pixels(5)}}, $T("Cancel") );
        var buttons = Html.div({ style: {textAlign: 'center'}}, addButton.draw(), cancelButton);

        cancelButton.observeClick(function(){
            self.close();
        });

        var tooltip;

        addButton.observeEvent('mouseover', function(event){
            if (!addButton.isEnabled()) {
                tooltip = IndicoUI.Widgets.Generic.errorTooltip(event.clientX, event.clientY, $T("You must select at least one item from the list"), "tooltipError");
            }
        });

        addButton.observeEvent('mouseout', function(event){
            Dom.List.remove(document.body, tooltip);
        });

        addButton.observeClick(function(){
            var mergedList = concat(
                selectedUserList.allItems(),
                selectedGroupList.allItems()
            );
            self.processFunction(mergedList);
            self.close();
        });

        return this.ExclusivePopup.prototype.draw.call(
            this,
            Html.div({},
                     Widget.block([
                         formPart,
                         userList,
                         buttons
                     ])));
    }

},
      function(title, process, searchGroups, conferenceId, onlyOne) {
          var self = this;

          this.searchGroups = exists(searchGroups)?searchGroups:false;
          this.onlyOne = any(onlyOne, false);

          this.criteria = new WatchObject();

          if (conferenceId) {
              this.criteria.set('conferenceId', conferenceId);
          }

          if (this.searchGroups) {
              this.parametersWidget = new TabWidget(
                  [
                      ["Users", self._drawUsers()],
                      ["Groups", self._drawGroups()]
                  ], 350, 150, 1);
          } else {
              this.parametersWidget = self._drawUsers();
          }

          this.parametersWidget.options = $L(["Users", "Groups"]);
          this.processFunction = process;
          this.ExclusivePopup(title, function(){return true;});
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
type("UserDataPopup", ["ExclusivePopup"],
     {
         draw: function() {
             var userData = this.userData;
             var self = this;
             self.parameterManager = new IndicoUtil.parameterManager();

             grant = [];
             if (this.grantSubmission) {
                 grant = ['Grant submission rights', $B(Html.checkbox({}), userData.accessor('submission'))];
             }
             return this.ExclusivePopup.prototype.draw.call(
                 this,
                 Widget.block([IndicoUtil.createFormFromMap([
                     [$T('Title'), $B(Html.select({}, Html.option({}, ""), Html.option({}, $T("Mr.")), Html.option({}, $T("Mrs.")), Html.option({}, $T("Ms.")), Html.option({}, $T("Dr.")), Html.option({}, $T("Prof."))), userData.accessor('title'))],
                     [$T('Family Name'), $B(self.parameterManager.add(Html.edit({style: {width: '300px'}}), 'text', false), userData.accessor('familyName'))],
                     [$T('First Name'), $B(Html.edit({style: {width: '300px'}}), userData.accessor('firstName'))],
                     [$T('Affiliation'), $B(Html.edit({style: {width: '300px'}}), userData.accessor('affiliation'))],
                     [$T('Email'), $B(self.parameterManager.add(Html.edit({style: {width: '200px'}}), 'text', false), userData.accessor('email'))],
                     [$T('Address'), $B(Html.textarea(), userData.accessor('address'))],
                     [$T('Telephone'), $B(Html.edit({style: {width: '150px'}}), userData.accessor('telephone'))],
                     [$T('Fax'), $B(Html.edit({style: {width: '150px'}}), userData.accessor('fax'))],
                     grant
                 ]),
                               Html.div({style: {textAlign: 'center'}},
                                        Widget.link(command(curry(this.action, userData, function() {self.close();}), Html.input("button", {}, $T("Save")))),
                                        Widget.link(command(function() {self.close();}, Html.input("button", {}, $T("Cancel")))))
                              ]));

         }

     },
     function(title, userData, action, grantSubmission) {
         this.userData = userData;
         this.action = action;
         this.grantSubmission = exists(grantSubmission)?grantSubmission:false;
         this.ExclusivePopup(title,  function(){return true;});
     }
    );


/**
 * Creates a list of users. Each user can be edited or removed.
 * It inherits from ListWidget who in turn inherits from WatchObject, so the usual WatchObject methods (get, set)
 * can be used on it. For example 'set' can be used to initialize the list.
 * This means that the users are stored with their id's as keys.
 * @param {String} style The class of the ul that will contain the users.
 * @param {Boolean} allowEdit. If true, each user will have an edit button to change their data.
 * @param {Function} editProcess. A function that will be called when a user is edited. The function will
 *                                be passed the new data as a WatchObject.
 */
type("UserListWidget", ["ListWidget"],
     {
         _drawItem: function(user) {
             var self = this;
             var userData = user.get();

             var editButton = Widget.link(command(function() {
                 editPopup = new UserDataPopup(
                     'Change user data',
                     userData.clone(),
                     function(newData, suicideHook) {
                         self.editProcess(userData, function(result) {
                             if (result) {
                                 userData.update(newData.getAll());
                                 if (!startsWith(userData.get('id'), 'newUser')) {
                                     userData.set('id', 'edited' + userData.get('id'));
                                 }
                             }
                         });
                         suicideHook();
                     }
                 );
                 editPopup.open();
             }, IndicoUI.Buttons.editButton()));

             var removeButton = Widget.link(command(function() {
                 self.removeProcess(userData, function(result) {
                     if (result) {
                         self.set(user.key, null);
                     }
                 });

             }, IndicoUI.Buttons.removeButton()));

             return Html.div({style:{display: 'inline'}},
                             userData.get('isGroup')?
                             $B(Html.span(), userData.accessor('name')):
                             Html.span({},
                                     Html.div({style: {cssFloat: "right", paddingRight: "10px"}}, self.allowEdit ? editButton : '',removeButton),
                                     $B(Html.span(), userData.accessor('familyName'), function(name){return name.toUpperCase();}),
                                       ', ',
                                       $B(Html.span(), userData.accessor('firstName'))));
         }
     },

     function(style, allowEdit, editProcess, removeProcess) {
         this.allowEdit = allowEdit;
         this.editProcess = editProcess;
         this.removeProcess = removeProcess;
         if (!exists(style)) {
             style = "UIPeopleList";
         }
         this.ListWidget(style);
     }
    );

/**
 * Creates a form field with a list of users.
 * Users can be added from an initial list of users, from the currently logged in user's favorites (user basket),
 * from a user search dialog, or from a 'new user' dialog.
 * The list of users (a UserListWidget, i.e. a WatchObject) can be retrieved by calling getUsers().
 *
 * The 'id' attribute of the users in the list will depend from their origin.
 * -If it was added from the search dialog, the id will be a number (corresponding to the avatar id).
 * -It it was added from the 'new user' dialog, the id will be 'newUserXX', where XX is auto-increment starting from 0.
 * -If it was added from the list of suggested users, it will retain the id of the user that was put in the list.
 * -It the user was edited, and the edited user corresponded to an Avatar, the id will be 'editedXX' where XX is the id of the Avatar used initially.
 *
 * @param {String } userDivStyle A CSS class for the div that will sourround the user list.
 * @param {String } userListStyle A CSS class for the user list. It will be passed to the inner UserListWidget.
 * @param {list} initialUsers A list of users that will appear initially. Example: <%= jsonEncode(DictPickler.pickle([AvatarHolder().getById(1), AvatarHolder().getById(2)])) %>
 * @param {list} optionalUsers A list of users that will be offered as options to be added. Example: <%= jsonEncode(DictPickler.pickle([AvatarHolder().getById(3), AvatarHolder().getById(4)])) %>
 * @param {list} favouriteUsers A list of users that will be offered as options to be added, under the category "Favorite users" Example: <%= jsonEncode(DictPickler.pickle(some_user.getPersonalInfo().getBasket().getUsers()) %>
 * @param {Boolean} allowSearch If True, a 'Search User' button will be present.
 * @param {Boolean} allowNew If True, a 'New User' button will be present.
 * @param {Boolean} allowEdit If True, users in the list will be able to be edited.
 * @param {Function} newProcess A function that will be called when new users (from new data, or from the search dialog, or from the suggested list) is added to the list.
 *                              The function will be passed a list of WatchObjects representing the users.
 * @param {Function} editProcess A function that will be called when a user is edited.
 *                               The function will be passed a WatchObject representing the user.
 * @param {Function} removeProcess A function that will be called when a user is removed.
 *                                 The function will be passed a WatchObject representing the user.
 * @param {list} privileges dictionary with the privileges that we can set for the users. There is a key and a tuple as vale: (label, default value for checked). E.g. {"grant-manager": ["event modification", false]}
 * @param {string} conferenceId for author list search
 */
type("UserListField", ["IWidget"], {
    _highlightNewUser: function(userId) {
        var self = this;
        IndicoUI.Effect.highLightBackground(self.userList.getId() + '_' + userId);
    },

    getUsers: function() {
        return $L(this.userList);
    },

    getPrivileges: function() {
        return this.selectedPrivileges;
    },

    draw: function() {
        var self = this;

        var select;
        var buttons1 = Html.div({style:{marginTop: pixels(10)}});

        if (self.allowSearch) {
            var searchUserButton = Html.input("button", {style:{marginRight: pixels(5)}}, $T('Add Existing') );
            searchUserButton.observeClick(function(){
                var handler = function(userList) {
                    self.newProcess(userList, function(value) {
                        if (value) {
                            each(userList, function(user){
                                if (self.userList.get("existingAv"+user.id)) {
                                    self.userList.set("existingAv"+user.id, null);
                                }
                                self.userList.set("existingAv"+user.id, $O(user));
                                self._highlightNewUser("existingAv"+user.id);
                            });
                        }
                    });
                };
                var userSearchPopup = new UserSearchPopup("Search users", handler, self.enableGroups, self.conferenceId);
                userSearchPopup.open();
            });
            buttons1.append(searchUserButton);
        }

        if (self.allowNew) {
            var addNewUserButton = Html.input("button", {style:{marginRight: pixels(5)}}, $T('Add New') );
            addNewUserButton.observeClick(function(){
                var newUserId = 'newUser' + self.newUserCounter++;
                var newUser = $O({'id': newUserId});
                newUserPopup = new UserDataPopup(
                    $T('New user'),
                    newUser,
                    function(newData, suicideHook) {
                        if (newUserPopup.parameterManager.check()) {
                            newUser.update(newData.getAll());
                            self.newProcess([newUser], function(result) {
                                if (result) {
                                    self.userList.set(newUserId, newUser);
                                    self._highlightNewUser(newUserId);
                                }
                            });
                            suicideHook();
                        }
                    }
                );
                newUserPopup.open();
            });
            buttons1.append(addNewUserButton);
        }

        self.allOptions = new WatchObject();
        if (self.favouriteUsers) {
            self.allOptions.update(self.favouriteUsers.getAll());
        }
        if (self.optionalUsers) {
            self.allOptions.update(self.optionalUsers.getAll());
        }

        if (self.favouriteUsers || self.optionalUsers) {

            var addUserButton = Html.input("button", {style:{marginRight: pixels(5)}}, $T('Add from favourites') );
            self.userSelectPopup = new AdditionalUsersPopup($T("Add from favourites and others"), self.favouriteUsers, self.optionalUsers, function(){

                    var newUserIds = getSelectedItems(self.userSelectPopup.selectList);
                    each(newUserIds, function(newUserId) {
                        var newUser = self.allOptions.get(newUserId).clone();
                        if (self.userList.get("existingAv"+newUserId)) {
                            self.userList.set("existingAv"+newUserId, null);
                        }
                        self.newProcess([newUser], function(result) {
                            if (result) {
                                self.userList.set("existingAv"+newUserId, newUser);
                                self._highlightNewUser("existingAv"+newUserId);
                            }
                        });
                    });

                    return true;
            });

            addUserButton.observeClick(function(){
                self.userSelectPopup.open();
            });
            buttons1.append(addUserButton);

        }

        var privilegesDiv = Html.span({style:{marginTop: pixels(10)}});
        var keysList = keys(this.privileges);
        if (keysList.length>0) {
            privilegesDiv.append(Html.span({},$T("Grant all these users with privileges: ")));
        }
        var comma = ", ";
        for (var i=0; i<keysList.length; i++) {
            if (i+1 == keysList.length) {
                comma = "";
            }
            var key = keysList[i];
            var value = this.privileges[key];
            var checkbox = Html.checkbox({id:key, style:{verticalAlign:"middle"}}, value[1]?value[1]:null);
            $B(this.selectedPrivileges.accessor(key), checkbox);
            privilegesDiv.append(Html.span({},checkbox, value[0] + comma));
        }

        return Widget.block([Html.div(this.userDivStyle,this.userList.draw()), privilegesDiv, buttons1]);

    }
},
     function(userDivStyle, userListStyle, initialUsers, optionalUsers, favouriteUsers, allowSearch,
              allowNew, allowEdit, newProcess, editProcess, removeProcess, enableGroups, privileges, conferenceId) {
         this.userList = new UserListWidget(userListStyle, allowEdit, editProcess, removeProcess);
         if (!exists(userDivStyle)) {
             userDivStyle = "UIPeopleListDiv";
         }
         this.userDivStyle = userDivStyle;
         this.optionalUsers = new WatchObject();
         this.favouriteUsers = new WatchObject();
         this.newProcess = newProcess;
         this.newUserCounter = 0;
         this.allowSearch = allowSearch;
         this.allowNew = allowNew;
         this.enableGroups = exists(enableGroups)?enableGroups:false;
         this.privileges = exists(privileges)?privileges:{};
         this.selectedPrivileges = new WatchObject();
         this.conferenceId = exists(conferenceId)?conferenceId:null;


         var self = this;

         each(initialUsers, function(user){
             if (any(user.isAvatar, false)) {
                 self.userList.set('existingAv' + user.id, $O(user));
             } else {
                 self.userList.set(user.id, $O(user));
             }

         });

         if (optionalUsers) {
             each(optionalUsers, function(user){
                 self.optionalUsers.set(user.id, $O(user));
             });
         } else {
             self.optionalUsers = null;
         }

         if (favouriteUsers) {
             each(favouriteUsers, function(user){
                 self.favouriteUsers.set(user.id, $O(user));
             });
         } else {
             self.favouriteUsers = null;
         }

     }
    );


/**
 * Creates a form field with a list of users.
 * Same as UserListField but no functions will be called when users are added, edited or removed.
 * See UserListField for the meaning of the arguments and other stuff.
 */
type("StaticUserListField", ["UserListField"], {},
     function(initialUsers, optionalUsers, favouriteUsers, allowSearch, allowNew, userListStyle){
         this.UserListFieldbase(initialUsers, optionalUsers, favouriteUsers, allowSearch, allowNew, userListStyle, userListNothing, userListNothing, userListNothing);
     }
    );

/**
 * Creates a user search pop-up dialog that queries the user
 * database.
 * @param {Function} process Callback method that is invoked
 *                   in order to process the users that are selected
 *                   from the list.
 * @param {Function} suicideHook A callback method that is passed by
 *                   the exclusivePopup method, and is called by the
 *                   function when the dialog needs to be destroyed.
 */
type ("AdditionalUsersPopup", ["ExclusivePopup"], {

    draw: function () {

        var self = this;

        var userSelect = function(){

            var favouriteUsersOptGroup;
            var optionalUsersOptGroup;

            if (self.favouriteUsers) {
                favouriteUsersOptGroup = Html.optgroup({label: $T('Favourite Users')});
                bind.element(favouriteUsersOptGroup, self.favouriteUsers, function(item){
                    return Html.option({value: item.key, className: 'favoriteUser'},
                                       item.get().get('familyName').toUpperCase() + ', ' + item.get().get('firstName'));
                });
            }

            if (self.optionalUsers) {
                optionalUsersOptGroup = Html.optgroup({label: $T('Other Users')});
                bind.element(optionalUsersOptGroup, self.optionalUsers, function(item){
                    return Html.option({value: item.key, className: 'favoriteUser'},
                                       item.get().get('familyName').toUpperCase() + ', ' + item.get().get('firstName'));
                });
            }

            return bind.element(Html.select({multiple: true, size:"20", style:{width:pixels(420), marginRight: pixels(5), padding:pixels(10)}}),
                                [self.favouriteUsers ? favouriteUsersOptGroup : '',
                                 self.optionalUsers ? optionalUsersOptGroup : '']);



        }; //end of userSelect

        self.selectList = userSelect();

        self.selectList.observe(function(){
            if (getSelectedItems(self.selectList).length > 0) {
                addButton.enable();
            }else {
                addButton.disable();
            }
        });

        var addButton = new DisabledButton(Html.input("button", {disabled:true}, $T("Add")));
        var cancelButton = Html.input("button", {style:{marginLeft: pixels(5)}}, $T("Cancel"));
        var buttons = Html.div("dialogButtons", addButton.draw(), cancelButton);

        cancelButton.observeClick(function(){
            self.close();
        });

        var tooltip;

        addButton.observeEvent('mouseover', function(event){
            if (!addButton.isEnabled()) {
                tooltip = IndicoUI.Widgets.Generic.errorTooltip(event.clientX, event.clientY, $T("You must select at least one item from the list"), "tooltipError");
            }
        });

        addButton.observeEvent('mouseout', function(event){
            Dom.List.remove(document.body, tooltip);
        });

        addButton.observeClick(function(){
            self.processFunction();
            self.close();
        });

        return this.ExclusivePopup.prototype.draw.call(
            this,
            Html.div({},
                     Widget.block([
                         self.selectList,
                         buttons
                     ])));
    }

    },
      function(title, favouriteUsers, optionalUsers, process) {
          var self = this;
          self.favouriteUsers = favouriteUsers;
          self.optionalUsers = optionalUsers;

          this.processFunction = process;
          this.ExclusivePopup(title, function(){return true;});
      }
     );

type("AddToFavoritesButton", ["RemoteSwitchButton"],
/**
 * Creates a button that adds a user to the 'favorites' list/basket
 * takes the initial state of the button and the user id as parameters
 */
     {
     },
     function(state, id) {

         var imageRemove = Html.img({
             // make the "star" colorful or grey depending on whether
             // the user is already in the favorites or not
             src: imageSrc("star"),
             alt: 'Remove from Favorites',
             title: $T('Remove from your list of favorite users')
             });

         var imageAdd = Html.img({
             // make the "star" colorful or grey depending on whether
             // the user is already in the favorites or not
             src: imageSrc("starGrey"),
                 alt: 'Add to Favorites',
             title: $T('Add to your list of favorite users')
         });

         // call the parent constructor
         this.RemoteSwitchButton(
             state,
             imageRemove,
             imageAdd,
             'user.favorites.removeUser',
             'user.favorites.addUsers',
             {value: [{ 'id': id }]});
     });