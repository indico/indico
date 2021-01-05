// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

ndRegForm.controller('SectionCtrl', function($scope, $rootScope, regFormFactory) {
  $scope.sectionApi = {};
  $scope.actions = {};

  var getRequestParams = function(section) {
    return {
      confId: $rootScope.confId,
      sectionId: section.id,
      confFormId: $rootScope.confFormId,
    };
  };

  $scope.sectionApi.disableSection = function(section) {
    $scope.$parent.animations.recoverSectionButton = 'button-highlight';
    regFormFactory.Sections.disable(
      getRequestParams(section),
      function(updatedSection) {
        regFormFactory.processResponse(updatedSection, {
          success: function(updatedSection) {
            section.enabled = updatedSection.enabled;
          },
        });
      },
      handleAjaxError
    );
  };

  $scope.sectionApi.saveConfig = function(section, data) {
    var requestParams = angular.extend(getRequestParams(section), data);
    regFormFactory.Sections.save(
      requestParams,
      function(updatedSection) {
        regFormFactory.processResponse(updatedSection, {
          success: function(updatedSection) {
            $scope.section = angular.extend($scope.section, updatedSection);
          },
        });
      },
      handleAjaxError
    );
  };

  $scope.sectionApi.updateTitle = function(section, data) {
    var requestParams = angular.extend(getRequestParams(section), {changes: data});

    regFormFactory.Sections.modify(
      requestParams,
      function(updatedSection) {
        regFormFactory.processResponse(updatedSection, {
          success: function(updatedSection) {
            $scope.section.title = updatedSection.title;
          },
        });
      },
      handleAjaxError
    );
  };

  $scope.sectionApi.updateDescription = function(section, data) {
    var requestParams = angular.extend(getRequestParams(section), {changes: data});

    regFormFactory.Sections.modify(
      requestParams,
      function(updatedSection) {
        regFormFactory.processResponse(updatedSection, {
          success: function(updatedSection) {
            $scope.section.description = updatedSection.description;
          },
        });
      },
      handleAjaxError
    );
  };

  $scope.sectionApi.moveField = function(section, field, position) {
    var requestParams = angular.extend(getRequestParams(section), {
      fieldId: field.id,
      endPos: position,
    });

    regFormFactory[field.inputType == 'label' ? 'Labels' : 'Fields'].move(
      requestParams,
      function(updatedSection) {
        regFormFactory.processResponse(updatedSection, {
          success: function(updatedSection) {},
        });
        // TODO in case backend rejects request we should update scope with something like:
        // if (response.error) {
        //     $scope.section.items = response.updatedSection.items;
        // }
      },
      handleAjaxError
    );
  };

  $scope.sectionApi.removeField = function(section, field) {
    $scope.dialogs.removefield.field = field;

    $scope.dialogs.removefield.callback = function(success) {
      if (success) {
        var requestParams = angular.extend(getRequestParams(section), {
          fieldId: field.id,
        });

        $scope.$apply(
          regFormFactory[field.inputType == 'label' ? 'Labels' : 'Fields'].remove(
            requestParams,
            {},
            function(updatedSection) {
              regFormFactory.processResponse(updatedSection, {
                success: function(updatedSection) {
                  $scope.section.items = $scope.section.items.filter(function(obj) {
                    return obj.id !== field.id;
                  });
                },
              });
            },
            handleAjaxError
          )
        );
      }
    };

    $scope.dialogs.removefield.open = true;
  };

  $scope.actions.openAddField = function(section, fieldType) {
    $scope.dialogs.newfield = true;
    var lastEnabledIndex = _.findLastIndex(section.items, function(item) {
      return item.isEnabled;
    });
    section.items.splice(lastEnabledIndex + 1, 0, {id: -1, isEnabled: true, inputType: fieldType});
  };
});

ndRegForm.directive('ndSection', function($rootScope, url) {
  return {
    replace: true,
    restrict: 'E',
    templateUrl: url.tpl('section.tpl.html'),
    controller: 'SectionCtrl',

    link: function(scope, element) {
      scope.buttons = {
        newfield: false,
        config: false,
        disable: false,
      };

      scope.dialogs = {
        newfield: false,
        config: {
          open: false,
          actions: {},
          formData: [],
        },
        removefield: {
          open: false,
        },
      };

      scope.state = {
        collapsed: false,
      };

      scope.$on('collapse', function(event, collapsed) {
        scope.state.collapsed = collapsed;
      });

      scope.$watch('state.collapsed', function(val) {
        var content = angular.element(element.children()[2]);
        if (val) {
          content.slideUp();
        } else {
          content.slideDown();
        }
      });

      scope.$watch('section.title', function(newVal, oldVal) {
        if (newVal !== oldVal) {
          scope.sectionApi.updateTitle(scope.section, {title: newVal});
        }
      });

      scope.$watch('section.description', function(newVal, oldVal) {
        if (newVal !== oldVal) {
          scope.sectionApi.updateDescription(scope.section, {description: newVal});
        }
      });

      scope.dialogs.config.actions.onOk = function(dialogScope) {
        if (dialogScope.sectionForm.$invalid === true) {
          // TODO Uncomment when AngularJS >= 1.2
          //      Current version doesn't generate ngForm names dynamicly
          // var forms = _.filter($.map(dialogScope.sectionForm, function(value, index) {
          //     return index;
          // }), function(index) {
          //     return index[0] != '$';
          // });

          // var firstInvalid = _.find(dialogScope.sectionForm, function(form) {
          //     return form.$invalid;
          // });

          // var invalid = _.find(forms, function(f) {
          //     return dialogScope.sectionForm[f].$invalid;
          // });

          // dialogScope.$apply(dialogScope.setSelectedTab(firstInvalid));
          return false;
        }

        scope.sectionApi.saveConfig(dialogScope.section, dialogScope.formData);
        return true;
      };

      scope.dialogs.config.actions.onCancel = function(dialogScope) {};
    },
  };
});

ndRegForm.directive('ndGeneralSection', function($timeout, url, sortableoptions) {
  return {
    require: 'ndSection',
    controller: 'SectionCtrl',

    link: function(scope) {
      scope.buttons.newfield = true;
      scope.buttons.disable = !scope.section.isPersonalData;
      scope.tplGeneralField = url.tpl('sections/generalfield.tpl.html');

      scope.sectionApi.removeNewField = function() {
        $.each(scope.section.items, function(index, item) {
          if (item.id === -1) {
            $timeout(function() {
              scope.section.items.splice(index, 1);
            }, 0);

            return false;
          }
        });
      };

      scope.fieldSortableOptions = {
        update: function(e, ui) {
          scope.sectionApi.moveField(scope.section, ui.item.scope().field, ui.item.index());
        },
        // TODO Re-enable when solved: http://bugs.jqueryui.com/ticket/5772
        // containment: '.field-list',
        handle: '.regform-field .field-sortable-handle',
        placeholder: 'regform-field-sortable-placeholder',
      };

      angular.extend(scope.fieldSortableOptions, sortableoptions);
    },
  };
});

ndRegForm.directive('ndSectionDialog', function(url) {
  return {
    require: 'ndDialog',

    controller: function($scope) {
      $scope.templateUrl = url.tpl('sections/dialogs/base.tpl.html');
      $scope.actions.init = function() {
        $scope.section = $scope.data;

        $scope.formData = {};
        $scope.formData.items = [];

        _.each($scope.config.formData, function(item) {
          if (Array.isArray(item) && $scope.section[item[0]] !== undefined) {
            $scope.formData[item[1]] = angular.copy($scope.section[item[0]][item[1]]);
          } else {
            $scope.formData[item] = angular.copy($scope.section[item]);
          }
        });

        _.each($scope.section.items, function(item, ind) {
          $scope.formData.items[ind] = angular.copy(item);
        });

        $scope.tabSelected = $scope.config.tabs[0].id;
      };

      $scope.addItem = function(args) {
        $scope.formData.items.push(
          $.extend({id: 'isNew', cancelled: false, pricePerPlace: false}, args)
        );
      };
    },

    link: function(scope) {
      scope.getTabTpl = function(section_id, tab_type) {
        return url.tpl('sections/dialogs/{0}-{1}.tpl.html'.format(section_id, tab_type));
      };
    },
  };
});

ndRegForm.filter('possibleDeparture', function() {
  return function(departure, scope) {
    if (scope.accommodation.arrival !== undefined) {
      var arrival = moment(scope.accommodation.arrival, 'DD/MM/YYY');
      var possibleDepartures = {};
      _.each(scope.section.departureDates, function(value, key) {
        var departure = moment(key, 'DD/MM/YYY');
        if (arrival.isBefore(departure) || arrival.isSame(departure)) {
          possibleDepartures[key] = value;
        }
      });
      return possibleDepartures;
    } else {
      return scope.section.departureDates;
    }
  };
});
