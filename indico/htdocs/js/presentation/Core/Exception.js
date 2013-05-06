/**
 * @author Tom
 */

function Exception(message, data, inner) {
	this.message = message;
	this.data = data;
	this.inner = inner;
}

Exception.prototype.toString = function() {
	var text = this.message;
	if (this.data) {
		text += " " + Json.write(this.data);
	}
	if (this.inner) {
		text += " < " + this.inner;
	}
	return text;
};
