/**
 * Dom
 * @author Tom
 */

/**
 * Returns dom node
 * @param {Object} object
 * @retutn {Dom} dom
 */
function getDom(object) {
	if (!exists(object)) {
		return Html.hidden().dom;
	}
	if (isDom(object)) {
		return object;
	}
	if (object.XElement) {
		return object.dom;
	}
	return document.createTextNode(str(object));
}

var Dom = {
	
	Event: {
		/**
		 * Observe event
		 * @param {Dom} dom
		 * @param {String} eventName
		 * @param {Function} observer
		 * @return {Function} function to remove observer
		 */
		observe: function(dom, eventName, observer) {
		  if (dom.addEventListener) {
		    dom.addEventListener(eventName, observer, false);
				return function() {
		      dom.removeEventListener(eventName, observer, false);
				};
		  } else {
				eventName = "on" + eventName;
		    dom.attachEvent(eventName, observer);
				return function() {
					dom.detachEvent(eventName, observer);
				};
		  }
		},
		
		/**
		 * Setup observer that is removed after is called for the first time
		 * @param {Dom} dom
		 * @param {String} eventName
		 * @param {Function} observer
		 * @return {Function} function to remove observer
		 */
		observeOnce: function(dom, eventName, observer) {
			// LEAK! Solution: Timer based scan for removed elements
			var stop;
			var method = function(evt) {
				stop();
				observer(evt);
			};
			stop = Dom.observe(dom, eventName, method);
			return stop;
		},
		
		/**
		 * Fires event
		 * @param {Dom} dom
		 * @param {String} eventName
		 * @return {Event} event
		 */
		dispatch: function(dom, eventName) {
			var event;
			if (document.createEvent) {
				event = document.createEvent("HTMLEvents");
				event.initEvent(eventName, true, true);
				dom.dispatchEvent(event);
			} else {
				event = document.createEventObject();
				dom.fireEvent("on" + eventName, event);
			}
			return event;
	  }
	},
	
	List: {
		// Enumerable
		each: function(dom, iterator) {
			return iterate(dom.childNodes, iterator);
		},
		
		// List
		length: function(dom) {
			return dom.childNodes.length;
		},
		item: function(dom, index) {
			return dom.childNodes[index];
		},
		append: function(dom, item) {
			dom.appendChild(getDom(item));
			return dom.childNodes.length - 1;
		},
		insert: function(dom, item, index) {
			if (!exists(index)) {
				index = 0; 
			}
			var items = dom.childNodes;
			if (index < items.length){
				dom.insertBefore(getDom(item), items[index]);
				return index;
			}
			while (index-- > items.length) {
				Dom.List.append(dom, null);
			}
			return Dom.List.append(dom, item);
		},
		remove: function(dom, item) {
			try {
				dom.removeChild(getDom(item));
				return Number.MAX_VALUE; // FIXME should return index
			} catch (e) {
				return -1;
			}
		},
		removeAt: function(dom, index) {
			var items = dom.childNodes;
			if (index >= items.length) {
				return null;
			}
			return dom.removeChild(items[index]);
		},
		clear: function(dom) {
			var items = [];
			var item;
			while ((item = dom.firstChild)) {
				items.push(dom.removeChild(item));
			}
			return items;
		}
	},
	
	Content: {
		get: function(dom) {
			return any(dom.textContent, dom.innerText);
		},
		add: function(dom, value) {
			if (!exists(value)) {
				return 0;
			}
			if (!isDom(value)) {
				if (value.XElement) {
					value = value.dom;
				} else {
					if (isArray(value) || value.Enumerable) {
						var number = 0;
						each(value, function(item) {
							number += Dom.Content.add(dom, item);
						});
						return number;
					} else {
						value = document.createTextNode(str(value));
					}
				}
			}
			dom.appendChild(value);
			return 1;
		},
		/**
		 * Sets content
		 * @param {Dom} dom
		 * @param {Object} ... content
		 */
		set: function(dom) {
			var old = Dom.List.clear(dom);
			iterate(arguments, function(value) {
				if (exists(value)) {
					Dom.Content.add(dom, value);
				}
			}, 1);
			return old;
		}
	},

	Style: {},
	
	getHead: function() {
		return obtain(Dom, "$head", function() {
			return document.getElementsByTagName("head")[0];
		});
	}
};

delayedBind(Dom, "createElementNS", 
	function() {
		return document.createElementNS
			? function(document, uri, name) {
				return document.createElementNS(uri, name);
			}
			: function(document, uri, name) {
				var namespace = name.split(":", 2)[0];
				if (!includes(document.namespaces, function(item) {
					return item.name == namespace && item.urn == uri;
				})) {
					document.namespaces.add(namespace, uri);
				}
				return document.createElement(name);
			};
	}
);

Dom.get = function(dom, name) {
	return dom[name];
};
delayedBind(Dom, "set",
	function(dom) {
		return dom.setAttributeNS
			? function(dom, name, value) {
				if (exists(value)) {
					dom.setAttributeNS(null, name, value);
				} else {
					dom.removeAttributeNS(null, name);
				}
				return dom;
			}
			: function(dom, name, value) {
				dom[name] = value;
				return dom;
			};
	}
);

delayedBind(Dom.Style, "get",
	function(document) {
		return document.defaultView
			? function(dom, key) {
				var value = dom.style[key];
				if (!exists(value)) {
					var css = document.defaultView.getComputedStyle(dom, null);
					if (exists(css)) {
						value = css[key];
					}
				}
				return value;
			}
			: function(dom, key) {
				return dom.style[key];
			};
	} 
);
Dom.Style.set = function(dom, key, value) {
	if (exists(value)) {
		dom.style[key] = value;
	} else {
		// CHECK THAT
		dom.style[key] = "";
	}
	return dom;
};
