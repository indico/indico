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

ndRegForm.controller('FieldCtrl', function($scope, regFormFactory) {
    $scope.fieldApi = {};

    var getRequestParams = function(field) {
        return {
            confId: $scope.confId,
            sectionId: $scope.section.id,
            fieldId: field.id
        };
    };

    $scope.fieldApi.disableField = function(field) {
        regFormFactory.Fields.disable(getRequestParams(field), function(updatedField) {
            $scope.field.disabled = updatedField.disabled;
        });
    };

    $scope.fieldApi.enableField = function(field) {
        regFormFactory.Fields.enable(getRequestParams(field), function(updatedField) {
            $scope.field.disabled = updatedField.disabled;
        });
    };

    $scope.fieldApi.removeField = function(field) {
        $scope.sectionApi.removeField($scope.section, field);
    };

    $scope.fieldApi.updateField = function(field, data) {
        var postData = getRequestParams(field);
        postData = angular.extend(postData, {fieldData: data});

        if ($scope.isNew()) {
            delete postData['fieldId'];
        }

        regFormFactory.Fields.save(postData, function(response) {
            $scope.field = angular.extend($scope.field, response);
        });
    };

    $scope.getName = function(input) {
        if (input == 'date') {
            return '_genfield_' + $scope.section.id + '_' + $scope.field.id;
        } else {
            return '*genfield*' + $scope.section.id + '-' + $scope.field.id;
        }
    };

    $scope.openFieldSettings = function() {
        $scope.dialog.open = true;
    };

    $scope.canBeDeleted = function(field) {
        return field.lock? field.lock.indexOf('delete') == -1 : false;
    };

    $scope.canBeDisabled = function(field) {
        return field.lock? field.lock.indexOf('disable') == -1 : false;
    };

    $scope.isNew = function() {
        return $scope.field.id == -1;
    };

    $scope.settings = {
        billable: false,
        date: false,
        defaultValue: false,
        number: false,
        placesLimit: false,
        rowsAndColumns: false,
        size: false,
        formData: [
            'caption',
            'description',
            'mandatory'
        ]
    };

    $scope.dialog = {
        open: false,
        title: function() {
            return $scope.isNew()? $T('New Field') : $T('Edit Field');
        },
        okButton: function() {
            return $scope.isNew()? $T('Add') : $T('Update');
        },
        onOk: function(dialogScope) {
            if(dialogScope.optionsForm.$invalid === true) {
                return false;
            }

            $scope.fieldApi.updateField($scope.field, dialogScope.formData);
            return true;
        },
        onCancel: function() {
            if ($scope.isNew()) {
                $scope.sectionApi.removeNewField();
            }
        }
    };
});

ndRegForm.controller('BillableCtrl', function($scope) {
    $scope.isBillable = function(item) {
        return (item.billable === true || item.isBillable === true) && !$scope.isDisabled(item);
    };

    $scope.isDisabled = function(item) {
        return (item.disabled === true || item.isEnabled === false) ||
            !$scope.hasPlacesLeft(item) || item.cancelled === true;
    };

    $scope.isRequired = function(item) {
        return item.required && !scope.isDisabled(item);
    };

    $scope.hasPlacesLeft = function(item) {
        if (!$scope.hasPlacesLimit) {
            return true;
        } else {
            return item.noPlacesLeft >= 0;
        }
    };

    $scope.hasPlacesLimit = function(item) {
        return item.placesLimit !== 0;
    };
});

ndRegForm.directive('ndField', function($rootScope, url, regFormFactory) {
    return {
        restrict: 'E',
        replace: true,
        templateUrl: url.tpl('field.tpl.html'),
        controller: 'FieldCtrl',

        link: function(scope) {
            // This is a broadcast message from parent (section) scope
            // TODO look for broadcast messages to children the angular way
            scope.$parent.$watch('dialogs.newfield', function(val) {
                if (val && scope.isNew()) {
                    scope.dialog.open = true;
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
        },

        link: function(scope) {
            scope.settings.billable = true;
            scope.settings.placesLimit = true;
            scope.settings.formData.push('billable');
            scope.settings.formData.push('price');
            scope.settings.formData.push('placesLimit');
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
        },

        link: function(scope) {
            scope.settings.date = true;
            scope.settings.formData.push(['values', 'displayFormats']);
            scope.settings.formData.push(['values', 'dateFormat']);
            scope.dateInputs = [
                '{0}_Day'.format(scope.getName(scope.field.input)),
                '{0}_Month'.format(scope.getName(scope.field.input)),
                '{0}_Year'.format(scope.getName(scope.field.input)),
                '{0}_Hour'.format(scope.getName(scope.field.input)),
                '{0}_Min'.format(scope.getName(scope.field.input))
            ];

            scope.showTime = function(str) {
                return str? str.match('H') !== null : false;
            };
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
        },

        link: function(scope) {
            scope.settings.billable = true;
            scope.settings.formData.push('billable');
            scope.settings.formData.push('price');
        }
    };
});

ndRegForm.directive('ndNumberField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/number.tpl.html');
        },

        link: function(scope) {
            scope.settings.billable = true;
            scope.settings.number = true;
            scope.settings.formData.push('billable');
            scope.settings.formData.push('price');
            scope.settings.formData.push(['values', 'minValue']);
            scope.settings.formData.push(['values', 'length']);

            scope.getValue = function(fieldName) {
                if (scope.userdata[fieldName] !== undefined) {
                    return scope.userdata[fieldName];
                } else {
                    return scope.field.values.minValue;
                }
            };

            scope.updateSubtotal = function(value) {
                if ((isNaN(parseInt(value, 10)) || parseInt(value, 10) < 0)) {
                    scope.subtotal = 0;
                } else {
                    scope.subtotal = parseInt(value, 10) * parseInt(scope.field.price, 10);
                }
            };

            scope.updateSubtotal(scope.field.values.minValue);
        }

    };
});

ndRegForm.directive('ndRadioField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/radio.tpl.html');
        },

        link: function(scope) {
            scope.settings.defaultValue = true;

            scope.getValue = function(fieldName) {
                if (scope.userdata[fieldName] !== '') {
                    return scope.userdata[fieldName];
                } else {
                    return scope.field.values.defaultItem;
                }
            };

            scope.settings.formData.push(['values', 'defaultItem']);
            scope.settings.formData.push(['values', 'inputType']);

            // TODO remove unused colmodel
            scope.settings.editionTable = {
                sortable: false,
                actions: ['remove', 'sortable'],
                colNames:[
                    $T("caption"),
                    $T("billable"),
                    $T("price"),
                    $T("places limit"),
                    $T("enable")],

                colModel: [
                    {name:'caption',
                     index:'caption',
                     align: 'center',
                     width:160,
                     editable: true,
                     edittype: "text",
                     editoptions: {
                        size: "30",
                        maxlength: "50"}},

                    {name:'billable',
                     index:'isBillable',
                     width: 60,
                     editable: true,
                     align: 'center',
                     defaultVal: false,
                     edittype: 'bool_select'},

                    {name: 'price',
                     index: 'price',
                     align: 'center',
                     width: 50,
                     editable: true,
                     edittype: "text",
                     editoptions: {
                        size: "7",
                        maxlength: "20"}},

                    {name: 'placesLimit',
                     index: 'placesLimit',
                     align: 'center',
                     width: 80,
                     editable: true,
                     edittype: "text",
                     editoptions: {
                        size: "7",
                        maxlength: "20"}},

                    {name: 'isEnabled',
                     index: 'isEnabled',
                     width: 60,
                     editable: true,
                     align: 'center',
                     edittype: 'bool_select',
                     defaultVal: true}
                ]
            };
        }
    };
});

ndRegForm.directive('ndRadiogroupField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/radiogroup.tpl.html');
        },

        link: function(scope) {
            scope.settings.defaultValue = true;
            scope.settings.formData.push(['values', 'defaultItem']);
            scope.settings.formData.push(['values', 'inputType']);
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
            scope.settings.formData.push(['values', 'length']);
        }
    };
});

ndRegForm.directive('ndTextField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/text.tpl.html');
        },

        link: function(scope) {
            scope.settings.size = true;
            scope.settings.formData.push(['values', 'length']);

            scope.getType = function() {
                // TODO There is no other way to distinguish the email field from the
                //      information coming from the server
                if (scope.field.id == 10) {
                    return 'email';
                }
                return 'text';
            };
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
            scope.settings.formData.push(['values', 'numberOfColumns']);
            scope.settings.formData.push(['values', 'numberOfRows']);
        }
    };
});

ndRegForm.directive('ndYesnoField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/yesno.tpl.html');
        },

        link: function(scope) {
            scope.settings.billable = true;
            scope.settings.placesLimit = true;
            scope.settings.formData.push('billable');
            scope.settings.formData.push('price');
            scope.settings.formData.push('placesLimit');
        }
    };
});

ndRegForm.directive('ndFieldDialog', function(url) {
    return {
        require: 'ndDialog',
        replace: true,
        templateUrl: url.tpl('fields/dialogs/base.tpl.html'),

        controller: function($scope) {
            $scope.actions.init = function() {
                $scope.field = $scope.data;
                $scope.settings = $scope.config;

                $scope.formData = {};
                $scope.formData.radioitems = [];
                $scope.formData.input = $scope.field.input;
                $scope.formData.disabled = $scope.field.disabled;

                _.each($scope.settings.formData, function(item) {
                    if (Array.isArray(item) && $scope.field[item[0]] !== undefined) {
                        $scope.formData[item[1]] = angular.copy($scope.field[item[0]][item[1]]);
                    } else {
                        $scope.formData[item] = angular.copy($scope.field[item]);
                    }
                });

                _.each($scope.field.values.radioitems, function(item, ind) {
                    $scope.formData.radioitems[ind] = {
                        id: item.id,
                        cancelled: item.cancelled
                    };
                });

                $scope.tabSelected = "tab-options";
            };

            $scope.addItem = function () {
                 $scope.formData.radioitems.push({id:'isNew'});
            };

            $scope.sortItems = function () {
                $scope.formData.radioitems = _.sortBy($scope.formData.radioitems, function(radioitem) {
                    return radioitem.caption.toLowerCase();
                });
            };
        },

        link: function(scope) {
            scope.getTpl = function(file) {
                return url.tpl(file);
            };
        }
    };
});
