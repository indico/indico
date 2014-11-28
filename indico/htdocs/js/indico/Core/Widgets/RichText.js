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

var executeOnload = false;
var __globalEditorTable = {};
var languages = {'en_GB' : 'en', 'fr_FR' : 'fr'};
var userLanguage = 'en_GB';

/*jsonRpc(Indico.Urls.JsonRpcService, "user.session.language.get",{}, function(result, error)
        {
            if (!error)
                userLanguage = result;
            else
                userLanguage = 'en_GB';
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
                     self.height);
             },5);
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
         },

         onChange: function(callback) {
             this.getEditor().on('change', callback);
         },

         afterPaste: function(callback) {
            this.getEditor().on('afterPaste', callback);
         }

     },
     function(width, height) {
         this.onLoadList = new WatchList();
         this.callbacks = new WatchList();
         this.width = width;
         this.height = height;

         this.divId = Html.generateId();
     });

type("ParsedRichTextEditor", ["RichTextEditor"],
        {
            clean: function() {
                    if (this.getEditor() && this.getEditor().getData) {
                        return cleanText(this.getEditor().getData(), this)
                    } else {
                        return false;
                    }
            }
        },

        function(width, height, sanitizationLevel) {
            this.RichTextEditor(width, height);
            this.sanitizationLevel = sanitizationLevel?sanitizationLevel:2;
        });


type("RichTextWidget", ["IWidget", "Accessor"],
     {
         draw: function() {
             this.richDiv.append(this.rich.draw());
             return Html.div({},
                             this.plain.draw(),
                             this.richDiv,
                             this.hideSwitchLink?null:Widget.link(this.switchLink));
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
                 if ((Util.Validation.isHtml(value)?'rich':'plain') != this.selected.get()) {
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

         postDraw: function() {
             this.rich.postDraw();
         },

         destroy: function() {
             this.rich.destroy();
         },

         onChange: function(callback) {
             this.plain.onChange(callback);
             if(this.loaded){
                 this.rich.onChange(callback);
             }
         }
     },
     function(width, height, initialText, mode, hideSwitchLink) {

         var textAreaParams = { style: {} };
         textAreaParams.style.width = pixels(width);
         textAreaParams.style.height = pixels(height);

         this.plain = new RealtimeTextArea(textAreaParams);
         this.rich = new RichTextEditor(width, height);
         this.richDiv = Html.div({});
         this.currentText = any(initialText, '');
         this.loaded = false;

         this.selected = new WatchValue();

         this.toPlainFunc = function(sync) {
             self.plain.setStyle('display', 'block');
             self.richDiv.setStyle('display', 'none');
             self.switchLink.set('toRich');
             self.activeAccessor = self.plain;
             self.selected.set('plain');
             if (sync !== false) {
                 self.synchronizePlain();
             }
         };

         this.toRichFunc  = function(sync) {
             self.plain.setStyle('display', 'none');
             self.richDiv.setStyle('display', 'block');
             self.switchLink.set('toPlain');
             self.activeAccessor = self.rich;
             self.selected.set('rich');
             if (sync !== false) {
                 self.synchronizeRich();
             }
         };
         this.hideSwitchLink=any(hideSwitchLink,false);
         var self = this;
         this.switchLink = new Chooser(
             {
                 toPlain: command(
                     self.toPlainFunc,
                     $T("switch to plain text")),
                 toRich: command(
                     self.toRichFunc,
                     $T("switch to rich text"))
            });

         if (exists(mode) && mode=='rich') {
             self.toRichFunc();
         } else if (exists(mode)){
             self.toPlainFunc();
         } else if (Util.Validation.isHtml(self.currentText)) {
             self.toRichFunc();
         } else {
             self.toPlainFunc();
         }

         this.rich.onLoad(function() {
             self.loaded = true;
             self.set(self.currentText, true);
         });

      });


type("ParsedRichTextWidget",['RichTextWidget'],
        {
         clean: function(){
             if(this.activeAccessor == this.rich)
                 return this.rich.clean();
             else if(this.activeAccessor == this.plain)
                 return cleanText(this.plain.get(),this.plain);
         }
        },
        function(width, height, initialText, mode, hideSwitchLink) {
            this.RichTextWidget(width, height, initialText, mode, hideSwitchLink);
            this.rich = new ParsedRichTextEditor(width, height);

            var self = this;

            if (exists(mode) && mode=='rich') {
                self.toRichFunc();
            } else if (exists(mode)){
                self.toPlainFunc();
            } else if (Util.Validation.isHtml(self.currentText)) {
                self.toRichFunc();
            } else {
                self.toPlainFunc();
            }

            this.rich.onLoad(function() {
                self.loaded = true;
                self.set(self.currentText, true);
            });

         });

type("RichTextInlineEditWidget", ["InlineEditWidget"],
        {
            _handleEditMode: function(value) {

                this.description = new RichTextWidget(600, 400, '','rich');
                this.description.set(value);
                return this.description.draw();
            },

            _handleDisplayMode: function(value) {
                var self = this;
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
                    if (value == "" && self.noValueText) {
                        value = '<em>' + self.noValueText + '</em>';
                    }
                    doc.body.innerHTML = '<link href="' + Indico.Urls.Base + '/css/Default.css" type="text/css" rel="stylesheet">' + (Util.Validation.isHtml(value)?value:escapeHTML(value));
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
        function(method, attributes, initValue, width, height, noValueText) {
            this.width = width ? width:600;
            this.height = height ? height:100;
            this.noValueText = noValueText;
            this.InlineEditWidget(method, attributes, initValue);
        });


type("ParsedRichTextInlineEditWidget", ["RichTextInlineEditWidget"],
        {
            _handleEditMode: function(value) {

                this.description = new ParsedRichTextWidget(600, 400, '', 'rich');
                this.description.set(value);
                return this.description.draw();
            },

            _handleContentEdit: function() {
                var self = this;
                this.saveButton = Widget.button(command(function() {
                        if (self._verifyInput() && self.description.clean()){
                            self._savedValue = self._getNewValue();
                            self.source.set(self._savedValue);
                        }
                }, 'Save'));

                var editButtons = Html.div({},
                    this.saveButton,
                    Widget.button(command(function() {
                        // back to the start
                        self.setMode('display');
                    }, 'Cancel')));

                // there are two possible states for the "switch" area
                return this._buildFrame(self._handleEditMode(self.value),
                                        editButtons);

            }
        },
        function(method, attributes, initValue, width, height, noValueText) {
            this.RichTextInlineEditWidget(method, attributes, initValue, width, height, noValueText);
        });


function initializeEditor( wrapper, editorId, text, callbacks, width, height ){
    // "wrapper" is the actual Indico API object that represents an editor

    try {

        CKEDITOR.replace(editorId, {language : userLanguage, width : width, height : height - 75});
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
        },5);
    }

}

function cleanText(text, target){
    try{
        var self = target;
        var killProgress = IndicoUI.Dialogs.Util.progress($T('Saving...'));
        var parsingResult = escapeHarmfulHTML(text);
        if( parsingResult[1] > 0) {

            var cleaningFunction = function(confirmed) {
                if(confirmed) {
                    self.set(parsingResult[0]);
                }
            };

            var security;
            switch(parsingResult[1]) {
                case 1:
                    security = "HTML";
                    break;
                case 2:
                    security = "HTML and scripts";
                    break;
                default:
                    security = "code";
                    break;
            }
            killProgress();

            // List of errors
            var showErrorList = Html.span("fakeLink", $T("here"));
            showErrorList.observeClick(function(){
                var ul = Html.ul({id: '',style:{listStyle: 'circle', marginLeft:'-25px'}});
                each(parsingResult[2], function(value){
                    ul.append(Html.li('', value));
                });
                var popupErrorList = new AlertPopup('List of forbidden elements', ul.dom);
                popupErrorList.open();
            });

            // Warning
            var popup = new ConfirmPopup($T("Warning!"), Html.div({style: {width:pixels(300), textAlign:'justify'}},
                                         $T("Your data contains some potentially harmful " + security +
                                         ", which cannot be stored in the database. Use the automatic Indico cleaner or clean the text manually (see the list of forbidden elements that you are using "), showErrorList, ")."),
                                         cleaningFunction, 'Clean automatically', 'Clean manually');
            popup.open();
            return false;
        }
        else{
            killProgress();
            return true;
        }
    } catch(error){
        if(killProgress)
            killProgress();
        if(typeof error == "string" && error.indexOf("Parse Error") != -1){
            var popup = new WarningPopup($T("Warning!"), $T("Format of your data is invalid. Please check the syntax."));
            popup.open();
            return false;
        }
        else
            throw error;
    }
}
