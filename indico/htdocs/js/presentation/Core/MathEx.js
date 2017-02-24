/**
 * @author Tom
 */

function Point(x, y) {
	if (!exists(x)) {
		this.x = 0;
		this.y = 0;
	} else if (isObject(x)) {
		this.x += x.x;
		this.y += x.y;
	} else if (!exists(y)) {
		this.x = x;
		this.y = x;
	} else {
		this.x = x;
		this.y = y;
	}
}

Point.prototype = {
	move: function(x, y) {
		if (isObject(x)) {
			this.x += x.x;
			this.y += x.y;
		} else {
			this.x += x;
			this.y += y;
		}
		return this;
	},
	scale: function(x, y) {
		if (isObject(x)) {
			this.x *= x.x;
			this.y *= x.y;
		} else if (!exists(y)) {
			this.x *= x;
			this.y *= x;
		} else {
			this.x *= x;
			this.y *= y;
		}
		return this;
	}
};
