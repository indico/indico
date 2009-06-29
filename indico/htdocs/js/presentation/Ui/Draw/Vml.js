/**
 * @author Tom
 */

var Vml = {
	scale: 100,
	units: 0
};

type("VmlGroup", ["DrawingGroup", "Html"], {
	setTransform: function(transform) {
		var style = {};
		if (exists(transform)) {
			style.left = Vml.internal.getScalar(any(transform.x, 0) - 1) + Vml.units;
			style.top = Vml.internal.getScalar(any(transform.y, 0) - 1) + Vml.units;
			style.rotation = Math.round(any(transform.angle, 0));
		} else {
			style.left = Vml.internal.getScalar(-1) + Vml.units;
			style.top = Vml.internal.getScalar(-1) + Vml.units;
			style.rotation = 0;
		}
		this.style(style);
	}
},
	function(name, attributes) {
		Vml.internal.initialize();
		this.Html(Vml.tag(name), attributes);
		this.DrawingGroup();
		this.setTransform(null);
		this.transform.observe(apply(this.setTransform, this));
	}
);

type("VmlShape", ["Drawing", "VmlGroup"], {
	setStroke: function(stroke) {
		var self = this;
		obtain(this, "strokeElement", function() {
			var element = new XElement(Vml.tag("stroke"));
			self.append(element);
			return element;
		}).attribute(exists(stroke)
			? {
				on: "true",
				color: stroke.color,
				weight: any(stroke.width, 1) + "px",
				opacity: any(stroke.opacity, 1),
				endcap: Vml.internal.lineCapToEndcap(stroke.cap),
				joinstyle: any(stroke.join, "miter"),
				dashstyle: Vml.internal.computeDashArray(stroke.dash)
			}
			:	{
				on: "false"
			});
	},
	setFill: function(fill) {
		var attributes = {};
		if (exists(fill)) {
			attributes.on = "true";
			var opacities = translate(exists(fill.opacity)
				? isArray(fill.opacity)
					? [fill.opacity[0], fill.opacity[1]]
					: [fill.opacity, fill.opacity]
				: [null, null], function(value) {
					return any(value, 1);
				}
			);
			attributes.opacity = opacities[1];
			attributes["o:opacity2"] = opacities[0];
			var colors = translate(exists(fill.color)
				? isArray(fill.color)
					? [fill.color[0], fill.color[1]]
					: [fill.color, fill.color]
				: [null, null], function(value) {
					return any(value, "white");
				}
			);
			attributes.color = colors[1];
			attributes.color2 = colors[0];
			if (empty(fill.gradient) || fill.gradient == "none") {
				attributes.type = "solid";
			} else if (fill.gradient == "linear") {
				attributes.type = "gradient";
				attributes.angle = fill.angle;
				attributes.method = "none";
			} else {
				switch (this.getTag()) {
					case "v:oval":
						attributes.type = "gradientradial";
						attributes.focusposition = Vml.internal.computeFocus(Point.fromArray(fill.position).placeToCircle(0.5, 0.5, 0.48).toArray());
						attributes.focussize = "0,0";
						attributes.method = "none";
						break;
					default:
						attributes.type = "gradientradial";
						attributes.focusposition = Vml.internal.computeFocus(fill.position)
						attributes.focussize = "0,0";
						attributes.method = "none";
						break;
				}
			}
		} else {
			attributes.on = "false";
		}
		var self = this;
		obtain(this, "fillElement", function() {
			var element = new XElement(Vml.tag("fill"));
			self.append(element);
			return element;
		}).attribute(attributes);
	}
},
	function(name, attributes) {
		this.VmlGroup(name, attributes);
		this.Drawing();
		this.setStroke(null);
		this.setFill(null);
		this.stroke.observe(apply(this.setStroke, this));
		this.fill.observe(apply(this.setFill, this));
	}
);

Vml.tag = function(name) {
	return ["urn:schemas-microsoft-com:vml", "v:" + name];
};

Vml.tagOffice = function(name) {
	return ["urn:schemas-microsoft-com:office:office", "o:" + name];
}

Vml.internal = {
	initialize: function() {
		obtain(Vml.internal, "$initialized", function() {
			StyleSheet.add({
				"v\\:*": {
					behavior: "url(#default#VML)"
				},
				"o\\:*": {
					behavior: "url(#default#VML)"
				}
			});
			return true;
		});
	},
	
	lineCapToEndcap: function(cap) {
		return (empty(cap) || cap == "butt")
			? "flat" : cap;
	},
	computeFocus: function(focus) {
		return !exists(focus) ? "0,0"
			: translate(focus,
				function(value) {
					return (value * 100) + "%"
				}
			).join(",");
	},
	getScalar: function(x) {
		return Math.round(x * Vml.scale);
	},
	getPoint: function(x, y) {
		return Vml.internal.getScalar(x) + "," + Vml.internal.getScalar(y);
	},
	computeDashArray: function(dash) {
//		var style = getArray(dash).join(" ");
//		if (!empty(style)) {
//			alert(style);
//		}
		return any(dash, "Solid");
	},
	computeColors: function(colors) {
		return translate(colors, function(value, key) {
			return (key * 100) + "% " + value;
		}).join(",");
	},
	parsePath: function(path, closed) {
		var array = [];
		var min = new Point(Number.POSITIVE_INFINITY);
		var max = new Point(Number.NEGATIVE_INFINITY);
		if (path.List) {
			path = path.allItems();
		}
		function setValue(x, y) {
			x = Vml.internal.getScalar(x);
			y = Vml.internal.getScalar(y);
			min.setMinimum(x, y);
			max.setMaximum(x, y);
			array.push(x, y);
		}
		var i = 0;
		while (i < path.length) {
			if (isArray(path[i])) {
				var control = path[i++];
				switch (control.length) {
					case 0:
						throw "Arc not yet implemented.";
					case 2:
						array.push("QB");
						setValue(control[0], control[1]);
						break;
					case 4:
						array.push("C");
						setValue(control[0], control[1]);
						setValue(control[2], control[3]);
						break;
//					case 6:
//						array.push("C", control[0], control[1], control[2], control[3]);
//						break;
					default:
						throw "Unsupported control point specification";
				}
			} else {
				array.push(i == 0 ? "M" : "L");
				setValue(path[i++], path[i++]);
			}
		}
		if (closed) {
			array.push("X");
		}
		array.push("E");
		return {
			path: array.join(" "),
			width: max.x - min.x + 1,
			height: max.y - min.y + 1
		};
	}
}

//Vml.canvas = function(x, y, width, height, source) {
//	return $B(new VmlGroup("group", {
//		style: {
//			position: "absolute",
//			width: width,
//			height: height
//		},
//		coordorigin: Vml.internal.getPoint(x, y),
//		coordsize: Vml.internal.getPoint(width, height)
//	}), source);
//};

Vml.canvas = function(x, y, width, height, source) {
	return $B(new Html(Vml.tag("group"), {
		style: {
			position: "absolute",
			left: -x,
			top: -y,
			width: 2,
			height: 2
		},
		coordorigin: Vml.internal.getPoint(0, 0),
		coordsize: Vml.internal.getPoint(2, 2)
	}), source);
};

Vml.group = function(source) {
	return $B(new VmlGroup("group", {
		style: {
			position: "absolute",
			width: Vml.internal.getScalar(2) + Vml.units,
			height: Vml.internal.getScalar(2) + Vml.units
		},
		coordorigin: Vml.internal.getPoint(-1, -1),
		coordsize: Vml.internal.getPoint(2, 2)
	}), source);
};

Vml.shape = function(path, closed) {
	var spec = Vml.internal.parsePath(path, closed);
//	var size = Vml.internal.getPoint(spec.width, spec.height);
//	var offset = Vml.internal.getPoint(-spec.width / 2, -spec.height / 2);
	var pathElement = new XElement(Vml.tag("path"), {
		v: spec.path
	});
	var shape = new VmlShape("shape", {
		style: {
			position: "absolute",
			width: Vml.internal.getScalar(2) + Vml.units,
			height: Vml.internal.getScalar(2) + Vml.units
		},
		coordorigin: Vml.internal.getPoint(-1, -1),
		coordsize: Vml.internal.getPoint(2, 2)
	});
	shape.append(pathElement);
	return shape;
};
