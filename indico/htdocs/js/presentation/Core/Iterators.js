/**
 * @author Tom
 */

/**
 * Invokes the iterator for the number times and returns a result of the iterator.
 * The iterator receives one argument, the number of the iteration.
 * @param {Number} number
 * @param {Object} iterator
 * @return {Object}
 */
function times(number, iterator) {
        for (var i = 0; i < number; i++) {
                iterator(i);
        }
        return iterator.result;
}

/**
 * For each item of the list invokes the iterator with two arguments:
 * the item of the list and index of the item.
 * The list is an array like object: an array,
 * or an object with numeric property length (e.g. arguments).
 * The offset is an optional argument that specifies the offset where the iteration starts.
 * Returns a result from the iterator.
 * @param {Array, Object} list
 * @param {Function} iterator
 * @param {Number} [offset]
 * @return {Object}
 */
function iterate(list, iterator, offset) {
        for (var i = any(offset, 0), length = list.length; i < length; i++) {
                iterator(list[i], i);
        }
        return iterator.result;
}

/**
 * For each property of the object invokes the iterator with two arguments:
 * a value of the property and a key of the property.
 * Returns a result from the iterator.
 * @param {Object} object
 * @param {Function} iterator
 * @return {Object}
 */
function enumerate(object, iterator) {
        for (var key in object) {
                iterator(object[key], key);
        }
        return iterator.result;
}

/**
 * According the type of the source invokes specific iteration routine:
 * for Enumerables calls its method each(),
 * for array like objects invokes iterate(),
 * for numbers times(), and for other objects enumerate().
 * Returns a result of the used function.
 * @param {Enumerable, Array, Number, Object} source
 * @param {Function} iterator
 * @return {Object}
 */
function each(source, iterator) {
        if (!exists(source)) {
                return iterator.result;
        }
        if (source.Enumerable) {
                return source.each(iterator);
        }
        if (isArray(source) || isNumber(source.length)) {
                return iterate(source, iterator);
        }
        if (isNumber(source)) {
                return times(source, iterator);
        }
        return enumerate(source, iterator);
}

function builder(construct, build) {
        var result = construct();
        var iterator = function(value, key) {
                build(result, key, value);
        };
        iterator.result = result;
        return iterator;
}

/**
 * Returns an iterator that stacks items to an array
 * and sets the array as the result of the iterator.
 * If a template is provided,
 * it first applies the template to these items.
 * @param {Function} [template]
 * @return {Function}
 */
function stacker(template) {
        var result = [];
        var iterator;
        if (exists(template)) {
                iterator = function(value, key) {
                        result.push(template(value, key));
                };
        } else {
                iterator = function(value) {
                        result.push(value);
                };
        }
        iterator.result = result;
        return iterator;
}

/**
 * Returns an iterator that adds items to an object
 * and sets the object as the result of the iterator.
 * If a template is provided,
 * it first applies the template to these items.
 * @param {Function} [template]
 * @return {Function}
 */
function mapper(template) {
        var result = {};
        var iterator;
        if (exists(template)) {
                iterator = function(value, key) {
                        result[key] = template(value, key);
                };
        } else {
                iterator = function(value, key) {
                        result[key] = value;
                };
        }
        iterator.result = result;
        return iterator;
}

function writer(template) {
        var iterator;
        if (exists(template)) {
                iterator = function(value, key) {
                        iterator.result += template(value, key);
                };
        } else {
                iterator = function(value, key) {
                        iterator.result += value;
                };
        }
        iterator.result = "";
        return iterator;
}

/**
 * Returns an iterator
 * that invokes the action also for items of nested arrays
 * and sets a result from the action as the result of the iterator
 * @param {Function} action
 * @return {Function}
 */
function linearizing(action) {
        function iterator(item) {
                if (isArray(item)) {
                        iterate(item, iterator);
                } else {
                        action(item);
                }
        }
        iterator.result = action.result;
        return iterator;
}

function where(match, action) {
	function iterator(item, key) {
		if (match(item, key)) {
			action(item);
		}
	}
	iterator.result = action.result;
	return iterator;
}

/**
 * Returns an iterator
 * that invokes the action only for existing items
 * and sets a result from the action as the result of the iterator
 * @param {Function} action
 * @return {Function}
 */
function existing(action) {
   return where(exists, action);
}

/**
 * Returns an iterator that applies the template on each item
 * and invokes the action on outputs from the template.
 * It sets a result from the action as the result of the iterator
 * @param {Function} action
 * @param {Function} template
 * @return {Function}
 */
function processing(action, template) {
        function iterator(value, key) {
                action(template(value, key));
        }
        iterator.result = action.result;
        return iterator;
}

function keyGetter(value, key) {
        return key;
}

/**
 * Specifies that item was found.
 */
var $found = {type: "Found"};

/**
 * Returns an index of the first match. If no item matches returns null.
 * @param {Object} items
 * @param {Function} match
 * @return {Number}
 */
function indexOf(items, match) {
        var index = 0;
        try {
                each(items, function(value, key) {
                        if (match(value, key)) {
                                throw $found;
                        }
                        index++;
                });
                return null;
        } catch (e) {
                if (e === $found) {
                        return index;
                }
                throw e;
        }
}

/**
 * Returns the value and the key of the first matched item.
 * @param {Object} items
 * @param {Object} match
 * @return {Array}
 */
function search(items, match) {
        var result;
        try {
                each(items, function(value, key) {
                        if (match(value, key)) {
                                result = [value, key];
                                throw $found;
                        }
                });
                return null;
        } catch (e) {
                if (e === $found) {
                        return result;
                }
                throw e;
        }
}

function lookup(items, match) {
        var result;
        try {
                each(items, function(value, key) {
                        result = match(value, key);
                        if (exists(result)) {
                                throw $found;
                        }
                });
                return null;
        } catch (e) {
                if (e === $found) {
                        return result;
                }
                throw e;
        }
}


/**
 * Returns template that return true if an input object (or its property with the given key) is equal to the value.
 * @param {Object} value
 * @param {String} [key]
 * @param {Function}
 */
function match(value, key) {
        if (exists(key)) {
                return function(object) {
                        return object[key] === value;
                };
        } else {
                return function(object) {
                        return object === value;
                };
        }
}
