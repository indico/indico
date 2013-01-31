/*
* This widget extends an *existing* UI button to allow it to be disabled
* and show a a tooltip while it is disabled.
*/
(function($, undefined) {
    $.widget('indico.disabledButtonWithTooltip',  $.extend({}, $.indico.disabledElementWithTooltip, {
        // Default options
        options: {
            elementClass: 'ui-dttbutton'
        },

        _create: function() {
            this.isUIButton = this.element.is('.ui-button');
            if(this.options.disabled === null) {
                this.options.disabled = this.isUIButton ? this.element.button('option', 'disabled') : false;
            }
            $.indico.disabledElementWithTooltip.prototype._create.apply(this, arguments);
        },

        _update: function() {
            if(this.isUIButton) {
                this.element.button(!this.options.disabled ? 'enable' : 'disable');
            }
            else {
                this.element.prop('disabled', this.options.disabled);
            }
            this.overlay.toggle(this.options.disabled);
        },

        destroy: function() {
            $.indico.disabledElementWithTooltip.prototype.destroy.apply(this, arguments);
            // restore ui-state-disabled since super's destroy removed it
            if(this.isUIButton) {
                this.element.button('option', 'disabled', this.options.disabled);
            }
        },

        _setOption: function(key, value) {
            if(key == 'disabled') {
                this.options.disabled = value;
                if(this.isUIButton) {
                    // HACK HACK HACK: We only want the UI disabled class if it's an UI button.
                    // Unfortunately there is no option to control this so we only call the super method
                    // if we have an UI button.
                    $.Widget.prototype._setOption.apply(this, arguments);
                }
                this._update();
            }
            else {
                $.Widget.prototype._setOption.apply(this, arguments);
            }
        }
    }));
})(jQuery);
