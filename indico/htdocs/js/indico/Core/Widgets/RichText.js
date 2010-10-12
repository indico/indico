var executeOnload = false;
var __globalEditorTable = {};
var languages = {'en_US' : 'en', 'fr_FR' : 'fr'};
var userLanguage = 'en_US';

/*jsonRpc(Indico.Urls.JsonRpcService, "user.session.language.get",{}, function(result, error)
        {
            if (!error)
                userLanguage = result;
            else
                userLanguage = 'en_US';
        });*/

type("RichTextEditor", ["IWidget", "Accessor"],
     {
         draw: function() {
             var self = this;
             this.div = Html.div({'id': 'text' + this.divId, style : {height: this.height + 75, width: this.width}});

             setTimeout(function() {
                 initializeEditor(
                     self,
                     'text' + self.divId ,
                     self.text ,
                     self.callbacks,
                     self.width,
                     self.height,
                     self.toolbarSet);
             },50);
             return this.div;
         },

         get: function() {
             if (this.getEditor() && this.getEditor().getData) {
                 return this.getEditor().getData();
             } else {
                 return '';
             }
         },

         set: function(text) {
             var self = this;

             if (this.getEditor() && this.getEditor().setData) {
                 this.getEditor().setData(text);
             } else {
                 this.text = text;
             }
         },

         observe: function(callback) {
             this.callbacks.append(callback);
         },

         unbind: function() {
             this.observing = false;
             this.callbacks.clear();
         },

         onLoad: function(callback) {
             this.onLoadList.append(callback);
         },

         destroy: function() {
             this.unbind();
         },

         getEditor: function() {
             return CKEDITOR.instances["text" + this.divId];
         }
     },
     function(width, height, toolbarSet) {
         this.onLoadList = new WatchList();
         this.callbacks = new WatchList();
         this.width = width;
         this.height = height;
         this.toolbarSet = toolbarSet?toolbarSet:'IndicoMinimum';

         this.divId = Html.generateId();
     });

type("RichTextWidget", ["IWidget", "Accessor"],
     {
         draw: function() {
             this.richDiv.append(this.rich.draw());
             return Html.div({},
                             this.plain.draw(),
                             this.richDiv,
                             Widget.link(this.switchLink));
         },

         observe: function(callback) {
            var self = this;

             var observeFunc = function(value) {

                 self.plain.unbind();
                 self.rich.unbind();

                 if (value == 'rich') {
                    self.rich.observe(function() {
                         callback(self.rich);
                     });
                 } else {
                     self.plain.observe(function() {
                         callback(self.plain);
                     });
                 }
             };

             this.selected.observe(observeFunc);
             observeFunc(this.selected.get());
         },

         get: function() {
             return this.activeAccessor.get();
         },

         set: function(value, noDetection) {

             this.currentText = value;

             if (!any(noDetection, false)) {
                 if ((this.isHtml(value)?'rich':'plain') != this.selected.get()) {
                     this.switchLink.get()(false);
                 }
             }

             if (value && (this.loaded || this.selected.get() == 'plain')) {
                 this.activeAccessor.set(value);
             }
         },

         synchronizePlain: function() {
             this.currentText = this.rich.get();
             this.plain.set(this.currentText);
         },

         synchronizeRich: function() {
             this.currentText = this.plain.get();
             this.rich.set(this.currentText);
         },

         isHtml: function(text) {
             if (/<.*>[\s\S]*<\/.*>/.exec(text)) {
                 return true;
             } else {
                 return false;
             }
         },

         postDraw: function() {
             this.rich.postDraw();
         },

         destroy: function() {
             this.rich.destroy();
         }
     },
     function(width, height, initialText, mode, toolbarSet) {

         var textAreaParams = { style: {} };
         textAreaParams.style.width = pixels(width);
         textAreaParams.style.height = pixels(height);

         this.plain = new RealtimeTextArea(textAreaParams);
         this.rich = new RichTextEditor(width, height, toolbarSet);
         this.richDiv = Html.div({});
         this.currentText = any(initialText, '');
         this.loaded = false;

         this.selected = new WatchValue();

         var toPlainFunc = function(sync) {
             self.plain.setStyle('display', 'block');
             self.richDiv.setStyle('display', 'none');
             self.switchLink.set('toRich');
             self.activeAccessor = self.plain;
             self.selected.set('plain');
             if (sync !== false) {
                 self.synchronizePlain();
             }
         };

         var toRichFunc  = function(sync) {
             self.plain.setStyle('display', 'none');
             self.richDiv.setStyle('display', 'block');
             self.switchLink.set('toPlain');
             self.activeAccessor = self.rich;
             self.selected.set('rich');
             if (sync !== false) {
                 self.synchronizeRich();
             }
         };

         var self = this;
         this.switchLink = new Chooser(
             {
                 toPlain: command(
                     toPlainFunc,
                     $T("switch to plain text")),
                 toRich: command(
                     toRichFunc,
                     $T("switch to rich text"))
            });

         if (exists(mode) && mode=='rich') {
             toRichFunc();
         } else if (exists(mode)){
             toPlainFunc();
         } else if (self.isHtml(self.currentText)) {
             toRichFunc();
         } else {
             toPlainFunc();
         }

         this.rich.onLoad(function() {
             self.loaded = true;
             self.set(self.currentText, true);
         });

      });


type("RichTextInlineEditWidget", ["InlineEditWidget"],
        {
            _handleEditMode: function(value) {

                this.description = new RichTextWidget(600, 400,
                                                      '','rich',
                                                      'IndicoMinimal');
                this.description.set(value);
                return this.description.draw();
            },

            _handleDisplayMode: function(value) {
                var iframeId = "descFrame" + Html.generateId();
                var iframe = Html.iframe({id: iframeId,name: iframeId,
                                          style:{width: pixels(600),
                                                 height:pixels(100),
                                                 border: "1px dotted #ECECEC"}});

                var loadFunc = function() {
                    var doc;

                    if (Browser.IE) {
                        doc = document.frames[iframeId].document;
                    } else {
                        doc = $E(iframeId).dom.contentDocument;
                    }
                    if (value == "") {
                        value = '<em>No description</em>';
                    }
                    doc.body.innerHTML = '<link href="css/Default.css" type="text/css" rel="stylesheet">' + value;
                };

                if (Browser.IE) {
                    iframe.dom.onreadystatechange = loadFunc;
                } else {
                    // for normal browsers
                    iframe.observeEvent("load", loadFunc);
                 }

                return iframe;
            },

            _handleBackToEditMode: function() {
                this.description.set(this._savedValue);
            },

            _getNewValue: function() {
                return this.description.get();
            }
        },
        function(method, attributes, initValue, width, height) {
            this.width = width ? width:600;
            this.height = height ? height:100;
            this.InlineEditWidget(method, attributes, initValue);
        });


function initializeEditor( wrapper, editorId, text, callbacks, width, height, toolbarSet ){
    // "wrapper" is the actual Indico API object that represents an editor

    try {

        CKEDITOR.replace(editorId, {language : userLanguage, width : width, height : height - 75, 'toolbar': toolbarSet});

        var cki = CKEDITOR.instances[editorId];

        cki.setData(text);
        cki.on ('key', function(e)
                {
                    each(callbacks, function(func) {
                        func();
                    })
                });

        // process onLoad events for each individual instance (wrapper)
        cki.on ('instanceReady', function(e)
                {
                    each(wrapper.onLoadList, function(callback) {
                                 callback();
                    });

                });

    }
    catch (error) {
        setTimeout(function() {
            initializeEditor(wrapper, editorId, text, callbacks, width, height);
        },50);
    }

}