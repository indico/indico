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


    $.widget( "ui.dropdown", {
        options: {
            effect_on: 'fadeIn',
            effect_off: 'fadeOut',
            time_on: 200,
            time_off: 200,
            positioning: {}
        },

        _close: function(elem, effect) {
            this._effect('off', elem.siblings('ul'), effect);
            elem.siblings('ul').find('ul').hide();
            elem.data('on', false);
            elem.parent().removeClass('selected');
            elem.siblings('ul').find('a').data('on', false);
        },

        _close_all: function(effect) {
            var self = this;
            this.element.children().find('a').each(function() {
                self._close($(this), effect);
            });
        },

        _open: function(elem) {
            var self = this;
            var sibl = elem.siblings('ul');
            this._effect('on', sibl);
            elem.data('on', true);
            elem.parent().addClass('selected');
            sibl.position($.extend({of: elem.parent()}, this.options.positioning[sibl.data('level')] ||
                                   {my: 'center top', at: 'center bottom', offset: '-1px 0px'}));
            elem.parent().siblings().find('a').each(function() {
                self._close($(this));
            });
        },

        _set_classes: function(elem, level) {
            var self = this;
            level = level || 0;
            elem.addClass('ui-list-menu-level-' + level);
            elem.addClass('ui-list-menu-level');
            elem.data('level', level);
            elem.children('li').children('ul').each(function() {
                self._set_classes($(this), level + 1);
            });
        },

        _menuize: function(elem) {
            var self = this;

            this._set_classes(elem);

            elem.addClass('ui-list-menu');
            elem.find('li a').each(function() {
                $this = $(this);
                if ($this.siblings('ul').length) {
                    $this.data('expandable', true);
                    // add little arrow
                    $this.before('<span class="arrow">▾</span>');
                }
                $this.siblings('ul').hide();
                $this.parent().addClass('');
            }).click(function() {
                var $this = $(this);
                if ($this.data('expandable')) {
                    if ($this.data('on')) {
                        self._close($this);
                    } else {
                        self._open($this);
                    }
                    return false;
                } else {
                    var result = $this.triggerHandler('menu_select', self.element);
                    if(!result) {
                        self._close_all();
                    }
                    return false;
                }
            });
        },

        _create: function() {
            var self = this;
            this._menuize(this.element);
            $(window).click(function() {
                self._close_all();
            });
        },

        _effect: function(st, elem, effect) {
            if (effect === undefined) {
                var func = this.options['effect_' + st];
            } else {
                var func = effect;
            }

            if (func === null) {
                // no pretty effects
                elem.hide();
            }
            else if (typeof func == 'function') {
                func.call(elem, this);
            } else {
                elem[func].call(elem, this.options['time_' + st]);
            }
        },

        close: function() {
            this._close_all(null);
        }
    });

})(jQuery);
