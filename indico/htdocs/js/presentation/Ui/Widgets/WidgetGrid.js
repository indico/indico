/**
 * @author Tom
 */

/**
 * 
 * @param {String} name
 * @param {String} caption
 * @param {Function} editable
 */
function Column(name, caption, editable) {
	this.name = name;
	this.caption = caption;
	this.editable = editable;
}

/**
 * 
 * @param {Object} source
 * @param {Object} style
 */
Widget.grid = function(source, style) {
	var $ = WidgetContext(this);
	
	var activeContext = null;
	function activateContext(context) {
		if (activeContext == context) {
			return;
		}
		if (exists(activeContext) && activeContext.get() == "edit") {
			activeContext.save();
		}
		activeContext = context;
	}
	
	var headRow = Html.tr({}, Html.th());
	bind.listEx(headRow, style.columns, function(column, target) {
		return [$B(Html.th(), column.caption)];
	}, 1);
	
	var head = $B(Html.thead(), headRow);
	
	var body = bind.listEx(Html.tbody(), $L(source), function(item, target) {
		var context = new WidgetEditableContext();

		var row = Html.tr();
		row.set($B(Html.th({rowSpan: 2}), item.key));
		bind.listEx(row, style.columns, function(column) {
			var content = $V(item.value, column.name);
			if (exists(column.editable)) {
				content = column.editable.call($, content, context);
			}
			return [$B(Html.td(), content)];
		}, 1);
		
		var toolsCell = Html.td();
		var toolsRow = $B(Html.tr(), toolsCell);
		$B(toolsCell.accessor("colSpan"), style.columns.length);
		
		context.observe(objectInvoker({
			view: function() {
				toolsCell.clear();
			},
			edit: function() {
				activateContext(context);
				toolsCell.set(
					Widget.button(command(context.save, "Save")),
					Widget.button(command(context.view, "Cancel")),
					Widget.button(command(function() {
						source.set(item.key.get(), null);
					}, "Delete"))
				);
			}
		}));

		return [
			row,
			toolsRow
		];
	}, 0, 2);
	
	return $B(Html.table(), [head, body]);
};
