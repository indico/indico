/**
 * @author Tom
 */

type("SvgGroup", ["DrawingGroup", "XElement"], {
	setTransform: function(transform) {
		var value = exists(transform)
			? "translate(" + any(transform.x, 0) + "," + any(transform.y, 0) + "),rotate(" + any(transform.angle, 0) + ")"
			: "";
		this.attribute({
			transform: value
		});
	}
},
	function(name, attributes) {
		this.XElement(Svg.tag(name), attributes);
		this.DrawingGroup();
		this.transform.observe(apply(this.setTransform, this));
	}
);

type("Svg", ["Drawing", "SvgGroup"], {
	setStroke: function(stroke) {
		this.attribute(exists(stroke)
			? {
				"stroke": any(stroke.color, "black"),
				"stroke-width": any(stroke.width, 1),
				"stroke-opacity": any(stroke.opacity, 1),
				"stroke-linecap": any(stroke.cap, "butt"),
				"stroke-linejoin": any(stroke.join, "miter"),
				"stroke-dasharray": Svg.internal.computeDashArray(stroke.dash, any(stroke.width, 1))
			}
			: {
				"stroke": "none",
				"stroke-width": "0",
				"stroke-opacity": "1",
				"stroke-linecap": "butt",
				"stroke-linejoin": "miter",
				"stroke-dasharray": "0"
			}
		);
	},
	setFill: function(fill) {
		var attributes = {};
		var element = null;
		if (exists(fill)) {
			if (empty(fill.gradient) || fill.gradient == "none") {
				attributes["fill-opacity"] = any(exists(fill.opacity)
					? isArray(fill.opacity)
						? fill.opacity[0]
						: fill.opacity
					: null, 1);
				attributes["fill"] = any(exists(fill.color)
					? isArray(fill.color)
						? fill.color[0]
						: fill.color
					: null, "white");
			} else {
				attributes["fill"] ="url(#" + this.fillId + ")";
				var stopDefs = [{
					offset: "0%"
				}, {
					offset: "100%"
				}];
				var stopOpacity = exists(fill.opacity)
					? isArray(fill.opacity) 
						? fill.opacity
						: [fill.opacity, fill.opacity]
					: [null, null];
				var stopColor = exists(fill.color)
					? isArray(fill.color) 
						? fill.color
						: [fill.color, fill.color]
					: [null, null];
				each(2, function(index) {
					stopDefs[index]["stop-opacity"] = any(stopOpacity[index], 1);
					stopDefs[index]["stop-color"] = any(stopColor[index], "white");
				});

				var stops = translate(stopDefs, function(def) {
					return new XElement(Svg.tag("stop"), def);
				});
				if (fill.gradient == "linear") {
					element = $B(new XElement(Svg.tag("linearGradient"), {
						id: this.fillId,
						x1: "0%",
						y1: "0%",
						x2: "0%",
						y2: "100%"
					}), stops);
				} else {
					switch (this.getTag()) {
						case "svg:ellipse":
							var focus = Point.fromArray(fill.position).placeToCircle(0.5, 0.5, 0.48);
							element = $B(new XElement(Svg.tag("radialGradient"), {
								id: this.fillId,
								cx: "50%",
								cy: "50%",
								r: "50%",
								fx: focus.x * 100 + "%",
								fy: focus.y * 100 + "%"
							}), stops);
							break;
						default:
							element = $B(new XElement(Svg.tag("radialGradient"), {
								id: this.fillId,
								cx: "50%",
								cy: "50%",
								r: (50 * Math.sqrt(2)) + "%",
								fx: fill.position[0] * 100 + "%",
								fy: fill.position[1] * 100 + "%"
							}), stops);
							break;
					}
					
				}
			}
		} else {
			attributes.fill = "none";
		}
		this.fillElement.set(element);
		this.attribute(attributes);
	}
},
	function(name, attributes) {
		this.SvgGroup(name, attributes);
		this.Drawing();
		this.fillElement = new WatchValue();
		this.fillId = Html.generateId();
		this.setStroke(null);
		this.setFill(null);
		this.stroke.observe(apply(this.setStroke, this));
		this.fill.observe(apply(this.setFill, this));
	}
);

Svg.tag = function(name) {
	return ["http://www.w3.org/2000/svg", "svg:" + name];
};

Svg.internal = {
	computeDashArray: function(dash, width) {
		return replaceEmpty(translate({
			Solid: [0],
			ShortDash: [2, 2],
			ShortDot: [0, 2],
			ShortDashDot: [2, 2, 0, 2],
			ShortDashDotDot: [2, 2, 0, 2, 0, 2],
			Dot: [1, 2],
			Dash: [4, 2],
			DashDot: [4, 2, 1, 2],
			LongDash: [8, 4],
			LongDashDot: [8, 2, 1, 2],
			LongDashDotDot: [8, 2, 1, 2, 1, 2]
		}[dash], function(item) {
			return item * width;
		}).join(","), "0");
	},
	parsePath: function(path, closed) {
		var array = [];
		var i = 0
		if (path.List) {
			path = path.allItems();
		}
		while (i < path.length) {
			if (isArray(path[i])) {
				var control = path[i++];
				var x, y;
				if (i <= path.length - 2) {
					x = path[i++];
					y = path[i++];
				} else {
					x = path[0];
					y = path[1];
				}
				switch (control.length) {
					case 0:
						throw "Arc not yet implemented.";
					case 2:
						array.push("Q", control[0], control[1], x, y);
						break;
					case 4:
						array.push("C", control[0], control[1], control[2], control[3], x, y);
						break;
//					case 6:
//						array.push("A", control[0], control[1], control[2], control[3], x, y);
//						break;
					default:
						throw "Unsupported control point specification";
				}
			} else {
				array.push(i == 0 ? "M" : "L", path[i++], path[i++]);
			}
		}
		if (closed) {
			array.push("Z");
		}
		return array.join(" ");
	}
};

Svg.canvas = function(x, y, width, height, source) {
	var defs = new XElement(Svg.tag("defs"));
	processListableAccessor(source, "fillElement",
		function(item) {
			defs.append(item);
		},
		function(item) {
			item.detach();
		}
	);
	
	return $B(new Html(Svg.tag("svg"), {
		version: "1.1",
		width: width,
		height: height
	}), [
		defs,
		$B(new SvgGroup("g").transform({
			x: -x,
			y: -y
		}), source)
	]);
};

Svg.group = function(source) {
	return $B(new SvgGroup("g"), source);
};

Svg.shape = function(path, closed) {
	var data = Svg.internal.parsePath(path, closed);
	return new Svg("path", {
		d: data
	});
};
