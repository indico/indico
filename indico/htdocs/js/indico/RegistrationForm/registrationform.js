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

ndRegForm.value('baseurl',
    Indico.Urls.Base + '/event/:confId/manage/registration/preview/'
);

ndRegForm.config(function(urlProvider) {
    urlProvider.setModulePath('/js/indico/RegistrationForm');
});

ndRegForm.factory('RESTAPI', ['$resource','baseurl', function($resource, baseurl) {

    var sectionurl = baseurl + 'sections/:sectionId';
    return {
        Sections: $resource(sectionurl, {8000: ":8000", confId: '@confId', sectionId: "@sectionId"},
                            {"enable": {method:'POST', url: sectionurl + "/enable"},
                             "disable": {method:'POST', url: sectionurl + "/disable"},
                             "remove": {method:'POST', url: sectionurl + "/remove"}
                            }),
    };
}]);



ndRegForm.directive('ndRegForm', function($rootScope, url, baseurl, RESTAPI) {
    return {
        replace: true,
        templateUrl:  url.tpl('registrationform.tpl.html'),

        scope: {
            confId: '@'
        },

        controller: function($scope, $resource) {
            $rootScope.confId = $scope.confId;

            var sections = RESTAPI.Sections.get({confId: $scope.confId}, function() {
                $scope.sections = sections["sections"];
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

            $scope.getTpl = function(file) {
                return url.tpl(file);
            };

            $scope.api = {
                createSection: function(data) {
                    var newSection = new RESTAPI.Sections(data.newsection);
                    newSection.$save({confId: $scope.confId}, function(data, headers) {
                        $scope.sections.push(data);
                    });
                }
            };
        }
    };
});

ndRegForm.directive('ndAddSectionDialog', function(url) {
    return {
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
        templateUrl: url.tpl('sections/dialogs/sectionmanagement.tpl.html')
    };
});

// TODO remove unused legacy jquery methods
// $(function(){
//     $(window).scroll(function(){
//         IndicoUI.Effect.followScroll();
//     });
// });
