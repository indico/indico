// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

IndicoUI.Effect = {
  followScroll: function() {
    $.each($('.follow-scroll'), function() {
      if (!$(this).data('original-offset')) {
        $(this).data('original-offset', $(this).offset());
      }

      var eloffset = $(this).data('original-offset');
      var windowpos = $(window).scrollTop();
      if (windowpos > eloffset.top) {
        if (!$(this).hasClass('sticky-scrolling')) {
          $(this).data({
            'original-left': $(this).css('left'),
            'original-width': $(this).css('width'),
          });
          $(this).css('width', $(this).width());
          $(this).css('left', eloffset.left);
          $(this).addClass('sticky-scrolling');
        }
      } else {
        if ($(this).hasClass('sticky-scrolling')) {
          $(this).css('left', $(this).data('original-left'));
          $(this).css('width', $(this).data('original-width'));
          $(this).removeClass('sticky-scrolling');
        }
      }
    });
  },
};
