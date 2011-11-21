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
        'sticky' : function(className) {
            $(window).scroll(function() {
                $(className || '.ui-follow-scroll').each(function(){
                    if (!$(this).data('original-offset')) {
                        $(this).data('original-offset', $(this).offset());
                    }

                    var eloffset = $(this).data('original-offset');
                    var windowpos = $(window).scrollTop();
                    if(windowpos > eloffset.top) {
                        $(this).addClass('scrolling');
                    } else {
                        $(this).removeClass('scrolling');
                    }
                });
            });
        }
    });
})(jQuery);
