// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

type(
  'BrowserHistoryBroker',
  [],
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
      this.currentHash = '#' + hash;
    },
  },
  function() {
    this.listeners = [];

    // keep the hash that is in use
    this.currentHash = window.location.hash;

    var self = this;

    // function that gets executed each time the hash changes
    var checkHashChanged = function() {
      if (self.currentHash != window.location.hash) {
        each(self.listeners, function(listener) {
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
  }
);
