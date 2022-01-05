// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

var ndFilters = angular.module('ndFilters', []);

ndFilters.filter('i18n', function() {
  return function(input) {
    var str = $T.gettext(input);
    if (arguments.length > 1) {
      str = str.format.apply(str, [].slice.call(arguments, 1));
    }
    return str;
  };
});

ndFilters.filter('range', function() {
  return function(input, min, max) {
    min = parseInt(min, 10) || 0;
    max = parseInt(max, 10);
    for (var i = min; i <= max; i++) {
      input.push(i);
    }
    return input;
  };
});
