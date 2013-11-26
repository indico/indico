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

ndRegForm.value('baseurl',
    Indico.Urls.Base + '/event/:confId/manage/registration/preview/'
);

ndRegForm.config(function(urlProvider) {
    urlProvider.setModulePath('/js/indico/RegistrationForm');
});

ndRegForm.factory('RESTAPI', ['$resource','baseurl', function($resource, baseurl) {

    var sectionurl = baseurl + 'sections/:sectionId';
    var fieldurl = sectionurl + '/fields/:fieldId';
    return {
        Sections: $resource(sectionurl, {8000: ":8000", confId: '@confId', sectionId: "@sectionId"},
                            {"enable": {method:'POST', url: sectionurl + "/enable"},
                             "disable": {method:'POST', url: sectionurl + "/disable"},
                             "move": {method:'POST', url: sectionurl + "/move"},
                             "title": {method:'POST', url: sectionurl + "/title"},
                             "description": {method:'POST', url: sectionurl + "/description"}
                            }),
        Fields: $resource(fieldurl, {8000: ":8000", confId: '@confId', sectionId: "@sectionId", fieldId: "@fieldId"},
                            {"enable": {method:'POST', url: fieldurl + "/enable"},
                             "disable": {method:'POST', url: fieldurl + "/disable"},
                             "move": {method:'POST', url: fieldurl + "/move"}
                            })
    };
}]);



ndRegForm.directive('ndRegForm', function($rootScope, url, baseurl, RESTAPI) {
    return {
        replace: true,
        templateUrl:  url.tpl('registrationform.tpl.html'),

        scope: {
            confId: '@',
            editMode: '@'
        },

        controller: function($scope, $resource) {
            $rootScope.confId = $scope.confId;
            $rootScope.editMode = $scope.editMode;

            var sections = RESTAPI.Sections.get({confId: $scope.confId}, function() {
                $scope.sections = sections["sections"];
                $rootScope.currency = sections["currency"];
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
                    RESTAPI.Sections.save({confId: $scope.confId,
                                            title: data.newsection.title,
                                            description: data.newsection.description},
                        function(newsection, headers) {
                            $scope.sections.push(newsection);
                    });
                },
                moveSection: function(section, position){
                    RESTAPI.Sections.move({confId: $scope.confId,
                                           sectionId: section.id,
                                           endPos: position},
                        function(section_updated, headers) {
                            section = section_updated;
                    });

                }
            };

            $scope.sectionSortableOptions = {
                start: function(e, ui) {
                    ui.placeholder.height(ui.helper.outerHeight());
                },

                update: function(e, ui) {
                    $scope.api.moveSection(ui.item.scope().section, ui.item.index());
                },
                axis: 'y',
                cursor: 'move',
                delay: 150,
                opacity: 0.5,
                handle: ".sortable-handle",
                placeholder: "regFormSortablePlaceHolder",
                disabled: !$rootScope.editMode
                //items: "nd-section"
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


ndRegForm.directive("ndTable", function(url) {
    return {

        restrict: 'E',
        scope: {
            data: "=",
            config: "=",
            formData: "=",
            filter: "=",
            filterValue: "="
        },
        replace: true,
        templateUrl: url.tpl('table.tpl.html'),

        controller: function($scope) {

            $scope.actionIsArray = function(action) {
                return _.isArray(action);
            };

            $scope.actionItem = function(item, action) {
                if(action == "remove") {
                    item["remove"] = true;
                } else if (action == "cancel") {
                    item["cancelled"] = true;
                } else if (action == "uncancel") {
                    item["cancelled"] = false;
                }
            };

            $scope.matchFilter = function(item) {
                if(item.remove === true) {
                    return false;
                } else if(item.id == "isNew") {
                    return true;
                } else if($scope.filter !== undefined && $scope.filterValue !== undefined) {
                    return item[$scope.filter] == $scope.filterValue;
                } else {
                    return true;
                }
            };

            $scope.itemSortableOptions = {
                start: function(e, ui ){
                    ui.placeholder.height(ui.helper.outerHeight());
                },

                disabled: $scope.config.actions.indexOf('sortable') == -1,
                axis: 'y',
                cursor: 'move',
                delay: 150,
                opacity: 0.5,
                handle: ".regFormItemSortableHandle",
                placeholder: "regFormSortablePlaceHolder",
                items: "tr"
            };
        }
    };
});

// TODO remove unused legacy jquery methods
// $(function(){
//     $(window).scroll(function(){
//         IndicoUI.Effect.followScroll();
//     });
// });
