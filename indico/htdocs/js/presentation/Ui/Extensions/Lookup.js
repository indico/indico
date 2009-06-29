/**
 * @author Tom
 */

extend(Html.prototype, {
	lookupField: function() {
		if (this.isField()) {
			return this;
		}
		return lookup(this, function(item) {
			return item.lookupField();
		});
	}
});
