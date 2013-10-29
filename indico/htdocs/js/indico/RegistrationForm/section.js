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

ndRegForm.directive('ndSection', function() {
    return {
        replace: true,
        templateUrl: Indico.Urls.Base + '/js/indico/RegistrationForm/section.tpl.html',

        controller: function($scope) {
            $scope.buttons = {
                newfield: false,
                config: false,
                disable: false
            };

            $scope.dialogs = {
                newfield: false,
                config: false
            };

            $scope.state = {
                collapsed: false
            };

            $scope.tabs = {};
        },

        link: function(scope, element) {
            element.attr("hi");
            var content = angular.element(element.children()[1]);

            scope.$watch('state.collapsed', function(val) {
                if (val) {
                    content.slideUp();
                } else {
                    content.slideDown();
                }
            });
        }
    };
});

ndRegForm.directive("ndGeneralSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.newfield = true;
            scope.buttons.disable = true;

            scope.tabs = [
                { id: 'config'              , name: $T("Configuration")     , type: 'config' },
                { id: 'editEvents'          , name: $T("Edit events")       , type: 'editionTable' },
                { id: 'canceledEvent'       , name: $T("Canceled events")   , type: 'cancelEvent' }
            ];
        }
    };
});

ndRegForm.directive("ndAccommodationSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.config = true;
            scope.buttons.disable = true;

            scope.tabs = [
                { id: 'config',               name: $T("Configuration"),             type    : 'config' },
                { id: 'editAccomodation',     name: $T("Edit accommodations"),       type    : 'editionTable' }
            ];
        }
    };
});

ndRegForm.directive("ndFurtherInformationSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.disable = true;
        }
    };
});

ndRegForm.directive("ndPersonalDataSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.newfield = true;
        }
    };
});

ndRegForm.directive("ndReasonSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.disable = true;
        }
    };
});

ndRegForm.directive("ndSessionsSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.config = true;
            scope.buttons.disable = true;

            scope.tabs = [
                { id: 'config',         name: $T("Configuration"),        type    : 'config' },
                { id: 'editSessions',   name: $T("Manage sessions"),      type    : 'editionTable' }
            ];
        }
    };
});

ndRegForm.directive("ndSocialEventSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.config = true;
            scope.buttons.disable = true;
        }
    };
});
