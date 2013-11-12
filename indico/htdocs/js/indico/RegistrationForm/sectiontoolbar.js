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

ndRegForm.directive("ndSectionToolbar", function(url) {
    return {
        replace: true,
        templateUrl: url.tpl('sectiontoolbar.tpl.html'),
        controller: 'SectionCtrl',
        scope: {
            section: '=',
            buttons: '=',
            dialogs: '=',
            fieldtypes: '=',
            state: '='
        },

        link: function(scope) {
            scope.openConfig = function() {
                scope.dialogs.config.open = true;
            };

            scope.toggleCollapse = function(e) {
                scope.state.collapsed = !scope.state.collapsed;
            };
        }
    };
});

ndRegForm.directive('ndFieldPicker', function($http, $compile, $templateCache, url) {
    return {
        link: function(scope, element) {
            $http.get(url.tpl('fieldpicker.tpl.html'), {cache: $templateCache})
                .success(function(template) {
                    var content = $compile(template)(scope);

                    element.qtip({
                        content: {
                            title: {
                                text: $T('Add new field')
                            },
                            text: content
                        },

                        position: {
                            my: 'top center',
                            at: 'bottom center'
                        },

                        show: {
                            event: 'click',
                            solo: true,
                            modal: {
                                on: true
                            }
                        },

                        hide: {
                            event: 'unfocus click',
                            fixed: true
                        },

                        style: {
                            classes: 'regFormAddField ui-tooltip-addField',
                            width: '267px',
                            padding: '20px',
                            name: 'light'
                        },

                        events: {
                            render: function(event, api) {
                                $(api.elements.content).on('click', 'a', function() {
                                    api.hide();
                                });
                            }
                        }
                    });
                });


                // TODO: delete this backbone implementation when replicated new field creation
                // events: {
                //     render: function(event, api) {
                //         $('.regFormAddFieldEntry', this).bind('click', function(event,ui) {
                //             var newFieldType = $(event.target).closest('.regFormAddFieldEntry').data('fieldType').split('-');
                //             var field = {
                //                 input   : newFieldType[0],
                //                 caption : '',
                //                 values  : {}
                //             };
                //             if(newFieldType[1]){
                //                 field.values.inputType = newFieldType[1];
                //             }
                //             self._createField(sectionId, field);
                //         });
                //     }
                // }
            // });
        }
    };
});
