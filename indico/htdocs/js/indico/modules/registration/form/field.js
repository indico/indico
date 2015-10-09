/* This file is part of Indico.
 * Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
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
    $scope.getDefaultFieldSetting = regFormFactory.getDefaultFieldSetting;

    var getRequestParams = function(field) {
        return {
            confId: $scope.confId,
            sectionId: $scope.section.id,
            fieldId: field.id,
            confFormId: $scope.confFormId
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

                    $scope.field.isEnabled = updatedField.isEnabled;
                    $scope.section.items.splice(index, 1);
                    $scope.section.items.push($scope.field);
                }
            });
        }, handleAjaxError);
    };

    $scope.fieldApi.enableField = function(field) {
        regFormFactory.Fields.enable(getRequestParams(field), function(updatedField) {
            regFormFactory.processResponse(updatedField, {
                success: function(updatedField) {
                    $scope.field.isEnabled = updatedField.isEnabled;
                    $scope.section.items.sort(function(a, b) {
                        return a.position - b.position;
                    });
                }
            });
        }, handleAjaxError);
    };

    $scope.fieldApi.removeField = function(field) {
        $scope.sectionApi.removeField($scope.section, field);
    };

    $scope.fieldApi.updateField = function(field, data) {
        var postData = angular.extend(getRequestParams(field), {fieldData: data});

        if ($scope.isNew()) {
            delete postData['fieldId'];
        }

        regFormFactory.Fields[$scope.isNew() ? 'save' : 'modify'](postData, function(response) {
            regFormFactory.processResponse(response, {
                success: function(response) {
                    if ($scope.isNew()) {
                        $scope.field = angular.extend($scope.field, response);
                    } else {
                        $scope.field = angular.extend($scope.field, postData.fieldData);
                    }
                }
            });
        }, handleAjaxError);
    };

    $scope.openFieldSettings = function() {
        $scope.dialog.open = true;
    };

    $scope.canBeDeleted = function(field) {
        return !field.fieldIsPersonalData;
    };

    $scope.canBeDisabled = function(field) {
        return !field.fieldIsRequired;
    };

    $scope.isNew = function() {
        return $scope.field.id == -1;
    };

    $scope.settings = {
        isBillable: false,
        date: false,
        defaultValue: false,
        singleColumn: false,
        itemtable: false,
        isRequired: true,
        number: false,
        placesLimit: false,
        rowsAndColumns: false,
        size: false,
        formData: [
            'title',
            'description',
            'isRequired'
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

            if ($scope.settings.itemtable) {
                var validCaptions = _.all(dialogScope.formData.radioitems, function(item) {
                    return item.remove || !!item.caption;
                });

                if (!validCaptions) {
                    dialogScope.$apply(dialogScope.setSelectedTab('tab-editItems'));
                    return false;
                }
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

    function checkEmail(email) {
        $scope.emailInfoMessage = '';
        email = email.trim();
        if (!email) {
            return;
        }
        $.ajax({
            url: $scope.checkEmailUrl,
            data: {email: email},
            error: handleAjaxError,
            success: function(data) {
                var msg;
                if (data.conflict == 'email') {
                    msg = $T.gettext('There is already a registration with this email address.');
                } else if (data.conflict == 'user') {
                    msg = $T.gettext('The user associated with this email address is already registered.');
                } else if (!data.user) {
                    msg = $T.gettext('The registration will not be associated with any indico account.');
                } else if (data.self) {
                    msg = $T.gettext('The registration will be associated with your Indico account.');
                } else {
                    var name = $('<span>', {text: data.user}).html();
                    msg = $T.gettext('The registration will be associated with the Indico account <strong>{0}</strong>.').format(name);
                }
                $('#regformSubmit').prop('disabled', !!data.conflict);
                $scope.emailInfoError = !!data.conflict;
                $scope.emailInfoMessage = msg;
                $scope.$apply();
            }
        });
    }

    $scope.fieldName = $scope.field.htmlName;
    $scope.emailInfoMessage = '';
    $scope.emailInfoError = false;
    if ($scope.field.htmlName == 'email') {
        $('#registrationForm').on('change input', 'input[name=email]', _.debounce(function() {
            checkEmail($(this).val());
        }, 250));
        checkEmail($scope.userdata.email);
    }
});

ndRegForm.controller('BillableCtrl', function($scope, $filter) {
    $scope.getBillableStr = function(item, uservalue) {
        var str = '';

        if ($scope.isBillable(item)) {
            str += ' {0} {1}'.format(item.price, $scope.currency);
        }

        if ($scope.hasPlacesLimit(item)) {
            if ($scope.hasPlacesLeft(item, uservalue)) {
                str += ' [{0} {1}]'.format($scope.getPlacesLeft(item, uservalue), $filter('i18n')('place(s) left'));
            } else {
                str += ' [{0}]'.format($filter('i18n')('no places left'));
            }
        }

        return str;
    };

    /*
     * Returns the places left for a field. Optionally corrected with the value
     * the user selected initially, and the current selection on the page.
     *
     * :param item: the item to be checked
     * :param uservalue: previously selected value that adds up to the currently stored total places left
     * :param selectedvalue: places selected currently selected substracting from the total places left
     */
    $scope.getPlacesLeft = function(item, uservalue, selectedvalue) {
        var places = item.noPlacesLeft;
        if (item._type == 'GeneralField' && item.inputType == 'checkbox') {
            if (uservalue) places += 1;
            if (selectedvalue) places -= 1;
        } else if (item._type == 'GeneralField' && item.inputType == 'yes/no') {
            if (uservalue) places += 1;
            if (selectedvalue == 'yes') places -= 1;
        } else if (item._type == 'RadioItem' || item._type == 'AccommodationType') {
            if (uservalue === item.id) places += 1;
            if (selectedvalue === item.id) places -= 1;
        } else if (item._type == 'SocialEventItem') {
            if (uservalue) places += uservalue;
            if (selectedvalue) places -= selectedvalue;
        }
        return places;
    };

    $scope.isBillable = function(item) {
        item = item || {};
        return item.isBillable;
    };

    $scope.isDisabled = function(item, uservalue) {
        item = item || {};
        return (item.disabled === true || item.isEnabled === false) ||
            !$scope.hasPlacesLeft(item, uservalue) || item.cancelled === true;
    };

    $scope.hasPlacesLeft = function(item, uservalue) {
        item = item || {};
        if (!$scope.hasPlacesLimit(item)) {
            return true;
        } else {
            return $scope.getPlacesLeft(item, uservalue) > 0;
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

    $scope.isVisible = function(field) {
        return field.isEnabled && !field.remove;
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
            scope.settings.isBillable = true;
            scope.settings.singleColumn = true;
            scope.settings.placesLimit = true;
            scope.settings.formData.push('isBillable');
            scope.settings.formData.push('price');
            scope.settings.formData.push('placesLimit');

            scope.$watch('userdata[fieldName]', function() {
                scope.checkboxValue = scope.userdata[scope.fieldName];
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
            scope.settings.formData.push('displayFormats');
            scope.settings.formData.push('dateFormat');
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
                delete scope.userdata[scope.field.htmlName];
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
            scope.settings.isBillable = true;
            scope.settings.isRequired = false;
            scope.settings.formData.push('isBillable');
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
            scope.settings.isBillable = true;
            scope.settings.number = true;
            scope.settings.formData.push('isBillable');
            scope.settings.formData.push('price');
            scope.settings.formData.push('minValue');
            scope.settings.formData.push('length');

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
                scope.radioValue.id = scope.getUserdataValue();
            });

            scope.getUserdataValue = function() {
                return scope.getId(scope.getValue(scope.fieldName));
            };

            scope.getInputTpl = function(itemType) {
                return url.tpl('fields/{0}.tpl.html'.format(itemType));
            };

            scope.anyBillableItemPayed = function(userdata) {
                if (userdata.paid) {
                    var item = _.find(scope.field.radioitems, function(item) {
                        return item.caption == userdata[scope.field.htmlName];
                    }) || {};

                    return item.isBillable && item.price !== 0;
                }

                return false;
            };

            scope.getId = function(fieldValue) {
                var id;

                if (fieldValue !== undefined) {
                    var item = _.find(scope.field.radioitems, function(item) {
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
                    return scope.field.defaultItem;
                } else {
                    return scope.userdata[fieldName];
                }
            };

            scope.getSelectedItem = function(itemId) {
                return _.find(scope.field.radioitems, function(item) {
                    return item.id == itemId;
                });
            };

            scope.settings.formData.push('defaultItem');
            scope.settings.formData.push('itemType');
            scope.settings.formData.push('withExtraSlots');

            scope.settings.editionTable = {
                sortable: false,
                actions: ['remove', 'sortable'],
                colNames:[
                    $T("Caption"),
                    $T("Billable"),
                    $T("Price"),
                    $T("Places limit"),
                    $T("Max. extra slots"),
                    $T("Extra slots pay"),
                    $T("Enabled")],

                colModel: [
                    {name: 'caption',
                     index:'caption',
                     align: 'center',
                     width: 160,
                     editable: true,
                     edittype: "text",
                     editoptions: {
                        size: "30",
                        maxlength: "50"}},

                    {name: 'isBillable',
                     index: 'isBillable',
                     width: 50,
                     editable: true,
                     align: 'center',
                     defaultVal: false,
                     edittype: 'bool_select'},

                    {name: 'price',
                     index: 'price',
                     align: 'center',
                     width: 50,
                     editable: true,
                     edittype: 'int',
                     pattern: '/^(\\d+(\\.\\d{1,2})?)?$/',
                     editoptions: {
                        size: "7",
                        maxlength: "20"}},

                    {name: 'placesLimit',
                     index: 'placesLimit',
                     align: 'center',
                     width: 50,
                     editable: true,
                     edittype: "text",
                     editoptions: {
                        size: "7",
                        maxlength: "20"}},

                    {name: 'maxExtraSlots',
                     index: 'maxExtraSlots',
                     align: 'center',
                     width: 50,
                     editable: true,
                     edittype: "text",
                     className: 'extra-slots',
                     editoptions: {
                        size: "7",
                        maxlength: "2"}},

                    {name: 'extraSlotsPay',
                     index: 'extraSlotsPay',
                     align: 'center',
                     width: 50,
                     editable: true,
                     edittype: "bool_select",
                     className: 'extra-slots',
                     defaultVal: false},

                    {name: 'isEnabled',
                     index: 'isEnabled',
                     width: 50,
                     editable: true,
                     align: 'center',
                     edittype: 'bool_select',
                     defaultVal: true}
                ]
            };
        }
    };
});

ndRegForm.directive('ndPhoneField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/phone.tpl.html');
        },

        link: function(scope) {
            scope.settings.fieldName = $T("Phone");
            scope.settings.formData.push('length');
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
            scope.settings.formData.push('length');
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
            scope.settings.formData.push('numberOfColumns');
            scope.settings.formData.push('numberOfRows');
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
            scope.settings.isBillable = true;
            scope.settings.placesLimit = true;
            scope.settings.formData.push('isBillable');
            scope.settings.formData.push('price');
            scope.settings.formData.push('placesLimit');
        }
    };
});

ndRegForm.directive('ndEmailField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/email.tpl.html');
        },
        link: function(scope) {
            scope.settings.fieldName = $T("Email address");
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
                $scope.formData.inputType = $scope.field.inputType;
                $scope.formData.isEnabled = $scope.field.isEnabled;
                $scope.formData.withExtraSlots = $scope.field.withExtraSlots;

                _.each($scope.settings.formData, function(item) {
                    if (Array.isArray(item) && $scope.field[item[0]] !== undefined) {
                        $scope.formData[item[1]] = angular.copy($scope.field[item[0]][item[1]]);
                    } else {
                        $scope.formData[item] = angular.copy($scope.field[item]);
                    }
                });

                if ($scope.field.inputType == 'radio') {
                    $scope.formData.radioitems = [];
                    _.each($scope.field.radioitems, function(item, ind) {
                        $scope.formData.radioitems[ind] = angular.copy(item);
                    });
                }

                $scope.toggleExtraSlotsColumns($scope.formData.withExtraSlots);
                $scope.tabSelected = "tab-options";
                $scope.parsePrice();
            };

            $scope.parsePrice = function() {
                if ($scope.formData.price !== undefined) {
                    $scope.formData.price = parseFloat($scope.formData.price);
                    if (isNaN($scope.formData.price)) {
                        $scope.formData.price = 0;
                    }
                }
            };

            $scope.addItem = function() {
                $scope.formData.radioitems.push({
                    placesLimit: 0,
                    price: 0,
                    isEnabled: true,
                    isBillable: false
                });

                $scope.toggleExtraSlotsColumns($scope.formData.withExtraSlots);
            };

            $scope.sortItems = function() {
                $scope.formData.radioitems = _.sortBy($scope.formData.radioitems, function(radioitem) {
                    return radioitem.caption.toLowerCase();
                });
            };

            $scope.toggleExtraSlotsColumns = function(value) {
                if (!!value) {
                    $('.regform-table .extra-slots').show();
                } else {
                    _.delay(function() {
                        $('.regform-table .extra-slots').hide();
                    }, 500);
                }
            };

            $scope.$watch('formData.withExtraSlots', function(newValue) {
                $scope.toggleExtraSlotsColumns(newValue);
            });
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
