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
            show: '=',
            heading: '@',
            okButton: '@',
            okCallback: '&',
            cancelButton: '@',
            cancelCallback: '&',
            api: '=',
            data: '=',
            config: "="
        },

        controller: function($scope) {
            $scope.actions = {
                init: function() {},
                cleanup: function() {},
                close: function() {
                    $scope.actions.cleanup();
                    $scope.show = false;
                    $scope.$apply($scope.show);
                },
                cancel: function() {
                    $scope.cancelCallback({dialogScope: $scope});
                    $scope.actions.close();
                },
                ok: function() {
                    $scope.okCallback({dialogScope: $scope});
                    $scope.actions.close();
                }
            };
        },

        link: function(scope, element) {
            var dialog = new ExclusivePopupWithButtons(
                scope.heading,
                scope.actions.cancel,
                false,
                false,
                true
            );

            dialog._onClose = function() {};

            dialog._getButtons = function() {
                return [
                    [scope.okButton, function() {
                        scope.actions.ok();
                    }],
                    [scope.cancelButton, function() {
                        scope.actions.cancel();
                    }]
                ];
            };

            dialog.draw = function() {
                return this.ExclusivePopupWithButtons.prototype.draw.call(this, element);
            };

            scope.setSelectedTab = function(tab_id) {
                scope.tabSelected = tab_id;
            };

            scope.isTabSelected = function(tab_id) {
                return scope.tabSelected === tab_id;
            };

            scope.$watch("show", function(val) {
                if (scope.show === true) {
                    scope.actions.init();
                    dialog.open();
                } else {
                    dialog.close();
                }
            });

            scope.$watch('heading', function(val) {
                dialog.title = val;
                dialog.canvas = null;
            });

            scope.$watch('okButton', function() {
                scope.okButton = scope.okButton || $T('Ok');
            });

            scope.$watch('cancelButton', function() {
                scope.cancelButton = scope.cancelButton || $T('Cancel');
            });

            dialog.draw();
        }
    };
});

ndDirectives.directive("contenteditable", function() {
    return {
        require: 'ngModel',
        link: function(scope, elem, attrs, ctrl) {
            // view -> model
            elem.on('blur', function(e, param) {
                elem.html(ctrl.$viewValue);
            });

            elem.on('keydown keypress', function(e) {
                if(e.keyCode === K['ESCAPE']) {
                    elem.blur();
                } else if(e.keyCode === K['ENTER']) {
                    scope.$apply(function() {
                        ctrl.$setViewValue(elem.html());
                    });
                    elem.blur();
                }
            });

            // model -> view
            ctrl.$render = function() {
                elem.html(ctrl.$viewValue);
            };
        }
    };
});

ndDirectives.directive('ndDatepicker', function() {
    return {
        restrict: 'E',
        scope: {
            showTime: '=',
            hiddenInputs: '@',
            dateFormat: '@'
        },

        link: function(scope, element) {
            var hiddenInputs =
                scope.$eval(scope.hiddenInputs) ||
                ['day', 'month', 'year', 'hour', 'min'];

            scope.init = function() {
                element.html(scope.getDatePicker().dom);
                _.each(hiddenInputs, function(id) {
                    element.append(
                        '<input type="hidden" value="" name="{0}" id="{1}"/>'.format(id, id)
                    );
                });
            };

            scope.getDatePicker = function() {
                return IndicoUI.Widgets.Generic.dateField(
                    scope.showTime,
                    null,
                    hiddenInputs,
                    null,
                    scope.dateFormat
                );
            };

            scope.$watch('dateFormat', function(newVal, oldVal) {
                scope.init();
            });

            scope.init();
        }
    };
});
