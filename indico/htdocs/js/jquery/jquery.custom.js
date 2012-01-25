(function($, undefined) {
    // Serialize a form to an object with the input names as the keys
    $.fn.serializeObject = function() {
        var obj = {};
        $.each(this.serializeArray(), function(i, pair) {
            obj[pair.name] = pair.value;
        });
        return obj;
    };

    $.extend($.ui, {
        'sticky' : function(arg1, arg2) {

            if (arg2 !== undefined) {
                var className = arg1, options = arg2;
            } else {
                if (typeof arg1 == "string") {
                    var className = arg1, options = {};
                } else {
                    var className = null, options = arg1;
                }
            }

            var scrolling = {};

            var visible = function(elem) {
                var eloffset = elem.data('original-offset');
                var windowpos = $(window).scrollTop();

                if (!eloffset) {
                    eloffset = elem.offset();
                    elem.data('original-offset', eloffset);
                }

                if(windowpos > eloffset.top) {
                    elem.addClass('scrolling');
                    return false;
                } else {
                    elem.removeClass('scrolling');
                    return true;
                }
            };

            $(window).scroll(function(event) {
                $(className || '.ui-follow-scroll').each(function(){
                    var now_scrolling = !visible($(this));

                    if (scrolling[this] !== now_scrolling) {
                        if (now_scrolling === false) {
                            options.normal.call(this, event);
                        } else {
                            options.sticky.call(this, event);
                        }
                        scrolling[this] = now_scrolling;
                    }

                });
            });
        }
    });


    // Simple solution for updating containment on resize
    $.widget("ui.reset_resizable", $.extend({}, $.ui.resizable.prototype, {
        resetContainment: function() {
            var element = this.containerElement, p = [];

            $([ "Top", "Right", "Left", "Bottom" ]).each(function(i, name) {
                p[i] = parseInt(element.css("padding" + name), 10) || 0;
            });

            this.containerSize = {
                height: (element.innerHeight() - p[3]),
                width: (element.innerWidth() - p[1])
            };
            this.parentData.width = this.containerSize.width;
            this.parentData.height = this.containerSize.height;
        }
    }));

    $.widget("ui.super_draggable", $.extend({}, $.ui.draggable.prototype, {
        _setContainment: function(newWidth, newHeight) {
            this.helperProportions.width = newWidth || $(this.element).width();
            //this.helperProportions.height = newHeight || $(this.element).height();
            $.ui.draggable.prototype._setContainment.call(this);
        }
    }));

    // Extension of `droppable` that better handles enabling/disabling droppables while a draggable
    // is on top
    $.widget("ui.super_droppable", $.extend({}, $.ui.droppable.prototype, {
        disable: function() {
            // "artificially" set `isover` to 0, so that if a draggable comes over again we fire `over`
            var data = this.element.data('droppable')
            data.isover = 0;
            data.isout = 1;
            // do as if the draggable was out
            this._out();
	    return this._setOption("disabled", true);
        },
        enable: function() {
	    return this._setOption("disabled", false);
        }
    }));

})(jQuery);
