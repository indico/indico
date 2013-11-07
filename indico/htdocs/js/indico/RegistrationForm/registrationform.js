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
    'ngResource'
]);

ndRegForm.value('ajaxquery',
    Indico.Urls.Base + '/event/:confId/manage/registration/preview/sections/:sectionId'
);

ndRegForm.config(function(urlProvider) {
    urlProvider.setModulePath('/js/indico/RegistrationForm');
});

ndRegForm.directive('ndRegForm', function(url, ajaxquery) {
    return {
        replace: true,
        templateUrl:  url.tpl('registrationform.tpl.html'),

        scope: {
            confId: '@'
        },

        controller: function($scope, $resource) {
            var Section = $resource(ajaxquery, {
                8000: ":8000",
                confId: $scope.confId,
                sectionId: "@sectionId"
            });

            var sections = Section.get(function() {
                $scope.sections = sections["items"];
            });

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

            $scope.api = {
                createSection: function(data) {
                    $scope.sections.push({
                        // TODO initialize properly
                        // id: '-1',
                        items: [],
                        title: data.newfield.title,
                        description: data.newfield.description
                    });
                },
                removeSection: function(sectionId) {
                    // TODO
                    console.log('removing setion');
                }
            };
        }
    };
});

ndRegForm.directive('ndAddSectionDialog', function(url) {
    return {
        templateUrl: url.tpl('dialogs/sectioncreation.tpl.html'),
        link: function(scope) {
            scope.actions.cleanup = function() {
                scope.newfield = undefined;
            };
        }
    };
});

ndRegForm.directive('ndManagementDialog', function(url) {
    return {
        templateUrl: url.tpl('dialogs/sectionmanagement.tpl.html')
    };
});

// TODO remove unused legacy jquery methods
// $(function(){
//     $(window).scroll(function(){
//         IndicoUI.Effect.followScroll();
//     });
// });
