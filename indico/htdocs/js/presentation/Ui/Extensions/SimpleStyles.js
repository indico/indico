/**
 * @author Tom
 */

extend(Html.prototype, {
	/**
	 * @return {Accessor}
	 */
	visible: function() {
		var self = this;
		return new Accessor(function() {
			return self.style("display") != "none";
		}, function(value) {
			return self.style("display", value ? null : "none");
		});
	},
	/**
	 * 
	 * @param {Number|String} height
	 * @param {Number|String} [width]
	 */
	scroll: function(height, width) {
		var style = {
			overflow: "auto",
			height: height
		};
		if (exists(width)) {
			style.width = width;
		}
		return this.style(style);
	},
	
	show: function() {
		return this.style({
			display: null,
			visibility: "visible"
		});
	},
	
	hide: function() {
		return this.style({
			display: null,
			visibility: "hidden"
		});
	},
	
	disable: function() {
		return this.setAttribute("disabled", "disabled");
	},

	enable: function() {
		return this.setAttribute("disabled", null);
	},
	
	collapse: function() {
		return this.style({
			display: null,
			visibility: "hidden"
		});
	},
	
	hide: function() {
		return this.style({
			display: null,
			visibility: "hidden"
		});
	}
	
});

iterate([
	"padding", "margin", "border"
], function(name) {
	Html.prototype[name] = function() {
		var style = {};
		switch (arguments.length) {
			case 1:
				style[name] = arguments[0];
				break;
			case 2:
				style[name + "Top"] = arguments[0];
				style[name + "Right"] = arguments[1];
				style[name + "Bottom"] = arguments[0];
				style[name + "Left"] = arguments[1];
				break;
			case 4:
				style[name + "Top"] = arguments[0];
				style[name + "Right"] = arguments[1];
				style[name + "Bottom"] = arguments[2];
				style[name + "Left"] = arguments[3];
				break;
		}
		return this.style(style);
	};
});

enumerate({
	relative: {
		set: {
			position: "relative"
		}
	},
	inline: {
		set: {
			display: "inline"
		}
	},
	block: {
		set: {
			display: "block"
		}
	},
	opacity: {
		args: ["opacity"]
	},
	size: {
		args: ["width", "height", "padding", "margin", "border"]
	},
	floating: {
		args: ["cssFloat", "width", "height"],
		set: {
			position: "relative"
		}
	},
	fill: {
		args: ["padding", "margin", "border"],
		set: {
			position: "absolute",
			width: "100%",
			height: "100%"
		}
	},
	place: {
		args: ["top", "left", "bottom", "right", "padding", "margin", "border"],
		set: {
			position: "absolute"
		}
	},
	topLeft: {
		args: ["left", "top", "width", "height", "padding", "margin", "border"],
		set: {
			position: "absolute",
			bottom: null,
			right: null
		}
	},
	topRight: {
		args: ["right", "top", "width", "height", "padding", "margin", "border"],
		set: {
			position: "absolute",
			bottom: null,
			left: null
		}
	},
	bottomLeft: {
		args: ["left", "bottom", "width", "height", "padding", "margin", "border"],
		set: {
			position: "absolute",
			top: null,
			right: null
		}
	},
	bottomRight: {
		args: ["right", "bottom", "width", "height", "padding", "margin", "border"],
		set: {
			position: "absolute",
			top: null,
			left: null
		}
	},
	border: {
		args: ["borderWidth", "borderStyle", "borderColor"]
	},
	color: {
		args: ["color"]
	},
	background: {
		args: ["background"]
	},
	lineHeight: {
		args: ["lineHeight"]
	},
	textAlign: {
		args: ["textAlign", "verticalAlign"]
	},
	verticalAlign: {
		args: ["verticalAlign"]
	}
}, function(def, name) {
	Html.prototype[name] = function() {
		var style = getObject(def.set);
		iterate(arguments, function(arg, index) {
			style[def.args[index]] = arg;
		});
		invoke(def.compute, style);
		return this.style(style);
	};
});

