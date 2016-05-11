/**
 * @author Tom
 */

/**
 * Creates a watch value and binds it to the source.
 * @param {Object} source
 * @param {Function} template
 * @return {WatchValue}
 */
function $V(source, template) {
	return bind.toAccessor(new WatchValue(), source, template);
}

/**
 * Creates two-way convertor from the source.
 * @param {Accessor} source
 * @param {Object} template
 */
function $C(source, template) {
	return bind.accessor(new WatchValue(), source, template);
}

/**
 * Observable value.
 */
type("WatchValue", ["WatchAccessor"], {
}, 
	/**
	 * Initializes a new watch value with the given value.
	 * @param {Object} value
	 */
	function(value) {
		var valueObservers = commands();
		this.WatchAccessor(
			function() {
				return value;
			}, function(newValue) {
				if (!equals(value, newValue)) {
					var oldValue = value;
					value = newValue;
					valueObservers(newValue, oldValue);
				}
			}, valueObservers.attach,
			function(observer) {
				return observer(value, value);
			}
		);
	}
);


type("WatchPair", ["WatchValue"], {
	key: null
},
	function(key, value) {
		this.key = key;
		this.WatchValue(value);
	}
);

