/**
 * @author Tom
 */

/**
 * 
 * @param {String} name
 * @param {String} caption
 * @param {Function} [editor]
 */
function Field(name, caption, editor) {
	this.name = name;
	this.caption = caption;
	this.editor = editor;
}

/**
 * 
 * @param {Accessor} source
 * @param {String} caption
 * @param {Function} [editor]
 * @return {Array}
 */
Widget.field = function(source, caption, editor) {
	var $ = WidgetContext(this);
	editor = any(editor, $.textEditor);
	return $.labelled(editor(source), caption)
};

/**
 * 
 * @param {Object} source
 * @param {Object} style
 * @return {XElement}
 */
Widget.form = function(source, style) {
	var $ = WidgetContext(this);
	return $.block([
		$.table($L(style.fields, function(field) {
			return $.field(source[field.name], field.caption, field.editor);
		})),
		$.button(command(style.save, $.t("Save"))),
		$.button(command(style.cancel, $.t("Cancel")))
	]);
};
