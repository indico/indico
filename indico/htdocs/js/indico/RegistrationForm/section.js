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

ndRegForm.controller('SectionCtrl', function($scope, $rootScope, regFormFactory) {
    $scope.sectionApi = {};
    $scope.actions = {};

    var getRequestParams = function(section) {
        return {
            confId: $rootScope.confId,
            sectionId: section.id
        };
    };

    $scope.sectionApi.disableSection = function(section) {
        $scope.$parent.animations.recoverSectionButton = 'button-highlight';
        regFormFactory.Sections.disable(getRequestParams(section), function(updatedSection) {
            regFormFactory.processResponse(updatedSection, {
                success: function(updatedSection)  {
                    section.enabled = updatedSection.enabled;
                }
            });
        });
    };

    $scope.sectionApi.saveConfig = function(section, data) {
        var requestParams = angular.extend(getRequestParams(section), data);
        regFormFactory.Sections.save(requestParams, function(updatedSection) {
            regFormFactory.processResponse(updatedSection, {
                success: function(updatedSection)  {
                    $scope.section = angular.extend($scope.section, updatedSection);
                    if (updatedSection.id == 'sessions') {
                        $scope.fetchSessions();
                    }
                }
            });
        });
    };

    $scope.sectionApi.updateTitle = function(section, data) {
        var requestParams = angular.extend(getRequestParams(section), data);

        regFormFactory.Sections.title(requestParams, function(updatedSection) {
            regFormFactory.processResponse(updatedSection, {
                success: function(updatedSection) {
                    $scope.section.title = updatedSection.title;
                }
            });
        });
    };

    $scope.sectionApi.updateDescription = function(section, data) {
        var requestParams = angular.extend(getRequestParams(section), data);

        regFormFactory.Sections.description(requestParams, function(updatedSection) {
            regFormFactory.processResponse(updatedSection, {
                success: function(updatedSection)  {
                    $scope.section.description = updatedSection.description;
                }
            });
        });
    };

    $scope.sectionApi.moveField = function(section, field, position) {
        var requestParams = angular.extend(getRequestParams(section), {
            fieldId: field.id,
            endPos: position
        });

        regFormFactory.Fields.move(requestParams, function(updatedSection) {
            regFormFactory.processResponse(updatedSection, {
                success: function(updatedSection) {}
            });
            // TODO in case backend rejects request we should update scope with something like:
            // if (response.error) {
            //     $scope.section.items = response.updatedSection.items;
            // }
        });
    };

    $scope.sectionApi.removeField = function(section, field) {
        $scope.dialogs.removefield.field = field;

        $scope.dialogs.removefield.callback = function(success) {
            if (success) {
                var requestParams = angular.extend(getRequestParams(section), {
                    fieldId: field.id
                });

                $scope.$apply(regFormFactory.Fields.remove(requestParams, {}, function(updatedSection) {
                    regFormFactory.processResponse(updatedSection, {
                        success: function(updatedSection) {
                            $scope.section.items = updatedSection.items;
                        }
                    });
                }));
            }
        };

        $scope.dialogs.removefield.open = true;
    };

    $scope.actions.openAddField = function(section, field, type) {
        $scope.dialogs.newfield = true;
        section.items.push({
            id: -1,
            disabled: false,
            input: field,
            lock: [],
            values: {
                inputType: type
            }
        });
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
                disable: false
            };

            scope.dialogs = {
                newfield: false,
                config: {
                    open: false,
                    actions: {},
                    formData: []
                },
                removefield: {
                    open: false
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

            scope.sectionApi.removeNewField = function() {
                if (scope.section.items[scope.section.items.length-1].id == -1) {
                    $timeout(function() {
                        scope.section.items.pop();
                    }, 0);
                }
            };

            scope.fieldSortableOptions = {
                update: function(e, ui) {
                    scope.sectionApi.moveField(scope.section, ui.item.scope().field, ui.item.index());
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
        priority: -1,
        link: function(scope) {
            scope.buttons.disable = false;
        }
    };
});

ndRegForm.directive("ndAccommodationSection", function($rootScope) {
    return {
        require: 'ndSection',
        link: function(scope) {
            scope.buttons.config = true;
            scope.buttons.disable = true;

            scope.billableOptionPayed = function(userdata) {
                if (userdata.accommodation !== undefined) {
                    var accommodation = userdata.accommodation.accommodationType || {};
                    return accommodation.billable === true && userdata.paid === true;
                }

                return false;
            };

            scope.updateArrival = function(arrival) {
                scope.arrival = arrival;
                scope.arrivalUpdated = true;
            };

            scope.possibleDeparture = function(departure) {
                if (scope.arrival !== undefined) {
                    var arrival = moment(scope.arrival, 'DD/MM/YYY');
                    departure = moment(departure[0], 'DD/MM/YYY');
                    return arrival.isBefore(departure);
                }

                return true;
            };

            scope.dialogs.config.arrivalDates = {
                sDate: moment($rootScope.confSdate).format('DD/MM/YYYY'),
                eDate: moment($rootScope.confEdate).format('DD/MM/YYYY')
            };

            scope.dialogs.config.departureDates = {
                sDate: moment($rootScope.confSdate).format('DD/MM/YYYY'),
                eDate: moment($rootScope.confEdate).format('DD/MM/YYYY')
            };

            scope.dialogs.config.updateArrivalDates = function(offset) {
                offset = offset || [0, 0];
                scope.dialogs.config.arrivalDates.sDate =
                    moment($rootScope.confSdate)
                        .subtract('d', parseInt(offset[0], 10))
                        .format('DD/MM/YYYY');
                scope.dialogs.config.arrivalDates.eDate =
                    moment($rootScope.confEdate)
                        .subtract('d', parseInt(offset[1], 10))
                        .format('DD/MM/YYYY');
            };
            scope.dialogs.config.updateArrivalDates(scope.section.arrivalOffsetDates);

            scope.dialogs.config.updateDepartureDates = function(offset) {
                offset = offset || [0, 0];
                scope.dialogs.config.departureDates.sDate =
                    moment($rootScope.confSdate)
                        .add('d', parseInt(offset[0], 10))
                        .format('DD/MM/YYYY');
                scope.dialogs.config.departureDates.eDate =
                    moment($rootScope.confEdate)
                        .add('d', parseInt(offset[1], 10))
                        .format('DD/MM/YYYY');
            };
            scope.dialogs.config.updateDepartureDates(scope.section.departureOffsetDates);

            scope.dialogs.config.formData.push('arrivalOffsetDates');
            scope.dialogs.config.formData.push('departureOffsetDates');
            scope.dialogs.config.tabs = [
                {id: 'config', name: $T("Configuration"), type: 'config' },
                {id: 'editAccomodation', name: $T("Edit accommodations"), type: 'editionTable' }
            ];

            scope.dialogs.config.editionTable = {
                sortable: false,
                colNames: [
                    $T("Accommodation option"),
                    $T("Billable"),
                    $T("Price"),
                    $T("Places limit"),
                    $T("Cancelled")
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
                           edittype: "text"
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
            scope.buttons.disable = true;

            scope.$watch('section.content', function(newVal, oldVal) {
                if (newVal !== oldVal) {
                    scope.sectionApi.updateDescription(scope.section, {description: newVal});
                }
            });
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
            var hasSession = function(id) {
                return _.find($scope.section.items, function(session) {
                    return session.id == id;
                }) !== undefined;
            };

            $scope.anyBillableSessionPayed = function(userdata) {
                if (userdata.paid) {
                    return _.any(userdata.sessionList, function(item) {
                        var session = _.find($scope.section.items, function(session) {
                            return session.id == item.id;
                        }) || {};

                        return session.billable && session.price !== 0;
                    });
                }

                return false;
            };

            $scope.anySessionEnabled = function() {
                return _.any($scope.section.items, function(session) {
                    return session.enabled === true;
                });
            };

            $scope.fetchSessions = function() {
                var sessions = regFormFactory.Sessions.query({confId: $rootScope.confId}, function() {
                    _.each(sessions, function (item, ind) {
                        if(!hasSession(item.id)) {
                            $scope.section.items.push({
                                id: item.id,
                                caption: item.title,
                                billable: false,
                                price: 0,
                                enabled: false
                            });
                        }
                    });
                });
            };

            $scope.fetchSessions();
        },

        link: function(scope) {
            scope.buttons.config = true;
            scope.buttons.disable = true;

            scope.isSelected = function(sessionId) {
                return _.any(scope.userdata.sessionList, function(e) {
                    return sessionId == e.id;
                });
            };

            scope.dialogs.config.formData.push('type');
            scope.dialogs.config.tabs = [
                {id: 'config', name: $T("Configuration"), type: 'config'},
                {id: 'editSessions', name: $T("Manage sessions"), type: 'editionTable'}
            ];

            scope.dialogs.config.editionTable = {
                sortable: false,

                colNames:[
                    $T('Session'),
                    $T('Billable'),
                    $T('Price'),
                    $T('Enabled')
                ],

                actions: [''],
                colModel: [
                       {
                           name:'caption',
                           index:'caption',
                           align: 'left',
                           width:200,
                           editoptions:{size:"30",maxlength:"80"},
                           editable: false,
                           edittype: "text"
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
            // keep track of the selected radio item
            scope.selectedRadioInput = {};
            // Keep track of the selected checkbox items (multiple)
            scope.selectedInputs = _.object(_.map(_.filter(scope.section.items, function(item) {
                    return item.cancelled != 'false';
                }), function(item){
                    return [item.id, false];
                }));
            // Keep track of the number of accompanying people
            scope.selectedPlaces = _.object(_.map(_.filter(scope.section.items, function(item) {
                    return item.cancelled != 'false';
                }), function(item){
                    return [item.id, 1];
                }));

            scope.$watch('userdata.socialEvents', function() {
                angular.forEach(scope.userdata.socialEvents, function(item){
                    scope.selectedRadioInput['id'] = item.id;  // Used when radio buttons
                    scope.selectedInputs[item.id] = true;  // Used when checkboxes
                    scope.selectedPlaces[item.id] = scope.getNoPlaces(item);
                });
            });

            scope.anySelected = function() {
                return _.any(scope.selectedInputs, function(e) {
                    return e;
                });;
            };

            scope.getMaxRegistrations = function(item) {
                if (item.placesLimit !== 0) {
                    return Math.min(item.maxPlace + 1, item.noPlacesLeft + scope.getNoPlaces(item));
                } else {
                    return item.maxPlace + 1;
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

            scope.anyBillableEventPayed = function(userdata) {
                if (userdata.paid) {
                    return _.any(userdata.socialEvents, function(item) {
                        return item.price !== 0;
                    });
                }

                return false;
            };

            scope.getNoPlaces = function(item) {
                var e = _.find(scope.userdata.socialEvents, function(e) {
                    return item.id == e.id;
                });

                if (e !== undefined) {
                    return e.noPlaces;
                } else {
                    return 0;
                }
            };

            scope.dialogs.config.formData.push('introSentence');
            scope.dialogs.config.formData.push('mandatory');
            scope.dialogs.config.formData.push('selectionType');
            scope.dialogs.config.tabs = [
                {id: 'config', name: $T("Configuration"), type: 'config'},
                {id: 'editEvents', name: $T("Edit events"), type: 'editionTable'},
                {id: 'canceledEvent', name: $T("Canceled events"), type: 'cancelEvent'}
            ];

            scope.dialogs.config.editionTable = {
                sortable: false,

                colNames: [
                    $T("Event name"),
                    $T("Billable"),
                    $T("Price"),
                    $T("Capacity"),
                    '',
                    $T("Accompanying"),
                    $T("Must pay")
                ],

                colHelp: [
                    '',
                    $T('Uncheck to make the attendance free of charge without changing the price'),
                    $T('Price for attending the event'),
                    $T('Maximum amount of participants on the event'),
                    '',
                    $T('Limit of accompanying persons a participant can bring'),
                    $T('Whether accompanying persons have to pay attendance or not')
                ],

                actions: [
                    'remove',
                    ['cancel', $T('Cancel this event'),'#tab-canceledEvent','icon-disable']
                ],

                colModel: [
                        {
                           name:'caption',
                           index:'caption',
                           align: 'center',
                           width:140,
                           editoptions:{size:"25",maxlength:"50"},
                           editable: true,
                           edittype: "text"
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
                           name:'placesLimit',
                           index:'placesLimit',
                           align: 'center',
                           sortable:false,
                           width:80,
                           editable: true,
                           edittype: "text",
                           editoptions:{size:"5",maxlength:"20"}
                        },
                        {width: 20},
                        {
                           name: 'maxPlace',
                           index: 'maxPlace',
                           align: 'center',
                           className: 'accompanying-col',
                           width: 60,
                           editable: true,
                           edittype: "int",
                           editoptions: {size:"6", maxlength:"20"}
                        },
                        {
                           name:'pricePerPlace',
                           index:'pricePerPlace',
                           width:80,
                           editable: true,
                           align: 'center',
                           className: 'accompanying-col',
                           defaultVal : false,
                           edittype:'bool_select'
                        }
                  ]
            };

            scope.dialogs.config.canceledTable = {
                sortable: false,
                colNames:[$T("Event name"), $T("Reason for cancellation")],
                actions: ['remove', ['uncancel', $T('Uncancel this event'),'#tab-editEvents','icon-checkmark']],
                colModel: [
                        {
                            index:'caption',
                            align: 'left',
                            width:160,
                            editoptions:{size:"30",maxlength:"50"},
                            editable: false
                        },
                        {
                            name:'reason',
                            index:'cancelledReason',
                            width:250,
                            editoptions:{size:"30",maxlength:"50"},
                            editable: true,
                            edittype: 'text'
                        }

                     ]
            };
        }
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

                _.each($scope.section.items, function (item, ind) {
                    $scope.formData.items[ind] = angular.copy(item);
                });

                $scope.tabSelected = $scope.config.tabs[0].id;
            };

            $scope.addItem = function () {
                 $scope.formData.items.push({id:'isNew', cancelled: false});
            };
        },

        link: function(scope) {
            scope.getTabTpl = function(section_id, tab_type) {
                return url.tpl('sections/dialogs/{0}-{1}.tpl.html'.format(section_id, tab_type));
            };
        }
    };
});

ndRegForm.filter('possibleDeparture', function () {
    return function (departure, scope) {
        if (scope.input.arrival !== undefined) {
            var arrival = moment(scope.input.arrival, 'DD/MM/YYY');
            var possibleDepartures = {};
            _.each(scope.section.departureDates, function(value, key) {
                var departure = moment(key, 'DD/MM/YYY');
                if(arrival.isBefore(departure) || arrival.isSame(departure)) {
                    possibleDepartures[key] = value;
                }
            });
            return possibleDepartures;
        } else {
            return scope.section.departureDates;
        }

    };
});
