/**
 * @author Tom
 */

/**
 * 
 * @param {List, Array} commands
 * @return {XElement}
 */
Widget.menu = function(commands) {
	return Widget.list($L(commands, Widget.link));
};
