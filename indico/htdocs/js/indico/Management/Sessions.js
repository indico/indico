/*
 * Manager for the modification control list of users/groups in session management
 *
 */
type("SessionControlManager", ["ModificationControlManager"], {

    _manageBothUserList: function(method, params) {
        var self = this;
        indicoRequest(
                method, params,
                function(result, error) {
                    if (!error) {
                        // Update both lists of the page
                        modificationControlManager.updateUserList(result[0]);
                        coordinationControlManager.updateUserList(result[1]);
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
        );
    },

	_getModifyAsConvenerParams: function(userId) {
        var params = this.params;
        params['userId'] = userId;
        return params;
    },

    _getRemoveParams: function(userId, kindOfUser) {
        var params = this.params;
        params['userId'] = userId;
        params['kindOfUser'] = kindOfUser;
        return params;
    },

    updateUserList: function(result) {
        this._updateUserList(result)
    },

	_updateUserList: function(result) {
        var self = this;
        // update the user list
        this.inPlaceListElem.set('');
        for (var i=0; i<result.length; i++) {
            var userRowElements = [];

            var kindOfUser = "principal";
            var userIdentifier = result[i]['id'];
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
                kindOfUser = "pending";
                userIdentifier = result[i]['email'];
                var fullName = $T('Non-registered-user');
                var elementStyle = "UIPerson";
            }
            if (result[i]['isConvener']) {
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, fullName,
                        Html.small({},' ('+ result[i]['email'] + ')'),
                        Html.small({style:{fontWeight:'bold', paddingLeft:'5px'}},' Convener'));
            } else {
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, fullName, Html.small({},' ('+ result[i]['email'] + ')'));
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
                id: 'r_' + kindOfUser + '_' + userIdentifier,
                style:{marginRight:'10px', cssFloat:'right', cursor:'pointer'}
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

            var row = Html.li({className: elementStyle, onmouseover: "this.style.backgroundColor = '#ECECEC';",
                                onmouseout : "this.style.backgroundColor='#ffffff';", style:{cursor:'auto'}});

            for (var j=userRowElements.length-1; j>=0; j--) { // Done the 'for' like this because of IE7
                row.append(userRowElements[j]);
            }
            this.inPlaceListElem.append(row);
        }
    },

    _addParticipantMenu: function(element, user) {
        var self = this;

        element.observeClick(function(e) {
            var menuItems = {};

            if (!user['isConvener']) {
                menuItems[$T('Add as convener')] = function() {
                    self._manageBothUserList(self.methods["addAsConvener"], self._getModifyAsConvenerParams(user['id']));
                    menu.close();
                };
            } else {
                menuItems[$T('Remove as convener')] = function() {
                    self._manageBothUserList(self.methods["removeAsConvener"], self._getModifyAsConvenerParams(user['id']));
                    menu.close();
                };
            }

            var menu = new PopupMenu(menuItems, [element], "popupList");
            var pos = element.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
    }

},

    function(confId, methods, params, inPlaceListElem, userCaption) {
        this.ModificationControlManager(confId, methods, params, inPlaceListElem, userCaption);
    }
);
