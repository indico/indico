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

ndRegForm.controller('SectionCtrl', ['$scope', '$rootScope','RESTAPI',  function($scope, $rootScope, RESTAPI) {
    $scope.api = {};
    $scope.actions = {};

    $scope.api.createSection = function(section) {
        // TODO see how to push a section into the list of sections
    };

    $scope.api.disableSection = function(section) {
        RESTAPI.Sections.disable({confId: $rootScope.confId, sectionId: section.id}, function(data) {
            section.enabled = data.enabled; //TODO: See why we cannot put section=data
        });
    };

    $scope.api.restoreSection = function(section) {
        RESTAPI.Sections.enable({confId: $rootScope.confId, sectionId: section.id}, function(data) {
            section.enabled = data.enabled; //TODO: See why we cannot put section=data
        });
    };

    $scope.api.removeSection = function(section) {
        RESTAPI.Sections.remove({confId: $rootScope.confId, sectionId: section.id}, function(data) {
            console.log($scope);
            //TODO: See how to update model!!
        });
    };

    $scope.api.saveConfig = function(section, data) {
        var postData = {confId: $rootScope.confId, sectionId: section.id};
        _.extend(postData, data);
        //postData.items = _.values(postData.items);
        RESTAPI.Sections.save(postData, function(sectionUpdated) {
            $scope.$parent.section = sectionUpdated;
            //TODO: why not with section variable?
        });
    };

    $scope.actions.openAddField = function(section, field, type) {
        $scope.dialogs.newfield = true;
        section.items.push({
            id: -1,
            input: field,
            values: {
                inputType: type
            }
        });
    };

    $scope.api.moveField = function(field, position) {
        RESTAPI.Fields.move({confId: $rootScope.confId,
                             sectionId: $scope.section.id,
                             fieldId: field.id,
                             endPos: position
        },  function(data) {
                $scope.field = data;
            });
    };
}]);

ndRegForm.directive('ndSection', function(url) {
    return {
        replace: true,
        templateUrl: url.tpl('section.tpl.html'),
        controller: 'SectionCtrl',

        link: function(scope, element) {

            scope.buttons = {
                newfield: false,
                config: false,
                disable: false
            };

            scope.dialogs = {
                newfield: false,
                config: {
                    open: false,
                    actions: {}
                }
            };

            scope.state = {
                collapsed: false
            };

            scope.$on('collapse', function(event, collapsed) {
                scope.state.collapsed = collapsed;
            });

            scope.$watch('state.collapsed', function(val) {
                var content = angular.element(element.children()[1]);
                if (val) {
                    content.slideUp();
                } else {
                    content.slideDown();
                }
            });

            scope.dialogs.config.actions.onOk = function(dialogScope) {
                scope.api.saveConfig(dialogScope.section, dialogScope.formData);
            };

            scope.dialogs.config.actions.onCancel = function(dialogScope) {
            };
        }
    };
});

ndRegForm.directive("ndGeneralSection", function($timeout) {
    return {
        require: 'ndSection',
        controller: 'SectionCtrl', //TODO check inheritance
        link: function(scope) {
            scope.buttons.newfield = true;
            scope.buttons.disable = true;

            // TODO can we move fieldtypes to the tpl? It only happens once
            // scope.fieldtypes = [
            //     {id: 'label',            desc: $T("Label")},
            //     {id: 'text',             desc: $T("Text input")},
            //     {id: 'number',           desc: $T("Number")},
            //     {id: 'textarea',         desc: $T("Text area")},
            //     {id: 'radio-dropdown',   desc: $T("Dropdown")},
            //     {id: 'radio-radiogroup', desc: $T("Choice")},
            //     {id: 'checkbox',         desc: $T("Checkbox")},
            //     {id: 'date',             desc: $T("Date")},
            //     {id: 'yesno',            desc: $T("Yes/No")},
            //     {id: 'telephone',        desc: $T("Phone")},
            //     {id: 'country',          desc: $T("Country")},
            //     {id: 'file',             desc: $T("File")}
            // ];

            scope.api.removeNewField = function() {
                if (scope.section.items[scope.section.items.length-1].id == -1) {
                    $timeout(function() {
                        scope.section.items.pop();
                    }, 0);
                }
            };

            scope.api.commitNewField = function() {

            };

            scope.fieldSortableOptions = {
                start: function(e, ui ){
                    ui.placeholder.height(ui.helper.outerHeight());
                },

                update: function(e, ui) {
                    scope.api.moveField(ui.item.scope().field, ui.item.index());
                },

                axis: 'y',
                cursor: 'move',
                delay: 150,
                opacity: 0.5,
                handle: ".regFormFieldSortableHandle",
                placeholder: "regFormSortablePlaceHolder"
                //items: "nd-section"
            };

        }
    };
});

ndRegForm.directive("ndPersonalDataSection", function() {
    return {
        require: 'ndGeneralSection',
        link: function(scope) {
            scope.buttons.disable = false;
        }
    };
});

ndRegForm.directive("ndAccommodationSection", function() {
    return {
        require: 'ndSection',

        link: function(scope) {
            scope.buttons.config = true;
            scope.buttons.disable = true;

            scope.dialogs.config.tabs = [
                {id: 'config',              name: $T("Configuration"),          type: 'config' },
                {id: 'editAccomodation',    name: $T("Edit accommodations"),    type: 'editionTable' }
            ];

            scope.dialogs.config.contentWidth = 615;

            scope.dialogs.config.editionTable = {
                sortable: false,
                colNames: [$T("caption"), $T("billable"),  $T("price"), $T("place limit"), $T("cancelled")],
                actions: ['remove'],
                colModel: [
                       {
                           name:'caption',
                           index:'caption',
                           align: 'center',
                           sortable:false,
                           width:100,
                           editoptions: {size:"30",maxlength:"50"},
                           editable: true
                       },
                       {
                           name:'billable',
                           index:'billable',
                           sortable:false,
                           width:60,
                           editable: true,
                           align: 'center',
                           edittype:'bool_select',
                           defaultVal: true

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
                           name:'cancelled',
                           index:'cancelled',
                           sortable:false,
                           width:60,
                           editable: true,
                           align: 'center',
                           defaultVal: false,
                           edittype:'bool_select'
                       }

                  ]
            };
        }
    };
});

ndRegForm.directive("ndFurtherInformationSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.disable = true;
        }
    };
});

ndRegForm.directive("ndReasonSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.disable = true;
        }
    };
});

ndRegForm.directive("ndSessionsSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.config = true;
            scope.buttons.disable = true;

            scope.dialogs.config.tabs = [
                {id: 'config',          name: $T("Configuration"),      type: 'config'},
                {id: 'editSessions',    name: $T("Manage sessions"),    type: 'editionTable'}
            ];

            scope.dialogs.config.contentWidth = 750;

            scope.dialogs.config.editionTable = {
                sortable: false,
                colNames:[$T('caption'),$T('billable'),$T('price'), $T('enabled')],
                actions: [''],
                colModel: [
                       {
                           name:'caption',
                           index:'caption',
                           align: 'left',
                           sortable:false,
                           width:200,
                           editoptions:{size:"30",maxlength:"80"},
                           editable: false
                       },
                       {
                           name:'billable',
                           index:'billable',
                           sortable:false,
                           width:60,
                           editable: true,
                           align: 'center',
                           edittype:'bool_select',
                           defaultVal: true
                       },
                       {
                           name:'price',
                           index:'price',
                           align: 'center',
                           sortable:false,
                           width:80,
                           editable: true,
                           editoptions:{size:"7",maxlength:"20"}
                       },
                       {
                           name:'enabled',
                           index:'enabled',
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

ndRegForm.directive("ndSocialEventSection", function() {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.config = true;
            scope.buttons.disable = true;
            scope.dialogs.config.tabs = [
                {id: 'config',          name: $T("Configuration"),     type: 'config'},
                {id: 'editEvents',      name: $T("Edit events"),       type: 'editionTable'},
                {id: 'canceledEvent',   name: $T("Canceled events"),   type: 'cancelEvent'}
            ];

            scope.dialogs.config.contentWidth = 800;

            scope.dialogs.config.editionTable = {
                sortable: false,
                colNames:[$T("caption"), $T("billabe"), $T("price"), $T("price/place"), $T("Nb places"), $T("Max./part.")],
                actions: ['remove', ['cancel', $T('Cancel this event'),'#tab-canceledEvent','icon-cancel']],
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
                           index:'billable',
                           sortable:false,
                           width:60,
                           editable: true,
                           align: 'center',
                           defaultVal : false,
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
                           name:'pricePerPlace',
                           index:'pricePerPlace',
                           sortable:false,
                           width:80,
                           editable: true,
                           align: 'center',
                           defaultVal : false,
                           edittype:'bool_select'
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
                           name:'maxPlace',
                           index:'maxPlace',
                           align: 'center',
                           sortable:false,
                           width:80,
                           editable: true,
                           editoptions:{size:"7",maxlength:"20"}
                        }
                  ]
            };


            scope.dialogs.config.canceledTable = {
                sortable: false,
                colNames:[$T("caption"), $T("Reason for cancellation")],
                actions: ['remove', ['uncancel', $T('Uncancel this event'),'#tab-editEvents','icon-cancel']],
                colModel: [
                        {
                            index:'caption',
                            align: 'center',
                            sortable:false,
                            width:160,
                            editoptions:{size:"30",maxlength:"50"},
                            editable: false
                        },
                        {
                            name:'reason',
                            index:'cancelledReason',
                            sortable:false,
                            width:250,
                            editoptions:{size:"30",maxlength:"50"},
                            editable: true
                        }

                     ]
            };
        }
    };
});

ndRegForm.directive('ndSectionDialog', function(url) {
    return {
        require: 'ndDialog',
        replace: true,
        templateUrl: url.tpl('sections/dialogs/base.tpl.html'),
        controller: function ($scope) {

            $scope.section = $scope.$eval($scope.asyncData);
            $scope.formData = {
                items: []
            }; //This is the way?

            _.each($scope.section.items, function (item, ind) {
                $scope.formData.items[ind] = {id: item.id, cancelled: item.cancelled}; //A way to initialize properly
            });

            $scope.getTabTpl = function(section_id, tab_type) {
                return url.tpl('sections/dialogs/{0}-{1}.tpl.html'.format(tab_type, section_id));
            };

            $scope.actions.init = function() {
                $scope.tabSelected = $scope.data.tabs[0].id;
            };

            $scope.addItem = function () {
                 $scope.formData.items.push({id:'isNew'});
            }

        }
    };
});
