/**
 * @author Tom
 */

/**
 * Curries the method with the args.
 * @param {Function} method
 * @param {Object} ... args
 * @return {Function}
 */
function curry(method) {
	var args = $A(arguments, 1);
	return function() {
		return method.apply(this, concat(args, arguments));
	};
}

function wrap(method, instance) {
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
function apply(method, instance) {
	var args = $A(arguments, 2);
	return function() {
		return method.apply(instance, concat(args, arguments));
	};
}

/**
 * Returns a template that invokes an input value on the object with the arguments.
 * @param {Object} self
 * @param {Array} [args]
 * @return {Function} template
 */
function invoker(object, args) {
	args = any(args, []);
	return function Invoke(func) {
		return (arguments.callee.result = func.apply(object, args));
	};
}

/**
 * Creates a sequential invoker from the functions.
 * @param {Function} ... functions
 * @return {Function} sequence
 */
function sequence() {
	var functions = compact(arguments);
	return function Sequence() {
		iterate(functions, invoker(this, $A(arguments)));
	};
}

/**
 * Returns a multi-function with attachable methods.
 * @return {Function} commands
 */
function commands() {
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
function command(method, caption) {
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
function invoke(method) {
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
function delay(method, timeout) {
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
function defer(method) {
	return delay(method, 1);
}

/**
 * Schedule execution of the method and returns a function to cancel the scheduled execution.
 * @param {Function} method
 * @return {Function} cancel
 */
function schedule(method) {
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

function delayedBind(target, key, builder) {
	target[key] = function() {
		var args = $A(arguments);
		var method = builder.apply(this, args);
		target[key] = method;
		return method.apply(this, args);
	};
}


