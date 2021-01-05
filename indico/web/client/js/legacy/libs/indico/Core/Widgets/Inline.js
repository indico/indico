// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

type('InlineWidget', ['IWidget'], {
  _error: function(error) {
    showErrorDialog(error);
  },
});

/*
 * This class implements a widget that interacts directly with the
 * remote server. States are handled, through a callback interface.
 */
type(
  'InlineRemoteWidget',
  ['InlineWidget'],

  {
    _handleError: function(error) {
      this._error(error);
    },

    _handleLoading: function(error) {
      return Html.span({}, 'loading...');
    },

    _handleLoaded: function() {
      // do nothing, overload
    },

    _handleSuccess: function() {
      // do nothing, overload
    },

    _handleBackToEditMode: function() {
      // do nothing, overload
    },

    draw: function() {
      var self = this;

      var content = this._handleContent();

      // if the widget is set to load on startup,
      // the content will be a 'loading' message
      this.wcanvas = Html.div({}, this.loadOnStartup ? this._handleLoading() : content);

      // observe state changes and call
      // the handlers accordingly
      this.source.state.observe(function(state) {
        if (state == SourceState.Error) {
          self._handleError(self.source.error.get());
          self.wcanvas.set(content);
          self.setMode('edit');
          self._handleBackToEditMode();
        } else if (state == SourceState.Loaded) {
          self._handleLoaded(self.source.get());
          self.wcanvas.set(content);
          self.setMode('display');
          self._handleSuccess();
        } else {
          self.wcanvas.set(self._handleLoading());
        }
      });

      return self.wcanvas;
    },
  },
  /*
   * method - remote method
   * attributes - attributes that are passed
   * loadOnStartup - should the widget start loading from the
   * server automatically?
   */
  function(method, attributes, loadOnStartup, callback) {
    loadOnStartup = exists(loadOnStartup) ? loadOnStartup : true;
    this.ready = new WatchValue();
    this.ready.set(false);
    this.loadOnStartup = loadOnStartup;
    this.source = indicoSource(method, attributes, null, !loadOnStartup, callback);
  }
);

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
