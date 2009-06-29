/**
 * Loader
 * @author Tom
 */

// Some parts taken from Prototype Javascript Framework

var Presentation = {
	path: ScriptRoot + "presentation/"
};

function include(script) {
	document.write("<script type=\"text/javascript\" src=\"" + script + "\"></script>");
}

var files = [
	"Core/Primitives.js",
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
	"Data/DateTime.js",
	"Ui/MimeTypes.js",
	"Ui/XElement.js",
	"Ui/Html.js",
	"Ui/Dom.js",
	"Ui/Style.js",
        "Ui/Extensions/Lookup.js",
        "Ui/Extensions/Layout.js",
        "Ui/Text.js",
	"Ui/Styles/SimpleStyles.js",
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

for (var i = 0; i < files.length; i++) {
	include(Presentation.path + files[i]);
}
