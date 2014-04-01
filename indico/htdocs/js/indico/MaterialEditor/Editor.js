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

var CONVERSION_POLL_INTERVAL = 10000;


function updateMaterialList(oldList, newList) {
    oldList.length = 0;

    for (var i in newList) if (newList[i]) {
        oldList.push(newList[i]);
    }
}

type("AddEditMaterialDialog", [],{
    _parentText: function(args) {
        var self = this;
        var text = null;

        //If we are editing a resource
        if (args.resourceId) {
            var isFatherProtected;
            if(self.material.materialProtection == -1){
                isFatherProtected = false;
            }
            else if(self.material.materialProtection == 1){
                isFatherProtected = true;
            }
            //then its value is 0
            else{
                //check the value of the material's parent
                isFatherProtected = self.material.parentProtected;
            }

            text = $T("Same as for the parent") + " " + self.materialName;

            text = Html.span({}, text, " ",
                    Html.unescaped.span({className: isFatherProtected ? 'strongProtPrivate' : 'strongProtPublic', style: {fontStyle: 'italic'}}," ",
                              Protection.ParentRestrictionMessages[isFatherProtected?1:-1]));
        } else {
            //if we are editing a material type
            if (args.subContId) {
                text = $T("Same as for the parent Subcontribution");
            } else if (args.contribId) {
                text = $T("Same as for the parent Contribution");
            } else if (args.sessionId) {
                text = $T("Same as for the parent Session");
            } else if (args.confId) {
                text = $T("Same as for the parent Conference");
            } else if (args.categId) {
                text = $T("Same as for the parent Category");
            }

            text = Html.span({}, text, " ",
                         Html.unescaped.span({className: args.parentProtected ? 'strongProtPrivate' : 'strongProtPublic', style: {fontStyle: 'italic'}}," ",
                                   Protection.ParentRestrictionMessages[args.parentProtected?1:-1]));
        }
        return text;
    }
});

type("AddMaterialDialog", ["AddEditMaterialDialog","ExclusivePopupWithButtons"], {
    _getButtons: function() {
        var self = this;
        return [
            [$T("Create Resource"), function() {
                self._upload();
            }],
            [$T("Cancel"), function() {
                self.close();
            }]
        ];
    },

    /*
     * Draws a pane that switches between a URL input and a file upload dialog.
     *
     * pm - A parameter manager
     * locationSelector - the locationSelector that will 'control' the pane
     */
    _drawResourcePathPane: function(locationSelector) {
        var MAX_MATERIAL_FIELDS = 5;
        var files = [Html.input('file', {name: 'file'})];
        var urlBoxes = [Html.edit({name: 'url'})];
        var toPDFCheckbox = Html.checkbox({style: {verticalAlign: 'middle'}}, true);
        var currentResourceLocation;
        toPDFCheckbox.dom.name = 'topdf';

        var self = this;

        var addInputLink = Widget.link(command(function() {
            self.tabWidget.disableTab(2);
            if(currentResourceLocation == 'local') {
                files.push(Html.input('file', {name: 'file', style: {display: 'block'}}));
            }
            else {
                urlBoxes.push(Html.edit({name: 'url'}));
            }

            // redraw resourcePathPane. is there an easier way?!
            resourcePathPane.set(currentResourceLocation);
        }, Html.span({}, ' ', $T("more"))));

        var resourcePathPane = new Chooser(
            new Lookup({
                'local':  function() {
                    currentResourceLocation = 'local';
                    // remove url boxes
                    for(var i = 0; i < urlBoxes.length; i++) {
                        self.pm.remove(urlBoxes[i]);
                    }
                    // setup Html.div() args with all file upload fields etc.
                    var args = [{}];
                    for(var i = 0; i < files.length; i++) {
                        args.push(self.pm.add(files[i], 'text', i > 0));
                        if(i == 0 && files.length < MAX_MATERIAL_FIELDS) {
                            args.push(addInputLink);
                        }
                    }
                    if (Indico.PDFConversion.HasFileConverter){
                        var pdfDivLabel = Html.label({style: {verticalAlign: 'middle'}, className: 'emphasis'},
                                $T("Convert to PDF"));
                        var pdfDiv = Html.div({style:{marginTop: '5px'}},
                                toPDFCheckbox,
                                pdfDivLabel
                                );
                        $(pdfDivLabel.dom).qtip({
                            content: {
                                text: $T("The only available file formats are: ") + Indico.PDFConversion.AvailablePDFConversions.toString().replace(/\./g,' ')
                            },
                            position: {
                                target: 'mouse',
                                adjust: { mouse: true, x: 11, y: 13 }
                            }
                        });
                        args.push(pdfDiv);
                    }

                    return Html.div.apply(null, args);
                },
                'remote': function() {
                    currentResourceLocation = 'remote';
                    // remove file upload fields
                    for(var i = 0; i < files.length; i++) {
                        self.pm.remove(files[i]);
                    }
                    // setup Html.div() args with all url boxes etc.
                    var args = [{}];
                    for(var i = 0; i < urlBoxes.length; i++) {
                        var divArgs = [
                            {},
                            Html.label('popUpLabel', $T("URL")),
                            self.pm.add(urlBoxes[i], 'url', i > 0)
                        ];
                        if(i == 0 && urlBoxes.length < MAX_MATERIAL_FIELDS) {
                            divArgs.push(addInputLink);
                        }
                        args.push(Html.div.apply(null, divArgs));
                    }
                    args.push(Html.div("smallGrey", $T("Example: http://www.example.com/YourPDFFile.pdf")));
                    setTimeout(function() { urlBoxes[0].dom.focus(); }, 200);
                    return Html.div.apply(null, args);
                }
            }));


        // whenever the user selects a different location,
        // change between an http link field and an upload box.
        // This could be done simply with:
        // $B(resourcePathPane, locationSelector);
        // but we need to change the focus too, so let's use an observer

        locationSelector.observe(function(value) {
            // switch to the appropriate panel
            resourcePathPane.set(value);

            // set the focus
            if (value == 'local') {
                files[0].dom.focus();
                if(self.tabWidget) {
                    if(files.length == 1) {
                        self.tabWidget.enableTab(2);
                    }
                    else {
                        self.tabWidget.disableTab(2);
                    }
                }
            } else {
                urlBoxes[0].dom.focus();
                if(self.tabWidget) {
                    if(urlBoxes.length == 1) {
                        self.tabWidget.enableTab(2);
                    }
                    else {
                        self.tabWidget.disableTab(2);
                    }
                }
            }
        });

        // change the upload type that will be sent in the request
        // (bind it with the selection box)
        $B(this.uploadType,
           locationSelector,
           {
               toSource: function(value) {
                   // unused;
               },
               toTarget: function(value) {
                   return value=='local'?'file':'link';
               }
           });

        // default is 'local' (local file)
        locationSelector.set('local');

        return resourcePathPane;

    },

    _parentText: function(args) {
        var text = null;

        if (args.subContId) {
            text = $T("Inherit from parent Subcontribution");
        } else if (args.contribId) {
            text = $T("Inherit from parent Contribution");
        } else if (args.sessionId) {
            text = $T("Inherit from parent Session");
        } else if (args.confId) {
            text = $T("Inherit from parent Conference");
        } else if (args.categId) {
            text = $T("Inherit from parent Category");
        }

        text = Html.span({}, text, " ",
                         Html.unescaped.span({className: args.parentProtected ? 'strongProtPrivate' : 'strongProtPublic', style: {fontStyle: 'italic'}}," ",
                                   Protection.ParentRestrictionMessages[args.parentProtected?1:-1]));

        return text;
    },


    _findTypeName: function(id) {
        for (var i in this.types) {
            if (this.types[i][0] == id) {
                return this.types[i][1];
            }
        }
        return id;
    },

    _drawProtectionPane: function(value) {

        var text = null;
        var entry = this.list.get(value) || this.list.get(value.toLowerCase());
        var selector = null;

        if (value == '') {
            return Html.div({style: {textAlign: 'left', fontStyle: 'italic', color: '#881122', marginTop: '10px'}},
                    $T('Please enter a name for the material type and then select who will be able to access this material type.'));
        } else if (exists(entry)) {

            // if the material is already in the tree, protection inheritance must
            // be resolved

            this.creationMode = 'resource';

            text = Html.span({}, $T("You're adding a resource to the existing material type"), " ", Html.span({style:{fontWeight: 'bold'}}, entry.get('title')), ". ", $T("Please specify who will be able to access it:"));

            // if the material is set to inherit from the parent, display it properly
            // and set the inherited protection accordingly
            var protection = Protection.resolveProtection(
                entry.get('protection'),
                entry.get('protectedOwner')?1:-1);

            var inheritanceText = Html.unescaped.span({className: 'strongRed', style: {fontStyle: 'italic'}},
                Protection.ParentRestrictionMessages[protection]);


            selector = new RadioFieldWidget([
                ['inherit', Html.span({className: protection == -1 ? 'strongProtPublic' : 'strongProtPrivate'}, $T("Inherit from parent material type ")+"\""+entry.get('title')+"\" ", inheritanceText)],
                ['private', Html.span({className: 'protPrivate'}, $T("Restricted: Can only be viewed by you and users/groups chosen by you from the list of users"))],
                ['public', Html.span({className: 'protPublic'}, $T("Public: Can be viewed by everyone"))]
            ], 'nobulletsListWrapping');


        } else {

            this.creationMode = 'material';

            text = Html.span({}, $T("This will be the first resource of type")," ", Html.span({style:{fontWeight: 'bold'}}, this._findTypeName(value)), ". ", $T("Please select who will be able to access this material type:"));

            selector = new RadioFieldWidget([
                ['inherit', this._parentText(this.args)],
                ['private', Html.span({className: 'protPrivate'}, $T("Restricted: Can only be viewed by you and users/groups chosen by you from the list of users"))],
                ['public', Html.span({className: 'protPublic'}, $T("Public: Can be viewed by everyone"))]
            ], 'nobulletsListWrapping');
        }

        this.protectionSelector = selector;

        var self = this;

        this.protectionSelector.observe(function(state) {

            self.userList.userList.clear();
            self.visibility.set(0);
            self.password.set('');

            // if 'private' is chosen or 'inherit' was chosen
            // and the parent resource is protected
            if (state == 'private') {
                self.tabWidget.enableTab(1);

                // depending on whether we're creating a new
                // material or just a result, we will enable/disable
                // visibility and access key
                if (self.creationMode == 'material') {
                    self.visibility.enable();
                    self.password.dom.disabled = false;
                } else {
                    self.visibility.disable();
                    self.password.dom.disabled = true;
                }

                // draw a little notification saying that
                // the added tab can be used
                self.tabWidget.showNotification(1, $T('You can specify users using this tab'));
            } else {
                self.tabWidget.disableTab(1);
            }

            // set the appropriate data structure behind the scenes
            self.protectionStatus.set('statusSelection',
                                      {'private': 1,
                                       'inherit': 0,
                                       'public': -1}[state]);
        });

        // set protection default to 'inherit'
        if (this.tabWidget) {
            this.protectionSelector.set('inherit');
        }

        return Html.div({style:{marginTop: '10px',
                                height: '150px'
                               }},
                        Html.div({style: {textAlign: 'left', fontStyle: 'italic', color: '#881122'}},
                                 $T(text)),
                        Html.div({style: {marginTop: '10px'}},
                                 selector ? selector.draw() : ''));
    },

    _drawUpload: function() {

        var self = this;


        // local file vs. url
        var locationSelector = new RadioFieldWidget([['local',$T('Local file')],['remote',$T('External resource (hyperlink)')]]);

        // draw the resource pane
        var resourcePathPane = this._drawResourcePathPane(locationSelector);

        // protection page
        var protectionPane = $B(
            Html.div({style:{visibility:this.forReviewing?['hidden']:['visible']}}),
            this.typeSelector,
            function(value) {
                return self._drawProtectionPane(value);
            });

        return $("<div></div>").append(
                        IndicoUtil.createFormFromMap(
                            [
                                [
                                    $T('Location'),
                                    Html.div({},
                                             this.forReviewing?[]:[locationSelector.draw()],
                                             Html.div({style:{paddingTop: '15px',
                                                              paddingBottom: '10px',
                                                              minHeight: '50px'}},
                                                      Widget.block(resourcePathPane)))
                                ],
                                this.forReviewing?[]:[
                                    $T('Material type'),
                                    Html.div({style:{height: '40px'}},
                                             this.typeSelector.draw())
                                ]

                            ]),
                        $(protectionPane.dom));

   },

   _drawAdvanced: function() {

       var self = this;

       var description = Html.textarea({id:'description', name: 'description', style:{width:'220px', height: '60px'}});
       var displayName = Html.input("text",{'name':'displayName', style:{width:'220px'}});

       return $("<div></div>").append(
                       IndicoUtil.createFormFromMap(
                           [
                               [
                                $T('Description'),
                                description
                               ],
                               [
                                   $T('Display Name'),
                                   Html.div({}, displayName,
                                                Html.div("smallGrey", $T("'Display name' will be used instead of the original file name")))
                               ]
                           ]) );

  },

    _upload: function() {

        var check = this.pm.check();

        if (check) {
            this.killProgress = IndicoUI.Dialogs.Util.progress();

            this.uploading = true;

            this.formDict.userList.set(Json.write(this.userList.getUsers()));

            this.formDict.statusSelection.set(this.protectionStatus.get('statusSelection'));

            this.formDict.visibility.set(this.protectionStatus.get('visibility'));
            this.formDict.password.set(this.protectionStatus.get('password'));
            this.formDict.uploadType.set(this.uploadType.get());

            // depending on whether we are selecting a material from the list
            // or adding a new one, we'll send either an id or a name

            var type = this.typeSelector.get();
            // in IE nothing is selected in the hidden select field -> it returns an empty type
            if(this.forReviewing && !type) {
                type = this.types[0][0];
            }
            this.formDict.materialId.set(type);

            $(this.form.dom).submit();

            return true;
        }
        return false;
    },

    _drawWidget: function() {
        var self = this;

        this.formDict = {};

        this.form = Html.form(
            {
                method: 'post',
                id: Html.generateId(),
                action: build_url(this.uploadAction, this.args),
                enctype: 'multipart/form-data'
            },
            this.tabWidget.draw());

        each(['statusSelection', 'visibility', 'password', 'userList', 'uploadType', 'materialId'],
             function(fieldName) {
                 var elem = Html.input('hidden', {name: fieldName});
                 self.formDict[fieldName] = elem;
                 self.form.append(elem);
             });

        each(this.args, function (value, key) {
            self.form.append(Html.input('hidden',{name: key}, value));
        });

        $(this.form.dom).ajaxForm({
            dataType: 'json',
            iframe: true,
            complete: function(){
                self.killProgress();
            },
            success: function(resp){
                if (resp.status == "ERROR") {
                    IndicoUI.Dialogs.Util.error(resp.info);
                } else if (resp.status == "NOREPORT") {
                    IndicoUtil.errorReport({
                        type: "noReport",
                        code: '0',
                        requestInfo: {},
                        message: resp.info });
                } else {
                    self.onUpload(resp.info);
                    // Firefox will keep "loading" if the iframe is destroyed
                    // right now. Let's wait a bit.
                    setTimeout(
                        function() {
                            self.close();
                        }, 100);
                }
            }
        });

        return Html.div({},
                        this.form);

    },

    postDraw: function() {

        var selection = "slides";

        // We're not sure that the type "Slides"
        // will have a "standard" id
        $.each(this.types, function(i, t) {
            if (t[1] == "Slides") {
                selection = t[0];
            }
        });

        this.typeSelector.set(selection);
        this.ExclusivePopupWithButtons.prototype.postDraw.call(this);
    },

    _drawProtectionDiv: function() {
        this.visibility = new RadioFieldWidget([
            [0, Html.unescaped.span('strongRed', $T("The link for this material will <strong>visible</strong> from the event page, to everyone"))],
            [1, Html.unescaped.span('strongRed', $T("The link will be <strong>invisible</strong> by default - only people who can access the material will be able to see it"))]]);

        this.password = Html.input('password',{});

        this.userList = new UserListField(
            'ShortPeopleListDiv', 'PeopleList',
            null, true, null,
            true, true, null, null,
            false, false, false, true,
            userListNothing, userListNothing, userListNothing);

        // Bind fields to data structure
        $B(this.protectionStatus.accessor('visibility'), this.visibility);
        $B(this.protectionStatus.accessor('password'), this.password);

        this.visibility.set(0);
        this.password.set('');

        return IndicoUtil.createFormFromMap(
                            [
                                [
                                    $T('Allowed users and groups'),
                                    this.userList.draw()
                                ],
                                [
                                    $T('Visibility'),
                                    this.visibility.draw()
                                ],
                                [
                                    $T('Access key'),
                                    this.password
                                ]
                            ]);
    },

    draw: function() {
        var self = this;

        self.newMaterial = $O();

        var protectionDiv = this._drawProtectionDiv();

        this.tabWidget = new JTabWidget([[$T('Basic'), this._drawUpload()],
                                        [$T("Protection"), protectionDiv],
                                        [$T('Advanced'), this._drawAdvanced()]],
                                       400);

        return this.ExclusivePopupWithButtons.prototype.draw.call(this, this._drawWidget());
    }


}, function(args, list, types, uploadAction, onUpload, forReviewing, addMaterialMode) {
    this.AddEditMaterialDialog();
    var self = this;
    this.list = list;
    this.types = types;
    this.uploadAction = uploadAction;
    this.uploading = false;
    this.onUpload = onUpload;
    this.forReviewing = forReviewing;
    this.addMaterialMode = addMaterialMode;
    this.args = clone(args);

    this.protectionStatus = $O();
    this.uploadType = new WatchValue();
    this.ExclusivePopupWithButtons(this.forReviewing?$T("Upload Paper"):$T("Upload Material"),
                        function() {
                            self.close();
                        });

    this.pm = new IndicoUtil.parameterManager();

    this.typeSelector = new TypeSelector(this.types,
                                        {style:{width: '150px'}},
                                        {style:{width: '150px'}, maxlength: '50'});
    if (!forReviewing) {
        this.typeSelector.plugParameterManager(this.pm);
    }
});

type("UploadTemplateDialog", ["ExclusivePopupWithButtons"], {

    _getButtons: function() {
        var self = this;
        return [
            [$T('Upload'), function() {
                if (self.pm.check()) {
                    self.killProgress = IndicoUI.Dialogs.Util.progress($T('Uploading...'));
                    self.uploading = true;
                    $(self.form.dom).submit();
                }
            }],
            [$T('Cancel'), function() {
                self.close();
            }]
        ];
    },

    _fileUpload: function() {
        var self = this;
        var pm = self.pm = new IndicoUtil.parameterManager();
        var uploadType = Html.input('hidden', {name: 'uploadType'});
        var selector = this._showFormatChooser(pm);
        var file = Html.input('file', {name: 'file'});
        var description = Html.textarea({name: 'description'});
        var name = Html.edit({name: 'name'});

        uploadType.set('file');

        pm.add(selector, 'text', false);
        pm.add(file, 'text', false);
        pm.add(description, 'text', true);
        pm.add(name, 'text', true);

        this.form = Html.form({
                            method: 'post',
                            id: Html.generateId(),
                            action: build_url(this.uploadAction, this.args),
                            enctype: 'multipart/form-data',
                            encoding: 'multipart/form-data'
                        },
                        Html.input('hidden', {name: 'conference'}, this.args.conference),
                        IndicoUtil.createFormFromMap(
                            [
                                [$T('Name'), name],
                                [$T('Type'), selector],
                                [$T('File'), file],
                                [$T('Description'), description]
                            ]).get(),
                        uploadType);

        $(this.form.dom).ajaxForm({
            dataType: 'json',
            iframe: true,
            complete: function(){
                self.killProgress();
            },
            success: function(resp){
                if (resp.status == "ERROR") {
                    IndicoUtil.errorReport(resp.info);
                } else {
                    self.close();
                    self.onUpload(resp.info);
                }
            }
        });

        return Html.div({}, this.form);
},

    _showFormatChooser: function(pm) {
        var self = this;
        var select = Html.select({name: 'format'});
        var text = Html.edit({name: 'format'});

        var chooser = new Chooser(new Lookup({
            select: function() {
                pm.remove(text);
                pm.add(select);

                return Html.div({}, bind.element(select, $L(self.types),
                                          function(value) {
                                              return Html.option({'value': value}, value);
                                          }),
                         " ",
                         $T("or"),
                         " ",
                         Widget.link(command(function() {
                             chooser.set('write');
                         }, $T("other"))));
            },

            write: function() {
                bind.detach(select);
                pm.remove(select);
                pm.add(text, 'text');
                return Html.div({}, text,
                                " ",
                               $T("or"),
                               " ",
                                Widget.link(command(function() {
                                    chooser.set('select');
                                }, $T("select from list"))));
            }
        }));
        chooser.set('select');

        return Widget.block(chooser);
    },

    draw: function() {
        return this.ExclusivePopupWithButtons.prototype.draw.call(this, this._fileUpload());
    }
}, function(title, args, width, height, types, uploadAction, onUpload) {
    var self = this;
    this.title = title;
    this.width = width;
    this.height = height;
    this.types = types;
    this.uploadAction = uploadAction;
    this.uploading = false;
    this.onUpload = onUpload;

    this.args = clone(args);
    this.ExclusivePopupWithButtons($T(title));
});

type("EditMaterialResourceBase", ["AddEditMaterialDialog", "ServiceDialogWithButtons", "PreLoadHandler"], {
    _preload: [
               function(hook){
                   this._preloadAllowedUsers(hook, this.action);
               }
           ],
    _preloadAllowedUsers: function(hook, method) {
        var self = this;

        var killProgress = IndicoUI.Dialogs.Util.progress($T("Loading dialog..."));
        self.args.includeFavList = IndicoGlobalVars.isUserAuthenticated && !exists(IndicoGlobalVars['favorite-user-ids']);
        var users = indicoSource(method, self.args);

        users.state.observe(function(state) {
            if (state == SourceState.Loaded) {
                var result = users.get();
                if (self.args.includeFavList) {
                    self.allowedUsers = result[0];
                    updateFavList(result[1]);
                } else {
                    self.allowedUsers = result;
                }
                killProgress();
                hook.set(true);
            } else if (state == SourceState.Error) {
                killProgress();
                IndicoUtil.errorReport(users.error.get());
            }
        });
    },

    _drawUserList: function(){

        return new UserListField(
                'ShortPeopleListDiv', 'PeopleList',
                this.allowedUsers, true, null,
                true, true, null, null,
                false, false, false, true,
                userListNothing, userListNothing, userListNothing);


    },

    _drawProtectionDiv: function() {
        var self = this;

        self.privateInfoDiv = self._drawPrivateInfoDiv();

        return Html.div(
                {style: {marginTop: pixels(5)}},
                self.privateInfoDiv.get());

    },

    _drawProtectionPane: function() {
        var self = this;

        var inheritanceText = Html.unescaped.span({className: 'strongRed', style: {fontStyle: 'italic'}},
                Protection.ParentRestrictionMessages[self.protection]);

        var text = Html.span({}, $T("Please select who will be able to access "), " ",Html.span({style:{fontWeight: 'bold'}}, self.protectionName), " :");

        self.protectionSelector  = new RadioFieldWidget([
            [0, self._parentText(this.args)],
            [1, Html.span({className: 'protPrivate'}, $T("Restricted: Can only be viewed by you and users/groups chosen by you from the list of users"))],
            [-1, Html.span({className: 'protPublic'}, $T("Public: Can be viewed by everyone"))]
            ], 'nobulletsListWrapping');

        self.protectionSelector.observe(function(value) {

            // if 'private' is chosen or 'inherit' was chosen
            // and the parent resource is protected
            if (value == 0 && self.item.get('protectedOwner') ||
                    value == 1) {
                self.tabWidget.enableTab(1);
                // draw a little notification saying that
                // the added tab can be used
                self.tabWidget.showNotification(1, $T('You can specify users using this tab'));
            } else {
                self.tabWidget.disableTab(1);
            }
        });

        return Html.div({style:{marginTop: '10px',height: '150px'}},
                        Html.div({style: {textAlign: 'left', fontStyle: 'italic', color: '#881122'}}, $T(text)),
                        Html.div({style: {marginTop: '10px'}}, self.protectionSelector.draw()));

    },
    _getButtons: function() {
        var self = this;
        return [
            [$T('Save'), function() {
            self._save();
            }],
            [$T('Cancel'), function() {
            self.close();
            }]
        ];
    },

    _drawWidget: function(){
        var self = this;

        var protectionDiv = self._drawProtectionDiv();

        var infoDiv = Html.div({},
                self._drawInfoPane().get(),
                this.forReviewing?[]:self._drawProtectionPane() );
        var widget = [[$T("Information"), infoDiv]];
        if(!this.forReviewing) {
            widget.push([$T("Protection") , protectionDiv]);
        }
        return new JTabWidget(widget, 400);
    },

    draw: function() {
        this.tabWidget =  this._drawWidget();
        return this.ServiceDialogWithButtons.prototype.draw.call(this, this.tabWidget.draw());
    },

    postDraw: function(){
        var self = this;
        this.ServiceDialogWithButtons.prototype.postDraw.call(this);
        self._bindData();
    }

},

    function(endPoint, method, args, title, closeHandler) {
        this.ServiceDialogWithButtons(endPoint, method, args, title, closeHandler);
    }
);


type("EditMaterialDialog", ["EditMaterialResourceBase"], {

    _save: function() {
        var params = clone(this.args);
        params.materialInfo = this.newMaterial;
        this.newMaterial.set('userList', this.userList.getUsers());

        // get a list of material titles
        var matTitles = translate(this.list,
            function(mat){
                return mat.get('title');
            });

        // look for one with the same name
        var i = -1;
        for (var j in matTitles) {
            if (matTitles[i] == params.materialInfo.get('title')) {
                i = j;
            }
        }

        if (i < 0) {
            this.types.push([params.materialInfo.get('id'), params.materialInfo.get('title')]);
        }

        if (this.pm.check()) {
            this.request(params);
        }
    },

    _success: function(response) {

        this.list.set(this.materialId, null);
        this.list.set(this.materialId, watchize(response.material));

        updateMaterialList(this.types, response.newMaterialTypes);

    },

    _drawPrivateInfoDiv: function(){

        var self = this;

        self.userList = self._drawUserList();

        this.visibility = new RadioFieldWidget([
            [0, Html.unescaped.span('strongRed', $T("The link for this material will <strong>visible</strong> from the event page, to everyone"))],
            [1, Html.unescaped.span('strongRed', $T("The link will be <strong>invisible</strong> by default - only people who can access the material will be able to see it"))]]);

        this.password = Html.input('password',{});

        return IndicoUtil.createFormFromMap(
                            [
                                [
                                    $T('Allowed users and groups'),
                                    self.userList.draw()
                                ],
                                [
                                    $T('Visibility'),
                                    self.visibility.draw()
                                ],
                                [
                                    $T('Access key'),
                                    self.password
                                ]
                            ]);

    },
    _drawInfoPane: function() {
        var self = this;

        self.materialTitle = Html.input("text",{'name':'title', style:{width:'220px'}});
        self.description = Html.textarea({id:'description', name: 'description', style:{width:'220px', height: '60px'}});

        self.pm = new IndicoUtil.parameterManager();
        self.pm.add(self.materialTitle, 'text', false);

        if (self.material.get('isBuiltin')) {
            $(self.materialTitle.dom).prop('readonly', true).css('color', '#888').qtip(
                {content: $T("This is a default material type and its name cannot be changed. You should create a new type instead."),
                 position: {my: 'bottom center', at: 'top center'}});
        }

        return IndicoUtil.createFormFromMap(
                [
                 [
                     $T('Title'),
                     Html.div({}, self.materialTitle,
                                  Html.div("smallGrey", $T("'Title' will be used instead of the original name")))
                 ],
                 [
                  $T('Description'),
                  self.description
                 ]
             ]);
    },

    _bindData: function(){
        var self = this;

        $B(self.visibility, self.newMaterial.accessor('hidden'));
        $B(self.password, self.newMaterial.accessor('accessKey'));
        $B(self.protectionSelector, self.newMaterial.accessor('protection'));
        $B(self.materialTitle, self.newMaterial.accessor('title'));
        $B(self.description, self.newMaterial.accessor('description'));
    }

},

     function(args, material, types, list, title) {
         this.material = material;
         this.materialId = this.material.get('id');
         this.types = types;
         this.list = list;
         this.item = material;
         this.protectionStatus = this.material.get('protection');
         this.newMaterial = $O(this.material.getAll());
         this.action = 'material.listAllowedUsers';
         this.protectionName = this.newMaterial.get('title');
         this.protection = Protection.resolveProtection(
                 this.newMaterial.get('protection'),
                 this.newMaterial.get('hasProtectedOwner')?1:-1);
         args = clone(args);
         args.materialId = this.materialId;

         var self = this;
         this.PreLoadHandler(
             self._preload,
             function() {
                 self.open();
             }
         );
         this.EditMaterialResourceBase(Indico.Urls.JsonRpcService, 'material.edit', args, title);
     }

    );


type("EditResourceDialog", ["EditMaterialResourceBase"], {

    _save: function() {
        var params = clone(this.args);
        params.resourceInfo = this.newResource;
        this.newResource.set('userList', this.userList.getUsers());
        if (this.pm.check()) {
            this.request(params);
        }
    },

    _success: function(response) {
        this.appender(watchize(response));
    },

    _drawPrivateInfoDiv: function(){

        var self = this;

        self.userList = self._drawUserList();

        return IndicoUtil.createFormFromMap(
                            [
                                [
                                    $T('Allowed users and groups'),
                                    self.userList.draw()
                                ]
                            ]);
    },

    _drawInfoPane: function() {
        var self = this;

        self.name = Html.input("text",{'name':'name', style:{width:'220px'}});
        self.url = Html.input("text",{'name':'url', style:{width:'220px'}});
        self.description = Html.textarea({id:'description', name: 'description', style:{width:'220px', height: '60px'}});

        self.pm = new IndicoUtil.parameterManager();
        self.pm.add(self.name, 'text', false);
        self.pm.add(self.url, 'url', false);

        return IndicoUtil.createFormFromMap(
                [
                 [
                     $T('Name'),
                     Html.div({}, self.name,
                                  Html.div("smallGrey", $T("'Name' will be used instead of the url")))
                 ],
                 [
                  $T('URL'),
                  self.url
                 ],
                 [
                  $T('Description'),
                  self.description
                 ]
             ]);
    },
    _bindData: function(){
        var self = this;
        $B(self.name, self.newResource.accessor('name'));
        $B(self.description, self.newResource.accessor('description'));
        $B(self.url, self.newResource.accessor('url'));
        $B(self.protectionSelector, self.newResource.accessor('protection'));
    }
},

     function(args, material, materialName, resource, domItem, appender, title, forReviewing) {
         args = clone(args);

         this.material = material;
         this.materialId = material.materialId;
         this.resource = resource;
         this.resourceId = resource.id;
         this.domItem = domItem;
         this.appender = appender;
         this.forReviewing = forReviewing;
         this.item = resource;
         this.materialName = materialName;
         this.protectionStatus = this.resource.get('protection');
         this.newResource = $O(this.resource.getAll());
         this.action = 'material.resources.listAllowedUsers';
         this.protectionName = this.newResource.get('name');
         this.protection = Protection.resolveProtection(
                 this.newResource.get('protection'),
                 this.newResource.get('hasProtectedOwner')?1:-1);
         var self = this;
         this.PreLoadHandler(
             self._preload,
             function() {
                 self.open();
             });

         args.resourceId = this.resourceId;
         args.materialId = this.materialId;

         this.EditMaterialResourceBase(Indico.Urls.JsonRpcService, 'material.resources.edit', args, title);
     }
 );


/**
 * Mouseover help popup to inform the user about the meaning
 * of each reviewing state, depending on the color of the icon.

var revStateHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
                                     '<ul style="list-style-type:none;padding:3px;margin:0px">'+

                                     '<li style="padding:2px">'+
                                     '<img src=' + imageSrc("dot_gray") + ' style="vertical-align:middle;padding-right:5px"><\/img>'+
                                     '<span>Material not subject to reviewing.<\/span>'+
                                     '<\/li>'+

                                     '<li style="padding:2px">'+
                                     '<img src=' + imageSrc("dot_orange") + ' style="vertical-align:middle;padding-right:5px"><\/img>'+
                                     '<span>Material subject to reviewing. Not yet submitted by the author.<\/span>'+
                                     '<\/li>'+

                                     '<li style="padding:2px">'+
                                     '<img src=' + imageSrc("dot_blue") + ' style="vertical-align:middle;padding-right:5px"><\/img>'+
                                     '<span>Material subject to reviewing. Currently under reviewing, cannot be changed.<\/span>'+
                                     '<\/li>'+

                                     '<li style="padding:2px">'+
                                     '<img src=' + imageSrc("dot_red") + ' style="vertical-align:middle;padding-right:5px"><\/img>'+
                                     '<span>Material already reviewed and rejected.<\/span>'+
                                     '<\/li>'+

                                     '<li style="padding:2px">'+
                                     '<img src=' + imageSrc("dot_green") + ' style="vertical-align:middle;padding-right:5px"><\/img>'+
                                     '<span>Material already reviewed and accepted.<\/span>'+
                                     '<\/li>'+

                                     '<\/ul>');
};*/

/**
 * Mouseover popup to inform that material is not modificable when user
 * hovers mouse above disabled add, remove or edit buttons.
 */
var modifyDisabledHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
                                     $T('Modifying this material is currently not possible because it is not under review.'));
};

var setMainResourceHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
                                     $T('Mark as main resource.'));
};

var mainResourceHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
                                     $T('Unmark main resource.'));
};

type("ResourceListWidget", ["ListWidget"], {

    _drawItem: function(pair) {
        var resourceId = pair.key;
        var resource = pair.get();

        var self = this;

        var resParams = clone(this.matParams);
        resParams.resourceId = resourceId;
        var deleteResource = function() {
            var confirmHandler = function(value){
                if (value) {
                    var killProgress = IndicoUI.Dialogs.Util.progress($T('Removing...'));

                    jsonRpc(Indico.Urls.JsonRpcService,
                            self.deleteResourceMethod,
                            resParams,
                            function(response,error) {
                                if (exists(error)) {
                                    killProgress();
                                    IndicoUtil.errorReport(error);
                                } else {
                                    self.resources.remove(resource);
                                    self.set(resourceId, null);
                                    updateMaterialList(self.materialTypes, response.newMaterialTypes);
                                    killProgress();
                                }
                            }
                           );
                }
            };
            new ConfirmPopup($T("Delete Resource"), $T("Are you sure you want to delete") + " "+resource.get('name')+"?", confirmHandler).open();
        };

        var setMainResource = function() {
            var killProgress = IndicoUI.Dialogs.Util.progress($T('Setting main resource...'));
            self.matParams.mainResourceId = resourceId;
            jsonRpc(Indico.Urls.JsonRpcService,
                    'material.setMainResource',
                    resParams,
                    function(response,error) {
                        if (exists(error)) {
                            killProgress();
                            IndicoUtil.errorReport(error);
                        } else {
                            killProgress();
                            //Crude way to redraw widget
                            var temp = self.getAll();
                            self.clear();
                            self.update(temp);
                        }
                    }
                   );
        };

        var removeMainResource = function() {
            var killProgress = IndicoUI.Dialogs.Util.progress($T('Setting main resource...'));
            self.matParams.mainResourceId = null;
            jsonRpc(Indico.Urls.JsonRpcService,
                    'material.removeMainResource',
                    resParams,
                    function(response,error) {
                        if (exists(error)) {
                            killProgress();
                            IndicoUtil.errorReport(error);
                        } else {
                            killProgress();
                            //Crude way to redraw widget
                            var temp = self.getAll();
                            self.clear();
                            self.update(temp);
                        }
                    }
                   );
        };

        var storedDataInfo = function(info) {
            var list = Html.ul("materialDescription");

            var labelAndValue = function(label, value) {
                list.append(Html.li({},Html.span({},Html.strong({},label+": "),value)));
            };

            labelAndValue('File Name',info.get('fileName'));
            labelAndValue('Size',Math.floor(info.get('fileSize')/1024)+ " KB");
            labelAndValue('Creation Date',info.get('creationDate'));

            var filetype = info.get('fileType');

            return Html.div(
                "resourceContainer", list);
        };

        var removeButton;
        var editButton;
        var setMain;
        var flag;
        var protectionIcon;

        if (resource.get('reviewingState') < 3 || (resource.get('reviewingState') == 3 && self.canReviewModify)) {
            flag = resource.get('reviewingState') == 3;
            var protection = Protection.resolveProtection(resource.get('protection'),self.matParams.materialProtection);

            protectionIcon = Html.span({}, protection==1?
                                           Html.img({src: imageSrc('protected'),
                                                     style: {verticalAlign: 'middle', paddingLeft:pixels(5)},
                                                     alt: "protected",
                                                     title: $T("This resource is protected")})
                                           :'');
            removeButton = Widget.link(command(deleteResource,IndicoUI.Buttons.removeButton()));
            editButton = Widget.link(command(function() {
                IndicoUI.Dialogs.Material.editResource(resParams, self.matParams, self.materialName, resource, resourceNode, function(resource) {
                    self.set(resource.get('id'), null);
                    self.set(resource.get('id'), resource);
                }, flag);
            },
                                             IndicoUI.Buttons.editButton())
                                    );
            if(resourceId != resParams.mainResourceId) {
                setMain = Widget.link(command(setMainResource,IndicoUI.Buttons.starButton(true)));
                setMain.dom.onmouseover = setMainResourceHelpPopup;
            }
            else {
                setMain = Widget.link(command(removeMainResource,IndicoUI.Buttons.starButton(false)));
                setMain.dom.onmouseover = mainResourceHelpPopup;
            }
        } else {
            removeButton = IndicoUI.Buttons.removeButton(true);
            removeButton.dom.title = '';

            editButton = IndicoUI.Buttons.editButton(true);
            editButton.dom.title = '';

            setMain = IndicoUI.Buttons.starButton(true);
            setMain.dom.title = '';

            // show the helper popups only for real files (not for 'converting to PDF' file)
            if (resource.get('type') != 'converting') {
                removeButton.dom.onmouseover = modifyDisabledHelpPopup;
                editButton.dom.onmouseover = modifyDisabledHelpPopup;
                setMain.dom.onmouseover = modifyDisabledHelpPopup;
            }
        }

        var informationTitle;
        if (resource.get('type') == 'converting') {
            informationTitle = Html.span({style: {paddingLeft: '5px', color: 'gray'}}, resource.get('name'));
        }
        else {
            informationTitle = Html.a({href: resource.get('url'), style: {paddingLeft: '5px'}}, resource.get('name'));
        }


        var information = [
            protectionIcon,
            informationTitle,
            resource.get('type') == 'stored' || 'converting' ? "" :[" (",Html.span({style:{fontStyle: 'italic', fontSize: '11px'}}, resource.get('url')),")"],
            removeButton,
            editButton,
            this.showMainResources ? setMain:Html.div({}),
            Html.div("descriptionLine", resource.get('description'))
        ];

        var resourceNode;
        if (resource.get('type') == 'stored') {
            var fileData = storedDataInfo(resource.get('file'));
            resourceNode = Widget.block(concat([IndicoUI.Buttons.arrowExpandIcon(fileData)], information));
            resourceNode.append(fileData);
        } else if (resource.get('type') == 'converting') {
            resourceNode = Html.div({}, Html.img({src:imageSrc("collapsd.png")}), information);
            $(resourceNode.dom).qtip({
                    content: {
                        text: $T('Indico is currently performing the conversion of the file to PDF. The conversion may take a few seconds.')
                    },
                    position: {
                        target: 'mouse',
                        adjust: { mouse: true, x: 11, y: 13 }
                    }
                });
        } else { // it is a link
            resourceNode = Html.div({style:{paddingLeft: '12px'}}, information);
        }

        if (resource.get('pdfConversionStatus') == 'converting') {
            var counter = 0;
            (function conversionWorker() {
                jsonRpc(Indico.Urls.JsonRpcService,
                        'material.get',
                        resParams,
                        function(response,error) {
                            if (response) {
                                // We suppose that the PDF file is not converted yet and so we gray it out.
                                if (counter == 0) {
                                    var convertingResource = clone(resource);
                                    convertingResource.url = '';
                                    convertingResource.id = resourceId + 'converting';
                                    convertingResource.name = resource.get('name').split('.')[0] + '.pdf';
                                    convertingResource.type = 'converting';
                                    self.resources.append(watchize(convertingResource));
                                }
                                // Now we check if the file is converted and if so, we show the PDF and stop the 'setTimetout'
                                for (var value in response.resources) {
                                    if (response.resources[value].name == resource.get('name').split('.')[0] + '.pdf') {
                                        self.set(resourceId + 'converting', null);
                                        self.set(response.resources[value].id, watchize(response.resources[value]));
                                        return;
                                    }
                                }
                                if (counter < 6) { // poll up to a maximum of 6 times if the PDF is already converted
                                    setTimeout(conversionWorker, CONVERSION_POLL_INTERVAL);
                                    counter++;
                                }
                             }
                        }
                       );
                    })();
        }

        return resourceNode;
    }

}, function(resources, matParams, materialTitle, materialTypes, showMainResources, canReviewModify, deleteResourceMethod) {
    this.matParams = matParams;
    this.resources = resources;
    this.materialName = materialTitle;
    this.materialTypes = materialTypes;
    this.ListWidget("materialListResource");
    this.showMainResources = showMainResources || false;
    this.canReviewModify = canReviewModify || false;
    this.deleteResourceMethod = deleteResourceMethod;

    var self = this;

    resources.each(
        function(value) {
            self.set(value.get('id'), value);
        });

    resources.observe(
        function(event, value) {
            self.set(value.get('id'), value);
        });

});

function contains(a, obj){
    for(var i = 0; i < a.length; i++) {
      if(a[i] === obj){
        return true;
      }
    }
    return false;
}

type("MaterialListWidget", ["RemoteWidget", "ListWidget"], {

    _drawItem: function(pair) {
        var self = this;

        var material = pair.get();
        var args = clone(self.args);
        var materialId = pair.key;
        args.materialId = materialId;

        //we use lowercase because for the default materials it is saved in the server like for example 'Paper',
        //but then in the selectBox it will be like 'paper'
        args.materialIdsList.set(material.get('title').toLowerCase(), materialId);
        args.mainResourceId = material.get('mainResource')?material.get('mainResource').get('id'):null;

        var deleteMaterial = function() {
            var confirmHandler = function(value){
                if(value){
                    var killProgress = IndicoUI.Dialogs.Util.progress($T('Removing...'));

                    jsonRpc(Indico.Urls.JsonRpcService,
                            'material.delete',
                            args,
                            function(response,error) {
                                if (exists(error)) {
                                    killProgress();
                                    IndicoUtil.errorReport(error);
                                } else {
                                    self.set(materialId, null);
                                    killProgress();

                                    updateMaterialList(self.types, response.newMaterialTypes);
                                }
                            }
                           );
                }
            };
            new ConfirmPopup($T("Delete Material"), $T("Are you sure you want to delete '")+material.get('title')+"'?", confirmHandler).open();
        };

        var menu;

        menu = Html.span(
            {},
            Widget.link(command(
                deleteMaterial,
                IndicoUI.Buttons.removeButton()
            )),
            Widget.link(command(
                function(){
                    IndicoUI.Dialogs.Material.editMaterial(
                        self.args,
                        self.types,
                        material,
                        self);
                },
                IndicoUI.Buttons.editButton()
            ))
        );

        args.materialProtection = material.get('protection');
        var matWidget = new ResourceListWidget(material.get('resources'), args, material.get('title'), self.types, self.showMainResources, self.canReviewModify, self.deleteResourceMethod);

        // check whenever a material gets empty (no resources) and delete it
        material.get('resources').observe(
            function(event, element) {
                if (event == 'itemRemoved' &&
                    material.get('resources').length.get() == 1) {
                    self.set(materialId, null);
                }
            });

        var item = [];
        var matWidgetDiv = matWidget.draw();
        if(material.get('reviewingState') == 1 || material.get('reviewingState') == 0){
            var protection =
                Protection.resolveProtection(material.get('protection'),
                                             material.get('protectedOwner')?1:-1);

            var protectionIcon = Html.span({}, protection==1?
                                           Html.img({src: imageSrc('protected'),
                                                     style: {verticalAlign: 'middle'},
                                                     alt: "protected",
                                                     title: $T("This material is protected")})
                                           :'');

            var item = [
                Html.div('topMaterialBar',
                         IndicoUI.Buttons.arrowExpandIcon(matWidgetDiv, true),
                         protectionIcon,
                         $B(Html.span({verticalAlign: 'middle'}),material.accessor('title')),
                         menu,
                         $B(Html.div("descriptionLine"), material.accessor('description'))),

                matWidgetDiv
            ];
        } else if(material.get('reviewingState') > 2 || self.canReviewModify){
            item = [matWidgetDiv];
        } else {
            if(material.get('isUnderReview')){
                item = Html.span({style: {fontSize: pixels(13), fontStyle: "italic"}}, $T("The paper has been set to be corrected, therefore the material can not be shown yet. If you want to see the previous paper, please click in 'History'"));
            }
            else {
                item = Html.span({style: {fontSize: pixels(13), fontStyle: "italic"}}, $T("The paper has not been submitted yet, therefore the material can not be shown yet."));
            }
        }

        var domElement = Html.div("materialEntry",item);

        if (self.highlight && self.highlight == pair.key){
            domElement.dom.className += " highlighted";
        }

        return domElement;

    },

    draw: function() {
        return this.RemoteWidget.prototype.draw.call(this);
    },

    _updateMaterialList: function(material) {
        // add type to custom list, if not there
        var i = -1;
        var niceTitle = null;

        for (var j in this.types) {
            if (this.types[j][1] == material.get('title') || this.types[j][0] == material.get('title')) {
                i = j;
                niceTitle = this.types[j][1];
                break;
            }
        }

        var newElement = [material.get('id'), niceTitle ? niceTitle : material.get('title')];

        if (i >= 0) {
            this.types[i] = newElement;
        } else {
            this.types.push(newElement);
        }
    },

    _loadMaterial: function(id) {
        var self = this;
        var source;
        var args = clone(self.args);
        args.materialId = id;
        source = indicoSource('material.get', args);
        source.state.observe(function(state) {

            if (state == SourceState.Loaded) {
                var material = $O($O(source).getAll());
                var obj = watchize(clone(material.get('resources')));
                material.set('resources', null);
                material.set('resources', obj);
                self.set(id,
                         material);

                self._updateMaterialList(material);

            }
        });
    },

    _postDraw: function(pair){
        var self = this;
    },


    makeMaterialLoadFunction: function() {
        var self = this;
        return function(infoList) {
            for(var i = 0; i < infoList.length; i++) {
                var info = infoList[i];
                if (self.get(info.material)) {
                    self.get(info.material).get('resources').append(watchize(info));
                } else {
                    self._loadMaterial(info.material);
                }
            }
        }
    },


    drawContent: function() {
        var self = this;

        $O(self.source).each(function(value, key){
            var obj = watchize(value);
            self.set(key, obj);
        });

        var openAddMaterialDialog = function(onUpdate) {
            IndicoUI.Dialogs.Material.add(self.args,
                    self,
                    self.types,
                    self.uploadAction,
                    onUpdate,
                    false,
                    self.addMaterialMode);
        };

        if (self.addMaterialMode) {
            openAddMaterialDialog(function(param) {window.location.reload(true);});
        }
        var link = Widget.link(command(function(){openAddMaterialDialog(self.makeMaterialLoadFunction());}, $T("Add Material")));


        return Html.div(
            {},
            Html.div({style:{textAlign: 'left'}}, link),
            Html.div({style:{overflow: 'auto', width: self.width, height: self.height}},
                     this.ListWidget.prototype.draw.call(this))
        );
    }
},

     function(args, types, uploadAction, width, height, showMainResources, listMethod, canReviewModify, addMaterialMode, deleteResourceMethod) {
         var self = this;
         this.width = width;
         this.height = height;
         this.args = args;
         this.types = types;
         this.uploadAction = uploadAction;
         this.ListWidget("materialList");
         if (!exists(listMethod)) {
             listMethod = 'material.list';
         }
         this.deleteResourceMethod = any(deleteResourceMethod, "material.resources.delete");

         this.canReviewModify = any(canReviewModify, false);
         this.addMaterialMode = addMaterialMode;
         this.RemoteWidget(listMethod, args);
         this.args.materialIdsList = $O();
         this.showMainResources = showMainResources || false;
         if(window.location.hash){
             this.highlight = window.location.hash.replace("#","");
         }
     }
);

type("ReviewingMaterialListWidget", ["MaterialListWidget"], {

    drawContent: function() {

        var self = this;

        $O(self.source).each(function(value, key){
            var obj = watchize(value);
            self.set(key, obj);
        });

        var link = Widget.link(command(function(){
                    IndicoUI.Dialogs.Material.add(self.args,
                                                  self,
                                                  self.types,
                                                  self.uploadAction,
                                                  self.makeMaterialLoadFunction(),
                                                  true,
                                                  self.addMaterialMode);
                }, $T("Upload paper")));
        var visibility = "hidden";
        if(self.canReviewModify){
            visibility = "visible";
        }
        return Html.div(
            {},
            Html.div({style:{textAlign: 'left', visibility: visibility, marginBottom: pixels(10)}}, link),
            Html.div({style:{overflow: 'auto', width: self.width, height: self.height, border:"1px solid #EAEAEA"}}, this.noMaterialText,
                     this.ListWidget.prototype.draw.call(this))
        );
    }
},
     function(args, types, uploadAction, width, height, canReviewModify, sendToReviewButton, textHasMaterials) {
         var self = this;
         this.MaterialListWidget(args, types, uploadAction, width, height, false, 'material.reviewing.list', canReviewModify, false, 'material.reviewing.resources.delete');
         this.canReviewModify = canReviewModify;
         this.sendToReviewButton = sendToReviewButton;
         this.textHasMaterials = textHasMaterials;
         this.noMaterialText = Html.div({style: {textAlign:"center", padding: pixels(5)}}, $T("No paper uploaded"));

         this.observe(function(){
                if (self.isEmpty()) {
                    self.sendToReviewButton.disabledButtonWithTooltip('disable');
                    self.textHasMaterials.hide();
                    $(self.noMaterialText.dom).show();

                }else {
                    self.sendToReviewButton.disabledButtonWithTooltip('enable');
                    self.textHasMaterials.show();
                    $(self.noMaterialText.dom).hide();
                }
            });
     }
    );

/*
type("AbstractSubmissionMaterialListWidget", ["MaterialListWidget"], {

    drawContent: function() {

        var self = this;

        $O(self.source).each(function(value, key){
            var obj = watchize(value);
            self.set(key, obj);
        });


        var link = Widget.link(command(function(){
                    IndicoUI.Dialogs.Material.add(null,
                                                  self,
                                                  null,
                                                  null,
                                                  self.makeMaterialLoadFunction(),
                                                  true);
                }, $T("Upload file")));
        return Html.div(
            {},
            Html.div({style:{textAlign: 'left'}}, link),
            Html.div({style:{overflow: 'auto'}},
                     this.ListWidget.prototype.draw.call(this))
        );
    }
},
     function(args) {
         this.MaterialListWidget({});
     }
    );
*/



type("MaterialEditorDialog", ["ExclusivePopupWithButtons"], {

    _getButtons: function() {
        var self = this;
        return [
            [$T("Close"), function() {
                self.close();
                window.location.reload(true);
            }]
        ];
    },

    draw: function() {
        var self = this;
        var changes = 0;

        var args = {
            'categId': this.categId,
            'confId': this.confId,
            'sessionId': this.sessId,
            'contribId': this.contId,
            'subContId': this.subContId,
            'parentProtected': this.parentProtected
        };

        // Remove null parameters
        each(args, function(value, key) {
            //sometimes 'null' value is set as a string
            if (value === null || value === undefined || value =="null") {
                delete args[key];
            }
        });

        var mlist = new MaterialListWidget(args, this.types, this.uploadAction, this.width, this.height, null, null, null, this.addMaterialMode);

        return this.ExclusivePopupWithButtons.prototype.draw.call(
            this,
            Html.div({style: {width: pixels(this.width),
                              height: pixels(this.height+10)}},
                     mlist.draw())
        );
    }
},

     function(categId, confId, sessId, contId, subContId, parentProtected, types, uploadAction, title, width, height, refresh, addMaterialMode) {
         this.categId = categId;
         this.confId = confId;
         this.sessId = sessId;
         this.contId = contId;
         this.subContId = subContId;
         this.types = types;
         this.uploadAction = uploadAction;
         this.width = width;
         this.height = height;
         this.refresh = refresh;
         this.addMaterialMode = addMaterialMode;
         this.parentProtected = parentProtected;
         this.ExclusivePopupWithButtons(title);
     });

type("MaterialConversionHelper", [], {

    setQtip: function(file) {
        $("img#"+file['id']).parent().qtip({
            content: {
                text: format($T('Indico is currently performing the conversion to PDF of the file:<br>{fileName}<br>The conversion may take a few seconds.'),
                        {fileName: file['name']})
            },
            position: {
                target: 'mouse',
                adjust: { mouse: true, x: 11, y: 13 }
            }
        });
    },

    poll: function(file, params, pdfImgURL) {
        var endTime = new Date();
        endTime.setDate(endTime.getDate() + 60);
        (function conversionWorker() {
            jsonRpc(Indico.Urls.JsonRpcService,
                    'material.resources.list',
                    params,
                    function(response,error) {
                        if (response) {
                            for (var value in response){
                                if (response[value].name == file['name'].split('.')[0] + '.pdf') {
                                    var convertedImg = $("img#"+file['id']);
                                    $(convertedImg).parent().qtip('destroy');
                                    $(convertedImg).parent().attr('href',response[value].url);
                                    $(convertedImg).parent().attr('title',response[value].name);
                                    $(convertedImg).attr('src', pdfImgURL);
                                    return;
                                }
                            }
                            if (new Date() < endTime) {
                                setTimeout(conversionWorker, CONVERSION_POLL_INTERVAL);
                            }
                        }
                    });
            })();
    }

},
function() {});

IndicoUI.Dialogs.Material = {

    add: function(args, list, types, uploadAction, onUpload, forReviewing, addMaterialMode) {
        var dialog = new AddMaterialDialog(args, list, types, uploadAction, onUpload, forReviewing, addMaterialMode);
        dialog.open();
    },

    editMaterial: function(args, types, material, list) {
        //var dialog = new EditMaterialDialog(args, types, material, list, $T("Edit Material"));
        var dialog = new EditMaterialDialog(args, material, types, list, $T("Edit Material"));
        dialog.execute();
    },

    editResource: function(args, material, materialName , resource, domItem, appender, forReviewing) {
        var dialog = new EditResourceDialog(args, material, materialName, resource, domItem, appender, $T("Edit Resource"), forReviewing);
        dialog.execute();
    },

    editor: function(categId, confId, sessId, contId, subContId, parentProtected, types, uploadAction, refresh, addMaterialMode) {
        var dialog = new MaterialEditorDialog(categId, confId, sessId, contId, subContId, parentProtected, types, uploadAction, $T("Edit Materials"), 400, 300, refresh, addMaterialMode);
        dialog.open();
        if (addMaterialMode) {
            dialog.close();
        }
    }
};
