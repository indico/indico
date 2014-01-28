/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
    Indico.Urls.Base + '/event/:confId/manage/registration/modify/'
);

ndRegForm.value('displayurl',
    Indico.Urls.Base + '/event/:confId/registration/sections'
);

ndRegForm.value('userurl',
    Indico.Urls.Base + '/event/:confId/registration/userdata'
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

// Hack for disabling cache in Internet Explorer
ndRegForm.config(['$httpProvider', function($httpProvider) {
    if (!$httpProvider.defaults.headers.get) {
        $httpProvider.defaults.headers.get = {};
    }
    //disable IE ajax request caching
    $httpProvider.defaults.headers.get['If-Modified-Since'] = '0';
}]);

ndRegForm.factory('regFormFactory', function($resource, $http, editionurl, displayurl, userurl) {
    var defaults = $http.defaults.headers;
    defaults.common = defaults.common || {};
    defaults.get = defaults.get || {};
    defaults.get['Content-Type'] = defaults.common['Content-Type'] = 'application/json';

    var sectionurl = editionurl + 'sections/:sectionId';
    var sessionsurl = Indico.Urls.Base + '/event/:confId/manage/sessions';
    var fieldurl = sectionurl + '/fields/:fieldId';

    return {
        processResponse: function(data, callback) {
            callback = callback || {};
            if(data.error) {
                IndicoUtil.errorReport(data.error);
                if (callback.error) {
                    callback.error(data);
                }
            } else if (callback.success) {
                callback.success(data);
            }
        },
        Sections: $resource(sectionurl, {confId: '@confId', sectionId: "@sectionId"}, {
            "remove": {url: sectionurl, method: 'DELETE', isArray: true},
            "getAllSections": {method: 'GET', isArray: true},
            "getVisibleSections": {url: displayurl, method: 'GET', isArray: true},
            "enable": {method: 'POST', url: sectionurl + "/enable"},
            "disable": {method: 'POST', url: sectionurl + "/disable"},
            "move": {method: 'POST', url: sectionurl + "/move"},
            "title": {method: 'POST', url: sectionurl + "/title"},
            "description": {method: 'POST', url: sectionurl + "/description"}
        }),
        Fields: $resource(fieldurl, {confId: '@confId', sectionId: "@sectionId", fieldId: "@fieldId"}, {
            "enable": {method:'POST', url: fieldurl + "/enable"},
            "disable": {method:'POST', url: fieldurl + "/disable"},
            "move": {method:'POST', url: fieldurl + "/move"}
        }),
        Sessions: $resource(sessionsurl, {confId: '@confId'}, {}),
        UserData: $resource(userurl, {confId: '@confId'}, {})
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
            confCurrency: '@',
            confSections: '@',
            confSdate: '@',
            confEdate: '@',
            editMode: '=',
            updateMode: '=',
            postUrl: '='
        },

        controller: function($scope, $resource) {
            $scope.sections = $scope.$eval($scope.confSections);

            $rootScope.confId = $scope.confId;
            $rootScope.confSdate = $scope.confSdate;
            $rootScope.confEdate = $scope.confEdate;
            $rootScope.editMode = $scope.editMode;

            $scope.dialogs = {
                addsection: false,
                management: false,
                error: false
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
                    if (data.sectionCreationForm.$invalid === true){
                        return false;
                    }

                    regFormFactory.Sections.save({
                        confId: $scope.confId,
                        title: data.newsection.title,
                        description: data.newsection.description
                    }, function(newsection) {
                        regFormFactory.processResponse(newsection, {
                            success: function(newsection)  {
                                $scope.sections.push(newsection);
                            }
                        });
                    });

                    return true;
                },
                moveSection: function(section, position){
                    regFormFactory.Sections.move({
                        confId: $scope.confId,
                        sectionId: section.id,
                        endPos: position
                    }, function(updatedSection) {
                        regFormFactory.processResponse(updatedSection, {
                            success: function(updatedSection)  {
                                section = updatedSection;
                            }
                        });
                    });
                },
                restoreSection: function(section) {
                    regFormFactory.Sections.enable({
                        confId: $rootScope.confId,
                        sectionId: section.id
                    }, function(updatedSection) {
                        regFormFactory.processResponse(updatedSection, {
                            success: function(updatedSection)  {
                                var index = -1;
                                _.find($scope.sections, function(section) {
                                    index++;
                                    return section.id == updatedSection.id;
                                });
                                section.enabled = updatedSection.enabled;
                                $scope.sections.splice(index, 1);
                                $scope.sections.push(section);
                            }
                        });
                    });
                },
                removeSection: function(section) {
                    regFormFactory.Sections.remove({
                        confId: $rootScope.confId,
                        sectionId: section.id
                    }, {}, function(updatedSections) {
                        regFormFactory.processResponse(updatedSections, {
                            success: function(updatedSections)  {
                                $scope.sections = updatedSections;
                            }
                        });
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
        },

        link: function(scope, element) {
            scope.validationStarted = false;
            scope.currency = scope.confCurrency;

            // User data retrieval
            if (scope.editMode) {
                scope.userdata = {};
            } else if (!scope.updateMode) {
                scope.userdata = regFormFactory.UserData.get({confId: scope.confId}, function() {
                    scope.userdata = scope.userdata.avatar || {};
                });
            } else {
                scope.userdata = regFormFactory.UserData.get({confId: scope.confId}, function() {
                    _.each(scope.userdata.miscellaneousGroupList, function(e) {
                        _.each(e.responseItems, function(e) {
                            scope.userdata[e.HTMLName] = e.value;
                        });
                    });
                });
            }

            element.on('submit', function(e) {
                if (!scope.validate()) {
                    e.preventDefault();
                    scope.dialogs.error = true;
                }
            });

            scope.validate = function() {
                scope.validationStarted = true;
                return scope.registrationForm.$valid;
            };
        }
    };
});

ndRegForm.directive('ndAddSectionDialog', function(url) {
    return {
        require: 'ndDialog',
        templateUrl: url.tpl('dialogs/sectioncreation.tpl.html'),

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
        templateUrl: url.tpl('dialogs/sectionmanagement.tpl.html')
    };
});

ndRegForm.directive('ndErrorDialog', function(url) {
    return {
        require: 'ndDialog',
        templateUrl: url.tpl('dialogs/errors.tpl.html')
    };
});

ndRegForm.directive('ndCurrency', function(url) {
    return {
        restrict: 'E',
        replace: true,
        templateUrl:  url.tpl('currency.tpl.html')
    };
});
