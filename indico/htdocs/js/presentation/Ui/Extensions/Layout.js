/**
 * @author Tom
 */

internal(function() {
	function computeX(style) {
		if (style.left < 0) {
			if (style.right < 0) {
				style.display = "none";
			} else {
				style.width = -(style.left + style.right);
				style.left = null;
			}
		} else if (style.right < 0) {
			style.width = -(style.left + style.right);
			style.right = null;
		}
	}
	function computeY(style) {
		if (style.top < 0) {
			if (style.bottom < 0) {
				style.display = "none";
			} else {
				style.height = -(style.top + style.bottom);
				style.top = null;
			}
		} else if (style.bottom < 0) {
			style.height = -(style.top + style.bottom);
			style.bottom = null;
		}
	}
	
	function boolToScrolling(arg) {
		return exists(arg)
			? arg
				? "auto"
				: "hidden"
			: null;
	}

	extend(Html.prototype, {
	
		wrap: function(arg) {
			return this.style({
				whiteSpace: exists(arg) 
					? arg
						? "normal"
						: "nowrap"
					: null
			});
		},
		scrolling: function() {
			var style = {};
			switch (arguments.length) {
				case 0:
					style.overflow = null;
					break;
				case 1:
					style.overflow = boolToScrolling(arguments[0]);
					break;
				case 2:
					style.overflowX = boolToScrolling(arguments[0]);
					style.overflowY = boolToScrolling(arguments[1]);
					break;
			}
			return this.style(style);
		},
		locateX: function(left, right) {
			var style = {
				left: left,
				right: right,
				width: null,
				position: "absolute"
			};
			computeX(style);
			return this.style(style);
		},
		locateY: function(top, bottom) {
			var style = {
				top: top,
				bottom: bottom,
				height: null,
				position: "absolute"
			};
			computeY(style);
			return this.style(style);
		},
		locate: function(top, left, bottom, right) {
			var style = {
				left: left,
				right: right,
				width: null,
				top: top,
				bottom: bottom,
				height: null,
				position: "absolute"
			};
			computeX(style);
			computeY(style);
			return this.style(style);
		},
		messageBox: function(width, height) {
			return this.style({
				left: "50%",
				top: "40%",
				marginLeft: -width / 2,
				marginTop: -height / 2,
				width: width,
				height: height,
				display: "block",
				position: "fixed"
			});
		},
		fixedBox: function(top, left, bottom, right) {
			var style = {
				left: left,
				right: right,
				width: null,
				top: top,
				bottom: bottom,
				height: null,
				display: "block",
				position: "fixed"
			};
			computeX(style);
			computeY(style);
			return this.style(style);
		}
	})
});

extend(Html.prototype, {
	isBody: function() {
		return document.body === this.dom;
	},

	layout: function(layout) {
		var self = this;
		invoke(self.removeLayout);
		if (isString(layout)) {
			layout = Layout[layout];
		}
		if (exists(layout)) {
			var layoutElement = function() {
				schedule(function() {
					layout(self);
				});
			};
			self.removeLayout = self.itemsUpdated.attach(layoutElement);
			layoutElement();
		}
		return self;
	},
	
	getOffsetParent: function() {
		return $E(this.getAttribute("offsetParent"));
	}
});

// based on mootools
delayedBind(Html.prototype, "getAbsolutePosition", function(dom) {
	return (this.dom.getBoundingClientRect && !Browser.WebKit)
        ? function() {
            var bound = this.dom.getBoundingClientRect();
            var html = document.documentElement;
            return new Point(
                Math.round(bound.left + html.scrollLeft - html.clientLeft),
                Math.round(bound.top + html.scrollTop - html.clientTop)
            );
        }
        : function() {
            var position = new Point();
            var element = this;
            while (exists(element) && !element.isBody()) {
                position.move(new Point(element.getAttribute("offsetLeft"), element.getAttribute("offsetTop")));
                element = element.getOffsetParent();
            }
            return position; 
		}
});

var Layout = {
	row: function() {
		var args = $A(arguments);
		return function(element) {
			var prev = 0;
			element.each(function(item, index) {
				var pos = args[index];
				if (!exists(prev)) {
					item.close();
				} else if (exists(pos)) {
					item.locate(0, prev, 0, -pos);
				} else {
					item.locate(0, prev, 0, 0);
				}
				prev = pos;
			});
		}
	},
	rows: function(height, spacing) {
		return function(element) {
			var totalHeight = spacing;
			element.each(function(item) {
				item.style({
					position: "absolute",
					display: "block",
					left: 0,
					right: 0,
					margin: 0,
					padding: 0,
					border: "0",
					width: null,
					top: totalHeight,
					height: height
				});
				totalHeight += height + spacing;
			});
			element.style({
				height: totalHeight,
				display: "block",
				position: "relative"
			});
		};
	}
//	vertical: function(element) {
//		var style = {
//			display: "block"
//		};
//		if (element.fixedHeight) {
//			var top = 0;
//			var height = element.getAttribute("clientHeight");
//			var count = element.length.get();
//			var top = 0;
//			element.each(function(item, index) {
//				var next = height * (index + 1) / count;
//				item.attribute({
//					$fixedHeight: false,
//					style: {
//						position: "absolute",
//						display: "block",
//						left: 0,
//						right: 0,
//						margin: "0",
//						padding: "0",
//						border: "0",
//						width: null,
//						top: top,
//						height: next - top
//					}
//				});
//				top = next;
//			});
//		} else {
//			var height = 0;
//			element.each(function(item) {
//				item.attribute({
//					$fixedHeight: false,
//					style: {
//						position: "absolute",
//						display: "block",
//						left: 0,
//						right: 0,
//						margin: "0",
//						padding: "0",
//						border: "0",
//						width: null,
//						top: height
//					}
//				});
//				height += item.getAttribute("offsetHeight");
//			});
//			style.height = height;
//		}
//		if (element.item(0).getStyle("offsetParent") !== element) {
//			style.position = "relative";
//		}
//		element.style(style);
//	}
};
