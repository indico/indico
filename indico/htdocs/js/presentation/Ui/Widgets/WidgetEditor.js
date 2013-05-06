/**
 * @author Tom
 */

/**
 *
 * @param {XElement, Function} target
 * @param {Function, String} [template]
 * @return {Function}
 */
function WidgetEditor(target, template) {
	return function(source) {
		var element = isFunction(target) ? target() : target;
		var templator;
		if (!exists(template)) {
			templator = template;
		} else if (isFunction(template)) {
			templator = function(value) {
				return template(value, source);
			};
		} else {
			templator = {
				toTarget: function(value) {
					return template.toTarget(value, source);
				},
				toSource: function(value) {
					return template.toSource(value, source);
				}
			};
		}
		return bind.accessor(element, source, templator);
	};
}

Widget.timeTemplate = {
	toTarget: formatTime,
	toSource: function(value, source) {
		var time = copyDate(source.get());
		setTime(time, parseTime(value));
		return time;
	}
};

Widget.dateTemplate = {
	toTarget: formatDate,
	toSource: function(value, source) {
		var date = copyDate(source.get());
		setDate(date, parseDate(value));
		return date;
	}
};

Widget.textEditor = WidgetEditor(Html.edit);
Widget.timeEditor = WidgetEditor(Html.edit, Widget.timeTemplate);
Widget.multiLineEditor = WidgetEditor(Html.textarea);

