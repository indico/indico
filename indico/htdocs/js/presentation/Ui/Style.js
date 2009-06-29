/**
 * Styles.js
 * @author Tom
 */

var Style = {
	
	/**
	 * Gets raw style
	 * @param {Dom} dom
	 * @param {String} key
	 * @return {Object} value
	 */
	getRaw: function(dom, key) {
		var value = dom.style[key];
		if (!exists(value) && exists(document.defaultView)) {
			var css = document.defaultView.getComputedStyle(dom, null);
			if (exists(css)) {
				value = css[key];
			}
		}
		return value;
	},
	
	/**
	 * Gets style
	 * @param {Dom} dom
	 * @param {String} key
	 * @return {Object} value
	 */
	get: function(dom, key) {
		var getter = Style.getters[key];
		if (exists(getter)) {
			return getter(dom);
		} else {
			var value = Style.getRaw(dom, key);
			return value == "auto" ? null : value;
		}
	},

	/**
	 * Sets style
	 * @param {Dom} dom
	 * @param {String} key
	 * @param {Object} value
	 */
  set: function(dom, key, value) {
    var setter = Style.setters[key];
		if (exists(setter)) {
			return setter(dom, value);
		} else {
			if (exists(value)) {
				dom.style[key] = value;
			} else {
				// CHECK THAT
				dom.style[key] = "";
			}
			return dom;
		}
  },
	
	/**
	 * Gets style values
	 * @param {Dom} dom
	 * @param {Array} [keys]
	 * @return {Object} values
	 */
	getValues: function(dom, keys) {
		var values = {};
		if (exists(keys)) {
			iterate(keys, function(key) {
				values[key] = Style.get(dom, key);
			});
		} else {
			var currentStyle = exists(dom.currentStyle) ? dom.currentStyle : dom.style;
			enumerate(currentStyle, function(value, key) {
				if (exists(value) && !isFunction(value)) {
					values[key] = Style.get(dom, key);
				}
			});
		}
		return values;
	},

	/**
	 * Sets style values
	 * @param {Dom} dom
	 * @param {Object} values
	 */
	setValues: function(dom, values) {
		enumerate(values, function(value, key) {
			Style.set(dom, key, value);
		});
		return dom;
	},

  getOpacity: function(dom) {
		var value = dom.style.opacity;
		return exists(value) ? parseFloat(value) : 1.0;
  },

  setOpacity: function(dom, value) {
    dom.style.opacity = (value == 1 || value === '')
			? '' : (value < 0.00001) ? 0 : value;
    return dom;
  },
	
	getFloat: function(dom) {
		var style = dom.style;
		return (style.cssFloat === undefined)
			? style.styleFloat : style.cssFloat;
	},

	setFloat: function(dom, value) {
		var style = dom.style;
		if (style.cssFloat === undefined) {
			style.styleFloat = value;
		} else {
			style.cssFloat = value;
		}
		return dom;
	}
};

Style.getters = {};
Style.setters = {};
enumerate({
	"opacity": "Opacity",
	"float": "Float",
	"styleFloat": "Float",
	"cssFloat": "Float"
}, function(value, key) {
	Style.getters[key] = Style["get" + value];
	Style.setters[key] = Style["set" + value];
});

