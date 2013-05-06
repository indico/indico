/**
 * @author Tom
 */

Widget.editableContainer = Widget.text; 

type("WidgetEditableContext", ["Switch"], {
}, 
	function() {
		this.Switch("view", "edit", ["save", "view"]);
		this.view();
	}
);

/**
 * 
 * @param {Function} view
 * @param {Function} edit
 * @return {Function}
 */
function WidgetEditable(view, edit) {
	return function(source, context) {
		var $ = WidgetContext(this);
		if (!exists(context)) {
			context = new WidgetEditableContext();
		}
		
		var target = $.editableContainer();
		var stopView = null;
		var editor = null;
		var field = {
			view: function(origin) {
				if (exists(editor)) {
					invoke(editor.stop);
				}
				stopView = view(target, source, function() {
					context.edit();
					editor.activate();
				});
			},
			edit: function(origin) {
				invoke(stopView);
				editor = edit(target, source);
			},
			save: function(origin) {
				if (exists(editor)) {
					invoke(editor.save);
				}
			}
		};
		
		var observer = objectInvoker(field);
		context.observe(observer);
		context.invokeObserver(observer);
		return target;
	};
}

/**
 * Returns text view with template
 * @param {Function} template
 * @return {Function}
 */
WidgetEditable.getTemplatedTextView = function(template) {
	return function(target, source, edit) {
		$B(target, source, template);
		return function() {
			bind.detach(target);
		};
	};
};

WidgetEditable.textView = WidgetEditable.getTemplatedTextView(null);

WidgetEditable.getSelectViewTemplate = function(items) {
	if (isArrayOrListable(items)) {
		return null;
	}
	return splitter(items);
};

/**
 * 
 * @param {Function} view
 * @return {Function}
 */
WidgetEditable.getClickableView = function(view) {
	return function(target, source, edit) {
		return sequence(
			target.observeClick(edit),
			view(target, source)
		);
	};
};

WidgetEditable.textViewClickable = WidgetEditable.getClickableView(WidgetEditable.textView);

/**
 * 
 * @param {Function} fieldBuilder
 * @return {Function}
 */
WidgetEditable.getFieldEditor = function(fieldBuilder) {
	return function(target, source) {
		var field = fieldBuilder();
		var accessor = getAccessorDeep(source);
		field.set(accessor.get());
		$B(target, field);
		return {
			activate: function() {
				if (exists(field.dom.select)) {
					field.dom.select();
				} else {
					field.dom.focus();
				}
			},
			save: function() {
				accessor.set(field.get());
			},
			stop: function() {
				bind.detach(target);
			}
		};
	};
};

WidgetEditable.textEdit = WidgetEditable.getFieldEditor(Html.edit);

/**
 * 
 * @param {List|Array|WatchObject|Object} items
 * @return {Function}
 */
WidgetEditable.getSelectEdit = function(items) {
	return WidgetEditable.getFieldEditor(function() {
		return Widget.select(items);
	});
};

Widget.textEditable = WidgetEditable(WidgetEditable.textView, WidgetEditable.textEdit);
Widget.textEditableClickable = WidgetEditable(WidgetEditable.textViewClickable, WidgetEditable.textEdit);

Widget.selectEditable = function(items, source, context) {
	return WidgetEditable(
		WidgetEditable.getTemplatedTextView(WidgetEditable.getSelectViewTemplate(items)),
		WidgetEditable.getSelectEdit(items)
	)(source, context);
};

Widget.selectEditableClickable = function(items, source, context) {
	return WidgetEditable(
		WidgetEditable.getClickableView(WidgetEditable.getTemplatedTextView(WidgetEditable.getSelectViewTemplate(items))),
		WidgetEditable.getSelectEdit(items)
	)(source, context);
};
