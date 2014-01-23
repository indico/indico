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

type("DebugWindow", [],
     {
         buildDialog : function() {

             this.debugInfo = Html.textarea({style:
                                             {width: '100%',
                                              height: '100%',
                                              background: 'red'}},
                                            '');

             return Html.div({style: {border: '1px dashed black',
                                      opacity: 0.7,
                                      position: 'fixed',
                                      width: '100%',
                                      bottom: '0px',
                                      height: '100px',
                                      left: '0px'
                                     }}, this.debugInfo);
         },
         addText: function(text) {
             this.debugInfo.set(this.debugInfo.get() + text + '\n');
         }
     },
     function() {
         $E(document.body).append(this.buildDialog());
     }
    );

var debugWindow = null;

function createDebugWindow() {
    debugWindow = new DebugWindow();
}

function debug(text){
    if (debugWindow) {
        debugWindow.addText(text);
    }
}

type("DebugObjectBox", [],
     {
         buildDialog : function(obj) {

             var list = $B(Html.ul({}), obj,
                 function(item) {
                     return Html.li({}, item.key + ': ', $B(Html.input('text'), item));
                 });


             return $B(Html.div({style: {border: '1px dashed black',
                                         opacity: 0.7,
                                         position: 'fixed',
                                         width: '300px',
                                         top: pixels(this.y),
                                         height: '100px',
                                         left: pixels(this.x),
                                         background: 'green'
                                        }}), list);
         }

     },
     function(obj, x, y) {
         this.x = x;
         this.y = y;

         $E(document.body).append(this.buildDialog(obj));
     }
    );

function debugObjectBox(obj, x, y) {
    new DebugObjectBox(obj, x, y);
}
