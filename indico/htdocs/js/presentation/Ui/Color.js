/**
 * @author Tom
 */



function Color() {
}

Color.dark = {};
Color.light = {};
Color.white = "#FFFFFF";
Color.black = "#000000";

// Tango palette
enumerate({
	yellow: ["#fce94f", "#edd400", "#c4a000"],
	orange: ["#fcaf3e", "#f57900", "#ce5c00"],
	brown: ["#e9b96e", "#c17d11", "#8f5902"],
	green: ["#8ae234", "#73d216", "#4e9a06"],
	blue: ["#729fcf", "#3465a4", "#204a87"],
	violet: ["#ad7fa8", "#75507b", "#5c3566"],
	red: ["#ef2929", "#cc0000", "#a40000"],
	silver: ["#eeeeec", "#d3d7cf", "#babdb6"],
	gray: ["#888a85", "#555753", "#2e3436"]
}, function(colors, name) {
	Color.light[name] = colors[0];
	Color[name] = colors[1];
	Color.dark[name] = colors[2];
});

