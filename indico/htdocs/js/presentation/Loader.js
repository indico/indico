/**
 * Loader
 * @author Tom
 */


if (typeof(this.include) !== "function") {
	this.include = function(script) {
	document.write("<script type=\"text/javascript\" src=\"" + script + "\"></script>");
}
}

// Some parts taken from Prototype Javascript Framework

var files = [
	"Core/Primitives.js",
	"Core/Exception.js",
	"Core/Iterators.js",
	"Core/Tools.js",
	"Core/String.js",
	"Core/Type.js",
	"Core/Interfaces.js",
	"Core/Commands.js",
    "Core/MathEx.js",
	"Data/Bag.js",
	"Data/Watch.js",
	"Data/WatchValue.js",
	"Data/WatchList.js",
	"Data/WatchObject.js",
	"Data/Binding.js",
	"Data/Logic.js",
	"Data/Json.js",
	"Data/Remote.js",
	"Data/DataStore.js",
	"Data/DateTime.js",
	"Data/Files.js",
	"Data/Cookies.js",
	"Ui/MimeTypes.js",
	"Ui/Dom.js",
	"Ui/XElement.js",
	"Ui/Html.js",
	"Ui/Color.js",
	"Ui/Text.js",
	"Ui/StyleSheet.js",
	"Ui/Extensions/SimpleStyles.js",
	"Ui/Extensions/Layout.js",
    "Ui/Extensions/Lookup.js",
	"Ui/Draw/Drawing.js",
	"Ui/Draw/Svg.js",
	"Ui/Draw/Vml.js",
	"Ui/Draw/Draw.js",
	"Ui/Widgets/WidgetBase.js",
	"Ui/Widgets/WidgetPage.js",
	"Ui/Widgets/WidgetComponents.js",
	"Ui/Widgets/WidgetControl.js",
	"Ui/Widgets/WidgetEditor.js",
	"Ui/Widgets/WidgetTable.js",
	"Ui/Widgets/WidgetField.js",
	"Ui/Widgets/WidgetEditable.js",
	"Ui/Widgets/WidgetMenu.js",
	"Ui/Widgets/WidgetGrid.js"
];

for (var i in files) {
	include(ScriptRoot + "presentation/" + files[i]);
}
