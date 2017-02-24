/**
 * Element.js
 * @author Tom
 */


// "Element" is used by Firefox for native DOM elements!

/**
 * Wrapper for a native DOM element. It handles cross-browser compatibility.
 */
type("XElement", ["List"], {
	
	/**
	 * Attaches the observer to a click event. Returns a function to detach the observer.
	 * @param {Function} observer
	 * @return {Function} function to remove observer
	 */
	observeClick: function(observer) {
		return this.observeEvent("click", observer);
	},

	/**
	 * Attaches the observer to a change event. Returns a function to detach the observer.
	 * @param {Function} observer
	 * @return {Function} function to remove observer
	 */
	observeChange: function(observer) {
		return this.observeEvent("change", observer);
	},
	
	observeKeyPress: function(observer) {
		return this.observeEvent("keypress", function(e) {
			var key = e.keyCode || e.which;
			return observer(key);
		});
	},
	
	/**
	 * Attaches the observer to an event with the given name. Returns a function to detach the observer.
	 * @param {String} eventName
	 * @param {Function} observer
	 * @return {Function} function to remove observer
	 */
	observeEvent: function(eventName, observer) {
		var self = this;
		return obtain(obtain(this, "eventObservers", construct(Object)), eventName, function() {
			var observers = commands();
			self.dom["on" + eventName] = function(e) {
				if (window.event) {
					e = window.event;
				}
 				return observers(e);
			};
			return observers;
		}).attach(observer);
	},
	
	/**
	 * Triggers an event with the given name. Returns an event object of the event.
	 * @param {String} eventName
	 * @return {Event} event
	 */
	dispatchEvent: function(eventName) {
		return Dom.Event.dispatch(this.dom, eventName);
  },
	
	getters: {},
	setters: {},
	/**
	 * Returns a value of an attribute with the given name.
	 * @param {String} name
	 * @return {Object} value
	 */
	getAttribute: function(name) {
    var getter = this.getters[name];
		return exists(getter)
			? getter.call(this)
			: Dom.get(this.dom, name);
	},
	
	/**
	 * Sets the value to an attribute with the given name. Returns the element.
	 * @param {String} name
	 * @param {Object} value
	 * @return {XElement}
	 */
	setAttribute: function(name, value) {
    var setter = this.setters[name];
		if (exists(setter)) {
			return setter.call(this, value);
		}
		Dom.set(this.dom, name, value);	
		return this;
	},
	
	/**
	 * Set multiple attributes
	 * @param {Object} values
	 */
	attribute: function(values) {
		var self = this;
		enumerate(values, function(value, name) {
			if (name.charAt(0) == "$") {
				var key = name.substr(1);
				if (isFunction(self[key])) {
					self[key](value);
				} else {
					self[key] = value;
				}
			} else {
				self.setAttribute(name, value);
			}
		});
		return this;
	},
	
	styleGetters: {},
	styleSetters: {},
	/**
	 * Gets style for the key.
	 * @param {String} key
	 * @return {Object} value
	 */
	getStyle: function(key) {
    var getter = this.styleGetters[key];
		return exists(getter)
			? getter(this.dom)
			: Dom.Style.get(this.dom, name);
	},

	/**
	 * Sets a style with the key and the value or styles with the values. Returns the element.
	 * @param {String} key
	 * @param {Object} value
	 */
	setStyle: function(key, value) {
    var setter = this.styleSetters[key];
		if (exists(setter)) {
			var self = this;
			enumerate(setter(value), function(v, k) {
				Dom.Style.set(self.dom, k, v);
			});
		} else {
			Dom.Style.set(this.dom, key, value);
		}
		return this;
	},
	
	/**
	 * Sets style values
	 * @param {Dom} dom
	 * @param {Object} values
	 */
	style: function(values) {
		var self = this;
		enumerate(values, function(value, key) {
			self.setStyle(key, value);
		});
		return this;
	},

	/**
	 * Returns an accessor for a attribute with the name.
	 * @param {String} name
	 * @return {Accessor} accessor
	 */
	accessor: function(name) {
		var self = this;
		return new Accessor(function() {
			return self.getAttribute(name);
		}, function(value) {
			return self.setAttribute(name, value);
		});
	},

	/**
	 * Returns content.
	 * @return {Array}
	 */
	getContent: function() {
		return Dom.Content.get(this.dom);
	},
	
	/**
	 * Adds the value to content. Returns a number of added nodes.
	 * @param {Object} value
	 * @return {Number} number of nodes
	 */
	addContent: function(value) {
		schedule(this.itemsUpdated);
		return Dom.Content.add(this.dom, value);
	},

	/**
	 * Returns a name of a tag of the element.
	 * @return {String} tag
	 */
	getTag: function() {
		return this.dom.tagName.toLowerCase();
	},
	
	getParent: function() {
		return $E(this.dom.parentNode);
	},
	
	detach: function() {
		var parent = this.getParent();
		if (exists(parent)) {
			parent.remove(this);
		}
	},
	
	destroy: function() {
		delete this.dom.$element;
		delete this.dom;
	},
	
	// Enumerable
	each: function(iterator) {
		return Dom.List.each(this.dom, function(item, index) {
			return iterator($E(item), index);
		});
	},
	
	// List
	length: function() {
		return Dom.List.length(this.dom);
	},
	item: function(index) {
		return $E(Dom.List.item(this.dom, index));
	},
	append: function(item) {
		schedule(this.itemsUpdated);
		return Dom.List.append(this.dom, item);
	},
	insert: function(item, index) {
		schedule(this.itemsUpdated);
		return Dom.List.insert(this.dom, item, index);
	},
	remove: function(item) {
		schedule(this.itemsUpdated);
		return Dom.List.remove(this.dom, item)
	},
	removeAt: function(index) {
		schedule(this.itemsUpdated);
		return Dom.List.removeAt(this.dom, index)
	},
	move: function(source, destination) {
		schedule(this.itemsUpdated);
		return Dom.List.move(this.dom, source, destination);
	},
	clear: function() {
		schedule(this.itemsUpdated);
		return Dom.List.clear(this.dom);
	}
},
	/**
	 * Creates a new element from the tag name or a native DOM element, sets the attributes, and adds the content.
	 * @param {String, Dom} tag name or source
	 * @param {Object} [attributes]
	 * @param {Object} ... content
	 */
	function(source, attributes) {
		var self = this;
		
		self.itemsUpdated = commands();
		if (isString(source)) {
			source = document.createElement(source);
		} else if (isArray(source)) {
			source = Dom.createElementNS(document, source[0], source[1]);
		}
		// <LEAK>
		self.dom = source;
		try {
			source.$element = self;
		} catch (e) {
			// ignore (IE expando bug, e.g. DispHTMLDOMTextNode)
		}
		XElement.elements.push(self);
		// </LEAK>
		self.length = new Getter(curry(XElement.getLength, self)); // closure leak avoidance
		if (exists(attributes)) {
			self.attribute(attributes);
		}
		iterate(arguments, function(item) {
			self.addContent(item);
		}, 2);
	}
);

XElement.prototype.setters.style = XElement.prototype.style;

XElement.getLength = function(element) {
	return Dom.List.length(element.dom);
};

XElement.elements = [];
XElement.cleanNow = function() {
	var elements = [];
	var body = document.body;
	var html = body.parentNode;
	iterate(XElement.elements, function(item) {
		if (item.dom && item.dom.offsetParent || item === body || item === html) {
			elements.push(item);
		} else {
			item.destroy();
		}
	});
	XElement.elements = elements;
};

XElement.clean = function() {
	schedule(XElement.cleanNow);
};

/**
 * Returns an element by the id or from the native DOM element.
 * @param {String, Dom} source
 * @return {XElement} element
 */
function $E(source) {
	if (isString(source)) {
		source = document.getElementById(source);
	}
	if (!exists(source)) {
		return source;
	}
	var element = source.$element;
	if (exists(element)) {
		return element;
	}
	return new Html(source);
}
