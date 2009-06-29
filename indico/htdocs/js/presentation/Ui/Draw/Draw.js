/**
 * @author Tom
 */

var Draw = Browser.IE ? Vml : Svg;

Draw.rect = function(x, y, width, height) {
	return Draw.shape([x, y, x + width, y, x + width, y + height, x, y + height], true);
};

Draw.rounded = function(x, y, width, height, rx, ry) {
	rx = Math.min(rx, width / 2);
	ry = Math.min(ry, height / 2);
	return Draw.shape([
		x + rx, y, x + width - rx, y, [x + width, y], x + width, y + ry,
		x + width, y + height - ry, [x + width, y + height], x + width - rx, y + height,
		x + rx, y + height, [x, y + height], x, y + height - ry,
		x, y + ry, [x, y]
	], true);
};

Draw.potato = function(x, y, width, height) {
	return Draw.rounded(x, y, width, height, Number.POSITIVE_INFINITY, Number.POSITIVE_INFINITY);
};

Draw.arrow = function(width, height, closed) {
	return Draw.shape([
		0, -height,
		+width, 0,
		0, +height
	], closed);
};

Draw.halfArrow = function(width, height, closed) {
	return Draw.shape([
		0, -height,
		+width, 0,
		0, 0
	], closed);
};

Draw.diamond = function(width, height) {
	return Draw.shape([
		0, 0,
		width, -height,
		width * 2, 0,
		width, +height
	], true);
};

Draw.line = function(x1, y1, x2, y2) {
	return Draw.shape([
		x1, y1,
		x2, y2
	]);
};

Draw.polygon = function(points) {
	return Draw.shape(bind.listEx(new WatchList(), points, function(point) {
		return [
			point.x,
			point.y
		];
	}, 0, 2));
};

Draw.Stroke = function(color, width, dash) {
	this.color = color;
	this.width = width;
	this.dash = dash;
};

Draw.Fill = function(color) {
	this.color = color;
};


Draw.Join = new NamedEnum("miter", "round", "bevel");
Draw.Cap = new NamedEnum("square", "round", "butt");
