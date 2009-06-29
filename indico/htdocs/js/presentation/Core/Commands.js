/**
 * @author Tom
 */

/**
 * Curries the method with the args.
 * @param {Function} method
 * @param {Object} ... args
 * @return {Function}
 */
global.curry = function(method) {
	var args = $A(arguments, 1);
	return function() {
		return method.apply(this, concat(args, arguments));
	};
}

global.wrap = function(method, instance) {
	return function() {
		return method.apply(instance, $A(arguments));
	}
}

/**
 * Returns a function that calls the method on the given instance.
 * @param {Function} method
 * @param {Object} instance
 * @param {Object} ... args
 * @return {Function}
 */
global.apply = function(method, instance) {
	var args = $A(arguments, 2);
	return function() {
		return method.apply(instance, concat(args, arguments));
	};
}


/**
 * Returns function that wraps method of given object
 * @param {Object} object
 * @param {String} key
 * @return {Function} invoker
 */
global.methodize = function(object, key) {
	return function() {
		var method = object[key];
		if (exists(method)) {
			return method.apply(object, $A(arguments));
		}
	};
}

/**
 * Returns a template that invokes an input value on the object with the arguments.
 * @param {Object} self
 * @param {Array} [args]
 * @return {Function} template
 */
global.invoker = function(object, args) {
	args = any(args, []);
	return function Invoke(func) {
		return (arguments.callee.result = func.apply(object, args));
	};
}

/**
 * Returns a template that invokes a method of the object determined by an input value with the arguments.
 * @param {Object} object
 * @param {Array} [args]
 * @return {Function} template
 */
global.objectInvoker = function(object, args) {
	args = any(args, []);
	return function(key) {
		var method = object[key];
		if (exists(method)) {
			return method.apply(object, args);
		}
	};
}

/**
 * Returns a template that invokes the method on an input value with the arguments.
 * @param {Function, String} method
 * @param {Array} [args]
 * @return {Function} template
 */
global.methodInvoker = function(method, args) {
	args = any(args, []);
	if (isFunction(method)) {
		return function(object) {
			return method.apply(object, args);
		};
	} else {
		return function(object) {
			var func = object[method];
			if (exists(func)) {
				return func.apply(object, args);
			}
		};
	}
}

/**
 * Creates a sequential invoker from the functions.
 * @param {Function} ... functions
 * @return {Function} sequence
 */
global.sequence = function() {
	var functions = compact(arguments);
	return function Sequence() {
		iterate(functions, invoker(this, $A(arguments)));
	};
}

/**
 * Returns a function with attachable targets.
 * @param {Function} method
 * @return {Function}
 */
global.commander = function(method) {
	var objects = new Bag();
	return mixinInstance(function() {
		return objects.each(methodInvoker(method, $A(arguments)));
	}, objects, Attachable);
}

/**
 * Returns a multi-function with attachable methods.
 * @return {Function} commands
 */
global.commands = function() {
	var methods = new Bag();
	return mixinInstance(function() {
		return methods.each(invoker(this, $A(arguments)));
	}, methods, Attachable);
}

/**
 * Creates a command from the method and the caption.
 * @param {Function} method
 * @param {String} caption
 * @return {Function} command
 */
global.command = function(method, caption) {
	function Command() {
		return method.apply(this, $A(arguments));
	}
	Command.caption = caption;
	return Command;
}

/**
 * Invokes the method with the arguments if it exists. 
 * @param {Function} command
 */
global.invoke = function(method) {
	if (exists(method)) {
		return method.apply(this, $A(arguments, 1));
	}
}

/**
 * Delays execution of the method for the timeout and returns a function to cancel the delayed execution.
 * @param {Function} method
 * @param {Number} timeout
 * @return {Function} cancel
 */
global.delay = function(method, timeout) {
	var id = setTimeout(method, timeout);
	return function() {
		clearTimeout(id);
	};
}

/**
 * Defers execution of the method and returns a function to cancel the deferred execution.
 * @param {Function} method
 * @return {Function} cancel
 */
global.defer = function(method) {
	return delay(method, 1);
}

/**
 * Schedule execution of the method and returns a function to cancel the scheduled execution.
 * @param {Function} method
 * @return {Function} cancel
 */
global.schedule = function(method) {
	if (exists(method.scheduled)) {
		return method.scheduled;
	} else {
		method.scheduled = defer(function() {
			delete method.scheduled;
			method();
		});
		return method.scheduled;
	}
}

global.delayedBind = function(target, key, builder) {
	target[key] = function() {
		var args = $A(arguments);
		var method = builder.apply(this, args);
		target[key] = method;
		return method.apply(this, args);
	};
}


