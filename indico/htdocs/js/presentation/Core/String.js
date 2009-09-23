/**
 * @author Tom
 */

/**
 * Returns true if the text contains the string.
 * @param {String} text
 * @param {String} string
 * @return {Boolean} result
 */
function contains(text, string) {
	return text.indexOf(string) != -1;
}

/**
 * Returns true if the text starts with the string.
 * @param {String} text
 * @param {String} string
 * @return {Boolean} result
 */
function startsWith(text, string) {
	return string == text.slice(0, string.length);
}

/**
 * Returns true if the text ends with the string.
 * @param {String} text
 * @param {String} str
 * @return {Boolean} result
 */
function endsWith(text, str) {
	return str == text.slice(-str.length);
}

var specialCharMap = {
  '\b': '\\b',
  '\t': '\\t',
  '\n': '\\n',
  '\f': '\\f',
  '\r': '\\r',
  '\\': '\\\\',
	'"': '\\"'
};

/**
 * Returns escaped string text.
 * @param {String} text
 * @return {String}
 */
function escapeString(text) {
	return "\"" + text.replace(/[\x00-\x1f\\\"]/g, function(value) {
		if (value in specialCharMap) {
			return specialCharMap[value]
		} else {
			return "\\u00" + zeroPad(value.charCodeAt(0).toString(16), 2);
		}
	}) + "\"";
}

/**
 * Returns text formatting template.
 * @param {String} text
 * @return {Function} templating function
 */
function textTemplate(template) {
	return function(args) {
		return format(template, args);
	};
}

/**
 * Formats the text using the args.
 * @param {String} text
 * @param {Array, Object} args
 * @return {String}
 */
function format(text, args) {
  return text.replace(/(\{\{)|(\}\})|(\{[^\}]*\})/g, function(string) {
    switch (string) {
			case "{{":
				return "{";
			case "}}":
				return "}";
		}
		if (!exists(args)) {
			return "";
		}
		return str(args[string.slice(1, -1)]);
  });
}


/**
 * Remove whitespace from begining and end of the text
 * @param {String} text
 * @return {String}
 */
function trim(text) {
	return trimEnd(trimStart(text));
}

function trimStart(text) {
	return text.replace(/^\s+/, "");
}

function trimEnd(text) {
	return text.replace(/\s+$/, "");
}

function padLeft(text, size, character) {
	while (text.length < size) {
		text = character + text;
	}
	return text;
}

function zeroPad(text, size) {
	return padLeft(text, size, "0");
}

function camelToDash(text) {
	return text.replace(/[A-Z]/g, function(item) {
		return "-" + item.toLowerCase();
	});
}

function decodeHtml(html) {
	var dom = obtain(decodeHtml, "dom", function() {
		return document.createElement("div");
	});
	dom.innerHTML = html;
	var result = [];
	var text = "";
	(function fetch(dom) {
		iterate(dom.childNodes, function(child) {
			if (child.nodeType == 1) {
				result.push(text);
				text = "";
				fetch(child);
				result.push(text);
				text = "";
			} else {
				text += child.nodeValue;
			}
		});
	})(dom);
	result.push(text);
	return result;
}

