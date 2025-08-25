// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

(function(global) {
  // rule-based url building is based on werkzeug.contrib.jsrouting

  function BuildError(message, ...rest) {
    let argString;
    if (rest.length) {
      argString = JSON.stringify(rest);
      argString = argString.substring(1, argString.length - 1);
    }
    this.name = 'BuildError';
    this.message = message + (argString ? `: ${argString}` : '');
    // remove the following when http://code.google.com/p/chromium/issues/detail?id=228909 is fixed
    const err = new Error(this.message);
    err.name = this.name;
    return err;
  }
  BuildError.prototype = new Error();
  BuildError.prototype.constructor = BuildError;

  const converterFuncs = {
    // Put any converter functions for custom URL converters here. The key is the converter's python class name.
    // If there is no function, encodeURIComponent is used - so there's no need to put default converters here!
    ListConverter(value) {
      if (_.isArray(value)) {
        value = value.join('-');
      }
      return encodeURIComponent(value);
    },
  };

  function splitObj(obj) {
    // Splits an object into keys and values (and the object itself for convenience)
    const names = [];
    const values = [];
    for (const name in obj) {
      names.push(name);
      values.push(obj[name]);
    }
    return {names, values, original: obj};
  }

  function suitable(rule, args) {
    // Checks if a rule is suitable for the given arguments
    const defaultArgs = splitObj(rule.defaults || {});
    const diffArgNames = _.difference(rule.args, defaultArgs.names);

    // If a rule arg that has no default value is missing, the rule is not suitable
    for (let i = 0; i < diffArgNames.length; i++) {
      if (!args.names.includes(diffArgNames[i])) {
        return false;
      }
    }

    if (_.difference(rule.args, args.names).length === 0) {
      if (!rule.defaults) {
        return true;
      }
      // If a default argument is provided with a different value, the rule is not suitable
      for (let i = 0; i < defaultArgs.names.length; i++) {
        const key = defaultArgs.names[i];
        const value = defaultArgs.values[i];
        if (value !== args.original[key]) {
          return false;
        }
      }
    }

    return true;
  }

  function build(rule, args) {
    let tmp = [];
    const processed = rule.args.slice();
    for (let i = 0; i < rule.trace.length; i++) {
      const part = rule.trace[i];
      if (part.is_dynamic) {
        const converter = converterFuncs[rule.converters[part.data]] || encodeURIComponent;
        const value = converter(args.original[part.data]);
        if (value === null) {
          return null;
        }
        tmp.push(value);
        processed.push(part.name);
      } else {
        tmp.push(part.data);
      }
    }
    tmp = tmp.join('');
    const pipe = tmp.indexOf('|');
    // if we had subdomain routes, the subdomain would come before the pipe
    const url = tmp.substring(pipe + 1);
    const unprocessed = _.difference(args.names, processed);
    return {url, unprocessed};
  }

  function fixParams(params) {
    const cleanParams = {};
    for (const key in params) {
      let value = params[key];
      if (value === '') {
        continue;
      }
      if (value === undefined || value === null) {
        // convert them to a string
        value = `${value}`;
      }
      if (!_.isObject(value) || _.isArray(value)) {
        cleanParams[key] = value;
      }
    }
    return cleanParams;
  }

  // eslint-disable-next-line camelcase
  function build_url(template, params, fragment) {
    let qsParams, url;

    params = fixParams(params);

    if (typeof template === 'string') {
      url = template;
      qsParams = params || {};
    } else if (template.type === 'flask_rules') {
      const args = splitObj(params || {});
      for (let i = 0; i < template.rules.length; i++) {
        const rule = template.rules[i];
        if (suitable(rule, args)) {
          const res = build(rule, args);
          if (res === null) {
            continue;
          }
          url = res.url;
          qsParams = _.pick(params, res.unprocessed);
          break;
        }
      }

      if (!url) {
        throw new BuildError('Could not build an URL', template.endpoint, params);
      }

      if ($('html').data('static-site')) {
        // See url_to_static_filename() in modules/events/static/util.py
        url = url.replace(/^\/event\/\d+/, '');
        if (url.indexOf('static/') === 0) {
          url = url.substring(7);
        }
        url = url.replace(/^\/+/, '').replace(/\/$/, '').replace(/\//g, '--');
        if (!url.match(/.*\.([^/]+)$/)) {
          url += '.html';
        }
      } else {
        url = Indico.Urls.BasePath + url;
      }
    } else {
      throw new BuildError('Invalid URL template', template);
    }

    if (!$('html').data('static-site')) {
      const qs = $.param(qsParams, true);
      if (qs) {
        url += (url.includes('?') ? '&' : '?') + qs;
      }
      if (fragment) {
        url += `#${fragment.replace(/^#/, '')}`;
      }
    }
    return url;
  }

  global.BuildError = BuildError;
  global.build_url = build_url; // eslint-disable-line camelcase
})(window);
