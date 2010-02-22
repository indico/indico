
type("AddMaterialDialog", ["ExclusivePopup"], {

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

    _drawTypeSelector: function(pm) {
        var self = this;
        var select = Html.select({name: 'materialId'});
        var text = Html.edit({name: 'materialId'});

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
                pm.add(text);
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

    _drawFileUpload: function() {
        var self = this;

        var pm = new IndicoUtil.parameterManager();

        var uploadType = Html.input('hidden', {name: 'uploadType'});
        var convert = Html.checkbox({}, true);
        var selector = this._drawTypeSelector(pm);
        var file = Html.input('file', {name: 'file'});
        var description = Html.textarea({name: 'description'});

        uploadType.set('file');

        // FIX: presentation issue
        convert.dom.name = 'topdf';

        pm.add(selector, 'text', false);
        pm.add(file, 'text', false);
        pm.add(description, 'text', true);

        return Html.div({},
                        IndicoUtil.createFormFromMap(
                            [
                                [$T('Type'), selector],
                                [$T('File'), file],
                                [$T('Description'), description],
                                [$T('Convert to PDF'), convert]
                            ]),
                        uploadType,
                        Html.div({style: {'textAlign': 'center'}},
                                 Widget.button(command(
                                     function() {
                                         if (pm.check()) {
                                             self.killProgress = IndicoUI.Dialogs.Util.progress($T('Uploading...'));
                                             self.uploading = true;
                                             self.form.dom.submit();
                                         }
                                     }, $T("Upload")))));
    },

    _drawLinkUpload: function() {
        var self = this;

        var pm = new IndicoUtil.parameterManager();

        var uploadType = Html.input('hidden', {name: 'uploadType'});
        var selector = this._drawTypeSelector(pm);
        var url = Html.edit({name: 'url'});
        var description = Html.textarea({name: 'description'});

        uploadType.set('link');

        pm.add(selector, 'text', false);
        pm.add(url, 'text', false);
        pm.add(description, 'text', true);

        return Html.div({},
                        IndicoUtil.createFormFromMap(
                            [
                                [$T('Type'),selector],
                                [$T('URL'), url],
                                [$T('Description'), description]
                            ]),
                        uploadType,
                        Html.div({style: {'textAlign': 'center'}},
                                 Widget.button(command(
                                     function() {
                                         if (pm.check()) {
                                             self.killProgress = IndicoUI.Dialogs.Util.progress();
                                             self.uploading = true;
                                             self.form.dom.submit();
                                         }
                                     }, $T("Upload")))));
    },

    _drawWidget: function() {
        var self = this;

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

        var loadFunc = function() {
            if (self.uploading) {
                self.killProgress();
                self.uploading = false;
                // need to pass the ID, due to IE
                self._iFrameLoaded(self.frameId);
            }
        };

        if (Browser.IE) {
            // cof! cof!
            iframe.dom.onreadystatechange = loadFunc;
        } else {
            // for normal browsers
            iframe.observeEvent("load", loadFunc);
        }

        each(this.args, function (value, key) {
            self.form.append(Html.input('hidden',{name: key}, value));
        });

        return Html.div({}, this.form, iframe);

    },

    draw: function() {
        this.tabWidget = new TabWidget([[$T('Upload File'), this._drawFileUpload()],
                                        [$T('Add Link'), this._drawLinkUpload()]],
                                       400, 200);

        return this.ExclusivePopup.prototype.draw.call(this,
                                                       this._drawWidget());
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

    this.ExclusivePopup($T("Upload Material"),
                        function() {
                            self.close();
                        });
});


type("EditMaterialDialog", ["ServiceDialog", "PreLoadHandler"], {
    _preload: [
        function(hook){
            var self = this;
            var users = indicoSource('material.listAllowedUsers', self.args);

            users.state.observe(function(state) {
                if (state == SourceState.Loaded) {
                    self.allowedUsers = users.get();
                    hook.set(true);
                }
            });
        }
    ],

    _saveCategory: function() {
        var params = clone(this.args);
        params.materialInfo = this.newMaterial;
        this.newMaterial.set('userList', this.userList.getUsers());
        this.request(params);
    },

    _success: function(response) {
        this.list.set(this.materialId, null);
        this.list.set(this.materialId, watchize(response));
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
            if (value === 0 && self.material.get('protectedOwner') ||
                value == 1) {
                privateInfoDiv.setStyle('border',null);
            } else {
                IndicoUI.Effect.frame(privateInfoDiv);
            }
        });

        var visibility = Html.select(
            {},
            Html.option({value: 0},$T('Visible for unauth. users')),
            Html.option({value: 1},$T('Hidden from unauth. users'))
        );

        self.userList =  new UserListField('ShortPeopleListDiv',
                                           'PluginPeopleList',
                                           self.allowedUsers,
                                           null,
                                           null,
                                           true, false, false,
                                           userListNothing, userListNothing, userListNothing, true);


        var privateInfoDiv = Html.div(
            {style:{padding:pixels(2)}},
            Html.div({},
                     Html.label({}, $T('Allowed users')),
                     self.userList.draw()),
            Html.div({style:{marginTop: pixels(4)}},
                     Html.label({}, $T('Visibility: ')),
                     $B(visibility,
                        self.newMaterial.accessor('hidden'))),
            Html.div({},
                     Html.label({}, $T('Access Key: ')),
                     $B(Html.input('password',{}),
                        self.newMaterial.accessor('accessKey')))
        );


        var protectionDiv = Html.div(
            {style: {marginTop: pixels(5)}},
            Html.div({},
                     Html.label({},$T("Status: ")),
                     $B(statusSelection,
                        self.newMaterial.accessor('protection'))
                    ),
            privateInfoDiv);

        var title = Html.input('text',{});
        var titleDiv = Widget.block([Html.label({},"Title: "),title]);
        var description = Html.textarea({name:'description',style: {width: '250px'}});
        var descDiv = Widget.block([Widget.block(Html.label({},"Description: ")),description]);
        var buttonDiv = Widget.block([
            Widget.button(command(function() {
                self._saveCategory();
            },$T('Save'))),
            Widget.button(command(function() {
                self.close();
            }, $T('Cancel')))
        ]);

        $B(title, self.newMaterial.accessor('title'));
        $B(description, self.newMaterial.accessor('description'));

        var tabControl = new TabWidget([
            [$T("Information"), Widget.block([titleDiv,descDiv])],
            [$T("Access Control") , protectionDiv]], 300,200, 0);

        return this.ExclusivePopup.prototype.draw.call(
            this,
            Html.div({},
                     tabControl.draw(),
                     buttonDiv));
    }
},

     function(args, material, list, title) {
         this.material = material;
         this.materialId = this.material.get('id');
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
         this.ServiceDialog(Indico.Urls.JsonRpcService, 'material.edit', args, title);
     }

    );

type("EditResourceDialog", ["ServiceDialog", "PreLoadHandler"], {
    _preload:
    [
        function(hook){
            var self = this;
            var users = indicoSource('material.resources.listAllowedUsers', self.args);

            users.state.observe(function(state) {
                if (state == SourceState.Loaded) {
                    self.allowedUsers = users.get();
                    hook.set(true);
                }
            });
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
        var nameDiv = Widget.block([Html.label({},$T("Name: ")),name]);
        var description = Html.textarea({name:'description',style: {width: '200px'}});
        var descDiv = Widget.block([Widget.block(Html.label({},$T("Description: "))),description]);
        var url = Html.input('text',{name:'url'});
        var urlDiv = Widget.block([Html.label({},$T("URL: ")),url]);
        var buttonDiv = Widget.block([
            Widget.button(command(function() {
                self._saveResource();
            }, $T('Save'))),
            Widget.button(command(function() {
                self.close();
            }, $T('Cancel')))
        ]);

        $B(name, self.newResource.accessor('name'));
        $B(description, self.newResource.accessor('description'));
        $B(url, self.newResource.accessor('url'));

        self.userList = new UserListField('VeryShortPeopleListDiv',
                                          'PluginPeopleList',
                                          self.allowedUsers,
                                          null,
                                          null,
                                          true, false, false,
                                          userListNothing, userListNothing, userListNothing, true);

        var statusSelection = Widget.select(
            $L({
                0:(self.resource.get('protectedOwner')?$T('Private'):$T('Public'))+' '+$T('(from parent)'),
                1:$T('Private (by itself)'),
                '-1':$T('Public (by itself)')
            })
        );

        statusSelection.observe(function(value) {
            if (value === 0 && self.resource.get('protectedOwner') ||
                value == 1) {
                privateInfoDiv.setStyle('border',null);
            } else {
                IndicoUI.Effect.frame(privateInfoDiv);
            }
        });

        var privateInfoDiv = Html.div(
            {style:{padding:pixels(2)}},
            Html.div({},
                     Html.label({}, $T('Allowed users')),
                     self.userList.draw()));

        var protectionDiv = Html.div(
            {style: {marginTop: pixels(5)}},
            Html.div({},
                     Html.label({},$T("Status: ")),
                     $B(statusSelection,
                        self.newResource.accessor('protection'))), privateInfoDiv);

        var tabControl = new TabWidget([
            [$T("Information"), Widget.block([nameDiv,this.resource.type=='stored'?[]:urlDiv,descDiv])],
            [$T("Access Control")   , protectionDiv]], 300,200, 0);
        tabControl.options = $L([$T("Information"), $T("Access Control")]);
        tabControl.selected.set($T("Information"));

        return this.ExclusivePopup.prototype.draw.call(
            this,
            Html.div({}, tabControl.draw(), buttonDiv));
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

         this.ServiceDialog(Indico.Urls.JsonRpcService, 'material.resources.edit', args, title);
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

            return Html.div(
                "resourceContainer",
                Html.div({style: {'float':'left'}},
                         IndicoUI.Widgets.Generic.remoteIcon(info.get('fileType'))),
                Html.div({style:{'float': 'left'}},list)
            );
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

}, function(resources, matParams) {

    this.matParams = matParams;
    this.resources = resources;

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

type("MaterialListWidget", ["RemoteWidget", "ListWidget"], {

    _drawItem: function(pair) {

        var self = this;

        var material = pair.get();
        var args = clone(self.args);
        var materialId = pair.key;
        args.materialId = materialId;

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

        var matWidget = new ResourceListWidget(material.get('resources'), args);

        // check whenever a material gets empty (no resources) and delete it
        material.get('resources').observe(
            function(event, element) {
                if (event == 'itemRemoved' &&
                    material.get('resources').length.get() == 1) {
                    self.set(materialId, null);
                }
            });

        var matWidgetDiv = matWidget.draw();

        var item = [
            IndicoUI.Buttons.arrowExpandIcon(matWidgetDiv, true),
            $B(Html.span({}),material.accessor('title')),
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


            }
        });
    },

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
                                          function(info) {
                                              if (self.get(info.material)) {
                                                  self.get(info.material).get('resources').append(watchize(info));
                                              } else {
                                                  self._loadMaterial(info.material);
                                              }
                                          });
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

     }
    );

type("MaterialEditorDialog", ["ExclusivePopup"], {
    draw: function() {
        var self = this;
        var changes = 0;

        var args = {
            'categId': intToStr(this.categId),
            'confId': intToStr(this.confId),
            'sessionId': intToStr(this.sessId),
            'contribId': intToStr(this.contId),
            'subContId': intToStr(this.subContId)
        };

        // Remove null parameters
        each(args, function(value, key) {
            if (value === null) {
                delete args[key];
            }
        });

        var mlist = new MaterialListWidget(args, this.types, this.uploadAction, this.width, this.height);

        return this.ExclusivePopup.prototype.draw.call(
            this,
            Html.div({style: {width: pixels(this.width),
                              height: pixels(this.height+50)}},
                     mlist.draw(),
                     Widget.button(command(function() {
                         self.close();
                         window.location.reload(true);
                     }, $T("Close")))));
    }
},

     function(confId, sessId, contId, subContId, types, uploadAction, title, width, height, refresh) {
         this.confId = confId;
         this.sessId = sessId;
         this.contId = contId;
         this.subContId = subContId;
         this.types = types;
         this.uploadAction = uploadAction;
         this.width = width;
         this.height = height;
         this.refresh = refresh;
         this.ExclusivePopup(title);
     });

IndicoUI.Dialogs.Material = {

    add: function(args, list, types, uploadAction, onUpload) {
        var dialog = new AddMaterialDialog(args, list, types, uploadAction, onUpload);
        dialog.open();
    },
    editMaterial: function(args, material, list) {
        var dialog = new EditMaterialDialog(args, material, list, $T("Edit Material"));
        dialog.execute();
    },

    editResource: function(args, material, resource, domItem, appender) {
        var dialog = new EditResourceDialog(args, material, resource, domItem, appender, $T("Edit Resource"));
        dialog.execute();
    },

    editor: function(confId, sessId, contId, subContId, types, uploadAction, refresh) {
        var dialog = new MaterialEditorDialog(confId, sessId, contId, subContId, types, uploadAction, $T("Edit Materials"), 400, 300, refresh);
        dialog.open();
    }
};
