// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

angular
  .module('nd', ['ndDirectives', 'ndFilters', 'ndServices', 'nd.regform'])

  .controller('AppCtrl', function($scope) {
    // Main application controller.
    // This is a good place for logic not specific to the template or route
    // such as menu logic or page title wiring.
  });
