/**
 * @author Tom
 */

this.global = this;

global.isDefined = function(name) {
	return name in global;
}

if (typeof(global.include) !== "function") {
	global.include = function(script) {
		document.write("<script type=\"text/javascript\" src=\"" + script + "\"></script>");
	}
}

global.extract = function(text, start, stop) {
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

global.equals = function(a, b) {
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
global.internal = function(block) {
	block();
}

/**
 * Two-way template that returns the input value.
 * @param {Object} value
 * @return {Object}
 */
global.pass = function(value) {
	return value;
}
pass.toTarget = pass;
pass.toSource = pass;

/**
 * Two-way template that returns inverted value.
 * @param {Object} value
 * @return {Boolean}
 */
global.invert = function(value) {
	return !value;
}
invert.toTarget = invert;
invert.toSource = invert;

/**
 * Returns true if the value is not undefined and not null.
 * @param {Object} value
 * @return {Boolean}
 */
global.exists = function(value) {
	return value !== undefined && value !== null;
}

/**
 * Returns true if the value is an empty array or object with no properties.
 * @param {Object} value
 * @return {Boolean}
 */
global.empty = function(value) {
	return !exists(value) || value === ""
		|| (isArray(value) && value.length === 0)
		|| (isObject(value) && (value.Enumerable ? value.isEmpty() : !hasProperties(value)));
}

/**
 * Returns true if the object has at least one property.
 * @param {Object} object
 * @return {Boolean}
 */
global.hasProperties = function(object) {
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
global.any = function() {
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
global.tryAny = function() {
	for (var i = 0; i < arguments.length; i++) {
		var method = arguments[i];
		try {
			return method();
		} catch (e) {
			
		}
	}
}

global.get = function(value, builder) {
	return exists(value) ? value : builder();
}

global.getByKey = function(object, property, value) {
	return property in object ? object[property] : value;
}

/**
 * Returns true if the value is an object.
 * @param {Object} value
 * @return {Boolean}
 */
global.isObject = function(value) {
	return typeof(value) == "object" && value !== null;
}

/**
 * Returns true if the value is a number.
 * @param {Object} value
 * @return {Boolean}
 */
global.isNumber = function(value) {
	return typeof(value) == "number";
}

/**
 * Returns true if the value is a string.
 * @param {Object} value
 * @return {Boolean}
 */
global.isString = function(value) {
	return typeof(value) == "string";
}

/**
 * Returns true if the value is a function.
 * @param {Object} value
 * @return {Boolean}
 */
global.isFunction = function(value) {
	return typeof(value) == "function";
}

/**
 * Returns true if the value is an array.
 * @param {Object} value
 * @return {Boolean}
 */
global.isArray = function(value) {
	return value instanceof Array;
}

/**
 * Returns true if the value is a DOM node.
 * @param {Object} value
 * @return {Boolean}
 */
global.isDom = function(value) {
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
global.init = function(object, property, value) {
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
global.obtain = function(object, property, initializer) {
	var result = object[property];
	return exists(result) ? result : object[property] = initializer();
}

global.obtainGet = function(object, property, initializer) {
	var result = object.get(property);
	if (!exists(result)) {
		result = initializer();
		object.set(property, result);
	}
	return result;
}

global.obtainSet = function(object, property, key, value) {
	obtain(object, property, newObject)[key] = value;
}

global.obtainAdd = function(object, property, value) {
	obtain(object, property, newArray).push(value);
}


/**
 * Copies properties
 * @param {Object} properties
 * @return {Object} result
 */
global.clone = function(object) {
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
global.extend = function(target, source) {
	for (var key in source) {
		target[key] = source[key];
	}
	return target;
}

/**
 * Function that does nothing.
 */
global.nothing = function() {
}

/**
 * Converts value to string. If the value is a function or does not exists it returns empty string.
 * @param {Object} value
 * @return {String}
 */
global.str = function(value) {
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
global.construct = function(type) {
	return function() {
		return new type();
	};
}

global.provide = function(type) {
	return function(value) {
		return exists(value) ? value : new type();
	};
}


global.newObject = construct(Object);
global.newArray = construct(Array);
global.getObject = provide(newObject);
global.getArray = provide(newArray);


global.objectize = function(key, value) {
	var obj = {};
	obj[key] = value;
	return obj;
}

global.setExisting = function(object, key, value) {
	if (exists(value)) {
		object[key] = value;
	}
}

/**
 * Browser detection from Prototype JavaScript Framework.
 */
global.Browser = {
	IE: (window.attachEvent && !window.opera) ? extract(navigator.appVersion, "MSIE ", ";") : false,
	Opera: window.opera ? extract(navigator.appVersion, "", " ") : false,
	WebKit: navigator.appVersion.indexOf('AppleWebKit/') > -1 ? extract(navigator.appVersion, "AppleWebKit/", " ") : false,
	Gecko: navigator.userAgent.indexOf('Gecko') > -1 && navigator.userAgent.indexOf('KHTML') == -1 ? extract(navigator.userAgent, "rv:", ")") : false,
	KHTML: navigator.appVersion.indexOf('KHTML') > -1 && navigator.appVersion.indexOf('AppleWebKit') == -1 ? extract(navigator.appVersion, "KHTML/", " ") : false,
	MobileSafari: !!navigator.userAgent.match(/Apple.*Mobile.*Safari/)
};

