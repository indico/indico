/**
 * @author Tom
 */


/**
 * Widget control
 * @param {Function} panelBuilder
 * @param {Function} [itemTemplate]
 * @param {Object} [attributes]
 * @return {Function} control builder
 */
function WidgetControl(panelBuilder, itemTemplate, attributes) {
	/**
	 * Builds a control
	 * @param {Object} source
	 * @return {Element}
	 */
	var controlBuilder = function(source) {
		// bind.element used because it should also bind the items to select field etc.
		return bind.element(panelBuilder(attributes), source, itemTemplate);
	};

	/**
	 * @param {Object} attribs
	 * @return {Function} control builder
	 */
	controlBuilder.customize = function(attribs) {
		return WidgetControl(panelBuilder, itemTemplate, merge(attributes, attribs));
	};
	
	extend(controlBuilder, WidgetBuilder);
	
	return controlBuilder;
}


Widget.link = WidgetControl(Html.a, Widget.clickable);
Widget.text = WidgetControl(Html.span);
Widget.inline = WidgetControl(Html.span, Widget.text);
Widget.line = WidgetControl(Html.p);
Widget.block = WidgetControl(Html.div);
Widget.lines = WidgetControl(Html.div, Widget.line);
