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

ndRegForm.directive('ndRegForm', function() {
    var baseUrl = Indico.Urls.Base + '/js/indico/RegistrationForm/';
    var ajaxUrl = Indico.Urls.Base + '/event/:confId/manage/registration/';

    return {
        restrict: "A",
        replace: true,
        templateUrl:  baseUrl + 'registrationform.tpl.html',

        scope: {
            confId: '@'
        },

        controller: function($scope, $resource) {
            $scope.baseUrl = Indico.Urls.Base + '/js/indico/RegistrationForm/';

            var Section = $resource(ajaxUrl + "preview/sections/:sectionId", {
                8000: ":8000",
                confId: $scope.confId,
                sectionId: "@sectionId"
            });

            var sections = Section.get(function() {
                $scope.sections = sections["items"];
            });
        }
    };
});

ndRegForm.controller("FieldCtrl", function($scope) {
    $scope.getName = function() {
        if ($scope.field.input == 'date') {
            return '_genfield_' + $scope.section.id + '_' + $scope.field.id;
        } else {
            return '*genfield*' + $scope.section.id + '-' + $scope.field.id;
        }
    };
});

ndRegForm.controller("RadioCtrl", function($scope) {
    $scope.isDisabled = function() {
        return ($scope.item.placesLimit !== 0 && $scope.item.noPlacesLeft === 0);
    };

    $scope.isBillable = function(item) {
        return $scope.item.isBillable && !$scope.isDisabled();
    };

    $scope.hasPlacesLeft = function(item) {
        return (!$scope.isDisabled() && $scope.item.placesLimit !== 0);
    };
});


    // $(function(){
    //     var confId = ${confId};
    //     var rfView = new RegFormEditionView({el: $("div#registrationForm")});
    //     var model = rfView.getModel();
    //     var sectionsMgmt = new RegFormSectionsMgmtView({el: $('#section-mgmt-popup'), model: model});
    //     var sectionCreate = new RegFormSectionsCreateView({el: $('#section-create-popup'), model: model});

    //     $(window).scroll(function(){
    //         IndicoUI.Effect.followScroll();
    //     });
    //     // Menu function
    //     $("#collapse_all").click(function(){
    //         $("div.regFormSectionContent:visible").slideUp("slow");
    //         $(".regFormButtonCollpase").button( "option", "icons", {primary: 'ui-icon-triangle-1-w'});
    //     });
    //     $("#expand_all").click(function(){
    //         $("div.regFormSectionContent:hidden").slideDown("slow");
    //         $(".regFormButtonCollpase").button("option", "icons", {primary: 'ui-icon-triangle-1-s'});
    //     });
    //     $("#sections_mgmt").click(function(){
    //         sectionsMgmt.show();
    //     });
    //     $("#section_create").click(function(){
    //         sectionCreate.show();
    //     });
    // });
