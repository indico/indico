/**
 * @author Tom
 */

/**
 * Read-only source.
 */
type("Getter", [], {
	/**
	 * Returns value from the source.
	 * @return {Object} value
	 */
	get: function() {}

},
	/**
	 *
	 * @param {Function} get
	 * @constructor
	 */
	function(get) {
		this.get = get;
	}
);

/**
 * Read-write source.
 */
type("Accessor", ["Getter"], {
	/**
	 * Sets the new value and returns the previous value.
	 * @param {Object} value
	 * @return {Object} old value
	 */
	set: function(value) {}
},
	/**
	 *
	 * @param {Function} get
	 * @param {Function} set
	 * @constructor
	 */
	function(get, set) {
		this.get = get;
		this.set = set;
	}
);

/**
 * Object with change notifications.
 */
type("Observable", [], {
	/**
	 * Attaches the new observer and returns function that detaches the observer.
	 * @param {Function} observer
	 * @return {Function} function to detach observer
	 */
	observe: function(observer) {}
},
	/**
	 *
	 * @param {Function} observer
	 * @constructor
	 */
	function(observer) {
		this.observe = observer;
	}
);

/**
 * Observable that can simulate a change.
 */
type("InvokableObservable", ["Observable"], {
	/**
	 * Simulates a change invoking the given observer.
	 * @param {Function} observer
	 */
	invokeObserver: function(observer) {}
},
	/**
	 *
	 * @param {Function} observer
	 * @param {Function} invokeObserver
	 * @constructor
	 */
	function(observer, invokeObserver) {
		this.observe = observer;
		this.invokeObserver = invokeObserver;
	}
);

/**
 * Observable read-only source.
 */
type("WatchGetter", ["Getter", "InvokableObservable"], {
},
	/**
	 *
	 * @param {Function} get
	 * @param {Function} observe
	 * @param {Function} invokeObserver
	 * @constructor
	 */
	function(get, observe, invokeObserver) {
		this.get = get;
		this.observe = observe;
		this.invokeObserver = invokeObserver;
	}
);

/**
 * Observable read-write source.
 */
type("WatchAccessor", ["WatchGetter", "Accessor"], {
},
	/**
	 *
	 * @param {Function} get
	 * @param {Function} set
	 * @param {Function} observe
	 * @param {Function} invokeObserver
	 * @constructor
	 */
	function(get, set, observe, invokeObserver) {
		this.get = get;
		this.set = set;
		this.observe = observe;
		this.invokeObserver = invokeObserver;
	}
);

/**
 * Sometimes unreadable source.
 */
type("CanGet", [], {
	/**
	 * Returns true if the source can be read.
	 * @return {Boolean} result
	 */
	canGet: function() {
		throw new Error("Not implemented");
	}
});

/**
 * Object with manual refreshing.
 */
type("Refreshable", [], {
	/**
	 * Triggers refresh.
	 */
	refresh: function() {}
},
	/**
	 *
	 * @param {Function} refresh
	 * @constructor
	 */
	function(refresh) {
		this.refresh = refresh;
	}
);

/**
 * Source state enumeration.
 */
var SourceState = new Enum("None", "Loading", "Loaded", "Committing", "Error");

/**
 * Abstract remote source.
 */
type("Source", ["Refreshable"], {
	/**
	 * State of the source.
	 * @type {WatchGetter}
	 */
	state: null,

	/**
	 * Error of the source.
	 * @type {WatchGetter}
	 */
	error: null
});

/**
 * Source with enumerable items.
 */
type("Enumerable", [], {
	/**
	 * Enumerates all items.
	 * @param {Function} iterator
	 * @return {Object} result of iterator
	 */
	each: function(iterator) {},

	isEmpty: function() {}
},
	/**
	 *
	 * @param {Object} each
	 * @constructor
	 */
	function(each, isEmpty) {
		this.each = each;
		this.isEmpty = isEmpty;
	}
);

type("WatchListable", ["Enumerable"], {
	/**
	 * Attaches the list observer and returns a function to detach the observer.
	 * @param {Object} listObserver
	 * @return {Function}
	 */
	observe: function(listObserver) {}
});

/**
 * Collection with sequential access.
 */
type("List", ["Enumerable"], {
	/**
	 * Number of items.
	 * @type {Getter}
	 */
	length: null,

	/**
	 * Returns item at index
	 * @param {Number} index
	 * @return {Object} item
	 */
	item: function(index) {},

	/**
	 * Returns accessor for item
	 * @param {Number} index
	 * @return {Accessor}
	 */
	accessor: function(index) {
		var self = this;
		return new Accessor(function() {
			return self.item(index);
		}, function(value) {
			return self.replaceAt(index, value);
		});
	},


	/**
	 * Returns all items in an array
	 * @return {Array} items
	 */
	allItems: function() {},

	/**
	 * Appends the new item and returns an index of the item.
	 * @param {Object} item
	 * @return {Number} index
	 */
	append: function(item) {},

	appendExisting: function(item) {
		if (exists(item)) {
			return this.append(item);
		} else {
			return this.length;
		}
	},

	appendMany: function(items) {
		var self = this;
		each(items, function(item) {
			self.append(item);
		});
	},

	/**
	 * Inserts the new item at the index if available,
	 * otherwise inserts the item at the beginning.
	 * Returns the index of the item.
	 * @param {Object} item
	 * @param {Number} [index]
	 * @return {Number} index
	 */
	insert: function(item, index) {},

	/**
	 * Removes the item and returns an index of the item.
	 * @param {Object} item
	 * @return {Number} index
	 */
	remove: function(item) {},

	removeMany: function(items) {
		var self = this;
		each(items, function(item) {
			self.remove(item);
		});
	},

	/**
	 * Removes an item at the given index and returns the item.
	 * @param {Object} index
	 * @return {Object} item
	 */
	removeAt: function(index) {},

	removeManyAt: function(indexes) {
		var self = this;
		each(indexes, function(index) {
			self.removeAt(index);
		});
	},

	/**
	 * Replaces item at index and returns previous item
	 * @param {Number} index
	 * @param {Object} item
	 * @return {Object} previous item
	 */
	replaceAt: function(index, item) {
		var old = this.removeAt(index);
	    this.insert(item, index);
		return old;
	},

	/**
	 * Moves an item from the source to the destination index
	 * and returns the item.
	 * @param {Number} source
	 * @param {Number} destination
	 * @return {Object} item
	 */
	move: function(source, destination) {
		var item = this.removeAt(source);
		this.insert(item, destination);
		return item;
	},

	/**
	 * Removes all items and return these items.
	 * @returns {Array} cleared elements
	 */
	clear: function() {},

	/**
	 * Returns index of item or null if not found
	 * @param {Object} item
	 * @return {Number} index
	 */
	indexOf: function(item) {}
},
	/**
	 * Builds a new list on top of the array.
	 * @param {Array} array
	 * @constructor
	 */
	function(array) {
		array = getArray(array);
		var self = this;
		this.length = new Getter(function() {
			return array.length;
		});
		this.item = function(index) {
			return array[index];
		};
		this.allItems = function() {
			return array.slice(0);
		};
		this.append = function(item) {
			array.push(item);
			return array.length - 1;
		};
		this.insert = function(item, index) {
			if (!exists(index)) {
				index = 0;
			}
			array.splice(index, 0, item);
			return index;
		};
		this.remove = function(item) {
			var index = this.indexOf(item);
			if (exists(index)) {
				array.splice(index, 1);
			}
			return index;
		};
		this.removeAt = function(index) {
			return array.splice(index, 1)[0];
		};
		this.clear = function() {
			var old = array;
			array = [];
			return old;
		};
		if (isFunction(array.indexOf)) {
			this.indexOf = function(item) {
				var index = array.indexOf(item);
				return (index === -1) ? null : index;
			};
		} else {
			this.indexOf = function(item) {
				for (var i in array) {
					if (array[i] === item) {
						return i;
					}
				}
				return null;
			};
		}
		this.each = function(iterator) {
			return iterate(array, iterator);
		};
		this.isEmpty = function() {
			return array.length === 0;
		};
	}
);

/**
 * Lookup
 */
type("Lookup", [], {
	/**
	 * Gets a value using the key.
	 * @param {String} key
	 * @return {Object} value
	 */
	get: function(key) {
		throw new Error("Not implemented");
	}
},
	function(values) {
		this.get = function(key) {
			var value = values[key];
			if (exists(value)) {
				if (value.Getter) {
					return value.get();
				} else if (isFunction(value)) {
					return value();
				}
			}
			return value;
		};
	}
);

/**
 * Map-like collection.
 */
type("Dictionary", ["Lookup", "Enumerable"], {

	/**
	 * Sets the value with the key and returns a previous value.
	 * @param {String} key
	 * @param {String} value
	 * @return {Object} old
	 */
	set: function(key, value) {
		throw new Error("Not implemented");
	},

	/**
	 * Get values of the all properties.
	 * @return {Object} values
	 */
	getAll: function() {
		throw new Error("Not implemented");
	},

	/**
	 * Updates multiple properties.
	 * @param {Object} values
	 * @return {Object} changes
	 */
	update: function(values) {
		throw new Error("Not implemented");
	},

	/**
	 * Replaces multiple properties.
	 * @param {Object} values
	 * @return {Object} changes
	 */
	replace: function(values) {
		throw new Error("Not implemented");
	},

	/**
	 * Deletes all properties and returns their values.
	 * @method clear
	 * @return {Object} changes
	 */
	clear: function() {
		throw new Error("Not implemented");
	}
});

/**
 * Attachable source.
 */
type("Attachable", [], {
	/**
	 * Attaches the new item and returns a function to detach this item.
	 * @param {Object} item
	 * @param {Function} item remover
	 */
	attach: function(item) {
		throw new Error("Not implemented");
	}
});

/**
 * Attachable source that can enumerate its items.
 */
type("EnumerableAttachable", ["Attachable", "Enumerable"]);



type("Equatable", [], {
	/**
	 *
	 */
	equals: function(item) {
		return this == item;
	}
});
