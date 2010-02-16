var executeOnload = false;
var __globalEditorTable = {};

type("RichTextEditor", ["IWidget", "Accessor"],
     {
         draw: function() {
             this.div = Html.div({'id': this.divId});

             this.postDraw();

             return this.div;
         },

         get: function() {
             if (this.editor && this.editor.GetData) {
                 return this.editor.GetData();
             } else {
                 return '';
             }
         },

         postDraw: function() {
             this.div.set('');

             this.div.dom.innerHTML = this.editor.CreateHtml();

             var self = this;

             this.onLoadFunc = function() {

                 if (self.text) {
                     self.set(self.text);
                 }

                 each(self.onLoadList,
                      function(callback) {
                          callback();
                      });

                 self.editor.Events.AttachEvent( 'OnSelectionChange',
                                                 function() {
                                                     if (!self.observing) {
                                                         self.startObserving();
                                                     }
                                                 } ) ;
             };

             if (this.editor && this.editor.SetData) {
                 this.onLoadFunc();
             } else {
                 executeOnLoad = true;
             }

         },

         set: function(text) {
             var self = this;

             if (this.editor && this.editor.SetData) {
                 this.editor.SetData(text);
                 this.editor.ResetIsDirty();
             } else {
                 this.text = text;
             }
         },

         observe: function(callback) {
             this.callbacks.append(callback);
         },

         startObserving: function() {
             this.observing = true;
             this.editor.ResetIsDirty();
             if (this.callbacks.length.get() > 0) {
                 this.fckTimer = window.setInterval("FCKeditor_OnChange('"+this.divId+"')",2000);
             }
         },

         unbind: function() {
             this.observing = false;
             this.callbacks.clear();
             window.clearInterval(this.fckTimer);
         },

         onLoad: function(callback) {
             this.onLoadList.append(callback);
         },

         destroy: function() {
             this.unbind();
             delete __globalEditorTable[this.divId];
         }

     },
     function(width, height, textAreaParams, toolbarSet) {
         this.onLoadList = new WatchList();
         this.callbacks = new WatchList();
         this.width = width;
         this.height = Browser.IE?height-75:height;
         this.params = exists(textAreaParams)?textAreaParams:{};

         this.divId = Html.generateId();

         this.editor = new FCKeditor(this.divId) ;
         this.editor.Width = width;
         this.editor.Height = height;
         this.editor.ToolbarSet = toolbarSet || 'IndicoMinimal' ;
         this.editor.BasePath = ScriptRoot + "fckeditor/" ;
         this.editor.Config.CustomConfigurationsPath = ScriptRoot + "fckeditor/indicoconfig.js"  ;
         __globalEditorTable[this.divId] = this;
         var self = this;

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
     function(width, height, textAreaParams, initialText, mode, toolbarSet) {

         if (!textAreaParams.style) {
             textAreaParams.style = {};
         }
         textAreaParams.style.width = pixels(width);
         textAreaParams.style.height = pixels(height);

         this.plain = new RealtimeTextArea(textAreaParams);
         this.rich = new RichTextEditor(width, height, textAreaParams, toolbarSet);
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

                this.description = new RichTextWidget(600, 400,{},'','rich','IndicoMinimal');
                this.description.set(value);
                return this.description.draw();
            },

            _handleDisplayMode: function(value) {

                var iframeId = "descFrame";
                var iframe = Html.iframe({id: iframeId,name: iframeId, style:{width: pixels(600),
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

            _getNewValue: function() {
                return this.description.get();
            }
        },
        function(method, attributes, initValue) {
            this.InlineEditWidget(method, attributes, initValue);
        });



function FCKeditor_OnComplete( editorInstance )
{
    __globalEditorTable[editorInstance.Name].editor = editorInstance;
    __globalEditorTable[editorInstance.Name].onLoadFunc();
}

function FCKeditor_OnChange( id ) {
    var value = __globalEditorTable[id];

    if(value.editor.IsDirty()) {
        each(value.callbacks, function(func) {
            func();
        })
        value.editor.ResetIsDirty();
    }

}