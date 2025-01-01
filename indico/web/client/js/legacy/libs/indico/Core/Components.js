// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

function imageFunctionGenerator(url) {
  return function(imageId, extension) {
    return url + '/' + imageId + '.' + (extension || 'png');
  };
}

var imageSrc = imageFunctionGenerator(Indico.Urls.ImagesBase);

function pixels(val) {
  return val + 'px';
}

function zeropad(number) {
  return ('' + number).length == 1 ? '0' + number : number;
}

/**
 @namespace IndicoUI interface library
*/

var IndicoUI = {
  // The current used layer level
  __globalLayerLevel: 0,

  // To keep track of all used layer levels.
  // A used level is set to true and level 0 is always used
  __globalLayerLevels: [true],

  /**
   * Set the element's z-index to the top layer
   */
  assignLayerLevel: function(element) {
    if (!exists(element)) return;
    // Find the highest used layer
    for (var i = this.__globalLayerLevel; i >= 0; i--) {
      if (this.__globalLayerLevels[i]) {
        this.__globalLayerLevel = i;
        break;
      }
    }

    var level = ++this.__globalLayerLevel;
    this.__globalLayerLevels[level] = true;
    element.setStyle('zIndex', this.__globalLayerLevel + 3000);
  },
  /**
   * Marks a layer level as unused, call this funtion
   * when closing an element
   */
  unAssignLayerLevel: function(element) {
    if (!exists(element)) return;
    var level = element.dom.style.zIndex;
    if (level == '') {
      return;
    }
    this.__globalLayerLevels[parseInt(level) - 3000] = false;
  },
};
