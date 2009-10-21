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

Point.fromPolar = function(r, a) {
	return new Point(r * Math.cos(a), r * Math.sin(a));
};

Point.fromArray = function(array) {
	return new Point(array[0], array[1]);
};

Point.fromVector = function(source, destination) {
	return new Point(destination.x - source.x, destination.y - source.y);
};

Point.prototype = {
	fromPolar: function(r, a) {
		this.x = r * Math.cos(a);
		this.y = r * Math.sin(a);
		return this;
	},
	fromArray: function(array) {
		this.x = array[0];
		this.y = array[1];
		return this;
	},
	toArray: function() {
		return [this.x, this.y];
	},
	getRadius: function() {
		return Math.sqrt(MathEx.sqr(this.x) + MathEx.sqr(this.y));
	},
	getAngle: function() {
		return Math.atan2(this.y, this.x);
	},
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
	},
	getOffset: function(x, y) {
		return new Point(this.x - x, this.y - y);
	},
	placeToCircle: function(cx, cy, r) {
		var o = this.getOffset(cx, cy);
		var or = o.getRadius();
		if (or > r) {
			this.fromPolar(r, o.getAngle());
			this.move(cx, cy);
		}
		return this;
	},
	setMinimum: function(x, y) {
		if (x < this.x) {
			this.x = x;
		}
		if (y < this.y) {
			this.y = y;
		}
	},
	setMaximum: function(x, y) {
		if (x > this.x) {
			this.x = x;
		}
		if (y > this.y) {
			this.y = y;
		}
	}
};

var Rad = {};

times(4, function(value) {
	Rad["q" + (value + 1)] = Math.PI * (value + 1) / 2;
});

var MathEx = {
	sqr: function(value) {
		return value * value;
	},
	degToRad: function(value) {
		return value * Math.PI / 180;
	},
	radToDeg: function(value) {
		return value * 180 / Math.PI;
	},
	getLength: function(pt1, pt2) {
		return Point.fromVector(pt1, pt2).getRadius();
	},
	getPolylineLength: function(points) {
		var length = 0;
		var previous = null;
		each(points, function(point) {
			if (exists(previous)) {
				length += MathEx.getLength(previous, point);
			}
			previous = point;
		});
		return length;
	},
	getPointOnPolyline: function(points, offset) {
		var pp = null;
		var previous = null;
		var result = lookup(points, function(point) {
			if (exists(previous)) {
				var vector = Point.fromVector(previous, point);
				var length = vector.getRadius();
				if (offset < length) {
					var angle = vector.getAngle();
					vector.scale(offset / length).move(previous);
					vector.angle = angle;
					return vector;
				}
				offset -= length;
			}
			pp = previous;
			previous = point;
		});
		if (!exists(result)) {
			result = new Point(previous);
			result.angle = MathEx.radToDeg(Point.fromVector(pp, previous).getAngle());
		}
		return result;
	}
};

function even(number) {
	return number % 2 === 0;
}

function odd(number) {
	return number % 2 !== 0;
}
