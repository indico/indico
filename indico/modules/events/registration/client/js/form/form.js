// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

window.ndRegForm = angular.module('nd.regform', ['ui.sortable', 'ngResource', 'ngSanitize']);

// ============================================================================
// Initialization
// ============================================================================

ndRegForm.value(
  'editionURL',
  Indico.Urls.Base + '/event/:confId/manage/registration/:confFormId/form/'
);

ndRegForm.value(
  'displayurl',
  Indico.Urls.Base + '/event/:confId/registration/:confFormId/sections'
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
  opacity: 0.9,
  tolerance: 'pointer',
});

ndRegForm.value('fieldDefaults', {
  defaultTextFieldSize: 60,
  defaultNumberValue: 0,
  defaultRadioItemType: 'dropdown',
  defaultNumberOfColumns: 60,
  defaultNumberOfRows: 2,
  defaultPrice: 0,
  defaultMinValue: 0,
  defaultPlacesLimit: 0,
  defaultDateFormat: '%d/%m/%Y',
  defaultPhoneSize: 30,
});

ndRegForm.config(function(urlProvider) {
  urlProvider.setModulePath('/dist/mod_assets/_/_/_/modules/events/registration/client/js/form');
});

ndRegForm.factory('regFormFactory', function(
  $resource,
  $http,
  editionURL,
  displayurl,
  fieldDefaults
) {
  var defaults = $http.defaults.headers;
  defaults.common = defaults.common || {};
  defaults.get = defaults.get || {};
  defaults.get['Content-Type'] = defaults.common['Content-Type'] = 'application/json';
  defaults.common['X-CSRF-Token'] = $('#csrf-token').attr('content');
  defaults.common['X-Requested-With'] = 'XMLHttpRequest';

  var urls = Indico.Urls.RegistrationForm;

  return {
    processResponse: function(data, callback) {
      callback = callback || {};
      if (data.error) {
        showErrorDialog(data.error);
        if (callback.error) {
          callback.error(data);
        }
      } else if (callback.success) {
        callback.success(data);
      }
    },
    getDefaultFieldSetting: function(setting) {
      return fieldDefaults[setting];
    },
    Sections: $resource(
      urls.section.add,
      {confId: '@confId', sectionId: '@sectionId', confFormId: '@confFormId'},
      {
        remove: {method: 'DELETE', url: urls.section.modify, isArray: true},
        enable: {method: 'POST', url: urls.section.toggle, params: {enable: true}},
        disable: {method: 'POST', url: urls.section.toggle, params: {enable: false}},
        move: {method: 'POST', url: urls.section.move},
        modify: {method: 'PATCH', url: urls.section.modify},
      }
    ),
    Fields: $resource(
      urls.field.add,
      {confId: '@confId', sectionId: '@sectionId', fieldId: '@fieldId', confFormId: '@confFormId'},
      {
        remove: {method: 'DELETE', url: urls.field.modify},
        enable: {method: 'POST', url: urls.field.toggle, params: {enable: true}},
        disable: {method: 'POST', url: urls.field.toggle, params: {enable: false}},
        move: {method: 'POST', url: urls.field.move},
        modify: {method: 'PATCH', url: urls.field.modify},
      }
    ),
    Labels: $resource(
      urls.text.add,
      {confId: '@confId', sectionId: '@sectionId', fieldId: '@fieldId', confFormId: '@confFormId'},
      {
        remove: {method: 'DELETE', url: urls.text.modify},
        enable: {method: 'POST', url: urls.text.toggle, params: {enable: true}},
        disable: {method: 'POST', url: urls.text.toggle, params: {enable: false}},
        move: {method: 'POST', url: urls.text.move},
        modify: {method: 'PATCH', url: urls.text.modify},
      }
    ),
  };
});

// ============================================================================
// Directives
// ============================================================================

ndRegForm.directive('ndRegForm', function($rootScope, url, sortableoptions, regFormFactory) {
  return {
    replace: true,
    templateUrl: url.tpl('registrationform.tpl.html'),

    scope: {
      confId: '@',
      confFormId: '@',
      confCurrency: '@',
      confSections: '@',
      eventStartDate: '@',
      eventEndDate: '@',
      userInfo: '@',
      registrationData: '@',
      registrationMetaData: '@',
      registrationUuid: '@',
      csrfToken: '&',
      editMode: '=',
      updateMode: '=',
      management: '=',
      notifyDefault: '=',
      postUrl: '=',
      checkEmailUrl: '=',
      isModerated: '=',
    },

    controller: function($scope, $resource, $location, $anchorScroll) {
      $scope.sections = angular.fromJson($scope.confSections);
      $scope.userInfo = angular.fromJson($scope.userInfo);
      $scope.registrationData = angular.fromJson($scope.registrationData);
      $scope.registrationMetaData = angular.fromJson($scope.registrationMetaData);

      $rootScope.confId = $scope.confId;
      $rootScope.confFormId = $scope.confFormId;
      $rootScope.eventStartDate = $scope.eventStartDate;
      $rootScope.eventEndDate = $scope.eventEndDate;
      $rootScope.editMode = $scope.editMode;
      $rootScope.notifyDefault = $scope.notifyDefault;

      $scope.csrfToken = $('#csrf-token').attr('content');
      $scope.dialogs = {
        addsection: false,
        management: false,
        addsectionManagerOnly: false,
        error: false,
      };

      $scope.actions = {
        collapseAll: function() {
          $scope.$broadcast('collapse', true);
        },
        expandAll: function() {
          $scope.$broadcast('collapse', false);
        },
        openAddSection: function(managerOnly) {
          $scope.dialogs[managerOnly ? 'addsectionManagerOnly' : 'addsection'] = true;
        },
        openManagement: function() {
          $scope.dialogs.management = true;
        },
      };

      $scope.api = {
        createSection: function(data, managerOnly) {
          if (data.sectionCreationForm.$invalid === true) {
            return false;
          }

          regFormFactory.Sections.save(
            {
              confId: $scope.confId,
              title: data.newsection.title,
              description: data.newsection.description,
              is_manager_only: managerOnly,
              confFormId: $scope.confFormId,
            },
            function(newsection) {
              regFormFactory.processResponse(newsection, {
                success: function(newsection) {
                  $scope.sections.push(newsection);
                  $scope.animations.section = 'section-highlight';
                  $location.hash('section' + newsection.id);
                  $anchorScroll();
                },
              });
            },
            handleAjaxError
          );

          return true;
        },
        moveSection: function(section, position) {
          regFormFactory.Sections.move(
            {
              confId: $scope.confId,
              sectionId: section.id,
              endPos: position,
              confFormId: $scope.confFormId,
            },
            function(updatedSection) {
              regFormFactory.processResponse(updatedSection, {
                success: function(updatedSection) {
                  section = updatedSection;
                },
              });
            },
            handleAjaxError
          );
        },
        restoreSection: function(section) {
          regFormFactory.Sections.enable(
            {
              confId: $rootScope.confId,
              sectionId: section.id,
              confFormId: $rootScope.confFormId,
            },
            function(updatedSection) {
              regFormFactory.processResponse(updatedSection, {
                success: function(updatedSection) {
                  var index = -1;
                  _.find($scope.sections, function(section) {
                    index++;
                    return section.id == updatedSection.id;
                  });
                  section.enabled = updatedSection.enabled;
                  $scope.sections.splice(index, 1);
                  $scope.sections.push(section);
                },
              });
            },
            handleAjaxError
          );
        },
        removeSection: function(section) {
          regFormFactory.Sections.remove(
            {
              confId: $rootScope.confId,
              sectionId: section.id,
              confFormId: $rootScope.confFormId,
            },
            {},
            function(data) {
              regFormFactory.processResponse(data, {
                success: function() {
                  $scope.sections = $scope.sections.filter(function(obj) {
                    return obj.id !== section.id;
                  });
                },
              });
            },
            handleAjaxError
          );
        },
      };

      $scope.sectionSortableOptions = {
        update: function(e, ui) {
          $scope.api.moveSection(ui.item.scope().section, ui.item.index());
        },
        // TODO Re-enable when solved: http://bugs.jqueryui.com/ticket/5772
        // containment: '.regform-section-list',
        disabled: !$rootScope.editMode,
        handle: '.regform-section .section-sortable-handle',
        placeholder: 'regform-section-sortable-placeholder',
      };

      $scope.getTpl = function(file) {
        return url.tpl(file);
      };

      angular.extend($scope.sectionSortableOptions, sortableoptions);
    },

    link: function(scope, element) {
      scope.validationStarted = false;
      scope.currency = scope.confCurrency;
      scope.regMetadata = {};

      scope.animations = {
        recoverSectionButton: '',
        section: '',
      };

      // User data retrieval
      if (scope.editMode) {
        scope.userdata = {};
      } else if (!scope.updateMode) {
        scope.userdata = _.extend({}, scope.userInfo);
      } else {
        scope.userdata = _.extend({}, scope.registrationData);
        scope.regMetadata = _.extend({}, scope.registrationMetaData);
      }

      element.on('submit', function(e) {
        if (!scope.validate()) {
          e.preventDefault();
          scope.dialogs.error = true;
        } else {
          $('#regformSubmit').prop('disabled', true);
        }
      });

      element.ready(function() {
        $(document).trigger('indico:registration-form-loaded');
      });

      scope.validate = function() {
        scope.validationStarted = true;
        return scope.registrationForm.$valid;
      };
    },
  };
});

ndRegForm.directive('ndCurrency', function(url) {
  return {
    restrict: 'E',
    replace: true,
    templateUrl: url.tpl('currency.tpl.html'),
  };
});

ndRegForm.directive('ndAddSectionDialog', function(url) {
  return {
    require: 'ndDialog',
    controller: function($scope) {
      $scope.templateUrl = url.tpl('dialogs/sectioncreation.tpl.html');
    },

    link: function(scope) {
      scope.actions.init = function() {
        scope.newsection = {};
      };

      scope.actions.cleanup = function() {
        scope.newsection = undefined;
      };
    },
  };
});

ndRegForm.directive('ndSectionManagementDialog', function(url) {
  return {
    require: 'ndDialog',
    controller: function($scope) {
      $scope.templateUrl = url.tpl('dialogs/sectionmanagement.tpl.html');
    },
    link: function(scope) {
      scope.$watch('disabled.length', function(val) {
        if (val === 0) {
          scope.show = false;
        }
      });
    },
  };
});

ndRegForm.directive('ndErrorDialog', function(url) {
  return {
    require: 'ndDialog',
    controller: function($scope) {
      $scope.templateUrl = url.tpl('dialogs/errors.tpl.html');
    },
  };
});
