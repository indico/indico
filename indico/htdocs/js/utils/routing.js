(function(global) {
    'use strict';
    // rule-based url building is based on werkzeug.contrib.jsrouting

    function BuildError(message) {
        var args = [];
        var arg_str;
        if (arguments.length > 1) {
            arg_str = JSON.stringify(Array.prototype.slice.call(arguments, 1));
            arg_str = arg_str.substring(1, arg_str.length - 1);
        }
        this.name = 'BuildError';
        this.message = message + (arg_str ? ': ' + arg_str : '');
        // remove the following when http://code.google.com/p/chromium/issues/detail?id=228909 is fixed
        var err = new Error(this.message);
        err.name = this.name;
        return err;
    }
    BuildError.prototype = new Error();
    BuildError.prototype.constructor = BuildError;


    function split_obj(obj) {
        // Splits an object into keys and values (and the object itself for convenience)
        var names = [];
        var values = [];
        for (var name in obj) {
            names.push(name);
            values.push(obj[name]);
        }
        return { names: names, values: values, original: obj };
    }

    function suitable(rule, args) {
        // Checks if a rule is suitable for the given arguments
        var default_args = split_obj(rule.defaults || {});
        var diff_arg_names = _.difference(rule.args, default_args.names);
        var i;

        // If a rule arg that has no default value is missing, the rule is not suitable
        for (i = 0; i < diff_arg_names.length; i++) {
            if (!~_.indexOf(args.names, diff_arg_names[i])) {
                return false;
            }
        }

        if (_.difference(rule.args, args.names).length == 0) {
            if (!rule.defaults) {
                return true;
            }
            // If a default argument is provided with a different value, the rule is not suitable
            for (i = 0; i < default_args.names.length; i++) {
                var key = default_args.names[i];
                var value = default_args.values[i];
                if (value != args.original[key]) {
                    return false;
                }
            }
        }

        return true;
    }

    function build(rule, args) {
        var tmp = [];
        var processed = rule.args.slice();
        for (var i = 0; i < rule.trace.length; i++) {
            var part = rule.trace[i];
            if (part.is_dynamic) {
                tmp.push(encodeURIComponent(args.original[part.data]));
                processed.push(part.name);
            }
            else {
                tmp.push(part.data);
            }
        }
        tmp = tmp.join('');
        var pipe = tmp.indexOf('|');
        // if we had subdomain routes, the subdomain would come before the pipe
        var url = tmp.substring(pipe + 1);
        var unprocessed = _.difference(args.names, processed);
        return { url: url, unprocessed: unprocessed };
    }

    function build_url(template, params, fragment) {
        var qsParams, url;

        if (_.contains(params, undefined) || _.contains(params, null)) {
            console.log(params);  // JSON.stringify skips undefined so let's log it here
            throw new BuildError('params contain undefined/null');
        }

        if (typeof template == 'string') {
            url = template;
            qsParams = params || {};
        }
        else if (template.type == 'flask_rules') {
            var args = split_obj(params || {});
            for (var i = 0; i < template.rules.length; i++) {
                var rule = template.rules[i];
                if (suitable(rule, args)) {
                    var res = build(rule, args);
                    url = res.url;
                    qsParams = _.pick(params, res.unprocessed);
                    break;
                }
            }

            if (!url) {
                throw new BuildError('Could not build an URL', template.endpoint, params);
            }

            url = Indico.Urls.Base + url;
        }
        else {
            throw new BuildError('Invalid URL template', template);
        }

        var qs = $.param(qsParams);
        if (qs) {
            url += (~url.indexOf('?') ? '&' : '?') + qs;
        }
        if (fragment) {
            url += '#' + fragment;
        }
        return url;
    }

    global.BuildError = BuildError;
    global.build_url = build_url;
})(window);
