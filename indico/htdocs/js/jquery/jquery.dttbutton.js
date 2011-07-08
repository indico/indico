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
            if(this.options.disabled === null) {
                this.options.disabled = this.element.button('option', 'disabled');
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

            // TODO: use mouseenter/mouseleave or simply hover when we have a proper tooltip (qtip2)
            this.options.tooltipElem = null;
            this.overlay.mousemove(function(e) {
                var text = $.isFunction(self.options.tooltip) ? self.options.tooltip() : self.options.tooltip;
                if(text) {
                    if(self.tooltipElem) {
                        self.tooltipElem.remove();
                    }
                    self.tooltipElem = $(IndicoUI.Widgets.Generic.errorTooltip(e.clientX, e.clientY, text, self.options.tooltipClass).dom);
                }
            }).mouseout(function(e) {
                if(self.tooltipElem) {
                    self.tooltipElem.remove();
                }
            });

            this._update();
        },

        _update: function() {
            this.element.button(!this.options.disabled ? 'enable' : 'disable');
            this.overlay.toggle(this.options.disabled);
        },

        destroy: function() {
            if(!this.element.hasClass('ui-dttbutton')) {
                return;
            }
            if(this.tooltipElem) {
                this.tooltipElem.remove();
            }
            this.overlay.remove();
            this.element.removeClass('ui-dttbutton').unwrap();
            $.Widget.prototype.destroy.apply(this, arguments);
            // restore ui-state-disabled since super's destroyremoved it
            this.element.button('option', 'disabled', this.options.disabled);
        },

        _setOption: function(key, value) {
            $.Widget.prototype._setOption.apply(this, arguments);
            if(key == 'disabled') {
                this._update();
            }
        }
    });
})(jQuery);
