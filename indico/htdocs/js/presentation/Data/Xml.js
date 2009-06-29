/**
 * @author Tom
 */

var Xml = {};

delayBind(Xml, "parse", function(source) {
	if (isDefined("DOMParser")) {
		return function(source) {
			var parser = new DOMParser(); 
			return parser.parseFromString(source, "text/xml"); 
		};
	} else if (isDefined("ActiveXObject")){ 
		return function(source) {
			var document = new ActiveXObject("Microsoft.XMLDOM"); 
			document.async = false; 
			document.loadXML(source);
			return document;
		};
	} else {
		throw "Xml parsing not supported."
	}
});

Xml.transform: function(xml, xslt, args) {
		var processor = new XSLTProcessor(); 
		processor.importStylesheet(xslt);
		if (exists(args)) {
			enumerate(args, function(value, key) {
				processor.setParameter("", key, value);
			});
		}
		return processor.transformToDocument(xml);
	}
};
