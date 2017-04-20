/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
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

var languages = {'en_GB' : 'en', 'fr_FR' : 'fr'};
var userLanguage = 'en_GB';


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
                     self.simple,
                     self.simpleAllowImages);
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
     function(width, height, simple, simpleAllowImages) {
         this.onLoadList = new WatchList();
         this.callbacks = new WatchList();
         this.width = width;
         this.height = height;
         this.simple = simple;
         this.simpleAllowImages = simpleAllowImages;

         this.divId = Html.generateId();
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


function initializeEditor( wrapper, editorId, text, callbacks, width, height, simple, simpleAllowImages){
    // "wrapper" is the actual Indico API object that represents an editor

    try {
        var config = {
            customConfig: false,
            language: userLanguage,
            entities: false,
            width: width,
            height: height - 75,
            blockedKeystrokes: [9 /* TAB */, CKEDITOR.SHIFT + 9  /* SHIFT + TAB */],
            keystrokes: [[CKEDITOR.CTRL + 75 /* CTRL + K */, 'link']],
            removeButtons: '',
            disableNativeSpellChecker: false,
            font_names: [
                'Sans Serif/"Liberation Sans", sans-serif',
                'Serif/"Liberation Serif", serif',
                'Monospace/"Liberation Mono", monospace'
            ].join(';'),
            contentsCss: _.union(CKEDITOR.getUrl('contents.css'), Indico.Urls.FontSassBundle),
            toolbarGroups: [
                {name: 'clipboard', groups: ['clipboard', 'undo']},
                {name: 'editing', groups: ['find', 'selection', 'spellchecker']},
                {name: 'links'},
                {name: 'insert'},
                {name: 'forms'},
                {name: 'tools'},
                {name: 'document', groups: ['mode', 'document', 'doctools']},
                {name: 'others'},
                '/',
                {name: 'basicstyles', groups: ['basicstyles', 'cleanup']},
                {name: 'paragraph', groups: ['list', 'indent', 'blocks', 'align', 'bidi']},
                {name: 'styles'},
                {name: 'colors'},
                {name: 'about'}
            ],
            format_tags: 'p;h1;h2;h3;pre',
            removeDialogTabs: 'image:advanced;link:advanced'
        };

        if (simple) {
            config.toolbar = [
                {name: 'clipboard', items: ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo']},
                {name: 'editing', items: ['Find', 'Replace']},
                {name: 'links', items: ['Link', 'Unlink', 'Anchor']},
                {name: 'insert', items: simpleAllowImages ? ['Image', 'HorizontalRule'] : ['HorizontalRule']},
                {name: 'document', items: ['Source']},
                {name: 'basicstyles', items: ['Bold', 'Italic', 'Underline', 'Strike', '-', 'RemoveFormat']},
                {name: 'paragraph', items: ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent']},
                {name: 'styles', items: ['Format']},
                {name: 'colors', items: ['TextColor']},
                {name: 'tables', items: ['Table']},
                {name: 'tools', items: ['Maximize']}
            ];
        }

        CKEDITOR.replace(editorId, config);
        var cki = CKEDITOR.instances[editorId];

        cki.setData(text);
        cki.on ('key', function(e)
                {
                    each(callbacks, function(func) {
                        func();
                    });
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
