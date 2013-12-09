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

ndRegForm.controller('SectionCtrl', function($scope, $rootScope, regFormFactory) {
    $scope.api = {};
    $scope.actions = {};

    var getRequestParams = function(section) {
        return {
            confId: $rootScope.confId,
            sectionId: section.id
        };
    };

    $scope.api.disableSection = function(section) {
        regFormFactory.Sections.disable(getRequestParams(section), function(updatedSection) {
            section.enabled = updatedSection.enabled;
        });
    };

    $scope.api.saveConfig = function(section, data) {
        var requestParams = angular.extend(getRequestParams(section), data);
        regFormFactory.Sections.save(requestParams, function(updatedSection) {
            $scope.$parent.section = updatedSection;
            //TODO: inject updatedSection into $scope.section
        });
    };

    $scope.api.updateTitle = function(section, data) {
        var requestParams = angular.extend(getRequestParams(section), data);

        regFormFactory.Sections.title(requestParams, function(updatedSection) {
            $scope.section.title = updatedSection.title;
        });
    };

    $scope.api.updateDescription = function(section, data) {
        var requestParams = angular.extend(getRequestParams(section), data);

        regFormFactory.Sections.description(requestParams, function(updatedSection) {
            $scope.section.description = updatedSection.description;
        });
    };

    $scope.api.moveField = function(section, field, position) {
        var requestParams = angular.extend(getRequestParams(section), {
            fieldId: field.id,
            endPos: position
        });

        regFormFactory.Fields.move(requestParams, function(updatedSection) {
            // TODO in case backend rejects request we should update scope with something like:
            // if (response.error) {
            //     $scope.section.items = response.updatedSection.items;
            // }
        });
    };

    $scope.actions.openAddField = function(section, field, type) {
        $scope.dialogs.newfield = true;
        section.items.push({
            id: -1,
            disabled: false,
            input: field,
            values: {
                inputType: type
            }
        });
    };
});

ndRegForm.directive('ndSection', function($rootScope, url) {
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
                    actions: {},
                    formData: []
                }
            };

            scope.state = {
                collapsed: false
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
                    scope.api.updateTitle(scope.section, {title: newVal});
                }
            });

            scope.$watch('section.description', function(newVal, oldVal) {
                if (newVal !== oldVal) {
                    scope.api.updateDescription(scope.section, {description: newVal});
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

ndRegForm.directive("ndGeneralSection", function($timeout, url, sortableoptions) {
    return {
        require: 'ndSection',
        controller: 'SectionCtrl',

        link: function(scope) {
            scope.buttons.newfield = true;
            scope.buttons.disable = true;
            scope.tplGeneralField = url.tpl('sections/generalfield.tpl.html');

            scope.hasDisabledFields = function() {
                return _.any(scope.section.items, function(field) {
                    return field.disabled === true;
                });
            };

            scope.api.removeNewField = function() {
                if (scope.section.items[scope.section.items.length-1].id == -1) {
                    $timeout(function() {
                        scope.section.items.pop();
                    }, 0);
                }
            };

            scope.fieldSortableOptions = {
                update: function(e, ui) {
                    scope.api.moveField(scope.section, ui.item.scope().field, ui.item.index());
                },
                // TODO Re-enable when solved: http://bugs.jqueryui.com/ticket/5772
                // containment: '.field-list',
                handle: ".regform-field .field-sortable-handle",
                placeholder: "regform-field-sortable-placeholder"
            };

            angular.extend(scope.fieldSortableOptions, sortableoptions);
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

            scope.dialogs.config.formData.push('arrivalOffsetDates');
            scope.dialogs.config.formData.push('departureOffsetDates');
            scope.dialogs.config.contentWidth = 615;
            scope.dialogs.config.tabs = [
                {id: 'config', name: $T("Configuration"), type: 'config' },
                {id: 'editAccomodation', name: $T("Edit accommodations"), type: 'editionTable' }
            ];

            scope.dialogs.config.editionTable = {
                sortable: false,
                colNames: [
                    $T("caption"),
                    $T("billable"),
                    $T("price"),
                    $T("place limit"),
                    $T("cancelled")
                ],
                actions: ['remove'],
                colModel: [
                       {
                           name:'caption',
                           index:'caption',
                           align: 'center',
                           width:100,
                           editoptions: {size:"30",maxlength:"50"},
                           editable: true,
                           edittype: "text",
                       },
                       {
                           name:'billable',
                           index:'billable',
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
                           width:50,
                           editable: true,
                           edittype: "text",
                           editoptions:{size:"7",maxlength:"20"}

                       },
                       {
                           name:'placesLimit',
                           index:'placesLimit',
                           align: 'center',
                           width:80,
                           editable: true,
                           edittype: "text",
                           editoptions:{size:"7",maxlength:"20"}
                       },
                       {
                           name:'cancelled',
                           index:'cancelled',
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
            scope.buttons.config = true;
            scope.buttons.disable = true;

            scope.dialogs.config.formData.push('content');
            scope.dialogs.config.tabs = [
                {id: 'config', name: $T("Configuration"), type: 'config'}
            ];
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

ndRegForm.directive("ndSessionsSection", function($rootScope, regFormFactory) {
    return {
        require: 'ndSection',

        controller: function($scope) {
            $scope._hasSession= function(id) {
                return _.find($scope.section.items, function(session) {
                    return session.id == id;
                }) !== undefined;
            };

            var sessions = regFormFactory.Sessions.query({confId: $rootScope.confId}, function() {
                _.each(sessions, function (item, ind) {
                    if(!$scope._hasSession(item.id)) {
                        $scope.section.items.push({
                            id: item.id,
                            caption: item.title,
                            billable: false,
                            price: 0, enabled: false
                        });
                    }
                });
            });
        },

        link: function(scope) {
            scope.buttons.config = true;
            scope.buttons.disable = true;

            scope.dialogs.config.formData.push('type');
            scope.dialogs.config.tabs = [
                {id: 'config', name: $T("Configuration"), type: 'config'},
                {id: 'editSessions', name: $T("Manage sessions"), type: 'editionTable'}
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
                           width:200,
                           editoptions:{size:"30",maxlength:"80"},
                           editable: false,
                           edittype: "text",
                       },
                       {
                           name:'billable',
                           index:'billable',
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
                           width:80,
                           editable: true,
                           edittype: "text",
                           editoptions:{size:"7",maxlength:"20"}
                       },
                       {
                           name:'enabled',
                           index:'enabled',
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

            scope.getMaxRegistrations = function(item) {
                if (item.placesLimit !== 0) {
                    return Math.min(item.maxPlace, item.noPlacesLeft);
                } else {
                    return item.maxPlace;
                }
            };

            scope.noAvailableEvent =function() {
                if (scope.section.items.length === 0) {
                    return true;
                } else {
                    return _.every(scope.section.items, function(item) {
                        return item.cancelled;
                    });
                }
            };

            scope.anyCancelledEvent = function() {
                return _.any(scope.section.items, function(item) {
                    return item.cancelled;
                });
            };

            scope.dialogs.config.contentWidth = 800;
            scope.dialogs.config.formData.push('introSentence');
            scope.dialogs.config.formData.push('selectionType');
            scope.dialogs.config.tabs = [
                {id: 'config', name: $T("Configuration"), type: 'config'},
                {id: 'editEvents', name: $T("Edit events"), type: 'editionTable'},
                {id: 'canceledEvent', name: $T("Canceled events"), type: 'cancelEvent'}
            ];

            scope.dialogs.config.editionTable = {
                sortable: false,

                colNames: [
                    $T("caption"),
                    $T("billabe"),
                    $T("price"),
                    $T("price/place"),
                    $T("Nb places"),
                    $T("Max./part.")
                ],

                actions: [
                    'remove',
                    ['cancel', $T('Cancel this event'),'#tab-canceledEvent','icon-cancel']
                ],

                colModel: [
                        {
                           name:'caption',
                           index:'caption',
                           align: 'center',
                           width:160,
                           editoptions:{size:"30",maxlength:"50"},
                           editable: true,
                           edittype: "text",
                        },
                        {
                           name:'billable',
                           index:'billable',
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
                           width:50,
                           editable: true,
                           edittype: "text",
                           editoptions:{size:"7",maxlength:"20"}
                        },
                        {
                           name:'pricePerPlace',
                           index:'pricePerPlace',
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
                           edittype: "text",
                           editoptions:{size:"7",maxlength:"20"}
                        },
                        {
                           name:'maxPlace',
                           index:'maxPlace',
                           align: 'center',
                           width:80,
                           editable: true,
                           edittype: "text",
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
                            width:160,
                            editoptions:{size:"30",maxlength:"50"},
                            editable: false,
                            edittype: "text",
                        },
                        {
                            name:'reason',
                            index:'cancelledReason',
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

        controller: function($scope) {
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

                _.each($scope.section.items, function (item, ind) {
                    $scope.formData.items[ind] = {
                        id: item.id,
                        cancelled: item.cancelled
                    };
                });

                $scope.tabSelected = $scope.config.tabs[0].id;
            };

            $scope.addItem = function () {
                 $scope.formData.items.push({id:'isNew'});
            };
        },

        link: function(scope) {
            scope.getTabTpl = function(section_id, tab_type) {
                return url.tpl('sections/dialogs/{0}-{1}.tpl.html'.format(section_id, tab_type));
            };
        }
    };
});
