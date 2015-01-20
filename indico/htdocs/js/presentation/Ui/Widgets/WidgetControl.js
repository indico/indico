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

Widget.button = WidgetControl(Html.button, Widget.clickable);

Widget.text = WidgetControl(Html.span);
Widget.inline = WidgetControl(Html.span, Widget.text);

Widget.line = WidgetControl(Html.p);

Widget.inlineBlock = WidgetControl(function() {
	return Html.span({
		display: "inline-block"
	});
});

Widget.block = WidgetControl(Html.div);
Widget.wrap = WidgetControl(Html.p, Widget.text);
Widget.lines = WidgetControl(Html.div, Widget.line);
Widget.stack = WidgetControl(Html.div, Widget.block);

Widget.listItem = WidgetControl(Html.li);
Widget.unordered = WidgetControl(Html.ul, Widget.listItem);
Widget.ordered = WidgetControl(Html.ol, Widget.listItem);

Widget.select = WidgetControl(Html.select, Widget.option);

Widget.list = Widget.unordered;

Widget.header6 = WidgetControl(Html.h6);
Widget.header6.next = Widget.header6;
times(5, function(index) {
	var number = 5 - index;
	Widget["header" + number] = extend(WidgetControl(Html["h" + number]), {
		next: Widget["header" + (number + 1)]
	});
});

Widget.header = Widget.header1;

Widget.strong = WidgetControl(Html.strong);
Widget.em = WidgetControl(Html.em);
Widget.small = WidgetControl(Html.small);
Widget.pre = WidgetControl(Html.pre);

Widget.hidden = WidgetControl(Html.hidden);
