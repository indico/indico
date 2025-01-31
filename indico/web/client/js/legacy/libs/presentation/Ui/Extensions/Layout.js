// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

extend(Html.prototype, {
  isBody: function() {
    return document.body === this.dom;
  },

  getOffsetParent: function() {
    return $E(this.getAttribute('offsetParent'));
  },
});

// based on mootools
delayedBind(Html.prototype, 'getAbsolutePosition', function(dom) {
  return this.dom.getBoundingClientRect && !Browser.WebKit
    ? function() {
        var bound = this.dom.getBoundingClientRect();
        var html = document.documentElement;
        return new Point(
          Math.round(bound.left + html.scrollLeft - html.clientLeft),
          Math.round(bound.top + html.scrollTop - html.clientTop)
        );
      }
    : function() {
        var position = new Point();
        var element = this;
        while (exists(element) && !element.isBody()) {
          position.move(
            new Point(element.getAttribute('offsetLeft'), element.getAttribute('offsetTop'))
          );
          element = element.getOffsetParent();
        }
        return position;
      };
});
