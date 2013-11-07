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

ndRegForm.controller('FieldCtrl', function($scope) {
    // TODO: do something similar to SectionCtrl
    // The purpose is having a field api to which several directives may need to work with
    // Explore the best way to implement it ;)
});

ndRegForm.directive('ndField', function(url) {
    return {
        restrict: 'E',
        replace: true,
        templateUrl: url.tpl('field.tpl.html'),

        controller: function($scope) {
            // TODO If we go for having a FieldCtrl, all this fiddling with the scope must be
            // moved to the link function
            $scope.dialogs = {
                settings: {
                    title: function() {
                        return $scope.fieldApi.isNew()? $T('New Field') : $T('Edit Field');
                    },
                    open: false,
                    okButton: function() {
                        return $scope.fieldApi.isNew()? $T('Add') : $T('Update');
                    },
                    onOk: function(dialogScope) {
                        $scope.field = dialogScope.field;
                        // TODO commit field to server
                    },
                    onCancel: function() {
                        if ($scope.fieldApi.isNew()) {
                            $scope.sectionApi.removeNewField();
                        }
                    }
                }
            };

            $scope.fieldApi = {
                isNew: function() {
                    return $scope.field.id == -1;
                }
            };

            // TODO set keys to true in ndWhateverField link function for activating
            // that particular setting in its edition dialog
            $scope.settings = {
                billable: false,
                date: false,
                defaultValue: false,
                number: false,
                placesLimit: false,
                rowsAndColumns: false,
                size: false
            };

            $scope.getName = function(input) {
                if (input == 'date') {
                    return '_genfield_' + $scope.section.id + '_' + $scope.field.id;
                } else {
                    return '*genfield*' + $scope.section.id + '-' + $scope.field.id;
                }
            };

            $scope.hasPlacesLeft = function(field) {
                return (field.placesLimit !== 0 && field.noPlacesLeft >= 0);
            };

            $scope.openFieldSettings = function() {
                $scope.dialogs.settings.open = true;
            };
        },

        link: function(scope) {
            // This is a broadcast message from parent (section) scope
            // TODO look for broadcast messages to children the angular way
            scope.$parent.$watch('dialogs.newfield', function(val) {
                if (val && scope.fieldApi.isNew()) {
                    scope.dialogs.settings.open = true;
                    scope.$parent.dialogs.newfield = false;
                }
            });
        }
    };
});

ndRegForm.directive('ndCheckboxField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/checkbox.tpl.html');
        }
    };
});

ndRegForm.directive('ndCountryField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/country.tpl.html');
        }
    };
});

ndRegForm.directive('ndDateField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/date.tpl.html');
            $scope.calendarimg = imageSrc("CalendarWidget");
        }
    };
});

ndRegForm.directive('ndFileField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/file.tpl.html');
        }
    };
});

ndRegForm.directive('ndLabelField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/label.tpl.html');
        }
    };
});

ndRegForm.directive('ndNumberField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/number.tpl.html');

            $scope.change = function() {
                // TODO do this the angular way
                // TODO var value = get value from input (avoid jQuery)
                $E('subtotal-{{ name }}').dom.innerHTML =
                    ((isNaN(parseInt(value, 10)) || parseInt(value, 10) < 0) ?
                    0:
                    parseInt(value, 10)) * scope.field.price;
            };
        }
    };
});

ndRegForm.directive('ndRadioField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/radio.tpl.html');

            // TODO there are other fields using this
            // Consider moving it to fieldApi, or even better, FielCtrl
            $scope.isDisabled = function() {
                return ($scope.item.placesLimit !== 0 && $scope.item.noPlacesLeft === 0);
            };

            $scope.isBillable = function(item) {
                return $scope.item.isBillable && !$scope.isDisabled();
            };

            $scope.hasPlacesLeft = function(item) {
                return (!$scope.isDisabled() && $scope.item.placesLimit !== 0);
            };
        },

        link: function(scope) {
            scope.settings.defaultValue = true;
        }
    };
});

ndRegForm.directive('ndRadiogroupField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/radiogroup.tpl.html');
        }
    };
});

ndRegForm.directive('ndTelephoneField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/telephone.tpl.html');
        },
        link: function(scope) {
            scope.settings.size = true;
        }
    };
});

ndRegForm.directive('ndTextField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/text.tpl.html');
        }
    };
});

ndRegForm.directive('ndTextareaField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/textarea.tpl.html');
        },
        link: function(scope) {
            scope.settings.rowsAndColumns = true;
        }
    };
});

ndRegForm.directive('ndYesnoField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/yesno.tpl.html');
        }
    };
});

ndRegForm.directive('ndFieldDialog', function(url) {
    return {
        require: 'ndDialog',
        replace: true,
        templateUrl: url.tpl('fields/dialogs/base.tpl.html'),
        link: function(scope, element, attrs) {
            scope.actions.init = function() {
                scope.field = scope.$eval(scope.asyncData);
            };
        }
    };
});
