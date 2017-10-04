/**
 * Remote
 * @author Tom
 */

/**
 * Returns a JSON-RPC value source.
 * @param {String} url
 * @param {String} method
 * @param {Object} [params]
 * @param {Object} [def]
 * @return {WatchAccessor} value
 */
function jsonRpcValue(url, method, params, def, dontStart, callback) {
    // not an object for url... curry
    var self = new Source();
    var object = mixWatchGetters(self, ["state", "error"]);
    object.set("data", def);
    mixinInstance(self, object.accessor("data"), WatchAccessor);

    function process(result, error) {
        if (exists(error)) {
            object.update({
                state: SourceState.Error,
                error: error
            });
        } else {
            object.update({
                state: SourceState.Loaded,
                data: result,
                error: null
            });
        }

        if (callback) {
            callback();
        }
    }

    self.set = function(value) {
        var old = self.get();
        object.update({
            state: SourceState.Committing,
            error: null
        });
        jsonRpcCommit(url, method, params, value, process);
        return old;
    };
    self.refresh = function() {
        object.update({
            state: SourceState.Loading,
            error: null
        });
        return jsonRpc(url, method, params, process);
    };
    if (!dontStart) {
        self.refresh();
    }
    return self;
}

/**
 * Commits the value over JSON-RPC and passes a result to the handler. Returns XMLHttpRequest object.
 * @param {String} url
 * @param {String} method
 * @param {Object} params
 * @param {Object} value
 * @param {Function} handler
 * @return {XMLHttpRequest} request
 */
function jsonRpcCommit(url, method, params, value, handler) {
        var args;
        if (!exists(params)) {
                args = value;
        } else if (isArray(params)) {
                args = $A(params);
                args.push(value);
        } else if (isObject(params)) {
                args = clone(params);
                args.value = value;
        } else {
                args = value;
        }
        return jsonRpc(url, method, args, handler);
}

/**
 * Invokes the method with the params over JSON-RPC and passes a result to the handler.
 * @param {String} url
 * @param {String} method
 * @param {Object} params
 * @param {Function} handler
 * @return {XMLHttpRequest} request
 */
function jsonRpc(url, method, params, handler) {
    url = build_url(url, {_method: method});  // add method to query string to get better logs
    $.ajax({
        url: url,
        method: 'POST',
        data: Json.write({
            origin: location.href,
            method: method,
            params: params
        }),
        dataType: 'json',
        contentType: 'application/json',
        error: function(xhr) {
            // we don't call handleAjaxError here - the legacy code using
            // this function is already doing it
            var error;
            try {
                error = JSON.parse(xhr.responseText).error;
            } catch (e) {
                error = {
                    title: $T.gettext('Something went wrong'),
                    message: '{0} ({1})'.format(data.statusText.toLowerCase(), data.status),
                    suggest_login: false,
                    report_url: null
                };
            }
            handler(null, error);
        },
        success: function(data) {
            handler(data.result, null);
        }
    });
}
