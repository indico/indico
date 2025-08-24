// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * If the template does not exist returns pass,
 * if the template is a function returns the template,
 * otherwise returns a function that
 * returns a property of an input value determined by the template.
 * @param {Function, String} [template]
 * @return {Function}
 */
function obtainTemplate(template) {
  if (!exists(template)) {
    return pass;
  }
  if (isFunction(template)) {
    return template;
  }
  return function(value) {
    return exists(value) ? value[template] : null;
  };
}

/**
 * If the template does not exist returns the setter,
 * if the template is a function returns a function
 * that applies the template on an input value and invokes the setter,
 * otherwise returns a function that invokes the setter
 * with a propertyof an input value determined by the template.
 * @param {Function, String} template
 * @param {Function} setter
 * @return {Function}
 */
function templatedSetter(template, setter) {
  if (!exists(template)) {
    return setter;
  }
  if (isFunction(template)) {
    return function(value) {
      setter(template(value));
    };
  }
  return function(value) {
    setter(exists(value) ? value[template] : null);
  };
}

/**
 * Returns a template that returns a case according an input value.
 * @param {Dictionary|Object} values
 * @return {Function}
 */
function splitter(values) {
  if (values.Lookup) {
    return function(key) {
      return values.get(key);
    };
  } else {
    return function(key) {
      return values[key];
    };
  }
}

/**
 * Selects a value from the options.
 */
type(
  'Chooser',
  ['WatchAccessor'],
  {
    /**
     * Returns a setter that selects a value from the options according the key.
     * @param {String} key
     * @return {Function} setter
     */
    option: function(key) {
      var self = this;
      return function() {
        self.set(key);
      };
    },
  },
  /**
   * Initializes chooser with the options.
   * @param {Object} options
   */
  function(options) {
    var value = $V();
    mixinInstance(this, value, WatchGetter);
    this.set = templatedSetter(splitter(options), value.set);
  }
);
