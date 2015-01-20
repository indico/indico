/**
 * @author Tom
 */

/**
 * Namespace for widgets;
 */
var Widget = {
	view: function(properties) {
		var context = new WidgetContext();
		if (this instanceof WidgetContext) {
			extend(context, this);
			context.parent = this;
		}
		if (exists(properties)) {
			extend(context, properties);
		}
		var view = $V();
		mixinInstance(context, view, WatchGetter);
		context.navigate = function(target) {
			context.render(view, target);
			return context;
		};
		return context;
	},
	navigator: function(target) {
		return curry(this.navigate, target);
	},
	getTarget: function(target) {
		throw new Exception("Cannot lookup target.", {
			target: target
		});
	},
	template: function(target, properties) {
		var $ = this;
		return function(item) {
			var data = {};
			if (exists(properties)) {
				extend(data, properties);
			}
			var view;
			if (exists(item) && item.WatchGetter) {
				if ("key" in item) {
					data.key = item.key;
				}
				data.value = item.get();
				item.observe(function(value) {
					view.value = value;
					view.navigate(target);
				});
			} else {
				data.value = item;
			}
			view = $.view(target, data);
			return view;
		};
	},
	presenter: function(source, target, properties) {
		return this.template(target, properties)(source);
	},
	repeater: function(source, target, properties) {
		return $L(source, this.template(target, properties));
	}
};

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

function WidgetDocument(view, context, loaded) {
	var hiddenElementCounter = 0;
	var hiddenElements = new WatchObject();
	var overlayElements = new WatchList();

	WidgetDocument.attachHidden = function(element) {
		var key = ++hiddenElementCounter;
		hiddenElements.set(key, element);
		return function() {
			hiddenElements.set(key, null);
		};
	};

	WidgetDocument.setOverlay = function(elements) {
		$B(overlayElements, elements);
	};
	
	window.onload = function() {
		invoke(loaded);
		var overlayContainer = Widget.block(overlayElements).fixedBox(0, 0, 0, 0);
		$B(overlayContainer.styleAccessor("display"), overlayElements.length,
			function(value) {
				return value == 0 ? "none" : "block";
			}
		);
		$B($E(window.document.body), [
			Widget.block($L(hiddenElements, function(value) {
				return value.get();
			})),
			Widget.block(Widget.view(view, context)),
			overlayContainer
		])
	};
}
