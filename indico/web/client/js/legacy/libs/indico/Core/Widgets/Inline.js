// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

type(
  'RealtimeTextBox',
  ['IWidget', 'WatchAccessor', 'ErrorAware'],
  {
    _setErrorState: function(text) {
      this._stopErrorList = this._setElementErrorState(this.input, text);
    },

    draw: function() {
      this.enableEvent();
      return this.IWidget.prototype.draw.call(this, this.input);
    },
    get: function() {
      if (this.input.dom.disabled) {
        return null;
      } else {
        return this.input.get();
      }
    },
    set: function(value) {
      return this.input.set(value);
    },
    observe: function(observer) {
      this.observers.push(observer);
    },
    observeEvent: function(event, observer) {
      return this.input.observeEvent(event, observer);
    },
    observeOtherKeys: function(observer) {
      this.otherKeyObservers.push(observer);
    },
    unbind: function() {
      bind.detach(this.input);
    },
    disable: function() {
      this.input.dom.disabled = true;
    },
    enable: function() {
      this.input.dom.disabled = false;
      this.enableEvent();
    },
    setStyle: function(prop, value) {
      this.input.setStyle(prop, value);
    },
    notifyChange: function(keyCode, event) {
      var value = true;
      var self = this;

      each(this.observers, function(func) {
        value = value && func(self.get(), keyCode, event);
      });
      return value;
    },
    enableEvent: function() {
      var self = this;

      this.input.observeEvent('keydown', function(event) {
        var keyCode = event.keyCode;
        var value = true;

        if (
          (keyCode < 32 && keyCode != 8) ||
          (keyCode >= 33 && keyCode < 46) ||
          (keyCode >= 112 && keyCode <= 123)
        ) {
          each(self.otherKeyObservers, function(func) {
            value = value && func(self.get(), keyCode, event);
          });
          return value;
        }
        return true;
      });

      // fire onChange event each time there's a new char
      this.input.observeEvent('keyup', function(event) {
        var keyCode = event.keyCode;

        if (
          !(
            (keyCode < 32 && keyCode != 8) ||
            (keyCode >= 33 && keyCode < 46) ||
            (keyCode >= 112 && keyCode <= 123)
          )
        ) {
          var value = self.notifyChange(keyCode, event);
          Dom.Event.dispatch(self.input.dom, 'change');
          return value;
        }
        return true;
      });
    },
  },
  function(args) {
    this.observers = [];
    this.otherKeyObservers = [];
    this.input = Html.input('text', args);
  }
);

type(
  'RealtimeTextArea',
  ['RealtimeTextBox'],
  {
    onChange: function(callback) {
      this.input.observeEvent('change', callback);
    },
  },
  function(args) {
    this.RealtimeTextBox(clone(args));
    this.input = Html.textarea(args);
  }
);

/**
 * Normal text field which is triggering an action when the user actions the ENTER key.
 */
type(
  'EnterObserverTextBox',
  ['IWidget', 'WatchAccessor'],
  {
    draw: function() {
      return this.IWidget.prototype.draw.call(this, this.input);
    },
    get: function() {
      return this.input.get();
    },
    set: function(value) {
      return this.input.set(value);
    },
    observe: function(observer) {
      this.input.observe(observer);
    },
  },
  function(id, args, keyPressAction) {
    var self = this;
    this.input = Html.input(id, args);
    // fire event when ENTER key is pressed
    this.input.observeEvent('keypress', function(event) {
      if (event.keyCode == 13) {
        Dom.Event.dispatch(self.input.dom, 'change');
        return keyPressAction();
      }
      Dom.Event.dispatch(self.input.dom, 'change');
    });
  }
);
