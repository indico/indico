/**
 * @author Tom
 */

Widget.t = function(id) {
	return id;
};

/**
 * Option template
 * @param {WatchPair, Object} item
 * @return {XElement} option
 */
Widget.option = function(item) {
	var option = Html.option();
	if (item.WatchPair) {
		$B(option, item);
		$B(option.accessor("value"), item.key);
		$B(option.accessor("selected"), item.selected);
		$B(option.accessor("disabled"), item.disabled);
	} else {
		option.setAttribute("value", item);
		option.set(item);
	}
	return option;
};

/**
 * Command template
 * @param {Function} command
 * @param {XElement} target
 * @return {String} caption
 */
Widget.clickable = function(command, target) {
	invoke(target.stopClickable);
	target.stopClickable = target.observeClick(function(event) {
		command(event);
		return false;
	});
	if (target.getTag() == "a") {
		target.setAttribute("href", "#");
	}
	return command.caption;
};
