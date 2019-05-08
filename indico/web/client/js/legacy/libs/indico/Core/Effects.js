// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

IndicoUI.Effect = {
    /**
        * Simple CSS manipulation that sets the element's 'display' property to a new style
        * @param {XElement} element the target element
        * @param {string} newStyle the new display style, e.g.: "inline", "block", "table-row".
        *                 If not existant, will be set to '', which usually restores the default style of the element.
        */
    appear: function(element, newStyle){
        if (!exists(newStyle)) {
            newStyle = '';
        }
        element.dom.style.display = newStyle;
    },

    /**
        * Simple CSS manipualtion that sets the element's
        * 'display' property to 'none'
        * @param {XElement} element the target element
        */
    disappear: function(element){
        element.dom.style.display = 'none';
    },

    followScroll: function() {
        $.each($('.follow-scroll'),function(){
            if (!$(this).data('original-offset')) {
                $(this).data('original-offset', $(this).offset());
            }

            var eloffset = $(this).data('original-offset');
            var windowpos = $(window).scrollTop();
            if(windowpos > eloffset.top) {
                if (!$(this).hasClass("scrolling")) {
                    $(this).data({
                        "original-left": $(this).css("left"),
                        "original-width": $(this).css("width")
                    });
                    $(this).css("width", $(this).width());
                    $(this).css("left", eloffset.left);
                    $(this).addClass('scrolling');
                }
            } else {
                if ($(this).hasClass("scrolling")) {
                    $(this).css("left", $(this).data("original-left"));
                    $(this).css("width", $(this).data("original-width"));
                    $(this).removeClass('scrolling');
                }
            }
        });
    }
};

