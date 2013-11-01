/* This file is part of Indico.
 * Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

var ndDirectives = angular.module("ndDirectives", []);

ndDirectives.directive("ndDialog", function() {
    return {
        restrict: 'E',
        scope: {
            heading: '@',
            show: '=',
            okButton: '@',
            okCallback: '&',
            cancelButton: '@',
            cancelCallback: '&',
            data: "@"
        },

        controller: function($scope) {
            $scope.close = function() {
                $scope.show = false;
                $scope.$apply($scope.show);
            };

            $scope.cancel = function() {
                $scope.cancelCallback({dialogScope: $scope});
                $scope.close();
            };

            $scope.ok = function() {
                $scope.okCallback({dialogScope: $scope});
                $scope.close();
            };
        },

        link: function(scope, element, attrs) {
            var dialog = new ExclusivePopupWithButtons(
                attrs.heading,
                scope.close,
                false,
                false,
                true
            );

            dialog._onClose = function() {};

            dialog._getButtons = function() {
                return [
                    [attrs.okButton, function() {
                        scope.ok();
                    }],
                    [attrs.cancelButton, function() {
                        scope.cancel();
                    }]
                ];
            };

            dialog.draw = function() {
                return this.ExclusivePopupWithButtons.prototype.draw.call(this, element);
            };

            scope.$watch("show", function() {
                if (scope.show === true) {
                    dialog.open();
                } else {
                    dialog.close();
                }
            });

            attrs.$observe('heading', function(val) {
                dialog.title = val;
                dialog.canvas = null;
            });

            dialog.draw();
        }
    };
});
