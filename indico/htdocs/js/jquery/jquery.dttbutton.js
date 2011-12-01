/*
* This widget extends an *existing* UI button to allow it to be disabled
* and show a a tooltip while it is disabled.
*/
(function($, undefined) {
    $.widget('cern.disabledButtonWithTooltip', {
        // Default options
        options: {
            disabled: null,
            tooltip: null,
            tooltipClass: 'tooltipError'
        },

        _create: function() {
            var self = this;
            this.isUIButton = this.element.is('.ui-button');
            if(this.options.disabled === null) {
                this.options.disabled = this.isUIButton ? this.element.button('option', 'disabled') : false;
            }
            // Wrap the element in a span and create an overlay so we can get mouse events for the disabled button
            this.element.addClass('ui-dttbutton').wrap('<span/>');
            var wrapper = this.element.closest('span');
            wrapper.css({
                display: 'inline-block',
                position: 'relative'
            });
            this.overlay = $('<div/>').css({
                position: 'absolute',
                top: 0,
                left: 0,
                height: '100%',
                width: '100%'
            }).appendTo(wrapper);

            this.overlay.qtip({
                content: {
                    text: self.options.tooltip
                },
                position: {
                    target: this.element
                }
            });
            this._update();
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
            if(!this.element.hasClass('ui-dttbutton')) {
                return;
            }
            this.overlay.remove();
            this.element.removeClass('ui-dttbutton').unwrap();
            $.Widget.prototype.destroy.apply(this, arguments);
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
    });
})(jQuery);
