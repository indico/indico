/**
 * @author Tom
 */

/**
 * Returns true if the object is an array or is listable.
 * @param {Object} object
 * @return {Boolean}
 */
function isArrayOrListable(object) {
	return isArray(object) || (object.Enumerable && !object.Dictionary);
}

/**
 * Creates a new array from the list starting at given offset and applying the template to each item.
 * @param {Array, Object} items
 * @param {Number} [offset]
 * @param {Function} [template]
 * @return {Array}
 */
function $A(list, offset, template) {
	return iterate(list, stacker(template), offset);
}

function translate(source, template) {
	return each(source, stacker(template));
}

function map(source, template) {
	return each(source, mapper(template));
}

function dict(source, template) {
	return each(source, builder(newObject, function(target, key, value) {
		var pair = template(value, key);
		target[pair[0]] = pair[1];
	}));
}

function extractStrings(source, template) {
	return translate(dict(source, function(value, key) {
		return [template(value, key), null];
	}), function(value, key) {
		return key;
	});
}

/**
 * Creates a new array that contains items from the list but not existing ones.
 * @param {Array, Object} items
 * @param {Number} [offset]
 * @param {Function} [template]
 * @return {Array}
 */
function compact(list, offset, template) {
	return iterate(list, existing(stacker(template)), offset);
}

/**
 * Creates a new array that contains items from the list and flattens sub-lists.
 * @param {Array, Object} items
 * @param {Number} [offset]
 * @param {Function} [template]
 * @return {Array}
 */
function linearize(list, offset, template) {
	return iterate(list, linearizing(existing(stacker(template))), offset);
}

function filter(list, match, offset, template) {
  return iterate(list, where(match, stacker(template)), offset)
}

/**
 * Returns true if the collection contains an item that matches.
 * @param {Object} collection
 * @param {Function} match
 * @return {Boolean} result
 */
function includes(collection, match) {
	return exists(indexOf(collection, match));
}

/**
 * Creates a new array that contains items from all the lists.
 * @param {Array, Object} ... lists
 * @return {Array}
 */
function concat() {
	var result = [];
	iterate(arguments, function(arg) {
		if (exists(arg)) {
			iterate(arg, function(item) {
				result.push(item);
			});
		}
	});
	return result;
}

/**
 * Creates a new object that contains merged properties of the input objects.
 * @params {Object} ... objects
 * @return {Object}
 */
function merge() {
	var result = {};
	iterate(arguments, function(arg) {
		if (exists(arg)) {
			extend(result, arg);
		}
	});
	return result;
}

function withoutProperties(object) {
	var result = merge(object);
	iterate(arguments, function(property) {
		delete result[property];
	}, 1);
	return result;
}

function keys(source) {
	return translate(source, keyGetter);
}
var values = translate;

/**
 * Adds the value as a new property to the object,
 * notifies the observer, and returns a new key.
 * @param {Object} object
 * @param {Object} value
 * @param {Function} observer
 * @return {String} key
 */
function addProperty(object, value, observer) {
	var key = 1;
	while (key in object) {
		key++;
	}
	object[key] = value;
	observer(value, key, null);
	return key;
}

/**
 * Changes a property with the given key of the object,
 * notifies the observer if the previous value was different,
 * and the returns previous value.
 * @param {Object} object
 * @param {Object} key
 * @param {Object} value
 * @param {Function} observer
 * @return {Object} old
 */
function changeProperty(object, key, value, observer) {
	var old = object[key];
	if (old !== value) {
		if (exists(value)) {
			object[key] = value;
		} else {
			delete object[key];
		}
		observer(value, key, old);
	}
	return old;
}

/**
 * Changes properties of the object,
 * notifies the observer with changes,
 * and returns the changes.
 * @param {Object} object
 * @param {Object} values
 * @param {Function} observer
 * @return {Object} changes
 */
function changeProperties(object, values, observer) {
	var changes = {};
	enumerate(values, function(value, key) {
		var old = object[key];
		if (!equals(old, value)) {
			changes[key] = old;
			object[key] = value;
		}
	});
	enumerate(changes, function(value, key) {
		observer(object[key], key, value);
	});
	return changes;
}

/**
 * Replaces properties of the object with new values,
 * notifies the observer with changes,
 * and returns the changes.
 * @param {Object} object
 * @param {Object} values
 * @param {Function} observer
 * @return {Object} changes
 */
function replaceProperties(object, values, observer) {
	var changes = clone(values);
	enumerate(object, function(value, key) {
		if (!(key in changes)) {
			changes[key] = null;
		}
	});
	return changeProperties(object, changes, observer);
}

/**
 * Creates an accessor for a property of the object with the given key.
 * @param {Object} object
 * @param {String} key
 * @return {Accessor} accessor
 */
function objectAccessor(object, key) {
	return new Accessor(function() {
		return object[key];
	}, function(value) {
		var oldValue = object[key];
		object[key] = value;
		return oldValue;
	});
}


/**
 * Creates watch getter from the watch accessor.
 * @param {WatchAccessor} accessor
 * @return {WatchGetter} getter
 */
function getWatchGetter(accessor) {
	return new WatchGetter(accessor.get, accessor.observe, accessor.invokeObserver);
}

/**
 * Returns true if the source implements CanGet interface and canGet() returns false.
 * @param {Object} source
 * @return {Boolean} result
 */
function cannotGet(source) {
	return source.CanGet ? !source.canGet() : false;
}

/**
 * Returns function that sets the value to the accessor.
 * @param {Accessor} accessor
 * @param {Object} value
 * @return {Function} setter
 */
function setter(accessor, value) {
	return function() {
		accessor.set(value);
	};
}

/**
 * Returns the deepest accessor.
 * @param {Accessor} accessor
 * @return {Accessor} accessor
 */
function getAccessorDeep(accessor) {
	while (true) {
		var value = accessor.get();
		if (!exists(value) || !value.Accessor) {
			return accessor;
		}
		accessor = value;
	}
}

/**
 * Creates a date from a natural representation.
 * @param {Number} year
 * @param {Number} month
 * @param {Number} day
 * @param {Number} hour
 * @param {Number} min
 * @param {Number} sec
 */
function date(year, month, day, hour, min, sec) {
	return new Date(year, month - 1, day, hour, min, sec);
}

/**
 * Creates a copy of the given date.
 * @param {Date} date
 * @return {Date} result
 */
function copyDate(date) {
	return new Date(date.getTime());
}


function getArgumentsCount(func) {
	// from Prototype
	var items = func.toString().match(/^[\s\(]*function[^(]*\((.*?)\)/)[1].split(",");
	return items.length == 1 && !items[0] ? 0 : items.length;
}


function multiDictSet(dict, key, value) {
	return obtain(dict, key, newWatchList).append(value);
}

function tryGet(source, key) {
	return exists(source) ? source.get(key) : null;
}

function path(source, path) {
	indexOf(path, function(step) {
		if (!exists(source)) {
			return true;
		}
		source = source[step];
	});
	return source;
}

function pathGet(source, path) {
	indexOf(path, function(step) {
		if (!exists(source)) {
			return true;
		}
		source = source.get(step);
	});
	return source;
}

function redirectToRoomLoc(room, loc){
    indicoRequest(
            'roomBooking.locationsAndRooms.getLink',
            {
                room: room,
                location: loc
            },
            function(result,error) {
                if (!error && result) {
                    window.location = result
                } else{
                    new AlertPopup($T("Warning"),$T("Location not available")).open();
                }
            }
        );
}
