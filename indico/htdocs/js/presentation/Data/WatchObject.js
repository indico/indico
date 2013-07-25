/**
 * WatchObject
 * @author Tom
 */


/**
 * Creates a watch object and binds it to the source.
 * @param {Object} source
 * @param {Function} template
 * @return {WatchObject}
 */
function $O(source, template) {
	return bind.toDictionary(new WatchObject(), source, template);
}

/**
 * Observable object.
 */
type("WatchObject", ["Dictionary", "Observable"], {
	/**
	 * Adds a new property, initializes it with the value, returns a key of the new property.
	 * @param {Object} value
	 * @return {String} key
	 */
	add: function(value) {},

	/**
	 * Creates a new watch getter for the key.
	 * @param {String} key
	 * @return {WatchGetter}
	 */
	getter: function(key) {
		var self = this;
		return new WatchGetter(function() {
			return self.get(key);
		}, function(observer) {
			return self.observe(function(value, key, self, old) {
				return observer(value, old);
			}, key);
		}, function(observer) {
			var value = self.get(key);
			return observer(value, value);
		});
	},

	/**
	 * Creates a new watch accessor for the key.
	 * @param {String} key
	 * @return {WatchAccessor}
	 */
	accessor: function(key) {
		var self = this;
		return new WatchAccessor(function() {
			return self.get(key);
		}, function(value) {
			return self.set(key, value);
		}, function(observer) {
			return self.observe(function(value, key, self, old) {
				return observer(value, old);
			}, key);
		}, function(observer) {
			var value = self.get(key);
			return observer(value, value);
		});
	}
},
	/**
	 * Initializes a new watch object and attaches watch accessors for the keys.
	 * @param {String} ... keys
	 */
	function() {
		var self = this;
		var properties = {};
		var propertyObservers = {};
		var objectObservers = commands();
		var notify = function(value, key, old) {
			var propertyObserver = propertyObservers[key];
			if (exists(propertyObserver)) {
				propertyObserver(value, key, self, old);
			}
			objectObservers(value, key, self, old);
		};

		// Enumerable
		this.each = function(iterator) {
			return enumerate(properties, iterator);
		};
		this.isEmpty = function() {
			return !hasProperties(properties);
		};

		// Dictionary
		this.get = function(key) {
			return properties[key];
		};
		this.set = function(key, value) {
			return changeProperty(properties, key, value, notify);
		};
		this.getAll = function() {
			return clone(properties);
		};
		this.update = function(values) {
			return changeProperties(properties, values, notify);
		};
		this.replace = function(values) {
			return replaceProperties(properties, values, notify);
		};
		this.clear = function() {
			var old = properties;
			properties = {};
			enumerate(old, function(value, key) {
				notify(null, key, value);
			});
			return old;
		};
		// Observable
		this.observe = function(observer, key) {
			if (exists(key)) {
				var propertyObserver = propertyObservers[key];
				if (!exists(propertyObserver)) {
					propertyObserver = commands();
					propertyObservers[key] = propertyObserver;
				}
				return propertyObserver.attach(observer);
			} else {
				return objectObservers.attach(observer);
			}
		};
		// WatchObject
		this.add = function(value) {
			return addProperty(properties, value, notify);
		};
		return mixWatchAccessors(this, arguments, this);
	}
);

/**
 * Defines a named watch type with the properties based on the mixins.
 * @param {Object} name
 * @param {Array} properties
 * @param {Array} [mixins]
 * @return {Function} constructor({Object} ... values)
 */
function watchType(name, properties, mixins) {
	var create = type(name, any(mixins, []), {}, function(source) {
		if (this instanceof arguments.callee) {
			var object = new WatchObject();
			var self = this;
			iterate(create.mixins, function(mixin) {
				mixWatchAccessors(self, self[mixin].watchProperties, object);
			});
			watchType.init(this, arguments);
		} else {
			return watchType.load(new arguments.callee(), source);
		}
	});
	create.watchProperties = properties;
	return create;
}

/**
 * 
 * @param {WatchType} target
 * @param {Array} values
 */
watchType.init = function(target, values) {
	var counter = 0;
	iterate(target.constructor.mixins, function(mixin) {
		iterate(target[mixin].watchProperties, function(property) {
			target[property].set(values[counter++]);
		});
	});
	return target;
};

/**
 * 
 * @param {WatchType} target
 * @param {Object} object
 */
watchType.load = function(target, object) {
	if (object instanceof target.constructor) {
		iterate(target.constructor.mixins, function(mixin) {
			iterate(target[mixin].watchProperties, function(property) {
				var value = object[property];
				if (exists(value) && value.Getter) {
					target[property].set(value.get());
				}
			});
		});
	} else {
		iterate(target.constructor.mixins, function(mixin) {
			iterate(target[mixin].watchProperties, function(property) {
				target[property].set(object[property]);
			});
		});
	}
	return target;
};

/**
 * Attaches watch getters created from the properties from the object to the target and returns the object.
 * @param {Object} target
 * @param {Array} properties
 * @param {WatchObject} [object]
 * @return {WatchObject}
 */
function mixWatchGetters(target, properties, object) {
	if (!exists(object)) {
		object = new WatchObject();
	}
	iterate(properties, function(property) {
		target[property] = object.getter(property);
	});
	return object;
}

/**
 * Attaches watch accessors created from the properties from the object to the target and returns the object.
 * @param {Object} target
 * @param {Array} properties
 * @param {WatchObject} [object]
 * @return {WatchObject}
 */
function mixWatchAccessors(target, properties, object) {
	if (!exists(object)) {
		object = new WatchObject();
	}
	iterate(properties, function(property) {
		target[property] = object.accessor(property);
	});
	return object;
}

/**
 * Attaches the accessors and the getters from the object to the target and returns the object.
 * @param {Object} target
 * @param {Array} accessors
 * @param {Array} getters
 * @param {WatchObject} [object]
 * @return {WatchObject}
 */
function mixWatchObject(target, accessors, getters, object) {
	if (!exists(object)) {
		object = new WatchObject();
	}
	iterate(properties, function(property) {
		target[property] = object.accessor(property);
	});
	iterate(getters, function(property) {
		target[property] = object.getter(property);
	});
	return object;	
}

newWatchObject = construct(WatchObject);
getWatchObject = provide(WatchObject);
