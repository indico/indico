/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

/* global angular, ndRegForm */

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
        regFormFactory[field.inputType === 'label' ? 'Labels' : 'Fields'].disable(getRequestParams(field), function(updatedField) {
            regFormFactory.processResponse(updatedField, {
                success: function(updatedField) {
                    var index = -1;
                    _.find($scope.section.items, function(item) {
                        index++;
                        return item.id === $scope.field.id;
                    });

                    $scope.field.isEnabled = updatedField.view_data.isEnabled;
                    $scope.section.items.splice(index, 1);
                    $scope.section.items.push($scope.field);
                }
            });
        }, handleAjaxError);
    };

    $scope.fieldApi.enableField = function(field) {
        regFormFactory[field.inputType === 'label' ? 'Labels' : 'Fields'].enable(getRequestParams(field), function(updatedField) {
            regFormFactory.processResponse(updatedField, {
                success: function(updatedField) {
                    var lastEnabledIndex = _.findLastIndex($scope.section.items, function(item) {
                        return item.isEnabled;
                    });
                    var updatedFieldIndex = $scope.section.items.indexOf($scope.field);
                    $scope.section.items.splice(updatedFieldIndex, 1);
                    $scope.field.isEnabled = updatedField.view_data.isEnabled;
                    $scope.section.items.splice(lastEnabledIndex + 1, 0, $scope.field);
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

        regFormFactory[field.inputType === 'label' ? 'Labels' : 'Fields'][$scope.isNew() ? 'save' : 'modify'](postData, function(response) {
            regFormFactory.processResponse(response, {
                success: function(response) {
                    $scope.field = angular.extend($scope.field, response.view_data);
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
        return $scope.field.id === -1;
    };

    $scope.getNumberOfSlots = function(item) {
        if (!item || !item.maxExtraSlots) {
            return 0;
        }

        return item.maxExtraSlots + 1;
    };

    $scope.showExtraSlotsInput = function(item, userdata, itemChecked, placesLeft) {
        var field = $scope.field,
            showExtraSlots = field.withExtraSlots && item.maxExtraSlots && itemChecked;

        if (!placesLeft && itemChecked && userdata && userdata[item.id] === 1) {
            return false;
        }

        return showExtraSlots;
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
        withExtraSlots: false,
        formData: [
            'title',
            'description',
            'isRequired'
        ]
    };

    $scope.dialog = {
        open: false,
        title: function() {
            return $scope.isNew() ? $T('New Field') : $T('Edit Field');
        },
        okButton: function() {
            return $scope.isNew() ? $T('Add') : $T('Update');
        },
        onOk: function(dialogScope) {
            if (dialogScope.optionsForm.$invalid === true) {
                dialogScope.$apply(dialogScope.setSelectedTab('tab-options'));
                return false;
            }

            if ($.isFunction($scope.validateFieldSettings) && !$scope.validateFieldSettings(dialogScope)) {
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

    var _checkEmailRemote = _.debounce(function _checkEmailRemote(email) {
        $.ajax({
            url: $scope.checkEmailUrl,
            data: {email: email, update: $scope.updateMode ? $scope.registrationUuid : null},
            error: handleAjaxError,
            success: function(data) {
                var msg;
                var name = data.user ? $('<span>', {text: data.user}).html() : null;
                if (data.conflict == 'email-already-registered') {
                    msg = $T.gettext('There is already a registration with this email address.');
                } else if (data.conflict == 'user-already-registered') {
                    msg = $T.gettext('The user associated with this email address is already registered.');
                } else if (data.conflict == 'no-user') {
                    msg = $T.gettext('There is no Indico user associated with this email address.');
                } else if (data.status == 'error' && (data.conflict == 'email-other-user' || data.conflict == 'email-no-user')) {
                    msg = $T.gettext("This email address is not associated with your Indico account.");
                } else if (data.conflict == 'email-other-user') {
                    msg = $T.gettext("The registration will be re-associated to a different user (<strong>{0}</strong>).").format(name);
                } else if (data.conflict == 'email-no-user') {
                    msg = $T.gettext("The registration will be disassociated from the current user (<strong>{0}</strong>).").format(name);
                } else if (!data.user) {
                    msg = $T.gettext('The registration will not be associated with any Indico account.');
                } else if (data.self) {
                    msg = $T.gettext('The registration will be associated with your Indico account.');
                } else if (data.same) {
                    msg = $T.gettext('The registration will remain associated with the Indico account <strong>{0}</strong>.').format(name);
                } else {
                    msg = $T.gettext('The registration will be associated with the Indico account <strong>{0}</strong>.').format(name);
                }
                $('#regformSubmit').prop('disabled', data.status == 'error');
                $scope.emailInfoError = data.status == 'error';
                $scope.emailInfoWarning = data.status == 'warning';
                $scope.emailInfoMessage = msg;
                $scope.$apply();
            }
        });
    }, 250);

    function checkEmail(email) {
        email = email.trim();
        if (email === $scope.checkedEmail) {
            return;
        }
        $scope.emailInfoError = false;
        $scope.emailInfoWarning = false;
        $scope.emailInfoMessage = email ? $T.gettext('Checking email address...') : '';
        $scope.checkedEmail = email;
        if (email) {
            _checkEmailRemote(email);
        }
    }

    $scope.fieldName = $scope.field.htmlName;
    $scope.emailInfoMessage = '';
    $scope.emailInfoError = false;
    $scope.emailInfoWarning = false;
    if ($scope.field.htmlName == 'email' && !$scope.editMode) {
        $('#registrationForm').on('change input', 'input[name=email]', _.debounce(function() {
            checkEmail($(this).val());
            $scope.$apply();
        }, 250));
        checkEmail($scope.userdata.email || '');
    }
});

ndRegForm.controller('BillableCtrl', function($scope, $filter) {
    $scope.getBillableStr = function(item, uservalue) {
        var str = '';

        if ($scope.changesPrice(item)) {
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
        var places = item.placesLimit;
        if ($scope.field.inputType == 'checkbox' || $scope.field.inputType == 'bool') {
            places -= ($scope.field.placesUsed || 0);
        } else if ($scope.field.inputType == 'single_choice' || $scope.field.inputType == 'accommodation') {
            places -= ($scope.field.placesUsed[item.id] || 0);
        } else if ($scope.field.inputType == 'multi_choice') {
            places -= ($scope.field.placesUsed[item.id] || 0);
        }
        return places;
    };

    $scope.isDisabled = function(item, uservalue) {
        item = item || {};
        return !$scope.hasPlacesLeft(item, uservalue) || !item.isEnabled;
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

    $scope.paymentBlocked = function(item, userdata, registrationMetaData, validation) {
        item = item || {};
        userdata = userdata || {};

        if (validation !== undefined) {
            return ($scope.changesPrice(item) && registrationMetaData.paid) || validation(userdata);
        } else {
            return $scope.changesPrice(item) && registrationMetaData.paid;
        }
    };

    $scope.hasBillableOptions = function(field) {
        return !!_.find(field.choices, function(item) {
            return item.isBillable && item.price !== 0;
        });
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

            scope.changesPrice = function(item) {
                return item && item.isBillable && item.price !== 0;
            };

            scope.$parent.$watch('dialogs.newfield', function(val) {
                if (val && scope.isNew()) {
                    scope.dialog.open = true;
                    scope.$parent.dialogs.newfield = false;
                }

                // After the field is loaded, we can check whether it's billable, etc
                // and disable it if needed
                scope.field.billableDisabled =
                    (scope.regMetadata.paid && (scope.field.isBillable && scope.field.price > 0)) ||
                    (scope.selectedItemIsBillable && scope.selectedItemIsBillable(scope.userdata, scope.regMetadata));
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
            scope.settings.fieldName = $T("Checkbox");
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

function splitDateTime(dt, fmt) {
    if (!dt) {
        return {date: '', time: null};
    }
    var dtObj = moment(dt),
        fmtParts = fmt.split(' ');
    return {
        date: dtObj.format(fmtParts[0]),
        time: fmtParts[1] ? dtObj.format(fmtParts[1]) : null
    };
}

ndRegForm.directive('ndDateField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/date.tpl.html');
        },

        link: function(scope) {
            var fmt = scope.field.dateFormat || scope.getDefaultFieldSetting('defaultDateFormat');

            fmt = fmt.replace(/%([HMdmY])/g, function(match, c) {
                return {H: 'HH', M: 'mm', d: 'DD', m: 'MM', Y: 'YYYY'}[c];
            });

            scope.dateTime = splitDateTime(scope.userdata[scope.field.htmlName], fmt);
            scope.settings.fieldName = $T("Date");
            scope.settings.date = true;
            scope.settings.formData.push('displayFormats');
            scope.settings.formData.push('dateFormat');
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
            scope.settings.isBillable = false;
            scope.settings.isRequired = false;
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

var ndSelectController = function($scope) {
    $scope.initFormData = function(formData, field) {
        formData.choices = [];
        _.each(field.choices, function(item, ind) {
            formData.choices[ind] = angular.copy(item);
        });
    };

    $scope.validateFieldSettings = function(dialogScope) {
        if (!dialogScope.hasRadioItems()) {
            dialogScope.setSelectedTab('tab-editItems');
            dialogScope.$apply();
            return false;
        }

        var settingsValid = true,
            choices = dialogScope.formData.choices.filter(function(item) {
                return item.remove !== true;
            });

        settingsValid = settingsValid && _.all(choices, function(item) {
            return !!item.caption;
        });

        settingsValid = settingsValid && _.all(choices, function(item) {
            return /^(\d*(\.\d{1,2})?)?$/.test(item.price);
        });

        settingsValid = settingsValid && _.all(choices, function(item) {
            return /^\d*$/.test(item.placesLimit);
        });

        if (dialogScope.settings.withExtraSlots) {
            settingsValid = settingsValid && _.all(choices, function(item) {
                return /^\d*$/.test(item.maxExtraSlots);
            });
        }

        if (!settingsValid) {
            dialogScope.settingsError = true;
            dialogScope.setSelectedTab('tab-editItems');
            dialogScope.$apply();
            return false;
        }

        return true;
    };

    $scope.onSingleFieldItemChange = function(item) {
        var valueElement = $('input[name={0}]'.format($scope.field.htmlName)),
            data = {};
        if (item.id) {
            data[item.id] = (+$('#extraSlotsSelect-{0}'.format(item.id)).val() + 1) || 1;
        }
        valueElement.val(JSON.stringify(data));
    };

    $scope.multiFieldItemChecked = function(event) {
        var valueElement = $('input[name={0}]'.format($scope.field.htmlName)),
            data = JSON.parse(valueElement.val() || '{}'),
            target = $(event.target);
        if (!$scope.checkedIds) {
            $scope.checkedIds = [];
        }
        if (target.prop('checked')) {
            data[target.prop('id')] = (+$('#extraSlotsSelect-{0}'.format(target.prop('id'))).val()) || 1;
            $scope.checkedIds.push(target.prop('id'));
        } else {
            delete data[target.prop('id')];
            $scope.checkedIds.splice($scope.checkedIds.indexOf(target.prop('id')), 1);
        }
        if ($scope.checkedIds.length === 0) {
            delete $scope.checkedIds;
        }
        valueElement.val(JSON.stringify(data));
    };

    $scope.onExtraSlotsChanged = function(item, value) {
        var valueElement = $('[name={0}]'.format($scope.field.htmlName)),
            data = JSON.parse(valueElement.val() || '{}');
        if (data[item.id]) {
            data[item.id] = value;
            valueElement.val(JSON.stringify(data));
        }
    };

    $scope.selectedItemIsBillable = function(userdata, registrationMetaData) {
        if (registrationMetaData.paid) {
            var item = _.find($scope.field.choices, function(item) {
                return userdata[$scope.field.htmlName] ? !!userdata[$scope.field.htmlName][item.id] : false;
            }) || {};

            return $scope.changesPrice(item);
        }

        return false;
    };
};

ndRegForm.directive('ndRadioField', function(url) {
    return {
        require: 'ndField',
        controller: ndSelectController,
        link: function(scope) {
            scope.settings.fieldName = $T("Choice");
            scope.tplInput = url.tpl('fields/radio.tpl.html');
            scope.settings.defaultValue = true;
            scope.settings.itemtable = true;
            scope.settings.withExtraSlots = true;

            // keep track of the selected radio item
            scope.radioValue = {};
            scope.$watch('userdata[fieldName]', function() {
                scope.radioValue.id = scope.getUserdataValue();
            });

            scope.getUserdataValue = function() {
                return scope.getId(scope.fieldName);
            };

            scope.getInputTpl = function(itemType) {
                return url.tpl('fields/{0}.tpl.html'.format(itemType));
            };

            scope.getId = function(fieldName) {
                if (!scope.userdata[fieldName] || scope.userdata[fieldName] === '') {
                    if (scope.field.defaultItem && scope.field.captions) {
                        return scope.field.defaultItem;
                    } else {
                        return '';
                    }
                } else {
                    return _.keys(scope.userdata[fieldName])[0];
                }
            };

            scope.getChoiceValue = function(fieldName) {
                // if we have it it userdata we already have the ``{uuid: places}`` object
                if (scope.userdata[fieldName]) {
                    return scope.userdata[fieldName];
                }
                // otherwise create one
                var val = {};
                var key = scope.getId(fieldName);
                if (key) {
                    val[scope.getId(fieldName)] = 1;
                }
                return val;
            };

            scope.getSelectedItem = function(itemId) {
                return _.find(scope.field.choices, function(item) {
                    return item.id == itemId;
                });
            };

            scope.settings.formData.push('defaultItem');
            scope.settings.formData.push('itemType');
            scope.settings.formData.push('withExtraSlots');

            scope.settings.editionTable = {
                sortable: false,
                actions: ['remove', 'sortable'],
                colNames: [
                    $T("Caption"),
                    $T("Billable"),
                    $T("Price"),
                    $T("Places limit"),
                    $T("Max. extra slots"),
                    $T("Extra slots pay"),
                    $T("Enabled")],

                colModel: [{
                    name: 'caption',
                    index: 'caption',
                    align: 'center',
                    width: 160,
                    editable: true,
                    edittype: "text",
                    editoptions: {
                        size: "30",
                        maxlength: "50"
                    }
                }, {
                    name: 'isBillable',
                    index: 'isBillable',
                    width: 50,
                    editable: true,
                    align: 'center',
                    defaultVal: false,
                    edittype: 'bool_select'
                }, {
                    name: 'price',
                    index: 'price',
                    align: 'center',
                    width: 50,
                    editable: true,
                    edittype: 'text',
                    pattern: '/^(\\d+(\\.\\d{1,2})?)?$/',
                    editoptions: {
                        size: "7",
                        maxlength: "20"
                    }
                }, {
                    name: 'placesLimit',
                    index: 'placesLimit',
                    align: 'center',
                    width: 50,
                    editable: true,
                    edittype: "text",
                    pattern: '/^\\d*$/',
                    editoptions: {
                        size: "7",
                        maxlength: "20"
                    }
                }, {
                    name: 'maxExtraSlots',
                    index: 'maxExtraSlots',
                    align: 'center',
                    width: 50,
                    editable: true,
                    edittype: "text",
                    pattern: '/^\\d*$/',
                    className: 'extra-slots',
                    editoptions: {
                        size: "7",
                        maxlength: "2"
                    }
                }, {
                    name: 'extraSlotsPay',
                    index: 'extraSlotsPay',
                    align: 'center',
                    width: 50,
                    editable: true,
                    edittype: "bool_select",
                    className: 'extra-slots',
                    defaultVal: false
                }, {
                    name: 'isEnabled',
                    index: 'isEnabled',
                    width: 50,
                    editable: true,
                    align: 'center',
                    edittype: 'bool_select',
                    defaultVal: true
                }]
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

ndRegForm.directive('ndBoolField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/bool.tpl.html');
        },

        link: function(scope) {
            scope.settings.fieldName = $T("Yes/No");
            scope.settings.isBillable = true;
            scope.settings.placesLimit = true;
            scope.settings.defaultValues = [$T("yes"), $T("no")];
            scope.settings.formData.push('isBillable');
            scope.settings.formData.push('price');
            scope.settings.formData.push('placesLimit');
            scope.settings.formData.push('defaultValue');
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

ndRegForm.directive('ndAccommodationField', function(url) {
    return {
        require: 'ndField',
        controller: function($scope) {
            $scope.tplInput = url.tpl('fields/accommodation.tpl.html');
            $scope.areArrivalDatesValid = function(data) {
                return moment(data['arrivalDateTo'], "DD/MM/YYYY")
                        .isAfter(moment(data['arrivalDateFrom'], "DD/MM/YYYY"));
            };

            $scope.areDepartureDatesValid = function(data) {
                return moment(data['departureDateTo'], "DD/MM/YYYY")
                        .isAfter(moment(data['departureDateFrom'], "DD/MM/YYYY"));
            };

            $scope.areAccommodationOptionsDefined = function(data) {
                // `No accommodation` option does not count as an actual option
                var choices = data.choices.filter(function(item) {
                    return item.remove !== true && !item.isNoAccommodation;
                });
                return choices.length !== 0;
            };

            $scope.validateFieldSettings = function(dialogScope) {
                var data = dialogScope.formData;
                if (!$scope.areArrivalDatesValid(data)) {
                    dialogScope.setSelectedTab('tab-accommodation');
                    dialogScope.$apply();
                    return false;
                }

                if (!$scope.areDepartureDatesValid(data)) {
                    dialogScope.setSelectedTab('tab-accommodation');
                    dialogScope.$apply();
                    return false;
                }

                if (!$scope.areAccommodationOptionsDefined(data)) {
                    dialogScope.setSelectedTab('tab-accommodation-options');
                    dialogScope.$apply();
                    return false;
                }

                var settingsValid = true,
                    choices = dialogScope.formData.choices.filter(function(item) {
                        return item.remove !== true;
                    });

                settingsValid = settingsValid && _.all(choices, function(item) {
                    return !!item.caption;
                });

                settingsValid = settingsValid && _.all(choices, function(item) {
                    return /^(\d*(\.\d{1,2})?)?$/.test(item.price);
                });

                settingsValid = settingsValid && _.all(choices, function(item) {
                    return /^\d*$/.test(item.placesLimit);
                });

                if (!settingsValid) {
                    dialogScope.settingsError = true;
                    dialogScope.setSelectedTab('tab-accommodation-options');
                    dialogScope.$apply();
                    return false;
                }

                return true;
            };

            function formatDate(date) {
                if (date) {
                    return moment(date).format('DD/MM/YYYY');
                }
            }

            $scope.initFormData = function(formData, field) {
                var eventStartDate = $scope.eventStartDate,
                    eventEndDate = $scope.eventEndDate;
                formData.choices = [];
                formData.arrivalDateFrom = formatDate(field.arrivalDateFrom) || moment(eventStartDate).subtract(2, 'days').format('DD/MM/YYYY');
                formData.arrivalDateTo = formatDate(field.arrivalDateTo) || moment(eventEndDate).format('DD/MM/YYYY');
                formData.departureDateFrom = formatDate(field.departureDateFrom) || moment(eventStartDate).add(1, 'days').format('DD/MM/YYYY');
                formData.departureDateTo = formatDate(field.departureDateTo) || moment(eventEndDate).add(3, 'days').format('DD/MM/YYYY');
                _.each(field.choices, function(item, ind) {
                    formData.choices[ind] = angular.copy(item);
                });

                // Adds `No accommodation` default choice the first time the Accommodation field is added
                if (!field.choices) {
                    formData.choices.push({
                        caption: 'No accommodation',
                        isBillable: false,
                        isEnabled: true,
                        isNoAccommodation: true,
                        placesLimit: 0,
                        price: 0,
                        placeholder: $T('Title of the "None" option')
                    });
                }
            };
        },
        link: function(scope) {
            scope.settings.accommodationField = true;
            scope.settings.fieldName = $T("Accommodation");

            scope.accommodation = {};

            scope.$watch('userdata[fieldName]', function() {
                var accUserData = scope.userdata[scope.field.htmlName];
                if (accUserData === undefined || accUserData.choice === null) {
                    return;
                }
                scope.accommodation.choice = accUserData.choice;
                scope.accommodation.arrivalDate = accUserData.arrivalDate;
                scope.accommodation.departureDate = accUserData.departureDate;
            });

            function updateAccommodationPostData(fieldName, value) {
                var accommodationField = $('[name=field_{0}]'.format(scope.field.id)),
                    accommodationData = accommodationField.val() ? JSON.parse(accommodationField.val()) : {};
                accommodationData[fieldName] = value;
                accommodationField.val(JSON.stringify(accommodationData));
            }

            scope.$watch('accommodation.arrivalDate', function(newValue) {
                updateAccommodationPostData('arrivalDate', moment(newValue).format('YYYY-MM-DD'));
            });

            scope.$watch('accommodation.departureDate', function(newValue) {
                updateAccommodationPostData('departureDate', moment(newValue).format('YYYY-MM-DD'));
            });

            scope.$watch('accommodation.choice', function(newValue) {
                if (!newValue) {
                    $('#registrationForm input[name=field_{0}]'.format(scope.field.id)).val('{}');
                } else {
                    updateAccommodationPostData('choice', newValue);
                    updateAccommodationPostData('isNoAccommodation',
                                                scope.isNoAccommodationChoice(newValue, scope.field));
                }
            });

            scope.isNoAccommodationChoice = function(choice, field) {
                return !!_.find(field.choices, function(c) {
                    return c.id === choice && c.isNoAccommodation;
                });
            };

            scope.billableOptionPayed = function(userdata, registrationMetaData) {
                if (userdata[scope.field.htmlName] !== undefined) {
                    var choice = _.find(scope.field.choices, function(choice) {
                        return userdata[scope.field.htmlName].choice == choice.id;
                    });
                    return choice && choice.isBillable && registrationMetaData.paid;
                }

                return false;
            };

            scope.possibleDeparture = function(departure) {
                if (scope.arrival !== undefined) {
                    var arrival = moment(scope.arrival, 'DD/MM/YYY');
                    departure = moment(departure[0], 'DD/MM/YYY');
                    return arrival.isBefore(departure);
                }

                return true;
            };

            scope.settings.formData.push('arrivalDateFrom');
            scope.settings.formData.push('arrivalDateTo');
            scope.settings.formData.push('departureDateFrom');
            scope.settings.formData.push('departureDateTo');
            scope.settings.formData.push('choices');
            scope.settings.isRequired = false;


            scope.settings.editionTable = {
                sortable: false,
                colNames: [
                    $T("Accommodation option"),
                    $T("Billable"),
                    $T("Price"),
                    $T("Places limit"),
                    $T("Enabled")
                ],
                actions: ['remove'],
                colModel: [
                    {
                        name: 'caption',
                        index: 'caption',
                        align: 'center',
                        width: 100,
                        editoptions: {size: "30", maxlength: "50"},
                        editable: true,
                        edittype: "text"
                    },
                    {
                        name: 'isBillable',
                        index: 'isBillable',
                        width: 60,
                        editable: true,
                        align: 'center',
                        edittype: 'bool_select',
                        defaultVal: true
                    },
                    {
                        name: 'price',
                        index: 'price',
                        align: 'center',
                        width: 50,
                        editable: true,
                        edittype: "text",
                        pattern: '/^(\\d+(\\.\\d{1,2})?)?$/',
                        editoptions: {size: "7", maxlength: "20"}
                    },
                    {
                        name: 'placesLimit',
                        index: 'placesLimit',
                        align: 'center',
                        width: 80,
                        editable: true,
                        edittype: "text",
                        pattern: '/^\\d*$/',
                        editoptions: {size: "7", maxlength: "20"}
                    },
                    {
                        name: 'isEnabled',
                        index: 'isEnabled',
                        width: 60,
                        editable: true,
                        align: 'center',
                        defaultVal: false,
                        edittype: 'bool_select'
                    }
                ]
            };
        }
    };
});

ndRegForm.directive('ndMultiChoiceField', function(url) {
    return {
        require: 'ndField',
        controller: ndSelectController,
        link: function(scope) {
            scope.tplInput = url.tpl('fields/multi_choice.tpl.html');
            scope.settings.fieldName = $T("Multi choice");
            scope.settings.itemtable = true;
            scope.settings.withExtraSlots = true;
            if (scope.userdata[scope.fieldName]) {
                scope.checkedIds = _.keys(scope.userdata[scope.fieldName]);
            }

            scope.settings.editionTable = {
                sortable: false,
                actions: ['remove', 'sortable'],
                colNames: [
                    $T("Caption"),
                    $T("Billable"),
                    $T("Price"),
                    $T("Places limit"),
                    $T("Max. extra slots"),
                    $T("Extra slots pay"),
                    $T("Enabled")
                ],
                colModel: [
                    {
                        name: 'caption',
                        index: 'caption',
                        align: 'center',
                        width: 160,
                        editable: true,
                        edittype: 'text',
                        editoptions: {
                            size: '30',
                            maxlength: '50'
                        }
                    },
                    {
                        name: 'isBillable',
                        index: 'isBillable',
                        width: 50,
                        editable: true,
                        align: 'center',
                        defaultVal: false,
                        edittype: 'bool_select'
                    },
                    {
                        name: 'price',
                        index: 'price',
                        align: 'center',
                        width: 50,
                        editable: true,
                        edittype: 'text',
                        pattern: '/^(\\d+(\\.\\d{1,2})?)?$/',
                        editoptions: {
                            size: '7',
                            maxlength: '20'
                        }
                    },
                    {
                        name: 'placesLimit',
                        index: 'placesLimit',
                        align: 'center',
                        width: 50,
                        editable: true,
                        edittype: 'text',
                        pattern: '/^\\d*$/',
                        editoptions: {
                            size: '7',
                            maxlength: '20'
                        }
                    },
                    {
                        name: 'maxExtraSlots',
                        index: 'maxExtraSlots',
                        align: 'center',
                        width: 50,
                        editable: true,
                        edittype: 'text',
                        pattern: '/^\\d*$/',
                        className: 'extra-slots',
                        editoptions: {
                            size: '7',
                            maxlength: '2'
                        }
                    },
                    {
                        name: 'extraSlotsPay',
                        index: 'extraSlotsPay',
                        align: 'center',
                        width: 50,
                        editable: true,
                        edittype: 'bool_select',
                        className: 'extra-slots',
                        defaultVal: false
                    },
                    {
                        name: 'isEnabled',
                        index: 'isEnabled',
                        width: 50,
                        editable: true,
                        align: 'center',
                        edittype: 'bool_select',
                        defaultVal: true
                    }
                ]
            };

            scope.settings.formData.push('withExtraSlots');
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

                if ($.isFunction($scope.$parent.initFormData)) {
                    $scope.$parent.initFormData($scope.formData, $scope.field);
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
                $scope.formData.choices.push({
                    placesLimit: 0,
                    price: 0,
                    isEnabled: true,
                    isBillable: false,
                    maxExtraSlots: 0
                });

                $scope.toggleExtraSlotsColumns($scope.formData.withExtraSlots);
            };

            $scope.addAccommodationOption = function() {
                $scope.formData.choices.push({
                    isEnabled: true,
                    price: 0,
                    placesLimit: 0
                });
            };

            $scope.sortItems = function() {
                $scope.formData.choices = _.sortBy($scope.formData.choices, function(radioitem) {
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

            scope.hasRadioItems = function() {
                return _.any(scope.formData.choices, function(item) {
                    return item.remove !== true;
                });
            };

            scope.arrivalDatesValid = function() {
                return scope.$parent.areArrivalDatesValid(scope.formData);
            };

            scope.departureDatesValid = function() {
                return scope.$parent.areDepartureDatesValid(scope.formData);
            };

            scope.hasAccommodationOptions = function() {
                return scope.$parent.areAccommodationOptionsDefined(scope.formData);
            };
        }
    };
});
