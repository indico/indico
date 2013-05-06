/**
 * @author Tom
 */

/**
 * 
 * @param {List|Array} rows
 * @param {List|Array} [headers]
 * @param {List|Array} [footers]
 * @return {XElement}
 */
function WidgetTable(rows, headers, footers) {
	if (headers) {
		headers.isHeader = true;
		rows.head = $L([headers]);
	}
	if (footers) {
		rows.foot = $L([footers]);
	}
	return Html.table(rows.tableAttributes,
		WidgetTable.rows(Html.thead(rows.headAttributes), rows.head),
		WidgetTable.rows(Html.tfoot(rows.footAttributes), rows.foot),
		WidgetTable.rows(Html.tbody(rows.bodyAttributes), any(rows.body, rows))
	);
}

WidgetTable.cell = function(item, target, isHeader) {
	var constructor = isHeader ? Html.th : Html.td;
	if (exists(item)) {
		if (item.XElement) {
			switch (item.getTag()) {
				case "td":
				case "th":
					return item;
				default:
					return $B(constructor(), item);
			}
		}
	} else {
		return constructor();
	}
};

WidgetTable.headerCell = function(item, target) {
	return WidgetTable.cell(item, target, true);
};

WidgetTable.row = function(row) {
	var $ = WidgetContext(this);
	if (row.XElement && row.getTag() == "tr") {
		return row;
	} else {
		var template = row.isHeader ? WidgetTable.headerCell : WidgetTable.cell;
		return $B(Html.tr(row.rowAttributes), any(row.cells, row), template);
	}
};

WidgetTable.rows = function(root, rows) {
	if (rows) {
		return $B(root, rows, WidgetTable.row);
	}
};

Widget.table = WidgetTable;

