/**
 * @author Tom
 */

function StyledItem(attributes, content) {
	this.attributes = attributes;
	this.content = content;
}


Widget.t = function(id) {
	return id;
};

/**
 * Option template
 * @param {WatchPair, Object} item
 * @return {XElement} option
 */
Widget.option = function(item) {
	var option = Html.option();
	if (item.WatchPair) {
		$B(option, item);
		$B(option.accessor("value"), item.key);
		$B(option.accessor("selected"), item.selected);
		$B(option.accessor("disabled"), item.disabled);
	} else {
		option.setAttribute("value", item);
		option.set(item);
	}
	return option;
};

/**
 * Command template
 * @param {Function} command
 * @param {XElement} target
 * @return {String} caption
 */
Widget.clickable = function(command, target) {
	invoke(target.stopClickable);
	target.stopClickable = target.observeClick(function(event) {
		command(event);
		return false;
	});
	if (target.getTag() == "a") {
		target.setAttribute("href", "#");
	}
	return command.caption;
};

/**
 * Return IMG
 * @param {String} url
 * @param {String} text
 * @return {XElement} IMG
 */
Widget.image = function(url, text) {
	return Html.img({
		alt: text,
		src: url
	});	
};

/**
 * Create object
 * @param {MimeType} type
 * @param {Object} params
 * @param {Number, String} width
 * @param {Number, String} height
 * @return {XElement}
 */
Widget.object = function(type, params, width, height) {
	if (Browser.IE) {
		return Html.object({
			classid: type.classid,
			codebase: type.codebase,
			width: width,
			height: height
		}, $A(params, 0, function(value, key) {
			return Html.param({
				name: key,
				value: value
			});
		}));
	} else {
		return Html.object({
			type: type.name,
			data: params.src,
			width: width,
			height: height
		}, Html.param({name: "pluginurl", value: type.url}),
		$A(params, 0, function(value, key) {
			return Html.param({
				name: key,
				value: value
			});
		}));
	}
};

/**
 * 
 * @param {XElement} target
 * @param {String, StyledItem} caption
 * @return {Array}
 */
Widget.labelled = function(target, caption) {
	var $ = WidgetContext(this);
	var label = $.label(caption);
	target.setAttribute("id", label.getAttribute("htmlFor"));
	return [
		label,
		target
	];
};

/**
 * Returns LABEL
 * @param {String, StyledItem} caption
 * @return {XElement}
 */
Widget.label = function(caption) {
	var $ = WidgetContext(this);
	caption = $.getCaption(caption);
	caption.attributes.htmlFor = Html.generateId();
	return Html.label(caption.attributes, caption.content);
};

/**
 * Returns caption
 * @param {String, StyledItem} caption
 * @return {StyledItem} result
 */
Widget.getCaption = function(caption) {
	if (caption instanceof StyledItem) {
		return caption;
	}
	var text = str(caption);
	var parts = text.split("_", 2);
	if (parts.length < 2) {
		return new StyledItem({}, parts.join(""));
	}
	if (parts[1] == "") {
		return new StyledItem({}, parts[0]);
	}
	var accessKey = parts[1].slice(0, 1); // parts[1][0] does not work in IE7
	var nextPart = parts[1].slice(1);
	if (parts[0] == "") {
		return new StyledItem({
			accessKey: accessKey.toLowerCase()
		}, [
			Html.span("access-key", accessKey),
			nextPart
		]);
	}
	return new StyledItem({
		accessKey: accessKey.toLowerCase()
	}, [
		parts[0],
		Html.span("access-key", accessKey),
		nextPart
	]);
};



//	/**
//	 * Returns table
//	 * @param {Source} source
//	 * @param {Array} headers
//	 * @param {Function} rowTemplate
//	 * @param {Object} stateCommands
//	 * @return {XElement}
//	 */
//	remoteTable: function(source, headers, rowTemplate, stateCommands) {
//		var table = Table.create(isArray(headers) ? headers : null,
//			new $L(source, rowTemplate), [
//				new Table.Cell(bind.commands($V(), source.state, stateCommands), {
//					colspan: any(headers.length, null)
//				}
//		)]);
//		return table;
//	},

