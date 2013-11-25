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

ndRegForm.directive('ndField', function($rootScope, url, RESTAPI) {
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
                        var postData = {confId: $scope.confId,
                                            sectionId: $scope.section.id,
                                            fieldData: dialogScope.formData
                                        };

                        if(!$scope.fieldApi.isNew()) postData.fieldId = dialogScope.field.id;
                        RESTAPI.Fields.save(postData,
                            function(data, headers) {
                                $scope.field = data;
                                dialogScope.field = data;
                            });
                    },
                    onCancel: function() {
                        if ($scope.fieldApi.isNew()) {
                            $scope.api.removeNewField();
                        }
                    }
                }
            };

            $scope.fieldApi = {
                isNew: function() {
                    return $scope.field.id == -1;
                },
                disableField: function(field) {
                    RESTAPI.Fields.disable({confId: $scope.confId,
                                            sectionId: $scope.section.id,
                                            fieldId: $scope.field.id},
                        function(data) {
                            $scope.field = data;
                    });
                },
                enableField: function(field) {
                    RESTAPI.Fields.enable({confId: $scope.confId,
                                           sectionId: $scope.section.id,
                                           fieldId: field.id},
                        function(data) {
                            $scope.field = data;
                    });
                },
                removeField: function(field) {
                    RESTAPI.Fields.remove({confId: $scope.confId,
                                           sectionId: $scope.section.id,
                                           fieldId: field.id},
                        function(data) {
                            $scope.section.items = data.items;
                    });
                }
            };

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


            $scope.openFieldSettings = function() {
                $scope.dialogs.settings.open = true;
            };

            // TODO Consider moving it to fieldApi, or even better, FielCtrl
            $scope.isDisabled = function(field) {
                return field.placesLimit !== 0 && field.noPlacesLeft === 0;
            };

            $scope.isBillable = function(field) {
                return field.billable && !$scope.isDisabled(field);
            };

            $scope.hasPlacesLeft = function(field) {
                return !$scope.isDisabled(field) && field.placesLimit !== 0 && field.noPlacesLeft >= 0;
            };

            $scope.isFieldActive = function (field) {
                return field.id != -1 && (field.disabled === false || $rootScope.editMode);
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
        },

        link: function(scope) {
            scope.settings.placesLimit = true;
            scope.settings.billable = true;
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
            $scope.calendarimg = imageSrc("calendarWidget");
        },

        link: function(scope) {
            scope.settings.date = true;
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
            scope.settings.number = true;
            scope.settings.billable = true;

            scope.change = function() {
                // TODO do this the angular way
                // TODO var value = get value from input (avoid jQuery)
                /*$E('subtotal-{{ name }}').dom.innerHTML =
                    ((isNaN(parseInt(value, 10)) || parseInt(value, 10) < 0) ?
                    0:
                    parseInt(value, 10)) * scope.field.price;*/
            };
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
            scope.dialogs.settings.contentWidth = 'auto';
            scope.dialogs.settings.editionTable = {
                sortable: false,
                actions: ['remove', 'sortable'],
                colNames:[$T("caption"), $T("billable"), $T("price"), $T("places limit"), $T("enable")],
                colModel: [
                        {
                           name:'caption',
                           index:'caption',
                           align: 'center',
                           sortable:false,
                           width:160,
                           editoptions:{size:"30",maxlength:"50"},
                           editable: true
                        },
                        {
                           name:'billable',
                           index:'isBillable',
                           sortable:false,
                           width:60,
                           editable: true,
                           align: 'center',
                           defaultVal: false,
                           edittype:'bool_select'
                        },

                        {
                           name:'price',
                           index:'price',
                           align: 'center',
                           sortable:false,
                           width:50,
                           editable: true,
                           editoptions:{size:"7",maxlength:"20"}

                        },
                        {
                           name:'placesLimit',
                           index:'placesLimit',
                           align: 'center',
                           sortable:false,
                           width:80,
                           editable: true,
                           editoptions:{size:"7",maxlength:"20"}

                        },
                        {
                           name:'isEnabled',
                           index:'isEnabled',
                           sortable:false,
                           width:60,
                           editable: true,
                           align: 'center',
                           edittype:'bool_select',
                           defaultVal: true
                        }
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
        },

        link: function(scope) {
            scope.settings.size = true;
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
        },

        link: function(scope) {
            scope.settings.placesLimit = true;
            scope.settings.billable = true;
        }
    };
});

ndRegForm.directive('ndFieldDialog', function(url) {
    return {
        require: 'ndDialog',
        replace: true,
        templateUrl: url.tpl('fields/dialogs/base.tpl.html'),

        controller: function($scope) {
            $scope.settings = $scope.$parent.settings;
            $scope.settings.dialogs = $scope.data;
            $scope.field = $scope.$eval($scope.asyncData);
            $scope.formData = {
                radioitems: [],
                input: $scope.field.input
            };

            _.each($scope.field.values.radioitems, function (item, ind) {
                $scope.formData.radioitems[ind] = {id: item.id, cancelled: item.cancelled}; //A way to initialize properly
            });

            $scope.actions.init = function() {
                $scope.tabSelected = "tab-options";
            };

            $scope.addItem = function () {
                 $scope.formData.radioitems.push({id:'isNew'});
            };
        }
    };
});
