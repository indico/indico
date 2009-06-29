/**
 * @author Tom
 */

type("ResourceReference", ["DataReference"], {
	
});

var Reso

var Resource = {
	
	get: function(store, id, revision) {
		return function() {
			
		}
	},
	build: function(store, id, data) {
		store.
	},
	
	
};


type("Resource", ["Observable"], {
	get: function(key) {},
	getAll: function() {},
	serialize: function() {
		return enumerate(this.getAll(), mapper(function(values, key) {
			return values.each(stacker(function(item, index) {
				switch (typeof(item)) {
			  	case "boolean":
			  	case "number":
			  	case "string":
			  		return item;
			  	case "object":
						if (!exists(item)) {
							return null;
						}
						if (value instanceof ResourceReference) {
							return {
								type: "reference",
								id: item.id.get(),
								value: item.revision.get()
							};
						}
						return str(item);
					default:
						return null;
			  }
			}));
		}));
	}
},
	function(store, data) {
		var observers = commands();
		this.Observable(observers.attach);
		
		function attachList(list) {
	  	list.observe(observers);
			return list;
		} 
		
		var properties = enumerate(data, mapper(function(values, key) {
			return attachList($L(values, function(value) {
				switch (typeof(value)) {
			  	case "boolean":
			  	case "number":
			  	case "string":
			  		return value;
			  	case "object":
						if (!exists(value)) {
							return null;
						}
			  		switch (value.type) {
							case "reference":
								return store.getReference(value.id, value.revision);
							default:
								return null;
						}
					default:
						return null;
			  }
			}));
		}));
		
		this.get = function(key) {
			var list = properties[key];
			if (!exists(list)) {
		  	properties[key] = attachList(new WatchList());
		  }
			return list;
		};
		this.getAll = function() {
			var result = {};
			enumerate(properties, mapper(function(list, key) {
				if (exists(list) && list.length.get() > 0) {
					result[key] = list;
				}
			}));
			return result;
		};
		this.accessor = function() {
			var current = this;
			iterate(arguments, function(arg) {
				if (current.Resource) {
					current = isNumber(arg)
						? current.get("$").accessor(arg)
						: current.get(arg);
				} else if (current.WatchList) {
					if (isNumber(arg)) {
						current = current.accessor(arg);
					} else {
						current = current.accessor(0);
						if (current)
					}
				}
				current = current.Resource
					? 
					: current.WatchList
						? isNumber(arg)
							? current.accessor(arg)
							: current.accessor(0).
				} else 
				current.
			})
		}
	}
);

type("ResourceStore", ["DataStore"], {
	
},
	function(url, initializer) {
		var store = this;
		var dataStore = new DataStore(url, function() {
			return buildResource(initializer());	
		});

		function buildResource() {
			
		}
		
	}
);
