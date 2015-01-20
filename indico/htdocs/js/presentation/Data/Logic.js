/**
 * Logic
 * @author Tom
 */

function callOrGet(source) {
	return isFunction(source) ? source() : source;
}


/**
 * If the template does not exist returns pass,
 * if the template is a function returns the template,
 * otherwise returns a function that
 * returns a property of an input value determined by the template.
 * @param {Function, String} [template]
 * @return {Function}
 */
function obtainTemplate(template) {
	if (!exists(template)) {
		return pass;
	}
	if (isFunction(template)) {
		return template;
	}
	return function(value) {
		return exists(value) ? value[template] : null;
	};
}

/** 
 * If the template does not exist returns the setter,
 * if the template is a function returns a function
 * that applies the template on an input value and invokes the setter,
 * otherwise returns a function that invokes the setter
 * with a propertyof an input value determined by the template.
 * @param {Function, String} template
 * @param {Function} setter
 * @return {Function}
 */
function templatedSetter(template, setter) {
	if (!exists(template)) {
		return setter;
	}
	if (isFunction(template)) {
		return function(value) {
			setter(template(value));
		};
	}
	return function(value) {
		setter(exists(value) ? value[template] : null);
	};
}

/**
 * Returns a template that returns an input value if exists.
 * If the value does not exist, returns the substitution.
 * @param {Object} substitution
 * @return {Function} template
 */
function getNoneTemplate(substitution) {
	return function(value) {
		return exists(value) ? value : callOrGet(substitution);
	};
}

/**
 * Returns a template that returns an input value
 * if the value represents empty string, otherwise returns the substitution.
 * @param {Object} substitution
 * @return {Function} template
 */
function getBlankTemplate(substitution) {
	return function(value) {
		return empty(value) ? callOrGet(substitution) : value;
	};
}

function replaceEmpty(value, substitution) {
	return empty(value) ? callOrGet(substitution) : value;
}

/**
 * Returns a template that returns depending on an input value:
 * noneSubstitution - if the value does not exist,
 * emptySubstitution - if the value is empty,
 * otherwise it applies the template to the input value and returns the result from the template.
 * @param {Function} template
 * @param {Object} noneSubstitution
 * @param {Object} emptySubstitution
 * @return {Function}
 */
function existenceTemplator(template, noneSubstitution, emptySubstitution) {
	return function(value) {
		return exists(value)
			? empty(value)
				? emptySubstitution
				: template(value)
			: noneSubstitution;
	};
}

/**
 * Returns a template splitter.
 * @param {Object} templates
 * @oaram {Function} [otherwise]
 * @return {Function}
 */
function templateSplitter(templates, otherwise) {
	otherwise = obtainTemplate(otherwise);
	return function(value) {
		var template = templates[value];
		if (exists(template)) {
			return template(value);
		} else {
			return otherwise(value);
		}
	};
}

/**
 * Returns a template that returns a case according an input value.
 * @param {Dictionary|Object} values
 * @return {Function}
 */
function splitter(values) {
	if (values.Lookup) {
		return function(key) {
			return values.get(key);
		};
	} else {
		return function(key) {
			return values[key];
		};
	}
}

/**
 * Selects a value from the options.
 */
type("Chooser", ["WatchAccessor"], {
	/**
	 * Returns a setter that selects a value from the options according the key.
	 * @param {String} key
	 * @return {Function} setter
	 */
	option: function(key) {
		var self = this;
		return function() {
			self.set(key);
		};
	}
},
	/**
	 * Initializes chooser with the options.
	 * @param {Object} options
	 */
	function(options) {
		var value = $V();
		mixinInstance(this, value, WatchGetter);
		this.set = templatedSetter(splitter(options), value.set);
	}
);

/**
 * Switchable getter.
 */
type("Switch", ["WatchGetter"], {
},
	/**
	 * Initializes switch with states (string) and transitions (array).
	 * @param {Array, String} ... transitions, states
	 */
	function() {
		var state = $V();
		var self = this;
		mixinInstance(this, state, WatchGetter);
		iterate(arguments, function(value) {
			if (isArray(value)) {
				self[value[0]] = function() {
					iterate(value, function(item) {
						state.set(item);
					});
				};
			} else {
				self[value] = function() {
					state.set(value);
				};
			}
		});
	}
);

var Logic = {
	/**
	 * Allows only one accessor to have other value than the default value.
	 * @param {Array} accessors
	 * @param {Object} defaultValue
	 */
	onlyOne: function(accessors, defaultValue) {
		iterate(accessors, function(accessor) {
			accessor.observe(function(value) {
				if (value !== defaultValue) {
					iterate(accessors, function(acc) {
						if (acc !== accessor) {
							acc.set(defaultValue);
						}
					});
				}
			});
		});
	}
};
