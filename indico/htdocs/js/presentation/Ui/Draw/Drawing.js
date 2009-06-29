/**
 * @author Tom
 */

type("DrawingGroup", [], {
	transform: watchSetter
},
	function() {
		this.transform = watchSetter();
	}
)

type("Drawing", [], {
	stroke: watchSetter,
	fill: watchSetter
},
	function() {
		this.stroke = watchSetter();
		this.fill = watchSetter();
	}
);
