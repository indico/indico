/**
 * @author Tom
 */

/**
 * Namespace for widgets;
 */
var Widget = {};

function WidgetContext(value) {
	return (value === window) ? new WidgetContext() : value;
}

WidgetContext.prototype = Widget;


function WidgetBuilder(method, attributes) {
	var builder = function(source, attribs) {
		var args = $A(arguments);
		if (args.length >= 2) {
			args[1] = merge(args[1] , attributes);
		}
		return method.apply(this, args);
	};
	builder.customize = function(attribs) {
		return WidgetBuilder(method, merge(attributes, attribs));
	};
	extend(builder, WidgetBuilder);
	return builder;
}

