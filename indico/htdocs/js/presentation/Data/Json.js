/**
 * @author Tom
 */

var Json = {
	/**
	 * Returns true if the json is valid.
	 * @param {String} json
	 * @return {Boolean}
	 */
	validate: function(json) {
		// from prototype
    json = json.replace(/\\./g, '@').replace(/"[^"\\\n\r]*"/g, '');
    return (/^[,:{}\[\]0-9.\-+Eaeflnr-u \n\r\t]*$/).test(json);
	},
	
	/**
	 * Decodes the json into an object.
	 * @param {String} json
	 * @return {Object}
	 */
	read: function(json) {
		try {
			if (!Json.validate(json)) {
				throw "Invalid json.";
			}
			return eval("(" + json + ")");
		} catch (e) {
			throw "Cannot read json. " + e;
		}
	},
	
	/**
	 * Encodes the object into a json.
	 * @param {Object} object
	 * @return {String} json
	 */
	write: function(object) {
		if (!exists(object)) {
			return "null";
		}
		switch(typeof(object)) {
			case "boolean":
			case "number":
				return str(object);
			case "string":
				return escapeString(object);
			case "object":
				if (object.Getter) {
					return Json.write(object.get());
				}
				if (object.Dictionary) {
					object = object.getAll();
				}
				if (object.Enumerable) {
					return "[" + object.each(stacker(Json.write)).join(",") + "]";
				}
				if (isArray(object)) {
					return "[" + iterate(object, stacker(Json.write)).join(",") + "]";
				}
				var properties = [];
				enumerate(object, function(value, key) {
					if (!isFunction(value)) {
						properties.push(escapeString(key) + ":" + Json.write(value));
					}
				});
				return "{" + properties.join(",") + "}";
			default:
				throw "Invalid object: " + str(object);
		}
	}
};

var $J = Json.write;

function jsonAlert(arg) {
	alert(Json.write(arg));
}
