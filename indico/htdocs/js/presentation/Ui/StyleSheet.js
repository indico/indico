/**
 * @author Tom
 */

var StyleSheet = {
	disableAll: function() {
		iterate(document.styleSheets, function(sheet) {
			sheet.disabled = true;
		});
	},
	
	add: function(rules) {
		var sheet = StyleSheet.obtain();
		var sheetRules = StyleSheet.getRules(sheet);
		enumerate(rules, function(style, selectors) {
			if (sheet.insertRule) {
				var index = sheetRules.length;
				sheet.insertRule(selectors + " " + StyleSheet.buildRule(style), index);
			} else {
				iterate(selectors.split(","), function(selector) {
					var index = sheetRules.length;
					sheet.addRule(selector, StyleSheet.buildRule(style));
				});
			}
		});
	},
	
	create: function(media) {
		var sheet;
		if (document.createStyleSheet) {
			sheet = document.createStyleSheet();
		} else {
			sheet = document.createElement("style");
			sheet.type = "text/css";
			Dom.getHead().appendChild(sheet);
			sheet = sheet.sheet;
		}
		if (exists(media)) {
			sheet.media = media;
		}
		return sheet;
	},
	
	obtain: function(sheet) {
		return get(sheet, function() {
			return obtain(StyleSheet, "$sheet", function() {
				StyleSheet.disableAll();
				return StyleSheet.create();
			});
		});
	},
	
	getRules: function(sheet) {
		return exists(sheet.cssRules) ? sheet.cssRules : sheet.rules;
	},
	
	buildRule: function(style) {
		var obj = {};
		enumerate(style, function(value, key) {
	  	var setter = Html.prototype.styleSetters[key];
	  	if (exists(setter)) {
	  		enumerate(setter(value), function(v, k){
	  			obj[k] = v;
	  		});
	  	} else {
				obj[key] = value;
			}
		});
		
		return "{" + enumerate(obj, writer(
			function(value, key) {
		  	return camelToDash(key) + ":" + value + ";";
		  }
		)) + "}";
	}
};
