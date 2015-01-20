/**
 * @author Tom
 */

/**
 * Widget page
 * @param {Array} name
 * @param {Function} render
 */
function WidgetPage(name, render) {
	WidgetPage.pages[WidgetPage.getKey(name)] = function(context) {
		context.page = name;
		return render(context);
	};
}

WidgetPage.pages = {};

/**
 * Returns page key
 * @param {Array} name
 * @return {String} key
 */
WidgetPage.getKey = function(name) {
	return "/" + name.join("/");
};


/**
 * Renders page with name using context
 * @param {Accessor} target
 * @param {Array} name
 */
Widget.render = function(target, name) {
	if (exists(this.parent)) {
		name = concat(this.parent.page, name);
	}
	target.set(WidgetPage.pages[WidgetPage.getKey(name)](this));
	return target;
};

