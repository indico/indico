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

type("PreLoadHandler", [],
     {
         execute: function() {

             var self = this;

             if (this.counter === 0) {
                 this.process();
             } else {
                 $L(this.actionList).each(function(preloadItem) {

                     var hook = new WatchValue();
                     hook.set(false);
                     hook.observe(function(value){
                         if (value) {
                             bind.detach(hook);
                             self.counter--;

                             if (self.counter === 0) {
                                 self.process();
                             }
                         }
                     });

                     if (preloadItem.PreLoadAction) {
                         preloadItem.run(hook);
                     } else {
                         preloadItem.call(self, hook);
                     }
                 });
             }
         }
     },
     function(list, process) {
         this.actionList = list;
         this.counter = list.length;
         this.process = process;
     }
    );


type("ProgressDialog",["ExclusivePopup"],
     {
         draw: function() {
             return this.ExclusivePopup.prototype.draw.call(
                 this,
                 $('<div class="loadingPopup"/>').append($('<div class="text"/>').html(this.text)),
                 {background: '#424242', border: 'none', padding: '20px', overflow: 'visible'},
                 {background: '#424242', border: 'none', padding: '1px', overflow: 'auto', display:"inline"}
             );
         }
     },
     function(text) {
         if (text === undefined) {
             this.text = $T('Loading...');
         } else {
             this.text = text;
         }
         this.ExclusivePopup();
     }
    );

IndicoUI.Dialogs = {};
