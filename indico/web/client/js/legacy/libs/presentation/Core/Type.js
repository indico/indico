/**
 * @author Tom
 */

/**
 * Creates a named type from the mixins, the code, and with the constructor.
 * @param {String} name
 * @param {Array} mixins
 * @param {Object} [code]
 * @param {Function} [constructor]
 * @return {Function} constructor
 */
function type(name, mixins, members, constructor) {
	constructor = any(constructor, function() {});
	members = getObject(members);
	members[name] = constructor;
	members.constructor = constructor;
	constructor.prototype = members;
	constructor.mixins = [name];
	mixinType(constructor, mixins);
	this[name] = constructor;
	return constructor;
}

/**
 * Mixes mixins into the target type.
 * @param {Function} target
 * @param {Array} mixins
 * @return {Function} target
 */
function mixinType(target, mixins) {
	var code = target.prototype;
	var mixs = target.mixins;
	iterate(mixins, function(mixinName) {
		var mixinCode = eval(mixinName);
		enumerate(mixinCode.prototype, function(value, key) {
			if (!exists(code[key]) || code[key] === Object.prototype[key]) {
				code[key] = value;
			}
		});
		if (exists(mixinCode.mixins)) {
			iterate(mixinCode.mixins, function(item) {
				if (!code[item]) {
					mixs.push(item);
				}
			});
		} else {
			// simple type
			if (!code[mixinName]) {
				mixs.push(mixinName);
			}
			init(code, mixinName, mixinCode);
		}
	});
	return target;
}

/**
 * Mixes the mixin of the source into the target instance.
 * @param {Object} target
 * @param {Object} source
 * @param {Object} mixin
 * @return {Object} target;
 */
function mixinInstance(target, source, mixin) {
	enumerate(mixin.prototype, function(value, key) {
		target[key] = source[key];
	});
	return target;
}

/**
 * Creates an enumeration of the given names.
 * @param {String} ... names
 * @constructor
 */
function Enum() {
	var self = this;
	iterate(arguments, function(item, index) {
		self[item] = index;
	});
}
