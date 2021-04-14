// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

ndRegForm.directive('ndTable', function(url, sortableoptions) {
  return {
    restrict: 'E',
    replace: true,
    templateUrl: url.tpl('table.tpl.html'),

    scope: {
      config: '=',
      formData: '=',
      filter: '=',
      filterValue: '=',
      validationStarted: '=',
    },

    controller: function($scope) {
      $scope.actionIsArray = function(action) {
        return _.isArray(action);
      };

      $scope.actionItem = function(item, action) {
        if (action == 'remove') {
          item['remove'] = true;
        } else if (action == 'cancel') {
          item['cancelled'] = true;
        } else if (action == 'uncancel') {
          item['cancelled'] = false;
        }
      };

      $scope.isSortable = function() {
        return $scope.config.actions.indexOf('sortable') != -1;
      };

      $scope.matchFilter = function(item) {
        if (item.remove === true) {
          return false;
        } else if ($scope.filter !== undefined && $scope.filterValue !== undefined) {
          return item[$scope.filter] === $scope.filterValue;
        } else if (!item.id) {
          return true;
        } else {
          return true;
        }
      };

      $scope.itemSortableOptions = {
        helper: function(e, tr) {
          var $originals = tr.children();
          var $helper = tr.clone();
          $helper.children().each(function(index) {
            // Set helper cell sizes to match the original sizes
            $(this).width($originals.eq(index).width());
          });
          return $helper;
        },
        containment: 'parent',
        disabled: !$scope.isSortable(),
        handle: '.table-sortable-handle',
        placeholder: 'regform-table-sortable-placeholder',
      };

      angular.extend($scope.itemSortableOptions, sortableoptions);
    },
  };
});
