/**
 * @author Tom
 */

WidgetBuilder.resize = function(width, height) {
	return this.customize({
		style: {
			width: width,
			height: height
		}
	});
};

WidgetBuilder.place = function(left, top, right, bottom) {
	return this.customize({
		style: {
			position: "absolute",
			left: left,
			top: top,
			right: right,
			bottom: bottom
		}
	});
};


Widget.locator = function(context, layout) {
	var $ = this;
	return enumerate(layout, stacker(function(location, key) {
		var element = context[key]($);
		return element.locate.apply(element, location);
	}));
};
