/**
 * Remote
 * @author Tom
 */

/**
 * Ready state enumeration.
 */
var ReadyState = new Enum("Uninitialized", "Loading", "Loaded", "Interactive", "Complete");

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

                        if(callback) {
                            callback();
                        }
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
 * Invokes the method with the params over JSON-RPC and passes a result to the handler. Returns XMLHttpRequest object.
 * @param {String} url
 * @param {String} method
 * @param {Object} params
 * @param {Function} handler
 * @return {XMLHttpRequest} request
 */
function jsonRpc(url, method, params, handler) {
        url = build_url(url, {_method: method});  // add method to query string to get better logs
        return jsonRequest(url, {
                version: "1.1",
                origin: location.href,
                method: method,
                params: params
        }, function(response, error) {
                if (exists(error)) {
                        handler(response, "SERVER: " + error);
                } else {
                        handler(response.result, response.error);
                }
        });
}

/**
 * Sends the value as JSON and passes a result to the handler. Returns XMLHttpRequest object.
 * @param {String} url
 * @param {Object} value
 * @param {Function} handler
 * @return {XMLHttpRequest} request
 */
function jsonRequest(url, value, handler) {
        return webRequest(url, "application/json", Json.write(value), function(result, error) {
                handler(exists(result) ? JSON.parse(result) : result, error);
        });
}


/**
 * Sends the body to the url and passes a result to the handler. Returns XMLHttpRequest object.
 * @param {String} url
 * @param {String} contentType
 * @param {String} body
 * @param {Function} handler
 * @return {XMLHttpRequest} request
 */
function webRequest(url, contentType, body, handler) {
        var token = $('#csrf-token').attr('content');
        var transport = new XMLHttpRequest();
        try {
                transport.open("POST", url, true);
                transport.setRequestHeader("Accept", "text/javascript, text/html, application/xml, text/xml, application/json, */*");
                transport.setRequestHeader("Content-Type", contentType);
                if (token) {
                        transport.setRequestHeader("X-CSRF-Token", token);
                }
                transport.onreadystatechange = function() {
                        if (transport.readyState != ReadyState.Complete) {
                                return;
                        }
                        delete transport.onreadystatechange;
                        var status = transport.status;
                        if (status >= 200 && status < 300) {
                                handler(transport.responseText, null);
                        } else {
                                handler(transport.responseText, [status, transport.statusText]);
                        }
                };
                transport.send(body);
        } catch (e) {
                handler(null, e);
        }
    return function() { return transport.abort(); };
}
