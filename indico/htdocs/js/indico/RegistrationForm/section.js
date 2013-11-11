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

ndRegForm.controller('SectionCtrl', ['$scope', '$rootScope','RESTAPI',  function($scope, $rootScope, RESTAPI) {
    $scope.api = {};

    $scope.api.createSection = function(section) {
        // TODO see how to push a section into the list of sections
    };

    $scope.api.disableSection = function(section) {
        RESTAPI.Sections.disable({confId: $rootScope.confId, sectionId: section.id}, function(data) {
            section.enabled = data.enabled; //TODO: See why we cannot put section=data
        });
    };

    $scope.api.restoreSection = function(section) {
        RESTAPI.Sections.enable({confId: $rootScope.confId, sectionId: section.id}, function(data) {
            section.enabled = data.enabled; //TODO: See why we cannot put section=data
        });
    };

    $scope.api.removeSection = function(section) {
        RESTAPI.Sections.remove({confId: $rootScope.confId, sectionId: section.id}, function(data) {
            //TODO: See how to update model!!
        });
    };

    $scope.api.addField = function(section, field) {
        // TODO properly initialize field
        section.items.push({
            id: -1,
            input: 'text',
            caption: 'testcaption',
            description: 'desc'
        });
    };
}]);

ndRegForm.directive('ndSection', function(url) {
    return {
        replace: true,
        templateUrl: url.tpl('section.tpl.html'),
        controller: 'SectionCtrl',

        link: function(scope, element) {

            scope.buttons = {
                newfield: false,
                config: false,
                disable: false
            };

            scope.dialogs = {
                newfield: false,
                config: false
            };

            scope.state = {
                collapsed: false
            };

            scope.sectionApi = {
                disableSection: function() {
                    scope.section.enabled = false;
                }
            };

            scope.tabs = [];

            scope.$on('collapse', function(event, collapsed) {
                scope.state.collapsed = collapsed;
            });

            scope.$watch('state.collapsed', function(val) {
                var content = angular.element(element.children()[1]);
                if (val) {
                    content.slideUp();
                } else {
                    content.slideDown();
                }
            });

            scope.$watch('section', function(val) {
                // TODO sync section with server
                console.log('Syncing section');
            });
        }
    };
});

ndRegForm.directive("ndGeneralSection", function($timeout) {
    return {
        require: 'ndSection',
        controller: 'SectionCtrl', //TODO check inheritance
        link: function(scope) {
            scope.buttons.newfield = true;
            scope.buttons.disable = true;

            // TODO can we move fieldtypes to the tpl? It only happens once
            // scope.fieldtypes = [
            //     {id: 'label',            desc: $T("Label")},
            //     {id: 'text',             desc: $T("Text input")},
            //     {id: 'number',           desc: $T("Number")},
            //     {id: 'textarea',         desc: $T("Text area")},
            //     {id: 'radio-dropdown',   desc: $T("Dropdown")},
            //     {id: 'radio-radiogroup', desc: $T("Choice")},
            //     {id: 'checkbox',         desc: $T("Checkbox")},
            //     {id: 'date',             desc: $T("Date")},
            //     {id: 'yesno',            desc: $T("Yes/No")},
            //     {id: 'telephone',        desc: $T("Phone")},
            //     {id: 'country',          desc: $T("Country")},
            //     {id: 'file',             desc: $T("File")}
            // ];

            scope.sectionApi.addField = function(fieldType, inputType) {
                var newfield = {
                    id: -1,
                    input: fieldType,
                    inputType: inputType,
                    caption: '',
                    values: {}
                };

                scope.section.items.push(newfield);
                scope.dialogs.newfield = true;
            };

            scope.sectionApi.removeNewField = function() {
                if (scope.section.items[scope.section.items.length-1].id == -1) {
                    $timeout(function() {
                        scope.section.items.pop();
                    }, 0);
                }
            };

            scope.sectionApi.commitNewField = function() {

            };

        }
    };
});

ndRegForm.directive("ndPersonalDataSection", function() {
    return {
        require: 'ndGeneralSection',
        link: function(scope) {
            scope.buttons.disable = false;
            scope.tabs = [
                {id: 'config',              name: $T("Configuration"),          type: 'config' },
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
                {id: 'config',              name: $T("Configuration"),          type: 'config' },
                {id: 'editAccomodation',    name: $T("Edit accommodations"),    type: 'editionTable' }
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
                {id: 'config',          name: $T("Configuration"),      type: 'config'},
                {id: 'editSessions',    name: $T("Manage sessions"),    type: 'editionTable'}
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
            scope.tabs = [
                {id: 'config',          name: $T("Configuration"),     type: 'config'},
                {id: 'editEvents',      name: $T("Edit events"),       type: 'editionTable'},
                {id: 'canceledEvent',   name: $T("Canceled events"),   type: 'cancelEvent'}
            ];
        }
    };
});

ndRegForm.directive('ndSectionDialog', function(url) {
    return {
        require: 'ndDialog',
        replace: true,
        templateUrl: url.tpl('sections/dialogs/base.tpl.html')
    };
});
