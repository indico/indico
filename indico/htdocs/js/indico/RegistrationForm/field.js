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
            regFormFactory.processResponse(updatedField, {
                success: function(updatedField) {
                    var index = -1;
                    _.find($scope.section.items, function(item) {
                        index++;
                        return item.id == $scope.field.id;
                    });

                    $scope.field.disabled = updatedField.disabled;
                    $scope.section.items.splice(index, 1);
                    $scope.section.items.push($scope.field);
                }
            });
        });
    };

    $scope.fieldApi.enableField = function(field) {
        regFormFactory.Fields.enable(getRequestParams(field), function(updatedField) {
            regFormFactory.processResponse(updatedField, {
                success: function(updatedField) {
                    var index = -1;
                    _.find($scope.section.items, function(item) {
                        index++;
                        return item.id == $scope.field.id;
                    });

                    $scope.field.disabled = updatedField.disabled;
                    $scope.section.items.splice(index, 1);
                    $scope.section.items.push($scope.field);
                }
            });
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
            regFormFactory.processResponse(response, {
                success: function(response) {
                    $scope.field = angular.extend($scope.field, response);
                }
            });
        });
    };

    $scope.getName = function(input) {
        if (input == 'date') {
            return '_genfield_' + $scope.section.id + '_' + $scope.field.id + '_';
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
        singleColumn: false,
        itemtable: false,
        mandatory: true,
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
            if (dialogScope.optionsForm.$invalid === true) {
                dialogScope.$apply(dialogScope.setSelectedTab('tab-options'));
                return false;
            }

            if ($scope.settings.itemtable && !dialogScope.hasRadioItems()) {
                dialogScope.$apply(dialogScope.setSelectedTab('tab-editItems'));
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

    $scope.fieldName = $scope.getName($scope.field.input);
});

ndRegForm.controller('BillableCtrl', function($scope, $filter) {
    $scope.getBillableStr = function(item, userValue, type) {
        var str = '';

        if ($scope.isBillable(item)) {
            str += ' {0} {1}'.format(item.price, $scope.currency);
        }

        if ($scope.hasPlacesLimit(item)) {
            if ($scope.hasPlacesLeft(item, userValue, type)) {
                str += ' [{0} {1}]'.format($scope.getNoPlacesLeft(item, userValue, type), $filter('i18n')('place(s) left'));
            } else {
                str += ' [{0}]'.format($filter('i18n')('no places left'));
            }
        }

        return str;
    };

    $scope.isBillable = function(item) {
        item = item || {};
        return item.billable || item.isBillable;
    };

    $scope.isDisabled = function(item, userValue, type) {
        item = item || {};
        return (item.disabled === true || item.isEnabled === false) ||
            !$scope.hasPlacesLeft(item, userValue, type) || item.cancelled === true;
    };

    $scope.hasPlacesLeft = function(item, userValue, type) {
        item = item || {};
        if (!$scope.hasPlacesLimit(item)) {
            return true;
        } else {
            return $scope.getNoPlacesLeft(item, userValue, type) > 0;
        }
    };

    $scope.hasPlacesLimit = function(item) {
        item = item || {};

        if (item.placesLimit !== undefined) {
            return item.placesLimit !== 0;
        }

        return false;
    };

    $scope.paymentBlocked = function(item, userdata, validation) {
        item = item || {};
        userdata = userdata || {};

        if (validation !== undefined) {
            return ($scope.isBillable(item) && userdata.paid) || validation(userdata);
        } else {
            return $scope.isBillable(item) && userdata.paid;
        }
    };

    $scope.getNoPlacesLeft = function(item, userValue, type) {
        var noPlaces = item.noPlacesLeft;
        if(type === 'checkbox' && userValue === 'yes'){
            noPlaces += 1;
        } else if (type === 'radio' && item.caption === userValue) {
            noPlaces += 1;
        } else if (type === 'accomodation' && item.id === userValue) {
            noPlaces += 1;
        } else if (type === 'socialEvent') {
            noPlaces += userValue;
        }
        return noPlaces;
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
            scope.checkboxValue = false;
            scope.settings.fieldName = $T("Multiple choices/checkbox");
            scope.settings.billable = true;
            scope.settings.singleColumn = true;
            scope.settings.placesLimit = true;
            scope.settings.formData.push('billable');
            scope.settings.formData.push('price');
            scope.settings.formData.push('placesLimit');

            scope.$watch('userdata[fieldName]', function() {
                scope.checkboxValue = scope.userdata[scope.fieldName] === 'yes';
            });
        }
    };
});

ndRegForm.directive('ndCountryField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/country.tpl.html');
        },

        link: function(scope) {
            scope.settings.fieldName = $T("Country");
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
            scope.settings.fieldName = $T("Date");
            scope.settings.date = true;
            scope.settings.formData.push(['values', 'displayFormats']);
            scope.settings.formData.push(['values', 'dateFormat']);
            scope.dateInputs = [
                '{0}Day'.format(scope.getName(scope.field.input)),
                '{0}Month'.format(scope.getName(scope.field.input)),
                '{0}Year'.format(scope.getName(scope.field.input)),
                '{0}Hour'.format(scope.getName(scope.field.input)),
                '{0}Min'.format(scope.getName(scope.field.input))
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
        },

        link: function(scope) {
            scope.settings.fieldName = $T("File");
            scope.removeAttachment = function() {
                delete scope.userdata[scope.getName(scope.field.input)];
            };
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
            scope.settings.fieldName = $T("Free Text");
            scope.settings.singleColumn = true;
            scope.settings.billable = true;
            scope.settings.mandatory = false;
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
            scope.settings.fieldName = $T("Number");
            scope.settings.billable = true;
            scope.settings.number = true;
            scope.settings.formData.push('billable');
            scope.settings.formData.push('price');
            scope.settings.formData.push(['values', 'minValue']);
            scope.settings.formData.push(['values', 'length']);

            scope.updateSubtotal = function() {
                var value = scope.userdata[scope.fieldName];
                if ((isNaN(parseInt(value, 10)) || parseInt(value, 10) < 0)) {
                    scope.subtotal = 0;
                } else {
                    scope.subtotal = parseInt(value, 10) * parseInt(scope.field.price, 10);
                }
            };

            scope.$watch('userdata[fieldName]', function() {
                scope.updateSubtotal();
            });
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
            scope.settings.fieldName = $T("Multiple options/One choice");
            scope.settings.defaultValue = true;
            scope.settings.itemtable = true;

            // keep track of the selected radio item
            scope.radioValue = {};

            scope.$watch('userdata[fieldName]', function(){
                scope.radioValue['id'] = scope.getId(scope.getValue(scope.fieldName));
            });

            scope.getInputTpl = function(inputType) {
                return url.tpl('fields/{0}.tpl.html'.format(inputType));
            };

            scope.anyBillableItemPayed = function(userdata) {
                if (userdata.paid) {
                    var item = _.find(scope.field.values.radioitems, function(item) {
                        return item.caption == userdata[scope.getName(scope.field.input)];
                    }) || {};

                    return item.isBillable && item.price !== '' && item.price !== 0;
                }

                return false;
            };

            scope.getId = function(fieldValue) {
                var id;

                if (fieldValue !== undefined) {
                    var item = _.find(scope.field.values.radioitems, function(item) {
                        return item.caption == fieldValue;
                    });

                    if (item !== undefined) {
                        id = item.id;
                    }
                }

                return id;
            };

            scope.getValue = function(fieldName) {
                if (!scope.userdata[fieldName] || scope.userdata[fieldName] === '') {
                    return scope.field.values.defaultItem;
                } else {
                    return scope.userdata[fieldName];
                }
            };

            scope.getSelectedItem = function(itemId) {
                return _.find(scope.field.values.radioitems, function(item) {
                    return item.id == itemId;
                });
            };

            scope.settings.formData.push(['values', 'defaultItem']);
            scope.settings.formData.push(['values', 'inputType']);

            scope.settings.editionTable = {
                sortable: false,
                actions: ['remove', 'sortable'],
                colNames:[
                    $T("Caption"),
                    $T("Billable"),
                    $T("Price"),
                    $T("Places limit"),
                    $T("Enabled")],

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

ndRegForm.directive('ndTelephoneField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/telephone.tpl.html');
        },

        link: function(scope) {
            scope.settings.fieldName = $T("Telephone");
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
            scope.settings.fieldName = $T("Text");
            scope.settings.size = true;
            scope.settings.formData.push(['values', 'length']);
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
            scope.settings.fieldName = $T("Textarea");
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
            scope.settings.fieldName = $T("Yes/No");
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
        controller: function($scope) {
            $scope.templateUrl = url.tpl('fields/dialogs/base.tpl.html');

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
                    $scope.formData.radioitems[ind] =  angular.copy(item);
                });

                $scope.tabSelected = "tab-options";
                $scope.parsePrice();
            };

            $scope.parsePrice = function() {
                if ($scope.formData.price !== undefined) {
                    $scope.formData.price = parseFloat($scope.formData.price);
                    if (isNaN($scope.formData.price)) {
                        $scope.formData.price = "";
                    }
                }
            };

            $scope.addItem = function() {
                $scope.formData.radioitems.push({
                    id:'isNew',
                    placesLimit: 0,
                    price: 0,
                    isEnabled: true,
                    isBillable: false
                });
            };

            $scope.sortItems = function() {
                $scope.formData.radioitems = _.sortBy($scope.formData.radioitems, function(radioitem) {
                    return radioitem.caption.toLowerCase();
                });
            };
        },

        link: function(scope) {
            scope.getTpl = function(file) {
                return url.tpl(file);
            };

            scope.hasRadioItems = function () {
                return _.any(scope.formData.radioitems, function(item) {
                    return item.remove !== true;
                });
            };
        }
    };
});
