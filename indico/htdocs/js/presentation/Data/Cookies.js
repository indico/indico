/**
 * @author Tom
 */

var Cookies = {
	set: function(name, value, days) {
		document.cookie = name + "=" + value
			+ "; expires=" + addDays(new Date(), any(days, 600)).toGMTString()
			+ "; path=/";
	},
	erase: function(name) {
		Cookies.set(name, "", -1);
	},
	get: function(name) {
		return Cookies.all()[name];
	},
	all: function() {
		var obj = {};
		iterate(document.cookie.split(";"), function(cookie) {
			var item = cookie.split("=", 2);
			if (item.length < 2) {
				return;
			}
			var key = trim(item[0]);
			var value = trim(item[1]);
			var previous = obj[key];
			if (isArray(previous)) {
				previous.push(value);
			} else if (exists(previous)) {
				obj[key] = [previous, value];
			} else {
				obj[key] = value;
			}
		});
		return obj;
	}
};
