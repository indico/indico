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


// Class to manage every field limited by words
type("WordsManager", [],
    {

    checkNumWords: function() {
        if ((this.maxWords - this._numWords(this.element.val())) < 0) {
            this.maxWordsCounter.set(Html.span({className:'formError'}, $T('Over the limit')));
        } else {
            this.maxWordsCounter.set(this.maxWords - this._numWords(this.element.val()) + $T(' words left'));
        }
        this.pm.check();
    },

    _numWords: function(value) {
        return Util.Text.wordsCounter(value);
    },

    _addEvents: function() {
        var self = this;
        this.element.on('change', function() {self.checkNumWords();});
        this.element.on('keyup', function() {self.checkNumWords();});
        this.element.on('blur', function() {self.checkNumWords();});
    },

    checkPM: function() {
        return this.pm.check();
    },


    checkPMEmptyField: function() {
        // Remove the previous pm, check if the field is empty, restore the previous pm
        this.pm.remove(this.element);
        this.pm.add(this.element, null, !this.isMandatory);
        if (this.pm.check()) {
            this.pm.remove(this.element);
            this.initializePM();
            return true;
        } else {
            this.pm.remove(this.element);
            this.initializePM();
            return false;
        }
    },

    initializePM: function() {
        var self = this;
        this.pm.add(this.element, null, !this.isMandatory, function(value) {
            if (self._numWords(value) > self.maxWords) {
                var numExceededWords = self._numWords(value) - self.maxWords;
                if (numExceededWords == 1) {
                    var error = Html.span({}, $T("Maximum number of words has been exceeded in ") + numExceededWords + $T(" word."));
                } else {
                    var error = Html.span({}, $T("Maximum number of words has been exceeded in ") + numExceededWords + $T(" words."));
                }
                return error;
            }
            else {
                self.element.removeClass('invalid');
                return null;
            }
        });
    }
},

function(element, maxWords, maxWordsCounter, isMandatory) {
    var self = this;
    this.element = element;
    this.maxWords = maxWords;
    this.maxWordsCounter = maxWordsCounter;
    this.isMandatory = isMandatory;
    this.pm = new IndicoUtil.parameterManager();
    this.initializePM();
    this._addEvents();
});


//Class to manage every field limited by characters
type("CharsManager", [],
    {

    checkNumChars: function() {
        if ((this.maxChars - this._numChars(this.element.val())) < 0) {
            this.maxCharsCounter.set(Html.span({className:'formError'}, $T('Over the limit')));
        } else {
            this.maxCharsCounter.set(this.maxChars - this._numChars(this.element.val()) + $T(' chars left'));
        }
        this.pm.check();
    },

    _numChars: function(value) {
        return value.length;
    },

    _addEvents: function() {
        var self = this;
        this.element.on('change', function() {self.checkNumChars();});
        this.element.on('keyup', function() {self.checkNumChars();});
        this.element.on('blur', function() {self.checkNumChars();});
    },

    checkPM: function() {
        return this.pm.check();
    },

    checkPMEmptyField: function() {
        // Remove the previous pm, check if the field is empty, restore the previous pm
        this.pm.remove(this.element);
        this.pm.add(this.element, null, !this.isMandatory);
        if (this.pm.check()) {
            this.pm.remove(this.element);
            this.initializePM();
            return true;
        } else {
            this.pm.remove(this.element);
            this.initializePM();
            return false;
        }
    },

    initializePM: function() {
        var self = this;
        this.pm.add(this.element, null, !this.isMandatory, function(value) {
            if (self._numChars(value) > self.maxChars) {
                var numExceededChars = self._numChars(value) - self.maxChars;
                if (numExceededChars == 1) {
                    var error = Html.span({}, $T("Maximum number of characters has been exceeded in ") + numExceededChars + $T(" character."));
                } else {
                    var error = Html.span({}, $T("Maximum number of characters has been exceeded in ") + numExceededChars + $T(" characters."));
                }
                return error;
            } else {
                self.element.removeClass('invalid');
                return null;
            }
        });
        return false;
    }
},

function(element, maxChars, maxCharsCounter, isMandatory) {
    this.element = element;
    this.maxChars = maxChars;
    this.maxCharsCounter = maxCharsCounter;
    this.isMandatory = isMandatory;
    this.pm = new IndicoUtil.parameterManager();
    this.initializePM();
    this._addEvents();
});



/*
 * AuthorsManager class
 */
type("AuthorsManager", [], {

    getNewId: function() {
        this.counter += 1;
        return this.root + this.counter;
    },

    getPrAuthors: function() {
        return this.prAuthors;
    },

    getCoAuthors: function() {
        return this.coAuthors;
    },

    getAllAuthors: function() {
        var l = $L(this.prAuthors.usersList);
        l.appendMany(this.coAuthors.usersList);
        return l;
    },

    updatePositions: function() {
        // Before update anything, save the previous values
        this.prevPrAuthors = this.prAuthors.getUsersList();
        this.prevCoAuthors = this.coAuthors.getUsersList();
        this.prAuthors.updateUserPositions();
        this.coAuthors.updateUserPositions();
    },

    getFromOtherList: function(authorId, listId) {
        if (listId == 'pr') {
            return this.getAuthorById(authorId, this.prevCoAuthors);
        } else if (listId == 'co') {
            return this.getAuthorById(authorId, this.prevPrAuthors);
        }
    },

    getAuthorById: function(authorId, list) {
        for (var i=0; i<list.length.get(); i++) {
            if (authorId == list.item(i)['id']) {
                return list.item(i);
            }
        }
        return null;
    },

    checkPrAuthorsList: function() {
        this.prAuthors.checkEmptyList();
    },

    manageAuthor: function(option, userId) {
        var author = this.getAuthorById(this.root+userId, this.prAuthors.getUsersList());
        if (!author) {
            author = this.getAuthorById(this.root+userId, this.coAuthors.getUsersList());
            if (option == 'edit')
                this.coAuthors.editUser(author);
            else if (option == 'remove')
                this.coAuthors.removeUser(author);
        } else {
            if (option == 'edit')
                this.prAuthors.editUser(author);
            else if (option == 'remove')
                this.prAuthors.removeUser(author);
        }
    },

    canDropElement: function(tableType, authorId) {
        // search the author in primary list
        var author = this.getAuthorById(authorId, this.prAuthors.getUsersList());
        if (!author) {
            // search the author in co authors list
            author = this.getAuthorById(authorId, this.coAuthors.getUsersList());
            if (tableType == 'pr') { // Trying to move a co-author to primary authors list
                return !this.prAuthors.isAlreadyInList(author['email'], false);
            }
        } else { // Author is a primary author
            if (tableType == 'co') { // Trying to move primary author to co-authors list
                return !this.coAuthors.isAlreadyInList(author['email'], false);
            }
        }
        return true;
    }


},

function(initialPrAuthors, initialCoAuthors, showSpeaker) {
    this.showSpeaker = any(showSpeaker, false);
	this.root = 'author_';
    this.counter = -1;
    this.prAuthors = new AuthorListManager($E('inPlacePrAuthors'),
            $E('inPlacePrAuthorsMenu'),  "primary author", initialPrAuthors, this);

    this.coAuthors = new AuthorListManager($E('inPlaceCoAuthors'),
            $E('inPlaceCoAuthorsMenu'),  "co-author", initialCoAuthors, this);
});



/*
 * Manager of authors list in abstract submission
 */
type("AuthorListManager", [], {

    addManagementMenu: function() {
        var self = this;
        this.inPlaceMenu.observeClick(function(e) {
            var menuItems = {};

            menuItems["searchUser"] = {action: function(){ self._addExistingUser($T("Add author"), true, this.confId, false,
                    true, true, false, true); }, display: $T('Search User')};
            menuItems["defineNew"] = {action: function(){ self._addNonExistingUser(); }, display: $T('Define New')};

            var menu = new PopupMenu(menuItems, [self.inPlaceMenu], "popupList", true);
            var pos = self.inPlaceMenu.getAbsolutePosition();
            menu.open(pos.x, pos.y + 20);
            return false;
        });
    },

    _addExistingUser: function(title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
                               showToggleFavouriteButtons) {
        // Create the popup to add new users
        var self = this;
        // params: (title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers, onlyOne,
        //          showToggleFavouriteButtons, chooseProcess)
        var chooseUsersPopup = new ChooseUsersPopup(title, allowSearch, conferenceId, enableGroups, includeFavourites, suggestedUsers,
                                                    onlyOne, showToggleFavouriteButtons, false,
                    function(userList) {
                        for (var i=0; i<userList.length; i++) {
                            if (!self.isAlreadyInList(userList[i]['email'], true)) {
                                userList[i]['id'] = self.authorsManager.getNewId();
                                userList[i]['isSpeaker'] = false;
                                self.usersList.append(userList[i]);
                            } else {
                                var popup = new AlertPopup($T('Add author'),
                                                $T('The email address (') + userList[i]['email'] +
                                                $T(') of a user you are trying to add is already used by another author. An author can be added only once and only in one list.'));
                                popup.open();
                            }
                        }
                        self._updateUserList();
                    });
        chooseUsersPopup.execute();
    },

    _addNonExistingUser: function() {
        var self = this;
        var newUser = $O();
        var newUserPopup = new AuthorDataPopup(
                $T('New author'),
                newUser,
                function(newData) {
                    var newUserData = {'id': self.authorsManager.getNewId(),
                                       'title': any(newData.get('title'), ''),
                                       'firstName': any(newData.get('firstName'), ''),
                                       'familyName': any(newData.get('familyName'), ''),
                                       'affiliation': any(newData.get('affiliation'), ''),
                                       'email': any(newData.get('email'), ''),
                                       'phone': any(newData.get('phone'), ''),
                                       'isSpeaker': any(newData.get('isSpeaker'), false)
                                      };
                    if (newUserPopup.parameterManager.check()) {
                        if (!self.isAlreadyInList(newUserData['email'], true)) {
                            newUserPopup.close();
                            self.usersList.append(newUserData);
                            self._updateUserList();
                        } else {
                            var popup = new AlertPopup($T('Add author'),
                                    $T('The email address (') + newUserData['email'] +
                                    $T(') is already used by another participant. Please modify email field value.'));
                            popup.open();
                        }
                    }
                });
        newUserPopup.open();
    },

    isAlreadyInList: function(email, checkAll) {
        // It checks if there is any user with the same email
        var uList = this.usersList;
        if (checkAll) {
            uList = this.authorsManager.getAllAuthors()
        }
        for (var i=0; i<uList.length.get(); i++) {
            if (email && email == uList.item(i)['email']) {
                return true;
            }
        }
        return false;
    },

    editUser: function(author) {
        var self = this;
        if (author) {
            var killProgress = IndicoUI.Dialogs.Util.progress();
            var user = $O(author);
            var editUserPopup = new AuthorDataPopup(
                $T('Edit author data'),
                user,
                function(newData) {
                    if (editUserPopup.parameterManager.check()) {
                        self._userModifyData(author, newData);
                        self._updateUserList();
                        editUserPopup.close();
                    }
                });
            editUserPopup.open();
            killProgress();
        } else {
            var popup = new AlertPopup($T('Edit author'), $T('The user you are trying to edit does not exist.'));
            popup.open();
        }
    },

    _userModifyData: function(author, newData) {
        author['title'] = any(newData.get('title'), '');
        author['familyName'] = any(newData.get('familyName'), '');
        author['firstName'] = any(newData.get('firstName'), '');
        author['affiliation'] = any(newData.get('affiliation'), '');
        author['email'] = any(newData.get('email'), '');
        author['phone'] = any(newData.get('phone'), '');
    },

    removeUser: function(author) {
        if (author) {
            this.usersList.remove(author);
            this._updateUserList();
            return;
        } else {
            var popup = new AlertPopup($T('Remove author'), $T('The user you are trying to remove does not exist.'));
            popup.open();
        }
    },

    _updateUserList: function() {
        // Update the users in the interface
        var self = this;
        this.inPlaceListElem.set('');
        var table;
        var tbody;
        var tr;
        var mainLi;
        var td;
        var div;
        var checkbox;
        var span;

        for (var i=0; i<this.usersList.length.get(); i++) {
            mainLi = Html.li({id: this.usersList.item(i)['id']});
            table = Html.table({className:'authorTable', cellspacing:'4px'});
            mainLi.append(table);
            tbody = Html.tbody();
            table.append(tbody);
            tr = Html.tr();
            tbody.append(tr);

            // Add author full name
            if (!this.usersList.item(i)['title'] && !this.usersList.item(i)['firstName']) {
                var fullName = this.usersList.item(i)['familyName'].toUpperCase();
            } else if (!this.usersList.item(i)['title'] && this.usersList.item(i)['firstName']) {
                var fullName = this.usersList.item(i)['familyName'].toUpperCase() + ', ' + this.usersList.item(i)['firstName'];
            } else if (this.usersList.item(i)['title'] && !this.usersList.item(i)['firstName']) {
                var fullName = this.usersList.item(i)['title'] + ' ' + this.usersList.item(i)['familyName'].toUpperCase();
            } else {
                var fullName = this.usersList.item(i)['title'] + ' ' + this.usersList.item(i)['familyName'].toUpperCase() + ', ' + this.usersList.item(i)['firstName'];
            }

            // Add author affiliation
            if (this.usersList.item(i)['affiliation']) {
                // Show affiliation
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, fullName + ' ('+ this.usersList.item(i)['affiliation'] + ')');
            } else {
                var userText = Html.span({className:'nameLink', cssFloat:'left'}, fullName);
            }
            td = Html.td({className:'authorText'}, userText);
            tr.append(td);

            // edit icon
            var imageEdit = Html.img({
                src: imageSrc("edit"),
                alt: $T('Edit author'),
                title: $T('Edit this author'),
                className: 'UIRowButton2',
                id: 'Edit' + this.usersList.item(i)['id'],
                style:{cssFloat:'right', cursor:'pointer'}
            });

            imageEdit.observeClick(function(event) {
                if (event.target) { // Firefox
                    var userId = event.target.id.split('_')[1];
                } else { // IE
                    var userId = event.srcElement.id.split('_')[1];
                }
                self.authorsManager.manageAuthor('edit', userId);
            });
            td = Html.td({}, imageEdit);
            tr.append(td);

            // remove icon
            var imageRemove = Html.img({
                src: imageSrc("remove"),
                alt: $T('Remove author'),
                title: $T('Remove this author from the list'),
                id: 'Remove' + this.usersList.item(i)['id'],
                style:{marginRight:'15px', cssFloat:'right', cursor:'pointer'}
            });

            imageRemove.observeClick(function(event) {
                if (event.target) { // Firefox
                    var userId = event.target.id.split('_')[1];
                } else { // IE
                    var userId = event.srcElement.id.split('_')[1];
                }
                self.authorsManager.manageAuthor('remove', userId);
            });
            td = Html.td({}, imageRemove);
            tr.append(td);

            // append second tr to allow to add as presenter
            if(this.authorsManager.showSpeaker){
                tr = Html.tr();
                tbody.append(tr);
                if (this.usersList.item(i)['isSpeaker']) {
                    var isSpeaker = true;
                    var divClassName = 'divSelected';
                } else {
                    var isSpeaker = false;
                    var divClassName = 'divNotSelected';
                }
                td = Html.td({colspan:'1'});
                tr.append(td);
                div = Html.div({id: this.presenterDiv + this.usersList.item(i)['id'], className: divClassName});
                td.append(div);

                    checkbox = Html.checkbox({id: this.cb + this.usersList.item(i)['id']}, isSpeaker);
                    checkbox.observeClick(function(event) {
                        if (event.target) { // Firefox
                            var cbId = event.target.id.split('_')[1] + '_' + event.target.id.split('_')[2];
                        } else { // IE
                            var cbId = event.srcElement.id.split('_')[1] + '_' + event.srcElement.id.split('_')[2];
                        }
                        self._switchPresenter(cbId);
                    });
                    span = Html.span({}, $T('This author will be also a '), Html.span({style:{fontWeight:'bold'}}, $T('presenter')));
                    div.append(checkbox);
                    div.append(span);
            }
            this.inPlaceListElem.append(mainLi);
        }
        if (this.userCaption == 'primary author') {
            this.checkEmptyList();
        }
    },

    updateUserPositions: function() {
        var newList = $L(); // aux list
        for (var i=0; i<this.inPlaceListElem.dom.children.length; i++) {
            var childId = this.inPlaceListElem.dom.children[i].id;
            var author = this.getItemById(childId);
            if (author) { // the author is in the same list
                newList.append(author);
            } else {
                // author is not in the same list
                var author = this.authorsManager.getFromOtherList(childId, this.idRoot);
                newList.append(author);
            }
        }
        this.usersList = newList;
    },

    _switchPresenter: function(userId) {
        if ($E(this.cb + userId).dom.checked) {
            $E(this.presenterDiv + userId).dom.className = 'divSelected';
        } else {
            $E(this.presenterDiv + userId).dom.className = 'divNotSelected';
        }
        var author = this.getItemById(userId);
        if (author) {
            author['isSpeaker'] = $E(this.cb + userId).dom.checked;
        }
    },

    checkEmptyList: function() {
        if (this.usersList.length.get() == 0) {
            return true;
        } else {
            $E('prAuthorError').dom.style.display = 'none';
            return false;
        }
    },

    getItemById: function(authorId) {
        for (var i=0; i<this.usersList.length.get(); i++) {
            if (authorId == this.usersList.item(i)['id']) {
                return this.usersList.item(i);
            }
        }
        return null;
    },

    getUsersList: function() {
        return this.usersList;
    },

    hasPresenter: function() {
        for (var i=0; i<this.usersList.length.get(); i++) {
            if (this.usersList.item(i)['isSpeaker'])
                return true;
        }
        return false;
    }

},

    function(inPlaceListElem, inPlaceMenu, userCaption, initialList, authorsManager) {
        this.inPlaceListElem = inPlaceListElem;
        this.inPlaceMenu = inPlaceMenu;
        this.userCaption = userCaption;
        this.authorsManager = authorsManager;
        if (this.userCaption == 'primary author') {
            this.presenterDiv = 'prPresenterDiv_';
            this.cb = 'prCb_';
            this.idRoot = 'pr';
        } else if (this.userCaption == 'co-author') {
            this.presenterDiv = 'coPresenterDiv_';
            this.cb = 'coCb_';
            this.idRoot = 'co';
        }
        this.usersList = $L();

        if (initialList != []) {
            // Add the initial users
            for (var i=0; i<initialList.length; i++) {
                initialList[i]['id'] = this.authorsManager.getNewId();
                this.usersList.append(initialList[i]);
            }
            this._updateUserList();
        }
    }
);


//Class to manage the attachments
type("AbstractFilesManager", [],
    {

    addElement: function() {
        this.uploadLink.dom.innerHTML = $T('Attach another file');
        var newElement = this._buildElement();
        this.inPlaceMaterial.append(newElement);
        this.materialCounter += 1;
    },

    _buildElement: function() {
        var self = this;
        var div = Html.div({id:'divFile_' + this.materialCounter});
        var input = Html.input('file', {id: 'file_' + this.materialCounter, name: 'file', className: 'absMaterialInput', size:'25'});
        this.fileSizeDict['file_' + this.materialCounter] = 0;
        this._addObserveChange(input);

        var removeLink = Html.span({id: 'removeFile_' + this.materialCounter, className: 'fakeLink'}, $T('Remove'));
        removeLink.observeClick(function(event) {
            if (event.target) { // Firefox
                var elemId = event.target.id.split('_')[1];
            } else { // IE
                var elemId = event.srcElement.id.split('_')[1];
            }
            self._removeElement(elemId);
        });

        div.append(input);
        div.append(removeLink);
        return div;
    },

    _addObserveChange: function(input) {
        var self = this;
        input.observeChange(function(key) {
            if (key.currentTarget) {
                if (key.currentTarget.files && key.currentTarget.files.length) {
                    if (!self._addFile(key.currentTarget.files[0].size, key.currentTarget.id)) {
                        var popup = new AlertPopup($T('Warning'), $T('You cannot attach this file because it exceeds the maximum size allowed per file. (') + Indico.FileRestrictions.MaxUploadFileSize + 'MB)');
                        popup.open();
                        self._replaceInput(key.currentTarget);
                    } else if (!self.checkTotalFilesSize()) {
                        var popup = new AlertPopup($T('Warning'), $T('The maximum size allowed in total (') + Indico.FileRestrictions.MaxUploadFilesTotalSize + 'MB) ' + $T('has been exceeded. Please remove some file before submitting the abstract.'));
                        popup.open();
                    }
                }
            }
        });
    },

    _replaceInput: function(oldInput) {
        var elemId = oldInput.id.split('_')[1];
        $E('divFile_' + elemId).remove(oldInput);
        var newInput = Html.input('file', {id: 'file_' + elemId, name: 'file', className: 'absMaterialInput', size:'25'});
        this.fileSizeDict['file_' + elemId] = 0;
        this._addObserveChange(newInput);
        $('#removeFile_' + elemId).before(newInput.dom);
        this.checkTotalFilesSize();
    },

    _removeElement: function(elemId) {
        if ($E('file_' + elemId).dom.files && $E('file_' + elemId).dom.files.length > 0)
            this.filesSize -= ($E('file_' + elemId).dom.files[0].size) / (1024*1024);
        this.fileSizeDict['file_' + elemId] = 0;
        this.inPlaceMaterial.remove($E('divFile_' + elemId));
        this.materialCounter -= 1;
        if (this.materialCounter == 0) {
            this.uploadLink.dom.innerHTML = $T('Attach a file');
        }
        this.checkTotalFilesSize();
    },

    _addFile: function(size, elemId) {
        // if 0, unlimited
        if (Indico.FileRestrictions.MaxUploadFileSize <= 0) {
            return true;
        }
        var sizeInMB = size / (1024 * 1024);
        if (this.fileSizeDict[elemId] != 0) {
            // The element is not new, it is going to be replaced
            this.filesSize -= this.fileSizeDict[elemId];
            this.fileSizeDict[elemId] = 0;
        }
        if (sizeInMB > Indico.FileRestrictions.MaxUploadFileSize) {
            return false;
        } else {
            this.filesSize += sizeInMB;
            this.fileSizeDict[elemId] = sizeInMB;
            return true;
        }
    },

    checkTotalFilesSize: function() {
        // if 0, unlimited
        if (Indico.FileRestrictions.MaxUploadFilesTotalSize <= 0) {
            return true;
        }
        if (this.filesSize > Indico.FileRestrictions.MaxUploadFilesTotalSize) {
            this.uploadLink.dom.style.display = 'none';
            this.sizeError.dom.style.display = '';
            return false;
        } else {
            this.uploadLink.dom.style.display = '';
            this.sizeError.dom.style.display = 'none';
            return true;
        }
    },

    _drawExistingMaterial: function() {
        for (var i=0; i<this.initialMaterial.length; i++) {
            var newElement = this._buildExistingElement(i);
            this.inPlaceExistingMaterial.append(newElement);
        }
        var divOthers = Html.div({className: 'subGroupTitleAbstract', style:{paddingBottom:'0px'}}, $T('Other files you want to attach'));
        this.inPlaceExistingMaterial.append(divOthers);
    },

    _buildExistingElement: function(pos) {
        var file = this.initialMaterial[pos];
        var div = Html.div({id:'divExFile_' + pos, className:'existingAttachment'});
        var a = Html.a({href: file['url']}, file['file']['fileName']);
        div.append(a);
        var imageRemove = this._getImageRemove(pos);
        div.append(imageRemove);
        var inputHidden = Html.input('hidden', {name: 'existingFile'}, file['id']);
        div.append(inputHidden);
        return div;
    },

    _getImageRemove: function(pos) {
        var self = this;
        var imageRemove = Html.img({
            src: imageSrc("remove"),
            alt: $T('Remove material'),
            title: $T('Remove this attached material'),
            id: 'RemoveEx_' + pos,
            style:{marginLeft:'15px', cursor:'pointer', verticalAlign:'bottom'}
        });
        imageRemove.observeClick(function(event) {
            if (event.target) { // Firefox
                var elemId = event.target.id.split('_')[1];
            } else { // IE
                var elemId = event.srcElement.id.split('_')[1];
            }
            self._removeExistingMaterial(elemId);
        });
        return imageRemove;
    },

    _removeExistingMaterial: function(elemId) {
        if (this.initialMaterial[elemId]) {
            this.initialMaterialCounter -= 1;
            this.inPlaceExistingMaterial.remove($E('divExFile_' + elemId));
            if (this.initialMaterialCounter <= 0) {
                this.inPlaceExistingMaterial.dom.style.display = 'none';
            }
        }

        this.checkTotalFilesSize();
    }
},

function(inPlaceMaterial, inPlaceExistingMaterial, uploadLink, sizeError, initialMaterial) {
    this.inPlaceMaterial = inPlaceMaterial;
    this.inPlaceExistingMaterial = inPlaceExistingMaterial;
    this.uploadLink = uploadLink;
    this.sizeError = sizeError;
    this.initialMaterial = initialMaterial;
    this.materialCounter = 0;
    this.filesSize = 0;
    this.fileSizeDict = {};
    if (this.initialMaterial.length > 0) {
        this.inPlaceExistingMaterial.dom.style.display = '';
        this.initialMaterialCounter = this.initialMaterial.length;
        this._drawExistingMaterial();
    }
});


type("AbstractFieldDialogFactory", [],
    {
        makeDialog: function(fieldType, conferenceId, fieldId) {
            switch (fieldType) {
                case "textarea":
                    return new AddAbstractTextAreaFieldDialog(conferenceId, fieldId);
                case "input":
                    return new AddAbstractInputFieldDialog(conferenceId, fieldId);
                case "selection":
                    return new AddAbstractSelectionFieldDialog(conferenceId, fieldId);
                default:
                    return new AddAbstractTextAreaFieldDialog(conferenceId, fieldId);
            }
        }
    }
);

type("AddAbstractFieldDialog", ["ExclusivePopupWithButtons"],
    {
        draw: function() {
            this._generateForm();

            var form = IndicoUtil.createFormFromMap(this._form);
            return this.ExclusivePopupWithButtons.prototype.draw.call(this, $('<div></div>').append(form));
        },

        _finalizeForm: function() {
            var mandatoryFlag = this._parameterManager.add(Html.checkbox({}), "checkBox", true);
            this._form.push([$T("Mandatory"), $B(mandatoryFlag, this.info.accessor("isMandatory"))]);
        },

        _generateForm: function() {
            this._initializeForm();
            this._finalizeForm();

            if (this.info.get("id") !== undefined) {
                this.__fetch();
            }
        },

        _initializeForm: function() {
            var fieldCaption = this._parameterManager.add(new RealtimeTextBox(), "text", false);
            this._form.push([$T("Caption"), $B(fieldCaption, this.info.accessor("caption")).draw()]);
        },

        _getButtons: function() {
            var self = this;

            var actionButton = [this.info.get("id") !== undefined? $T('Update') : $T('Add'), function() {
                self.__submit();
            }];

            var cancelButton = [$T('Cancel'), function() {
                self.close();
            }];

            return [actionButton, cancelButton];
        },

        __fetch: function(fieldType) {
            var self = this;
            var killProgress = IndicoUI.Dialogs.Util.progress($T("Loading field..."));

            indicoRequest("abstracts.fields.getField", self.info,
                function(result, error) {
                    if (!error) {
                        self.__fillForm(result);
                        killProgress();
                    } else {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
            );
        },

        __fillForm: function(field) {
            this.info.set("name", field.name);
            this.info.set("caption", field.caption);
            this.info.set("isMandatory", field.isMandatory);
        },

        __preSubmit: function() {
            // Override if preprocess befor submit is required
        },

        __submit: function() {
            var self = this;
            self.__preSubmit();

            if (self._parameterManager.check()) {
                var killProgress = IndicoUI.Dialogs.Util.progress($T("Saving field..."));
                indicoRequest("abstracts.fields.setField", self.info,
                    function(result, error) {
                        if (!error) {
                            killProgress();
                            self.close();
                            window.location.reload();
                        } else {
                            killProgress();
                            IndicoUtil.errorReport(error);
                        }
                    }
                );
            }
        }
    },

    function(conferenceId, fieldId, fieldTypeTitle) {
        this.info = $O({"specific": $O()});
        this.info.set("conference", conferenceId);
        this.info.set("id", fieldId);

        this._parameterManager = new IndicoUtil.parameterManager();
        this._form = [];

        var title = (fieldId !== undefined? $T("Edit Field: ") : $T("Add Field: ")) + fieldTypeTitle;
        this.ExclusivePopupWithButtons(title);
    }
);

type("AddAbstractTextFieldDialog", ["AddAbstractFieldDialog"],
    {
        _initializeForm: function() {
            this.AddAbstractFieldDialog.prototype._initializeForm.call(this);

            var selection = Html.select({},
                Html.option({value: "chars"}, "Characters"),
                Html.option({value: "words"}, "Words")
            );

            var fieldMaxLength = this._parameterManager.add(new RealtimeTextBox(), "int", true);
            var fieldLimitation = this._parameterManager.add(selection, "text", false);
            fieldMaxLength = $B(fieldMaxLength, this.info.accessor("maxLength")).draw();
            fieldLimitation = $B(fieldLimitation, this.info.accessor("limitation"));

            var widget = Html.div({},
                Html.div({}, fieldMaxLength),
                Html.div({}, fieldLimitation)
            );

            this._form.push([$T("Max length"), widget]);
        },

        __fillForm: function(field) {
            this.AddAbstractFieldDialog.prototype.__fillForm.call(this, field);
            this.info.set("maxLength", field.maxLength);
            this.info.set("limitation", field.limitation);
        },

        __preSubmit: function() {
            var self = this;
            var maxLength = this.info.get("maxLength");

            if (typeof maxLength === "string") {
                if (maxLength.trim() === "") {
                    self.info.set("maxLength", 0);
                }
            }
        }
    },

    function(conferenceId, fieldId, fieldTypeTitle) {
        this.AddAbstractFieldDialog(conferenceId, fieldId, fieldTypeTitle);
    }
);

type("AddAbstractTextAreaFieldDialog", ["AddAbstractTextFieldDialog"], {},
    function(conferenceId, fieldId) {
        this.AddAbstractTextFieldDialog(conferenceId, fieldId, $T("Text"));
        this.info.set("type", "textarea");
    }
);

type("AddAbstractInputFieldDialog", ["AddAbstractTextFieldDialog"], {},
    function(conferenceId, fieldId) {
        this.AddAbstractTextFieldDialog(conferenceId, fieldId, $T("Input"));
        this.info.set("type", "input");
    }
);

type("AddAbstractSelectionFieldDialog", ["AddAbstractFieldDialog"],
    {
        _initializeForm: function() {
            this.AddAbstractFieldDialog.prototype._initializeForm.call(this);
            this.fieldOptions = $("<div></div>").fieldarea({fields_caption: $T("option"),
                                                            parameter_manager: this._parameterManager,
                                                            ui_sortable: true});
            this._form.push([$T("Options"), this.fieldOptions]);
        },

        __fillForm: function(field) {
            this.AddAbstractFieldDialog.prototype.__fillForm.call(this, field);
            this.fieldOptions.fieldarea("setInfo", field["options"]);
        },

        __preSubmit: function() {
            this.info.set("options", this.fieldOptions.fieldarea("getInfo"));
        }
    },

    function(conferenceId, fieldId) {
        this.AddAbstractFieldDialog(conferenceId, fieldId, $T("Selection"));
        this.info.set("type", "selection");
    }
);
