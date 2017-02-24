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
		}
	})
});

extend(Html.prototype, {
	isBody: function() {
		return document.body === this.dom;
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
};
