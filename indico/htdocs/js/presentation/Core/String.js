/**
 * @author Tom
 */

/**
 * Returns true if the text starts with the string.
 * @param {String} text
 * @param {String} string
 * @return {Boolean} result
 */
function startsWith(text, string) {
	return string == text.slice(0, string.length);
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
