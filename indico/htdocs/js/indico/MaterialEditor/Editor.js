function updateMaterialList(oldList, newList) {
    oldList.length = 0;

    for (var i in newList) if (newList[i]) {
        oldList.push(newList[i]);
    }
}


type("AddMaterialDialog", ["ExclusivePopupWithButtons"], {

    _drawButtons: function() {

        var self = this;

        var buttonDiv = Html.div({},
            Widget.button(command(function() {
                self._upload();
            }, "Create Resource")));

        return buttonDiv;
    },

    _iFrameLoaded : function(iframeId) {

        var doc;

        if (Browser.IE) {
            // *sigh*
            doc = document.frames[iframeId].document;
        } else {
            doc = $E(iframeId).dom.contentDocument;
        }

        // textContent would be more appropriate, but IE...
        var res = Json.read(doc.body.innerHTML);

        var self = this;

        if (res.status == "ERROR") {
            IndicoUtil.errorReport(res.info);
        } else {
            this.onUpload(res.info);
            // Firefox will keep "loading" if the iframe is destroyed
            // right now. Let's wait a bit.
            setTimeout(
                function() {
                    self.close();
                }, 100);
        }
    },

    /*
     * Draws a pane that switches between a URL input and a file upload dialog.
     *
     * pm - A parameter manager
     * locationSelector - the locationSelector that will 'control' the pane
     */
    _drawResourcePathPane: function(locationSelector) {

        var file = Html.input('file', {name: 'file'});
        var urlBox = Html.edit({name: 'url'});
        var toPDFCheckbox = Html.checkbox({style: {verticalAlign: 'middle'}}, true);
        toPDFCheckbox.dom.name = 'topdf';

        var self = this;

        var resourcePathPane = new Chooser(
            new Lookup({
                'local':  function() {
                    self.pm.remove(urlBox);
                    return Html.div({},
                                    self.pm.add(file, 'text'),
                                    Html.div({style:{marginTop: '5px'}},
                                             toPDFCheckbox,
                                             Html.label({style: {verticalAlign: 'middle'}, className: 'emphasis'}
                                                        , $T("Convert to PDF (when applicable)")))
                                   );
                },
                'remote': function() {
                    self.pm.remove(file);
                    setTimeout(function() { urlBox.dom.focus();
                                            urlBox.set('http://'); }, 200);
                    return Html.div({},
                                    Html.label('popUpLabel', $T("URL")),
                                    self.pm.add(urlBox, 'url'),
                                    Html.div("smallGrey", "Example: http://www.example.com/YourPDFFile.pdf"));
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
                file.dom.focus();
            } else {
                urlBox.dom.focus();
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
            text = $T("Same people as parent Subcontribution");
        } else if (args.contribId) {
            text = $T("Same people as parent Contribution");
        } else if (args.sessionId) {
            text = $T("Same people as parent Session");
        } else if (args.confId) {
            text = $T("Same people as parent Conference");
        } else if (args.categId) {
            text = $T("Same people as parent Category");
        }

        text = Html.span({}, text, " ",
                         Html.unescaped.span({className: 'strongRed', style: {fontStyle: 'italic'}}," ",
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
        var entry = this.list.get(value);
        var selector = null;

        if (value == '') {
            return Html.div({});

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
                ['inherit', Html.span({}, $T("Same people as the parent material type ")+"\""+entry.get('title')+"\" ", inheritanceText)],
                ['private', $T("Only me and the users I specify")],
                ['public', $T("Everyone")]
            ], 'nobulletsListWrapping');


        } else {

            this.creationMode = 'material';

            text = Html.span({}, $T("This will be the first resource of type")," ", Html.span({style:{fontWeight: 'bold'}}, this._findTypeName(value)), ". ", $T("Please select who will be able to access this material type:"));

            selector = new RadioFieldWidget([
                ['inherit', this._parentText(this.args)],
                ['private', $T("Only me and the users I specify")],
                ['public', $T("Everyone")]
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
                    self.password.enable();
                } else {
                    self.visibility.disable();
                    self.password.disable();
                }

                // draw a little notification saying that
                // the added tab can be used
                self.notification  = new NotificationBalloonPopup(
                    selector.radioDict[state],
                    Html.div({style:{width: '120px'}}, $T("You can specify users using this tab")));

                var pos = self.tabWidget.tabs[1].getAbsolutePosition();

                // open it, pointing to tab
                self.notification.open(pos.x + self.tabWidget.tabs[1].dom.offsetWidth/2, pos.y);

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

        this.pm = new IndicoUtil.parameterManager();
        var typeSelector = new TypeSelector(this.pm, this.types, {style:{width: '150px'}},{style:{width: '150px'}, maxlength: '50'});
        var description = Html.textarea({name: 'description', style:{width:'220px', height: '60px'}});

        // local file vs. url
        var locationSelector = new RadioFieldWidget([['local',$T('Local file')],['remote',$T('External resource (hyperlink)')]]);

        // draw the resource pane
        var resourcePathPane = this._drawResourcePathPane(locationSelector);
        // protection page
        var protectionPane = $B(
            Html.div({}),
            typeSelector,
            function(value) {
                return self._drawProtectionPane(value);
            });

        // make typeSelector available to the object
        this.typeSelector = typeSelector;

        return Html.div({},
                        IndicoUtil.createFormFromMap(
                            [
                                [
                                    $T('Location'),
                                    Html.div({},
                                             locationSelector.draw(),
                                             Html.div({style:{paddingTop: '15px',
                                                              paddingBottom: '10px',
                                                              minHeight: '50px'}},
                                                      Widget.block(resourcePathPane)))
                                ],
                                [
                                    $T('Description'),
                                    description
                                ],
                                [
                                    $T('Material type'),
                                    Html.div({style:{height: '40px'}}, typeSelector.draw())
                                ]

                            ]),
                        protectionPane);

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

            this.formDict.materialId.set(this.typeSelector.get());

            this.form.dom.submit();

        }
    },


    _drawWidget: function() {
        var self = this;

        this.formDict = {};
        this.frameId = Html.generateId();

        var iframe = Html.iframe({id: this.frameId, name: this.frameId, style: {display: 'none'}});

        this.form = Html.form(
            {
                target: this.frameId, method: 'post',
                id: Html.generateId(),
                action: this.uploadAction,
                enctype: 'multipart/form-data',
                encoding: 'multipart/form-data'
            },
            this.tabWidget.draw());

        each(['statusSelection', 'visibility', 'password', 'userList', 'uploadType', 'materialId'],
             function(fieldName) {
                 var elem = Html.input('hidden', {name: fieldName});
                 self.formDict[fieldName] = elem;
                 self.form.append(elem);
             });

        var loadFunc = function() {
            if (self.uploading) {
                self.killProgress();
                self.uploading = false;
                // need to pass the ID, due to IE
                self._iFrameLoaded(self.frameId);
            }
        };

        if (Browser.IE) {
            iframe.dom.onreadystatechange = loadFunc;
        } else {
            // for normal browsers
            iframe.observeEvent("load", loadFunc);
        }

        each(this.args, function (value, key) {
            self.form.append(Html.input('hidden',{name: key}, value));
        });

        return Html.div({},
                        this.form,
                        iframe);

    },

    postDraw: function() {

        var selection = "slides";

        // We're not sure that the type "Slides"
        // will have a "standard" id
        for (i in this.types) {
            if (this.types[i][1] == "Slides") {
                selection = this.types[i][0];
            }
        }

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
            false, false, true,
            userListNothing, userListNothing, userListNothing);

        // Bind fields to data structure
        $B(this.protectionStatus.accessor('visibility'), this.visibility);
        $B(this.protectionStatus.accessor('password'), this.password);

        this.visibility.set(0);
        this.password.set('');

        var privateInfoDiv = IndicoUtil.createFormFromMap(
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

        return privateInfoDiv;
    },

    draw: function() {
        var self = this;

        self.newMaterial = $O();

        var protectionDiv = this._drawProtectionDiv();

        this.tabWidget = new TabWidget([[$T('Upload'), this._drawUpload()],
                                        [$T("Protection"), protectionDiv]],
                                       400, 300);

        return this.ExclusivePopupWithButtons.prototype.draw.call(this,
                                                                  this._drawWidget(),
                                                                  this._drawButtons(), {backgroundColor: 'white'}, {backgroundColor: 'white'});
    }


}, function(args, list, types, uploadAction, onUpload) {

    var self = this;
    this.list = list;
    this.types = types;
    this.uploadAction = uploadAction;
    this.uploading = false;
    this.onUpload = onUpload;

    this.args = clone(args);
//    this.args.materialId = material;

    this.protectionStatus = $O();
    this.uploadType = new WatchValue();

    this.ExclusivePopupWithButtons($T("Upload Material"),
                        function() {
                            self.close();
                        });
});


type("EditMaterialResourceBase", ["ServiceDialogWithButtons"], {

    _preloadAllowedUsers: function(hook, method) {
        var self = this;

        var killProgress = IndicoUI.Dialogs.Util.progress($T("Loading dialog..."));
        if (IndicoGlobalVars.isUserAuthenticated && !exists(IndicoGlobalVars['favorite-user-ids'])) {
            self.args.includeFavList = true;
        } else {
            self.args.includeFavList = false;
        }
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
    }
},

    function(endPoint, method, args, title, closeHandler) {
        this.ServiceDialogWithButtons(endPoint, method, args, title, closeHandler);
    }
);

type("EditMaterialDialog", ["EditMaterialResourceBase", "PreLoadHandler"], {
    _preload: [
        function(hook){
            this._preloadAllowedUsers(hook, 'material.listAllowedUsers');
        }
    ],

    _saveCategory: function() {
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

        this.request(params);
    },

    _success: function(response) {
        this.list.set(this.materialId, null);
        this.list.set(this.materialId, watchize(response.material));

        updateMaterialList(this.types, response.newMaterialTypes);

    },

    draw: function() {
        var self = this;

        self.newMaterial = $O(self.material.getAll());

        var statusSelection = Widget.select(
            $L({
                0:(self.material.get('protectedOwner')?$T('Private'):$T('Public'))+' '+$T('(from parent)'),
                1:$T('Private (by itself)'),
                '-1':$T('Public (by itself)')
            })
        );

        statusSelection.observe(function(value) {
            if (value == 0 && self.material.get('protectedOwner') ||
                value == 1) {
                self.privateInfoDiv.show();
            } else {
                self.privateInfoDiv.hide();
            }
        });

        var visibility = Html.select(
            {},
            Html.option({value: 0},$T('Visible for unauth. users')),
            Html.option({value: 1},$T('Hidden from unauth. users'))
        );

        this.userList = new UserListField(
                'ShortPeopleListDiv', 'PeopleList',
                this.allowedUsers, true, null,
                true, true, null, null,
                false, false, true,
                userListNothing, userListNothing, userListNothing);

        self.privateInfoDiv = Html.div(
            {style:{padding:pixels(2)}},
            Html.div({},
                     Html.label({}, $T('Allowed users')),
                     self.userList.draw()),
            Html.div({style:{marginTop: pixels(15)}},
                     Html.label({}, $T('Visibility: ')),
                     $B(visibility,
                        self.newMaterial.accessor('hidden'))),
            Html.div({style:{marginTop: pixels(10)}},
                     Html.label({}, $T('Access Key: ')),
                     $B(Html.input('password',{}),
                        self.newMaterial.accessor('accessKey')))
        );
        if ( !self.material.get('protectedOwner')) {
            self.privateInfoDiv.hide();
        }

        var protectionDiv = Html.div(
            {style: {marginTop: pixels(5)}},
            Html.div({style:{paddingBottom:pixels(10)}},
                     Html.label({},$T("Status: ")),
                     $B(statusSelection,
                        self.newMaterial.accessor('protection'))
                    ),
            self.privateInfoDiv);

        var title = Html.input('text',{});
        var titleDiv = Html.div({style:{paddingBottom:pixels(20)}}, Html.label({},"Title: "), title);
        var description = Html.textarea({name:'description', style: {width: '100%'}});
        var descDiv = Html.div({style:{paddingRight:pixels(10)}}, Html.label({}, $T("Description: ")), description);

        $B(title, self.newMaterial.accessor('title'));
        $B(description, self.newMaterial.accessor('description'));

        statusSelection.notifyObservers();

        var tabControl = new TabWidget([
            [$T("Information"), Widget.block([titleDiv,descDiv])],
            [$T("Protection") , protectionDiv]], 300,325);

        var saveButton = Html.input('button', {style: {marginRight: pixels(3)}}, $T('Save'));
        var cancelButton = Html.input('button', {style: {marginLeft: pixels(3)}}, $T('Cancel'));
        saveButton.observeClick(function(){
            self._saveCategory();
        });
        cancelButton.observeClick(function(){
            self.close();
        });
        var buttonDiv = Html.div({}, saveButton, cancelButton);

        return this.EditMaterialResourceBase.prototype.draw.call(this, tabControl.draw(), buttonDiv);
    }
},

     function(args, types, material, list, title) {
         this.material = material;
         this.materialId = this.material.get('id');
         this.types = types;
         this.list = list;

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

type("EditResourceDialog", ["EditMaterialResourceBase", "PreLoadHandler"], {
    _preload:
    [
        function(hook){
            this._preloadAllowedUsers(hook, 'material.resources.listAllowedUsers');
        }
    ],

    _saveResource: function() {
        var params = clone(this.args);
        params.resourceInfo = this.newResource;
        this.newResource.set('userList', this.userList.getUsers());
        this.request(params);
    },

    _success: function(response) {
        this.appender(watchize(response));
    },

    draw: function() {
        var self = this;

        self.newResource = clone(this.resource);
        var name = Html.input('text',{});
        var nameDiv = Html.div({style:{paddingBottom:pixels(10)}}, Html.label({},$T("Name: ")),name);
        var url = Html.input('text',{name:'url'});
        var urlDiv = Html.div({style:{paddingBottom:pixels(10)}}, Html.label({},$T("URL: ")), url);
        var description = Html.textarea({name:'description',style: {width: '100%'}});
        var descDiv = Html.div({style:{paddingRight:pixels(5)}}, Html.label({},$T("Description: ")), description);


        $B(name, self.newResource.accessor('name'));
        $B(description, self.newResource.accessor('description'));
        $B(url, self.newResource.accessor('url'));

        this.userList = new UserListField(
                'VeryShortPeopleListDiv', 'PeopleList',
                this.allowedUsers, true, null,
                true, true, null, null,
                false, false, true,
                userListNothing, userListNothing, userListNothing);

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
        var statusSelection = Widget.select(
                $L({
                    0:(isFatherProtected?$T('Private'):$T('Public'))+' '+$T('(from parent)'),
                    1:$T('Private (by itself)'),
                    '-1':$T('Public (by itself)')
                })
            );

        statusSelection.observe(function(value) {

            if (value == 0 && isFatherProtected || value == 1) {
                self.privateInfoDiv.show();
            }
            else {
                self.privateInfoDiv.hide();
            }
        });

        self.privateInfoDiv = Html.div(
            {style:{padding:pixels(2)}},
            Html.div({},
                     Html.label({}, $T('Allowed users')),
                     self.userList.draw()));

        if ( !isFatherProtected) {
            self.privateInfoDiv.hide();
        }

        var protectionDiv = Html.div(
            {style: {marginTop: pixels(5)}},
            Html.div({style:{paddingBottom:pixels(10)}},
                     Html.label({},$T("Status: ")),
                     $B(statusSelection,
                        self.newResource.accessor('protection'))), self.privateInfoDiv);

        var tabControl = new TabWidget([
            [$T("Information"), Widget.block([nameDiv,this.resource.type=='stored'?[]:urlDiv,descDiv])],
            [$T("Protection")   , protectionDiv]], 300,200);
        tabControl.options = $L([$T("Information"), $T("Protection")]);
        tabControl.selected.set($T("Information"));

        statusSelection.notifyObservers();

        var saveButton = Html.input('button', {style: {marginRight: pixels(3)}}, $T('Save'));
        var cancelButton = Html.input('button', {style: {marginLeft: pixels(3)}}, $T('Cancel'));
        saveButton.observeClick(function(){
            self._saveResource();
        });
        cancelButton.observeClick(function(){
            self.close();
        });
        var buttonDiv = Html.div({}, saveButton, cancelButton);

        return this.EditMaterialResourceBase.prototype.draw.call(this, tabControl.draw(), buttonDiv);

    }
},

     function(args, material, resource, domItem, appender, title) {
         args = clone(args);

         this.material = material;
         this.materialId = material.materialId;
         this.resource = resource;
         this.resourceId = resource.id;
         this.domItem = domItem;
         this.appender = appender;

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
 */
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
};

/**
 * Mouseover popup to inform that material is not modificable when user
 * hovers mouse above disabled add, remove or edit buttons.
 */
var modifyDisabledHelpPopup = function(event) {
    IndicoUI.Widgets.Generic.tooltip(this, event,
                                     $T('Modifying this material is currently not possible because it has been already submitted.'));
};

type("ResourceListWidget", ["ListWidget"], {

    _drawItem: function(pair) {
        var resourceId = pair.key;
        var resource = pair.get();

        var self = this;

        var resourceNode;
        var resParams = clone(this.matParams);
        resParams.resourceId = resourceId;

        var deleteResource = function() {
            if (confirm($T("Are you sure you want to delete")+" "+resource.get('name')+"?")) {
                var killProgress = IndicoUI.Dialogs.Util.progress($T('Removing...'));
                jsonRpc(Indico.Urls.JsonRpcService,
                        'material.resources.delete',
                        resParams,
                        function(response,error) {
                            if (exists(error)) {
                                killProgress();
                                IndicoUtil.errorReport(error);
                            } else {
                                var parent = resourceNode.dom.parentNode;
                                self.resources.remove(resource);
                                self.set(resourceId, null);
                                killProgress();

                                if (response.newMaterialTypes) {
                                    updateMaterialList(self.materialTypes, response.newMaterialTypes);
                                }

                            }
                        }
                       );
            }
        };

        var storedDataInfo = function(info) {
            var list = Html.ul();

            var labelAndValue = function(label, value) {
                list.append(Html.li({},Html.span({},Html.strong({},label+": "),value)));
            };

            labelAndValue('File Name',info.get('fileName'));
            labelAndValue('Size',Math.floor(info.get('fileSize')/1024)+ " KB");
            labelAndValue('Creation Date',info.get('creationDate'));

            var filetype = info.get('fileType');

            return Html.div(
                "resourceContainer",
                Html.div({style: {'float':'left'}},
                                    Html.img({
                                        alt: filetype,
                                        style: {
                                            width: '20px',
                                            height: '20px'
                                        },
                                        src: imageSrc(Indico.FileTypeIcons[filetype.toLowerCase()])
                                    }),
                         Html.div({style:{'float': 'left'}},list)));
        };

        var removeButton;
        var editButton;

        if (resource.get('reviewingState') < 3) {
            removeButton = Widget.link(command(deleteResource,IndicoUI.Buttons.removeButton()));
            editButton = Widget.link(command(function() {
                IndicoUI.Dialogs.Material.editResource(resParams, self.matParams, resource, resourceNode, function(resource) {
                    self.set(resource.get('id'), null);
                    self.set(resource.get('id'), resource);
                });
            },
                                             IndicoUI.Buttons.editButton())
                                    );
        } else {
            removeButton = IndicoUI.Buttons.removeButton(true);
            removeButton.dom.title = '';
            removeButton.dom.onmouseover = modifyDisabledHelpPopup;

            editButton = IndicoUI.Buttons.editButton(true);
            editButton.dom.title = '';
            editButton.dom.onmouseover = modifyDisabledHelpPopup;
        }

        var information = [
            Html.a({href: resource.get('url'), style: {paddingLeft: '5px'}}, resource.get('name')),
            resource.get('type') == 'stored'?"":[" (",Html.span({style:{fontStyle: 'italic', fontSize: '11px'}}, resource.get('url')),")"],
            removeButton,
            editButton,
            Html.div("descriptionLine", resource.get('description'))
        ];

        if (resource.get('type') == 'stored') {
            var fileData = storedDataInfo(resource.get('file'));
            resourceNode = Widget.block(concat([IndicoUI.Buttons.arrowExpandIcon(fileData)], information));
            resourceNode.append(fileData);
        } else {
            resourceNode = Html.div({style:{paddingLeft: '12px'}}, information);
        }

        return resourceNode;
    }

}, function(resources, matParams, materialTitle, materialTypes) {
    this.matParams = matParams;
    this.resources = resources;
    this.materialName = materialTitle;
    this.materialTypes = materialTypes;
    this.ListWidget();

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
        var deleteMaterial = function() {
            if (confirm("Are you sure you want to delete '"+material.get('title')+"'?")) {
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

        var reviewingState = material.get('reviewingState');
        var revStateImg = "";
        if (reviewingState > 0) {
            revStateImg = self._getReviewingStateImage(material.get('reviewingState'));
        }

        var menu;

        if (material.get('reviewingState') < 3) { // if material can be modified
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
                )),
                revStateImg);

        } else { // material cannot be modified: we use grey icons without click popup, just a mouseover help information popup
            var ab = IndicoUI.Buttons.addButton(true);
            ab.dom.title = '';
            ab.dom.onmouseover = modifyDisabledHelpPopup;

            var rb = IndicoUI.Buttons.removeButton(true);
            rb.dom.title = '';
            rb.dom.onmouseover = modifyDisabledHelpPopup;

            var eb = IndicoUI.Buttons.editButton(true);
            eb.dom.title = '';
            eb.dom.onmouseover = modifyDisabledHelpPopup;

            menu = Html.span({},ab,rb,eb,revStateImg);
        }

        args.materialProtection = material.get('protection');
        var matWidget = new ResourceListWidget(material.get('resources'), args, material.get('title'), self.types);

        // check whenever a material gets empty (no resources) and delete it
        material.get('resources').observe(
            function(event, element) {
                if (event == 'itemRemoved' &&
                    material.get('resources').length.get() == 1) {
                    self.set(materialId, null);
                }
            });

        var matWidgetDiv = matWidget.draw();
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
            IndicoUI.Buttons.arrowExpandIcon(matWidgetDiv, true),
            protectionIcon,
            $B(Html.span({verticalAlign: 'middle'}),material.accessor('title')),
            menu,
            $B(Html.div("descriptionLine"), material.accessor('description')),
            matWidgetDiv
        ];

        return item;
    },

    _getReviewingStateImage : function(reviewingState) {
        // stores an image with the reviewing status of the material
        var imgAttrs = {
            style: {'marginLeft': '5px', 'verticalAlign': 'middle'},
            title:''
        };

        switch (reviewingState) {
        case 1:
            imgAttrs.alt = 'Not subject to reviewing';
            imgAttrs.src = imageSrc("dot_gray");
            break;
        case 2:
            imgAttrs.alt = 'Not yet submitted by author';
            imgAttrs.src = imageSrc("dot_orange");
            break;
        case 3:
            imgAttrs.alt = 'Submitted by author, pending revision';
            imgAttrs.src = imageSrc("dot_blue");
            break;
        case 4:
            imgAttrs.alt = 'Submitted by author, judged Accepted';
            imgAttrs.src = imageSrc("dot_green");
            break;
        case 5:
            imgAttrs.alt = 'Submitted by author, judged Rejected';
            imgAttrs.src = imageSrc("dot_red");
            break;
        default:
            break;
        }

        var revState = Html.img(imgAttrs);
        revState.dom.onmouseover = revStateHelpPopup;

        return revState;
    },

    draw: function() {
        return this.RemoteWidget.prototype.draw.call(this);
    },

    _updateMaterialList: function(material) {
        // add type to custom list, if not there
        var i = -1;

        for (var j in this.types) {
            if (this.types[j][1] == material.get('title')) {
                i = j;
                break;
            }
        }

        var newElement = [material.get('id'), material.get('title')];

        if (i >= 0) {
            this.types[i] = newElement;
        } else {
            this.types.push(newElement);
        }
    },

    _loadMaterial: function(id) {
        var self = this;

        var args = clone(self.args);
        args.materialId = id;

        var source = indicoSource('material.get', args);

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

    drawContent: function() {

        var self = this;

        $O(self.source).each(function(value, key){
            var obj = watchize(value);
            self.set(key, obj);
        });

        var materialLoadFunction = function(info) {
            if (self.get(info.material)) {
                self.get(info.material).get('resources').append(watchize(info));
            } else {
                self._loadMaterial(info.material);
            }
        };

        var link = Widget.link(command(function(){

            IndicoUI.Dialogs.Material.add(self.args,
                                          self,
                                          self.types,
                                          self.uploadAction,
                                          materialLoadFunction);
        }, $T("Add Material")));
        return Html.div(
            {},
            Html.div({style:{textAlign: 'left'}}, link),
            Html.div({style:{overflow: 'auto', width: self.width, height: self.height}},
                     this.ListWidget.prototype.draw.call(this))
        );
    }
},

     function(args, types, uploadAction, width, height) {
         var self = this;
         this.width = width;
         this.height = height;
         this.args = args;
         this.types = types;
         this.uploadAction = uploadAction;
         this.ListWidget("materialList");
         this.RemoteWidget('material.list',
                           args);
         this.args.materialIdsList = $O();
     }
);

type("MaterialEditorDialog", ["ExclusivePopupWithButtons"], {

    _drawButtons: function() {

        var self = this;
        var buttonDiv = Html.div({},
            Widget.button(command(function() {
                self.close();
                window.location.reload(true);
            }, $T("Close"))));

        return buttonDiv;
    },


    draw: function() {
        var self = this;
        var changes = 0;

        var args = {
            'categId': intToStr(this.categId),
            'confId': intToStr(this.confId),
            'sessionId': intToStr(this.sessId),
            'contribId': intToStr(this.contId),
            'subContId': intToStr(this.subContId),
            'parentProtected': this.parentProtected
        };

        // Remove null parameters
        each(args, function(value, key) {
            if (value === null) {
                delete args[key];
            }
        });

        var mlist = new MaterialListWidget(args, this.types, this.uploadAction, this.width, this.height);

        return this.ExclusivePopupWithButtons.prototype.draw.call(
            this,
            Html.div({style: {width: pixels(this.width),
                              height: pixels(this.height+10)}},
                     mlist.draw()),
            this._drawButtons()
        );
    }
},

     function(confId, sessId, contId, subContId, parentProtected, types, uploadAction, title, width, height, refresh) {
         this.confId = confId;
         this.sessId = sessId;
         this.contId = contId;
         this.subContId = subContId;
         this.types = types;
         this.uploadAction = uploadAction;
         this.width = width;
         this.height = height;
         this.refresh = refresh;
         this.parentProtected = parentProtected;
         this.ExclusivePopupWithButtons(title);
     });

IndicoUI.Dialogs.Material = {

    add: function(args, list, types, uploadAction, onUpload) {
        var dialog = new AddMaterialDialog(args, list, types, uploadAction, onUpload);
        dialog.open();
    },
    editMaterial: function(args, types, material, list) {
        var dialog = new EditMaterialDialog(args, types, material, list, $T("Edit Material"));
        dialog.execute();
    },

    editResource: function(args, material, resource, domItem, appender) {
        var dialog = new EditResourceDialog(args, material, resource, domItem, appender, $T("Edit Resource"));
        dialog.execute();
    },

    editor: function(confId, sessId, contId, subContId, parentProtected, types, uploadAction, refresh) {
        var dialog = new MaterialEditorDialog(confId, sessId, contId, subContId, parentProtected, types, uploadAction, $T("Edit Materials"), 400, 300, refresh);
        dialog.open();
    }
};
