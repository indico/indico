/**
 * Binding
 * @author Tom
 */

// SUPER LEVEL

/**
 * Binds the target to the source using the template. If the target is a write-only elements, it uses bind.element(), otherwise it uses bind().
 * @param {Object} target
 * @param {Object} source
 * @param {Object} template
 */
function $B(target, source, template) {
	if (exists(target) && target.XElement && cannotGet(target)) {
		return bind.element(target, source, template);
	} else {
		return bind(target, source, template);
	}
}

// HIGH LEVEL

/**
 * Direct binding.
 * @param {Accessor, List, Dictionary} target
 * @param {Object} source
 * @param {Function, String} [template]
 * @return {Accessor, List, Dictionary} target
 */
var bind = function(target, source, template) {
	if (!exists(source)) {
		return bind.detach(target);
	}
	if (!exists(target)) {
		return obtainTemplate(template)(source);
	}
	if (target.Accessor) {
		return bind.accessor(target, source, template);
	}
	if (target.List) {
		return bind.toList(target, source, template);
	}
	if (target.Dictionary) {
		return bind.toDictionary(target, source, template);
	}
	bind.detach(target);
	throw new Error("Not implemented.");
};

/**
 * Place source to the target element.
 * @param {XElement} target
 * @param {XElement, Object} source
 * @param {Function} [template]
 */
bind.element = function(target, source, template) {
	return bind.attach(target, bind.internal.element(target, source, template));
};

// MEDIUM LEVEL

/**
 * Two-way binding of accessors.
 * @param {Accessor} target
 * @param {Accessor, Object} source
 * @param {Object|String} [template]
 * @return {Accessor} target
 */
bind.accessor = function(target, source, template, listenOnly) {
	if (cannotGet(target)) {
		if (cannotGet(source)) {
			return bind.detach(target);
		} else {
			return bind.toAccessor(target, source, template);
		}
	} else if (source.Accessor) {
		if (cannotGet(source)) {
			return bind.toAccessor(source, target, template);
		} else {
			var toTarget, toSource;
			if (!exists(template)) {
				toTarget = null;
				toSource = null;
			} else if (isString(template)) {
				toTarget = template;
				toSource = function(value) {
					source[template] = value;
				};
			} else {
				toTarget = template.toTarget;
				toSource = template.toSource;
			}
			var lock = {};
			bind.toAccessor(target, source, toTarget, listenOnly, lock);
			bind.toAccessor(source, target, toSource, true, lock);
			return target;
		}
	} else {
		return bind.toAccessor(target, source, template);
	}
};

/**
 * Binds the target to the source accessor.
 * @param {Accessor} target
 * @param {Object} [source]
 * @param {Function, String} [template]
 * @return {Accessor} target
 */
bind.toAccessor = function(target, source, template, listenOnly, lock) {
	return bind.setter(target, source, templatedSetter(template, function(value) {
		if (lock) {
			if (!lock.active) {
				lock.active = true;
				target.set(value);
				lock.active = null;
			}
		} else {
			target.set(value);
		}
	}), listenOnly);
};

/**
 * Binds the target list to the source.
 * @param {List} target
 * @param {Object} [source]
 * @param {Function, String} [template]
 * @return {List} target
 */
bind.toList = function(target, source, template) {
	return bind.setter(target, source, function(value) {
		if (!exists(value)) {
			target.clear();
			return null;
		}
		if (isArrayOrListable(value)) {
			return bind.internal.list(target, value, template);
		}
		return bind.internal.objectToList(target, value, template);
	});
};

/**
 * Binds the target dictionary to the source.
 * @param {Dictionary} target
 * @param {Object} [source]
 * @param {Function, String} [template]
 * @return {Dictionary} target
 */
bind.toDictionary = function(target, source, template) {
	return bind.setter(target, source, function(value) {
		if (!exists(value)) {
			target.clear();
			return null;
		}
		if (isArrayOrListable(value)) {
			return bind.internal.listToDictionary(target, value, template);
		}
		return bind.internal.objectToDictionary(target, value, template);
	});
};

// LOW LEVEL

/**
 * Binds two lists.
 * @param {List} target
 * @param {WatchList, Enumerable, Array} source
 * @param {Function, String} [template]
 * @return {List} target
 */
bind.list = function(target, source, template) {
	return bind.attach(target, bind.internal.list(target, source, template));
};

/**
 * Binds the target list tp the source object.
 * @param {List} target
 * @param {WatchObject, Object} source
 * @param {Function, String} [template]
 * @return {List} target
 */
bind.objectToList = function(target, source, template) {
	return bind.attach(target, bind.internal.objectToList(target, source, template));
};

/**
 * Binds the target dictionary to the source list.
 * @param {Dictionary} target
 * @param {WatchList, Enumerable, Array} source
 * @param {Function, String} [template]
 * @return {Dictionary} target
 */
bind.listToDictionary = function(target, source, template) {
	return bind.attach(target, bind.internal.listToDictionary(target, source, template));
};

/**
 * Binds the target dictionary to the source object.
 * @param {Dictionary} target
 * @param {WatchObject, Object} source
 * @param {Function, String} [template]
 * @return {Dictionary} target
 */
bind.objectToDictionary = function(target, source, template) {
	return bind.attach(target, bind.internal.objectToDictionary(target, source, template));
};

/**
 * Binds the list sequentially
 * @param {List} target
 * @param {WatchList, Enumerable, Array} source
 * @param {Function} template
 */
bind.sequence = function(target, source, template) {
	return bind.attach(target, bind.internal.sequence(target, source, template));
};

/**
 *
 * @param {List} target
 * @param {WatchList, Enumerable, Array} source
 * @param {Function, String} [template]
 * @param {Number} [offset]
 * @param {Number} [multiplier]
 * @return {List}
 */
bind.listEx = function(target, source, template, offset, multiplier){
	return bind.attach(target, bind.internal.listEx(target, source, template, offset, multiplier));
};

/**
 * Binds the target using the setter to the source getter.
 * @param {Object} target
 * @param {Getter, Object} source
 * @param {Function} setter
 * @return {Object} target
 */
bind.setter = function(target, source, setter, listenOnly) {
	function gain(value, listenOnly) {
		if (exists(value) && value.Getter) {
			return bind.internal.getter(gain, value, listenOnly);
		}
		if (!listenOnly) {
			setter(value)
		}
	}
	return bind.attach(target, gain(source, listenOnly));
};

/**
 * Attaches the binding stop function to the target.
 * @param {Object} target
 * @param {Function} stop
 * @return {Object}
 */
bind.attach = function(target, stop) {
	if (target.unbind) {
		target.unbind();
		if (stop) {
			target.unbind = stop;
		} else {
			delete target.unbind;
		}
	} else if (stop) {
		target.unbind = stop;
	}
	return target;
};


/**
 * Unbinds the target.
 * @param {Object} target
 * @return {Object} target
 */
bind.detach = function(target) {
	if (target.unbind) {
		target.unbind();
		delete target["unbind"];
	}
	return target;
};

// INTERNAL LEVEL

bind.internal = {};

bind.internal.element = function(target, source, template) {
	if (!exists(target)) {
		return obtainTemplate(template)(source);
	}

	function gain(value) {
		if (!exists(value) || value.XElement || !isObject(value)) {
			target.clear();
			target.append(obtainTemplate(template)(value, target));
			return null;
		}
		if (value.Getter) {
			return bind.internal.getter(gain, value);
		}
		if (isArrayOrListable(value)) {
			return bind.internal.list(target, value, template);
		}
		return bind.internal.list(target, $L(value), template);
	}

	return gain(source);
};

bind.internal.getter = function(gain, value, listenOnly) {
	var stop = gain(value.get(), listenOnly);
	if (value.WatchGetter) {
		return sequence(stop, value.observe(sequence(stop, function(value) {
			gain(value);
		})));
	}
	return stop;
};

bind.internal.list = function(target, list, template) {
	template = obtainTemplate(template);
	function inserter(item, index) {
		target.insert(template(item, target), index);
	}
	target.clear();
	return processListable(list, {
		itemAdded: inserter,
		itemRemoved: function(item, index) {
			target.removeAt(index);
		},
		itemMoved: function(item, source, destination) {
			target.move(source, destination);
		}
	});
};

bind.internal.objectToList = function(target, object, template) {
	template = obtainTemplate(template);
	if (object.WatchObject) {
		var list = new WatchList();
		each(object, function(value, key) {
			list.append(new WatchPair(key, value));
		});
		return sequence(
			bind.internal.list(target, list, template),
			object.observe(function(value, key, obj, old) {
				if (exists(value)) {
					var result = search(list, match(key, "key"));
					if (exists(result)) {
						result[0].set(value);
					} else {
						list.append(new WatchPair(key, value));
					}
				} else {
					var index = indexOf(list, match(key, "key"));
					if (exists(index)) {
						list.removeAt(index);
					}
				}
			})
		);
	} else {
		target.clear();
		each(object, function(value, key) {
			target.append(template(new WatchPair(key, value), target));
		});
	}
	return null;
};

bind.internal.listToDictionary = function(target, source, template) {
	throw new Error("Not implemented.");
};

bind.internal.objectToDictionary = function(target, source, template) {
	if (source.WatchObject) {
		throw new Error("Not implemented.");
	}
	if (exists(template)) {
		source = map(source, template);
	}
	target.update(source);
	return null;
};

bind.internal.sequence = function(target, list, template) {
	template = obtainTemplate(template);
	function update() {
		target.clear();
		each(list, function(item, index) {
			target.insert(template(item, index, target), index);
		});
	}
	update();
	if (list.WatchList) {
		return list.observe(update);
	}
	return null;
};

bind.internal.listEx = function(target, list, template, offset, multiplier) {
	template = obtainTemplate(template);
	if (!exists(offset)) {
		offset = 0;
	}
	if (!exists(multiplier)) {
		multiplier = 1;
	}
	function inserter(item, index) {
		var items = template(item, target);
		var start = offset + multiplier * index;
		for (var i = 0; i < multiplier; i++) {
			target.insert(items[i], start + i);
		}
	}
	each(list, inserter);
	if (list.WatchList) {
		return list.observe({
			itemAdded: inserter,
			itemRemoved: function(item, index) {
				index = offset + multiplier * index;
				times(multiplier, function() {
					target.removeAt(index);
				});
			},
			itemMoved: function(item, source, destination) {
				// CHECK THAT
				source = offset + multiplier * source;
				destination = offset + multiplier * destination;
				times(multiplier, function() {
					target.move(source, destination);
				});
			}
		});
	}
	return null;
};


