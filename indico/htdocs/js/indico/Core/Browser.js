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

type("BrowserHistoryBroker", [],
     // handle the interaction with browser history and hashes
     {
         addListener: function(listener) {
             /* add a listener that will be notified each time
                the hash changes */

             this.listeners.push(listener);

             // the listener needs to know the broker,
             // so that it can register deliberate actions
             // (which are not back nor forward)
             listener.registerHistoryBroker(this);
         },

         setUserAction: function(hash) {

             /* set an action that was performed by the user:
                that means an anchor update */

             window.location.hash = hash;
             this.currentHash = '#'+hash;
         }
     },
     function() {
         this.listeners = [];

         // keep the hash that is in use
         this.currentHash = window.location.hash;

         var self = this;

         // function that gets executed each time the hash changes
         var checkHashChanged = function() {

             if (self.currentHash != window.location.hash) {
                 each(self.listeners,
                      function(listener) {
                          listener.notifyHistoryChange(window.location.hash);
                      });
                 self.currentHash = window.location.hash;
             }
         };

         // onhashchange is nice (IE8, Chrome, FF 3.6, HTML5?)
         if (document.body.onhashchange !== undefined) {
             $E(document.body).observeEvent('hashchange', checkHashChanged);
         } else {
             // for older browsers, use setInterval()
             setInterval(checkHashChanged, 500);
         }

         // btw, IE7 not supported

     });
