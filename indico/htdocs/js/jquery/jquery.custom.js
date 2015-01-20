(function($, undefined) {
    // Serialize a form to an object with the input names as the keys
    $.fn.serializeObject = function() {
        var obj = {};
        $.each(this.serializeArray(), function(i, pair) {
            obj[pair.name] = pair.value;
        });
        return obj;
    };

    $.fn.textContains = function(term) {
        term = term.toLowerCase();
        return this.filter(function() {
            return $(this).text().toLowerCase().indexOf(term) > -1;
        });
    };

    $.fn.valueContains = function(term) {
        term = term.toLowerCase();
        return this.filter(function() {
            return $(this).val().toLowerCase().indexOf(term) > -1;
        });
    };

    $.fn.hasCSS = function(propertyName, value) {
        return this.css(propertyName) === value;
    };

    var __gotoToday = $.datepicker._gotoToday;

    $.extend($.datepicker, {
        /* Select the current date, don't just show it ### */
        _gotoToday: function(id) {

            _.bind(__gotoToday, this)(id);

            var target = $(id);
            this._setDateDatepicker(target, new Date());
            this._selectDate(id, this._getDateDatepicker(target));
        }
    });

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
    $.widget("indico.reset_resizable", $.ui.resizable, {
        widgetEventPrefix: 'resize',
        _create: function() {
            this.element.data('ui-resizable', this);
            this._super();
        },
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
    });

    $.widget("indico.super_draggable", $.ui.draggable, {
        widgetEventPrefix: 'drag',
        _create: function() {
            this.element.data('ui-draggable', this);
            this._super();
        },
        _setContainment: function(newWidth, newHeight) {
            this.helperProportions.width = newWidth || $(this.element).width();
            //this.helperProportions.height = newHeight || $(this.element).height();
            $.ui.draggable.prototype._setContainment.call(this);
        }
    });

    // Extension of `droppable` that better handles enabling/disabling droppables while a draggable
    // is on top
    $.widget("indico.super_droppable", $.ui.droppable, {
        widgetEventPrefix: 'drop',
        _create: function() {
            this.element.data('ui-droppable', this);
            this._super();
        },
        disable: function() {
            // "artificially" set `isover` to 0, so that if a draggable comes over again we fire `over`
            var data = this.element.data('ui-droppable');
            data.isover = 0;
            data.isout = 1;
            // do as if the draggable was out
            this._out();
            return this._setOption("disabled", true);
        },
        enable: function() {
            return this._setOption("disabled", false);
        }
    });

    // Extension of selector 'contains' in order to allow no case sensitive
    $.extend($.expr[':'], {
        'contains': function (elem, i, match, array) {
            return (elem.textContent || elem.innerText || '').toLowerCase().indexOf((match[3] || "").toLowerCase()) >= 0;
        }
    });

    $.widget('indico.disabledElementWithTooltip', {
        // Default options
        options: {
            disabled: null,
            tooltip: null,
            tooltipClass: 'tooltipError',
            elementClass: 'ui-disabled-element'
        },

        _create: function() {
            var self = this;
            if(this.options.disabled === null) {
                this.options.disabled = false;
            }
            // Wrap the element in a span and create an overlay so we can get mouse events for the disabled button
            this.element.addClass(this.options.elementClass).wrap('<span/>');
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
            this.element.prop('disabled', "disabled");
            this.overlay.toggle(this.options.disabled);
        },

        destroy: function() {
            if(!this.element.hasClass(this.options.elementClass)) {
                return;
            }
            this.overlay.remove();
            this.element.removeClass(this.options.elementClass).unwrap();
            $.Widget.prototype.destroy.apply(this, arguments);
        },

        _setOption: function(key, value) {
            if(key == 'disabled') {
                this.options.disabled = value;
                this._update();
            }
            else {
                $.Widget.prototype._setOption.apply(this, arguments);
            }
        }
    });

    //Extract a param from the current url
    $.urlParam = function(name){
        var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
        if (!results) { return null; }
        return results[1] || null;
    };

    // Based on code from http://detectmobilebrowsers.com/
    (function(ua, target) {
        target.mobileBrowser = /(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows (ce|phone)|xda|xiino/i.test(ua) || /1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(ua.substr(0, 4))
    })(navigator.userAgent || navigator.vendor || window.opera, $);

})(jQuery);
