/**
 * @author Tom
 */

this.global = this;

if (typeof(global.include) !== "function") {
    var include = function(script) {
        document.write("<script type=\"text/javascript\" src=\"" + script + "\"></script>");
    }
}

function load(code) {
    if (window.execScript) {
        return window.execScript(code);
    }
    global.eval(code);
}

function extract(text, start, stop) {
    var startIndex;
    if (!empty(start)) {
        startIndex = text.indexOf(start);
        if (startIndex < 0) {
            return null;
        }
        startIndex += start.length;
    }
    var stopIndex = text.indexOf(stop, startIndex);
    if (stopIndex < startIndex) {
        return null;
    }
    return text.substring(startIndex, stopIndex);
}

function equals(a, b) {
    if (!exists(a))
        return !exists(b);
    if (!exists(b))
        return !exists(a);
    if (a.Equatable)
        return a.equals(b);
    if (b.Equatable)
        return b.equals(a);
    return a == b;
}

/**
 * Makes declarations internal
 * @param {Function} block
 */
function internal(block) {
    block();
}

/**
 * Two-way template that returns the input value.
 * @param {Object} value
 * @return {Object}
 */
function pass(value) {
    return value;
}
pass.toTarget = pass;
pass.toSource = pass;

/**
 * Two-way template that returns inverted value.
 * @param {Object} value
 * @return {Boolean}
 */
function invert(value) {
    return !value;
}
invert.toTarget = invert;
invert.toSource = invert;

/**
 * Returns true if the value is not undefined and not null.
 * @param {Object} value
 * @return {Boolean}
 */
function exists(value) {
    return value !== undefined && value !== null;
}

/**
 * Returns true if the value is an empty array or object with no properties.
 * @param {Object} value
 * @return {Boolean}
 */
function empty(value) {
    return !exists(value) || value === ""
        || (isArray(value) && value.length === 0)
        || (isObject(value) && (value.Enumerable ? value.isEmpty() : !hasProperties(value)));
}

/**
 * Returns true if the object has at least one property.
 * @param {Object} object
 * @return {Boolean}
 */
function hasProperties(object) {
    for (var key in object) {
        return true;
    }
    return false;
}

/**
 * Returns the first existing value.
 * @param {Object} ... values
 * @return {Object}
 */
function any() {
    for (var i = 0, length = arguments.length; i < length; i++) {
        var arg = arguments[i];
        if (exists(arg)) {
            return arg;
        }
    }
}

/**
 * Returns a return value of the first function that does not throw an exception.
 * @param {Function} ... functions
 * @return {Object}
 */
function tryAny() {
    for (var i = 0; i < arguments.length; i++) {
        var method = arguments[i];
        try {
            return method();
        } catch (e) {

        }
    }
}

function get(value, builder) {
    return exists(value) ? value : builder();
}


/**
 * Returns true if the value is an object.
 * @param {Object} value
 * @return {Boolean}
 */
function isObject(value) {
    // We do not use _.isObject here since it has another idea of what
    // an "object" is.
    return typeof(value) == "object" && value !== null;
}

/**
 * Returns true if the value is a number.
 * @param {Object} value
 * @return {Boolean}
 */
var isNumber = _.isNumber;

/**
 * Returns true if the value is a string.
 * @param {Object} value
 * @return {Boolean}
 */
var isString = _.isString;

/**
 * Returns true if the value is a function.
 * @param {Object} value
 * @return {Boolean}
 */
var isFunction = _.isFunction;

/**
 * Returns true if the value is an array.
 * @param {Object} value
 * @return {Boolean}
 */
var isArray = _.isArray;

/**
 * Returns true if the value is a DOM node.
 * @param {Object} value
 * @return {Boolean}
 */
function isDom(value) {
    return exists(value) && isNumber(value.nodeType);
}

/**
 * Sets the value to the property of the object
 * if the property does not exist or contains a not existing value
 * and returns that new value.
 * Otherwise returns the current value of the property.
 * @param {Object} object
 * @param {String} property
 * @param {Object} value
 * @return {Object} result
 */
function init(object, property, value) {
    var result = object[property];
    return exists(result) ? result : object[property] = value;
}

/**
 * Initializes the property of the object using the initializer
 * if the property does not exist or contains a not existing value
 * and returns a value returned from the initializer.
 * Otherwise returns the current value of the property.
 * @param {Object} object
 * @param {String} property
 * @param {Function} initializer
 * @return {Object} result
 */
function obtain(object, property, initializer) {
    var result = object[property];
    return exists(result) ? result : object[property] = initializer();
}


/**
 * Copies properties
 * @param {Object} properties
 * @return {Object} result
 */
function clone(object) {
    var result = new object.constructor();
    for (var key in object) {
        result[key] = object[key];
    }
    return result;
}

/**
 * Copies properties of the source to the target and returns the target.
 * @param {Object} target
 * @param {Object} source
 * @return {Object} target
 */
function extend(target, source) {
    for (var key in source) {
        target[key] = source[key];
    }
    return target;
}

/**
 * Function that does nothing.
 */
function nothing() {
}

/**
 * Converts value to string. If the value is a function or does not exists it returns empty string.
 * @param {Object} value
 * @return {String}
 */
function str(value) {
    switch (typeof(value)) {
        case "boolean":
            return value ? "true" : "false";
        case "number":
        case "object":
            if (value === null) {
                return "";
            }
        case "string":
            return String(value);
        default:
            return "";
    }
}

/**
 * Returns a function that creates an instance from given type.
 * @param {Function} type
 * @return {Function}
 */
function construct(type) {
    return function() {
        return new type();
    };
}

function provide(type) {
    return function(value) {
        return exists(value) ? value : new type();
    };
}


var newObject = construct(Object);
var newArray = construct(Array);
var getObject = provide(newObject);
var getArray = provide(newArray);


function objectize(key, value) {
    var obj = {};
    obj[key] = value;
    return obj;
}

/**
 * Browser detection from Prototype JavaScript Framework.
 */
var Browser = {
    IE: (window.attachEvent && !window.opera) ? extract(navigator.appVersion, "MSIE ", ";") : false,
    WebKit: navigator.appVersion.indexOf('AppleWebKit/') > -1 ? extract(navigator.appVersion, "AppleWebKit/", " ") : false,
    Gecko: navigator.userAgent.indexOf('Gecko') > -1 && navigator.userAgent.indexOf('KHTML') == -1 ? extract(navigator.userAgent, "rv:", ")") : false,
    KHTML: navigator.appVersion.indexOf('KHTML') > -1 && navigator.appVersion.indexOf('AppleWebKit') == -1 ? extract(navigator.appVersion, "KHTML/", " ") : false
};

