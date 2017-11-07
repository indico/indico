/**
 * WatchCollection
 * @author Tom
 */


/**
 * Creates a watch list and binds it to the source.
 * @param {Object} source
 * @param {Function} template
 * @return {WatchCollection}
 */
function $L(source, template) {
	return bind.toList(new WatchList(), source, template);
}

/**
 * Observable list.
 */
type("WatchList", ["WatchListable", "List"], {
	/**
	 * Creates a new watch accessor for the key.
	 * @param {String} key
	 * @return {WatchAccessor}
	 */
	accessor: function(index) {
		var self = this;
		return new WatchAccessor(function() {
			return self.item(index);
		}, function(value) {
			return self.replaceAt(index, value);
		}, function(observer) {
			return self.observe({
				itemAdded: function(it, idx) {
					if (idx == index) {
						observer(it, self.item(index + 1));
					} else if (idx < index) {
						observer(self.item(index), self.item(index + 1));
					}
				},
				itemRemoved: function(it, idx) {
					if (idx == index) {
						observer(self.item(index), it);
					} else if (idx < index) {
						observer(self.item(index), self.item(index - 1));
					}
				},
				itemMoved: function(it, idx) {
					var src = idx[0];
					var dst = idx[1];
					if (src == index) {
						if (dst != index) {
							observer(self.item(index), it);
						}
					} else if (src < index) {
						if (dst >= index) {
							observer(self.item(index), self.item(index - 1));
						}
					} else {
						if (dst <= index) {
							observer(self.item(index), self.item(index + 1));
						}
					}
				}
			});
		}, function(observer) {
			var value = self.item(index);
			return observer(value, value);
		});
	}
},
	/**
	 * Initializes a new watch list with the items.
	 * @param {Object} ... items
	 */
	function() {
		var self = this;
		var items = new List($A(arguments));
		var length = $V(items.length);
		var listObservers = commands();
	
		// Enumerable
		this.each = items.each;
		this.isEmpty = items.isEmpty;
			
		// List
		this.length = getWatchGetter(length);
		this.item = items.item;
		this.allItems = items.allItems;
		this.append = function(item) {
			var index = items.append(item);
			listObservers("itemAdded", item, index, self);
			length.set(items.length.get());
			return index;
		};
		this.insert = function(item, index) {
		    if (!exists(index) || index < items.length.get()){
				index = items.insert(item, index);
				listObservers("itemAdded", item, index, self);
				length.set(items.length.get());
				return index;
			}
			while (index-- > items.length) {
				self.append(null);
			}
			return self.append(item);
		};
		this.remove = function(item) {
			var index = items.remove(item);
			if (index >= 0) {
				listObservers("itemRemoved", item, index, self);
				length.set(items.length.get());
			}
			return index;
		};
		this.removeAt = function(index) {
			var item = items.removeAt(index);
			if (exists(item)) {
				listObservers("itemRemoved", item, index, self);
			}
			length.set(items.length.get());
			return item;
		};
		this.move = function(source, destination) {
			var item = items.move(source, destination);
			listObservers("itemMoved", item, [source, destination], self);
			length.set(items.length.get());
			return item;
		};
		this.clear = function() {
			// FIXME?
			var old = items.clear();
			iterate(old, function(item) {
				listObservers("itemRemoved", item, 0, self);
			});
			length.set(items.length.get());
			return old;
		};
		this.indexOf = items.indexOf;
		
		// WatchListable
		this.observe = function(listObserver) {
			var observer = isFunction(listObserver) ? listObserver : function(evt) {
				var eventObserver = listObserver[evt];
				if (exists(eventObserver)) {
					eventObserver.apply(listObserver, $A(arguments, 1));
				}
			};
			return listObservers.attach(observer);
		};
	}
);

function processListable(source, processor) {
	each(source, processor.itemAdded);
	if (source.WatchListable) {
		return source.observe(processor);
	}
}

function processListableAccessor(source, key, append, remove) {
	processListable(source, {
		itemAdded: function(item) {
			var accessor = item[key];
			if (exists(accessor)) {
				bind.setter(accessor, accessor, function(value, old) {
					if (exists(old)) {
						remove(old);
					}
					if (exists(value)) {
						append(value);
					}
				});
			}
		},
		itemRemoved: function(item) {
			var accessor = item[key];
			if (exists(accessor)) {
				bind.stop(accessor);
				var old = accessor.get();
				if (exists(old)) {
					remove(old);
				}
			}
		}
	});
}

newWatchList = construct(WatchList);
getWatchList = provide(WatchList);
