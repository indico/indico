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

ndRegForm.directive("ndSectionToolbar", function() {
    var baseUrl = Indico.Urls.Base + '/js/indico/RegistrationForm/';

    return {
        replace: true,
        templateUrl: baseUrl + 'tpls/sectiontoolbar.tpl.html',

        scope: {
            buttons: '=',
            dialogs: '=',
            state: '='
        },

        controller: function($scope) {
            $scope.openConfig = function() {
                $scope.dialogs.config = true;
            };

            $scope.openNewField = function() {
                $scope.dialogs.newfield = true;
            };

            $scope.disable = function() {
                // TODO implement disable
                console.log("Disable");
            };

            $scope.toggleCollapse = function(e) {
                $scope.state.collapsed = !$scope.state.collapsed;
            };
        }
    };
});
