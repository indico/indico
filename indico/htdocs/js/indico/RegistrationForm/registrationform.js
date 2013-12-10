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

var ndRegForm = angular.module('nd.regform', [
    'ui.sortable',
    'ngResource'
]);

// ============================================================================
// Initialization
// ============================================================================

ndRegForm.value('editionurl',
    Indico.Urls.Base + '/event/:confId/manage/registration/preview/'
);

ndRegForm.value('displayurl',
    Indico.Urls.Base + '/event/:confId/registration/sections'
);

ndRegForm.value('sortableoptions', {
    start: function(e, ui) {
        var borderOffset = 2;
        ui.placeholder.height(ui.helper.outerHeight() - borderOffset);
    },
    axis: 'y',
    cursor: 'move',
    delay: 150,
    distance: 10,
    opacity: 0.90,
    tolerance: 'pointer'
});

ndRegForm.config(function(urlProvider) {
    urlProvider.setModulePath('/js/indico/RegistrationForm');
});

ndRegForm.factory('regFormFactory', function($resource, editionurl, displayurl) {

    var sectionurl = editionurl + 'sections/:sectionId';
    var fieldurl = sectionurl + '/fields/:fieldId';
    return {
        Sections: $resource(sectionurl, {8000: ":8000", confId: '@confId', sectionId: "@sectionId"}, {
            "remove": {url: sectionurl, method: 'DELETE', isArray: true},
            "getAllSections": {method: 'GET', isArray: true},
            "getVisibleSections": {url: displayurl, method: 'GET', isArray: true},
            "enable": {method: 'POST', url: sectionurl + "/enable"},
            "disable": {method: 'POST', url: sectionurl + "/disable"},
            "move": {method: 'POST', url: sectionurl + "/move"},
            "title": {method: 'POST', url: sectionurl + "/title"},
            "description": {method: 'POST', url: sectionurl + "/description"}
        }),
        Fields: $resource(fieldurl, {8000: ":8000", confId: '@confId', sectionId: "@sectionId", fieldId: "@fieldId"}, {
            "enable": {method:'POST', url: fieldurl + "/enable"},
            "disable": {method:'POST', url: fieldurl + "/disable"},
            "move": {method:'POST', url: fieldurl + "/move"}
        }),
        Sessions: $resource(Indico.Urls.Base + '/event/:confId/manage/sessions', {8000: ":8000", confId: '@confId'}, {})
    };
});

// ============================================================================
// Directives
// ============================================================================

ndRegForm.directive('ndRegForm', function($rootScope, url, sortableoptions, regFormFactory) {
    return {
        replace: true,
        templateUrl:  url.tpl('registrationform.tpl.html'),

        scope: {
            confId: '@',
            confSdate: '@',
            confEdate: '@',
            editMode: '=',
            currency: '@'
        },

        controller: function($scope, $resource) {
            $rootScope.confId = $scope.confId;
            $rootScope.confSdate = $scope.confSdate;
            $rootScope.confEdate = $scope.confEdate;
            $rootScope.editMode = $scope.editMode;
            $rootScope.currency = $scope.currency;

            if($rootScope.editMode) {
                $scope.sections = regFormFactory.Sections.getAllSections({confId: $scope.confId}, {});
            } else {
                $scope.sections = regFormFactory.Sections.getVisibleSections({confId: $scope.confId}, {});
            }

            $scope.dialogs = {
                addsection: false,
                management: false
            };

            $scope.actions = {
                collapseAll: function() {
                    $scope.$broadcast('collapse', true);
                },
                expandAll: function() {
                    $scope.$broadcast('collapse', false);
                },
                openAddSection: function() {
                    $scope.dialogs.addsection = true;
                },
                openManagement: function() {
                    $scope.dialogs.management = true;
                }
            };

            $scope.getTpl = function(file) {
                return url.tpl(file);
            };

            $scope.api = {
                createSection: function(data) {
                    if(data.sectionCreationForm.$invalid === true){
                        return false;
                    }

                    regFormFactory.Sections.save({
                        confId: $scope.confId,
                        title: data.newsection.title,
                        description: data.newsection.description
                    }, function(newsection) {
                        $scope.sections.push(newsection);
                    });

                    return true;
                },
                moveSection: function(section, position){
                    regFormFactory.Sections.move({
                        confId: $scope.confId,
                        sectionId: section.id,
                        endPos: position
                    }, function(updatedSection) {
                        section = updatedSection;
                    });
                },
                restoreSection: function(section) {
                    regFormFactory.Sections.enable({
                        confId: $rootScope.confId,
                        sectionId: section.id
                    }, function(updatedSection) {
                        section.enabled = updatedSection.enabled;
                    });
                },
                removeSection: function(section) {
                    regFormFactory.Sections.remove({
                        confId: $rootScope.confId,
                        sectionId: section.id
                    }, function(updatedSections) {
                        $scope.sections = updatedSections;

                    });
                }
            };

            $scope.sectionSortableOptions = {
                update: function(e, ui) {
                    $scope.api.moveSection(ui.item.scope().section, ui.item.index());
                },
                // TODO Re-enable when solved: http://bugs.jqueryui.com/ticket/5772
                // containment: '.regform-section-list',
                disabled: !$rootScope.editMode,
                handle: ".regform-section .section-sortable-handle",
                placeholder: "regform-section-sortable-placeholder"
            };

            angular.extend($scope.sectionSortableOptions, sortableoptions);
        }
    };
});

ndRegForm.directive('ndAddSectionDialog', function(url) {
    return {
        require: 'ndDialog',
        templateUrl: url.tpl('sections/dialogs/sectioncreation.tpl.html'),

        link: function(scope) {
            scope.actions.init = function() {
                scope.newsection = {};
            };

            scope.actions.cleanup = function() {
                scope.newsection = undefined;
            };
        }
    };
});

ndRegForm.directive('ndManagementDialog', function(url) {
    return {
        require: 'ndDialog',
        templateUrl: url.tpl('sections/dialogs/sectionmanagement.tpl.html')
    };
});
