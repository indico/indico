/**
 * @author Tom
 */

function MessageBox(width, height, view, closed) {
	var close = function() {
		stopObserving();
		WidgetDocument.setOverlay([]);
		closed();
	};
	var overlay = Widget.block().fixedBox(0, 0, 0, 0).background(Color.black).opacity(0.5);
	var stopObserving = overlay.observeClick(close);
	WidgetDocument.setOverlay([
		overlay,
		Widget.block(Widget.view(view, {
			close: close
		})).messageBox(width, height)
	]);
}
