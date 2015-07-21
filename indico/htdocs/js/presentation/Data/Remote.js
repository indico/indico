/**
 * Remote
 * @author Tom
 */

var activeWebRequests = 0;

/**
 * Ready state enumeration.
 */
var ReadyState = new Enum("Uninitialized", "Loading", "Loaded", "Interactive", "Complete");

//function jsonRpcStore(url, method, params) {
//      function commit() {
//
//      }
//
//      var store = {
//              list: function(handler) {
//
//              },
//              fetch: function(key, handler) {
//                      schedule()
//              }
//      };
//
//      return store;
//}

/**
 * Returns a JSON-RPC object source. Argument dontWatch specifies if the changes have not to be commited to the server.
 * @param {String} url
 * @param {String} method
 * @param {Object} [params]
 * @param {Boolean} [dontWatch]
 * @return {WatchObject, Source}
 */
function jsonRpcObject(url, method, params, dontWatch) {
        // not an object for url... curry
        var self = new Source();
        var sourceObject = mixWatchGetters(self, ["state", "error"]);
        var dataObject = new WatchObject();
        mixinInstance(self, dataObject, WatchObject);

        var updating = false;
        var requests = {};
        function commit(key, value) {
                var data = {};
                var empty = true;
                enumerate(requests, function(value, key) {
                        if (value) {
                                data[key] = dataObject.get(key);
                                empty = false;
                        }
                });
                requests = {};
                if (!empty) {
                        jsonRpcCommit(url, method, params, data, process, url);
                }
        }
        function commitKey(key) {
                if (!updating) {
                        requests[key] = true;
                        defer(commit);
                }
        }

        function process(result, error) {
                if (exists(error)) {
                        sourceObject.update({
                                state: SourceState.Error,
                                error: error
                        });
                } else {
                        if (exists(result)) {
                                updating = true;
                                if (!dontWatch) {
                                        enumerate(result, function(value, key) {
                                                dataObject.set(key, watch(watchize(value), curry(commitKey, key)));
                                        });
                                } else {
                                        enumerate(result, function(value, key) {
                                                dataObject.set(key, value);
                                        });
                                }
                                updating = false;
                        }
                        sourceObject.update({
                                state: SourceState.Loaded,
                                error: null
                        });
                }
        }

        dataObject.observe(function(value, key) {
                commitKey(key);
        });
        self.refresh = function() {
                sourceObject.update({
                        state: SourceState.Loading,
                        error: null
                });
                return jsonRpc(url, method, params, process);
        };
        self.refresh();
        return self;
}

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
                handler(exists(result) ? Json.read(result) : result, error);
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
        var transport = Web.transport();
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
                        activeWebRequests--;
                        delete transport.onreadystatechange;
                        var status = transport.status;
                        if (status >= 200 && status < 300) {
                                handler(transport.responseText, null);
                        } else {
                                handler(transport.responseText, [status, transport.statusText]);
                        }
                };
                transport.send(body);
                activeWebRequests++;
        } catch (e) {
                handler(null, e);
        }
    return function() { return transport.abort(); };
}

/**
 * Requests static resource via HTTP GET
 * @param {String} url
 * @param {Function} handler
 * @return {XMLHttpRequest} request
 */
function webGet(url, handler) {
        var transport = Web.transport();
        try {
                transport.open("GET", url, true);
                transport.setRequestHeader("Accept", "text/javascript, text/html, application/xml, text/xml, application/json, */*");
                transport.setRequestHeader("Cache-Control", "max-age=1000000000");
                transport.onreadystatechange = function() {
                        if (transport.readyState != ReadyState.Complete) {
                                return;
                        }
                        transport.onreadystatechange = null;
                        var status = transport.status;
                        if (status >= 200 && status < 300) {
                                handler(transport.responseText, null);
                        } else {
                                handler(transport.responseText, [status, transport.statusText]);
                        }
                };
                transport.send(null);
        } catch (e) {
                handler(null, e);
        }
    return function() { return transport.abort(); };
}

var Web = {};

/**
 * Returns a new XMLHttpRequest.
 * @return {XMLHttpRequest}
 */
if (exists(global.XMLHttpRequest)) {
        Web.transport = function(){
                return new XMLHttpRequest();
        };
} else {
        Web.transport = function(){
        return tryAny(
                function() { return new ActiveXObject('Msxml2.XMLHTTP'); },
                function() { return new ActiveXObject('Microsoft.XMLHTTP'); }
        );
        };
}


function apiRequest(path, payload, opts) {
    // We always use cookie authentication and copy the payload object
    payload = $.extend({
        cookieauth: true
    }, payload || {});

    // Additional options
    opts = $.extend({
        method: 'GET',
        silentErrors: false // when true, no error dialog is shown for HTTPAPIErrors
    }, opts);

    // For convenience we map booleans to yes/no
    $.each(payload, function(key, val) {
        if(val === true || val === false) {
            payload[key] = val ? 'yes' : 'no';
        }
    });

    var dfd = $.Deferred();
    var requestInfo = {
        origin: 'unknown',
        params: payload,
        method: opts.method,
        path: path
    };

    $.ajax({
        url: (opts.method == 'POST' ? Indico.Urls.APIBase : Indico.Urls.ExportAPIBase) + path + '.json',
        data: payload,
        type: opts.method,
        cache: false, // we really don't want caching for AJAX requests!
        dataType: 'json'
    }).fail(function(xhr, status, error) {
        var errorMessage = 'Unknown Error';
        var resp, code = '';

        try {
            // Maybe we have JSON
            resp = $.parseJSON(xhr.responseText);
        }
        catch(e) {
            // We got HTML. Probably 404 or something like that.
            if(~xhr.responseText.indexOf('errorBoxContent')) {
                errorMessage = $(xhr.responseText).find('#errorBoxContent h1').text();
            }
            else {
                errorMessage = error;
            }
            dfd.reject(errorMessage);
            code = 'HTTP-' + error;
        }

        // Handle JSON error
        if(resp) {
            dfd.reject(resp.message);
            if(resp._type == 'HTTPAPIError' && opts.silentErrors) {
                return;
            }
            if(resp.message) {
                errorMessage = resp.message;
            }
            code = 'APIError';
        }

        IndicoUtil.errorReport({
            title: $T('Error'),
            message: $T('API request failed:') + ' ' + errorMessage,
            inner: [],
            requestInfo: requestInfo,
            code: code
        });
    }).done(function(resp) {
        if (resp._type == 'HTTPAPIError') {
            dfd.reject(resp.message);
            if(!opts.silentErrors) {
                IndicoUtil.errorReport({
                    title: $T('Error'),
                    message: $T('API request failed:') + ' ' + resp.message,
                    inner: [],
                    requestInfo: requestInfo,
                    code: 'APIError'
                });
            }
            return;
        }
        dfd.resolve(resp);
    });

    return dfd.promise();
}
