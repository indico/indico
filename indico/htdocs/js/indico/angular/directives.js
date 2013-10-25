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

ndDirectives.directive("ndDialog", function($timeout) {
    return {
        transclude: true,
        template: "<div ng-transclude></div>",

        scope: {
            title: "@"
        },

        link: function(scope, element, attrs) {

            var dialog = new ExclusivePopupWithButtons(attrs.title);

            dialog.draw = function() {
                return this.ExclusivePopupWithButtons.prototype.draw.call(this, element);
            };

            dialog._onClose = function() {

            };

            attrs.$observe("show", function(val) {
                if (scope.$eval(val) === true) {
                    dialog.open();
                } else {
                    dialog.close();
                }
            });

        }
    };
});
