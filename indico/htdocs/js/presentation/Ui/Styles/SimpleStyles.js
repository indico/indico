/**
 * @author Tom
 */

extend(XElement.prototype, {
	/**
	 * @return {Accessor}
	 */
	visible: function() {
		var self = this;
		return new Accessor(function(){
			return self.getStyle("display") != "none";
		}, function(value){
			return self.setStyle("display", value ? null : "none");
		});
	},
	/**
	 * 
	 * @param {Number|String} height
	 * @param {Number|String} [width]
	 */
	scroll: function(height, width) {
		var style = {
            overflow: "auto",
            height: height
        };
		if (exists(width)) {
			style.width = width;
		}
		return this.setStyle(style);
	}
});

