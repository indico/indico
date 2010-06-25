var executeOnload = false;
var __globalEditorTable = {};
var languages = {'en_US' : 'en', 'fr_FR' : 'fr'};
var userLanguage;

jsonRpc(Indico.Urls.JsonRpcService, "user.session.language.get",{}, function(result, error)
        {
            if (!error)
                userLanguage = result;
            else
                userLanguage = 'en_US';
        });

type("RichTextWidget", ["IWidget", "Accessor"],
     {
         draw: function() {
             selfReference = this;
             this.div = Html.div({'id': 'text' + this.divId, style : {height: this.height + 75, width: this.width}});
             window.setTimeout("initializeEditor('text' + selfReference.divId , selfReference.text , selfReference.callbacks, selfReference.width, selfReference.height, selfReference.toolbarSet)",50);
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

type("RichTextInlineEditWidget", ["InlineEditWidget"],
        {
            _handleEditMode: function(value) {

                this.description = new RichTextWidget(600, 400,'IndicoMinimal');
                this.description.set(value);
                return this.description.draw();
            },

            _handleDisplayMode: function(value) {
                var iframeId = "descFrame" + Html.generateId();
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
        function(method, attributes, initValue, width, height) {
            this.width = width ? width:600;
            this.height = height ? height:100;
            this.InlineEditWidget(method, attributes, initValue);
        });


function initializeEditor( editorId, text, callbacks, width, height, toolbarSet ){
    try {

        CKEDITOR.replace(editorId, {language : userLanguage, width : width, height : height - 75, 'toolbar': toolbarSet});
        CKEDITOR.instances[editorId].setData(text);
        CKEDITOR.instances[editorId].on ('key', function(e)
                {
                    each(callbacks, function(func) {
                        func();
                    })
                });
    }
    catch (error) {
        window.setTimeout("initializeEditor(editorId, text, callbacks, width, height)",50);
    }

}