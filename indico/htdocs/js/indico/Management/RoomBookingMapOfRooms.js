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

function aspectListNothing(data, func) {
    each(data, function() {
        func(true);
    });
}

function singleAspectNothing(user, func) {
    func(true);
}

/**
 * Creates an aspect creation / edit pop-up dialog.
 * @param {String} title The title of the popup.
 * @param {Object} aspectData A WatchObject that has to have the following keys/attributes:
 *                          id, name, centerLatitude, centerLongitude, topLeftLatitude, topLeftLongitude,
 *                          bottomRightLatitude, bottomRightLongitude, zoomLevel, defaultOnStartup.
 *                          Its information will be displayed as initial values in the dialog.
 * @param {Function} action A callback function that will be called if the aspect presses ok.
 *                          The function will be passed a WatchObject with the new values.
 */
type("MapAspectDataPopup", ["ExclusivePopupWithButtons"],
    {
        param: function(aspectData, label, propertyName) {
            var edit = Html.edit({style: {width: '300px'}});
            var accessor = aspectData.accessor(propertyName);
            this.parameterManager.add(edit, 'text', false);
            var binding = $B(edit, accessor);
            return [$T(label), binding];
        },

        draw: function() {
            var aspectData = this.aspectData;
            var self = this;
            self.parameterManager = new IndicoUtil.parameterManager();

            var form = IndicoUtil.createFormFromMap([
                this.param(aspectData, 'Name', 'name'),
                this.param(aspectData, 'Center latitude', 'centerLatitude'),
                this.param(aspectData, 'Center longitude', 'centerLongitude'),
                this.param(aspectData, 'Top-left latitude', 'topLeftLatitude'),
                this.param(aspectData, 'Top-left longitude', 'topLeftLongitude'),
                this.param(aspectData, 'Bottom-right latitude', 'bottomRightLatitude'),
                this.param(aspectData, 'Bottom-right longitude', 'bottomRightLongitude'),
                this.param(aspectData, 'Zoom level', 'zoomLevel'),
                [$T('Default on start-up'), $B(Html.checkbox({}), aspectData.accessor('defaultOnStartup'))]
            ]);

            return this.ExclusivePopupWithButtons.prototype.draw.call(this, form);
        },

        _getButtons: function() {
            var self = this;
            return [
                [$T('Save'), function() {
                    self.action(self.aspectData, function() {
                        self.close();
                    });
                }],
                [$T('Cancel'), function() {
                    self.close();
                }]
            ];
        }
    },
    function(title, aspectData, action) {
        this.aspectData = aspectData;
        this.action = action;
        this.ExclusivePopupWithButtons(title);
    }
);

/**
 * Creates a list of aspects. Each aspect can be edited or removed.
 * It inherits from ListWidget who in turn inherits from WatchObject, so the usual WatchObject
 * methods (get, set) can be used on it. For example 'set' can be used to initialize the list.
 * This means that the aspects are stored with their id's as keys.
 * @param {String} style The class of the ul that will contain the aspects.
 * @param {Boolean} allowEdit. If true, each aspect will have an edit button to change their data.
 * @param {Function} editProcess. A function that will be called when a aspect is edited. The function
 *                                will be passed the new data as a WatchObject.
 */
type("MapAspectListWidget", ["ListWidget"],
     {
         _drawItem: function(aspect) {
             var self = this;
             var aspectData = aspect.get();

             var editButton = Widget.link(command(function() {
                 var editPopup = new MapAspectDataPopup(
                     'Change map aspect data',
                     aspectData.clone(),
                     function(newData, suicideHook) {
                         if (editPopup.parameterManager.check()) {
                             //  editProcess will be passed a WatchObject representing the aspect.
                             self.editProcess(aspectData, function(result) {
                                 if (result) {
                                     aspectData.update(newData.getAll());
                                     if (!exists(newAspect.get('defaultOnStartup'))) {
                                         newAspect.set('defaultOnStartup', false);
                                     }
                                     if (!startsWith(aspectData.get('id'), 'newAspect')) {
                                         aspectData.set('id', 'edited' + aspectData.get('id'));
                                     }
                                 }
                             }, newData);
                             suicideHook();
                         }
                     }
                 );
                 editPopup.open();
             }, IndicoUI.Buttons.editButton()));

             var removeButton =
                 Widget.link(command(function() {
                             // removeProcess will be passed a WatchObject representing the aspect.
                             self.removeProcess(aspectData, function(result) {
                                     if (result) {
                                         self.set(aspect.key, null);
                                     }
                                 });

             }, IndicoUI.Buttons.removeButton()));

             var buttonDiv = Html.div({style: {cssFloat: "right", paddingRight: pixels(10)}});

             buttonDiv.append(editButton) ;
             buttonDiv.append(removeButton);

             var b1 = $B(Html.span(), aspectData.accessor('name'));
             var b2 = $B(Html.span(), aspectData.accessor('defaultOnStartup'), function(x) {return x ? ' (' + $T('Default') + ')' : ''});

             var aspectName = Html.span({}, b1, b2);

             return Html.span({}, buttonDiv, aspectName);
         }
     },

     function(style, editProcess, removeProcess) {

         this.style = any(style, "UIAspectsList");
         this.editProcess = any(editProcess, singleAspectNothing);
         this.removeProcess = any(removeProcess, singleAspectNothing);

         this.ListWidget(style);
     }
    );


/**
 * Creates a form field with a list of aspects.
 */
type("MapAspectListField", ["IWidget"], {

    getAspects: function() {
        return $L(this.aspectList);
    },

    clear: function() {
        this.aspectList.clearList();
    },

    draw: function() {
        var self = this;

        var select;
        var buttonDiv = Html.div({style:{marginTop: pixels(10)}});

        var addNewAspectButton = Html.input("button", {style:{marginRight: pixels(5)}}, $T('Add Map Aspect') );

        addNewAspectButton.observeClick(function(){

            var newAspectId = self.newAspectCounter++;
            var newAspect = $O({'id': newAspectId});

            var newAspectPopup = new MapAspectDataPopup(
                $T('New map aspect'),
                newAspect,
                function(newData, suicideHook) {
                    if (newAspectPopup.parameterManager.check()) {
                        newAspect.update(newData.getAll());
                        if (!exists(newAspect.get('defaultOnStartup'))) {
                            newAspect.set('defaultOnStartup', false);
                        }
                        self.newProcess(newAspect, function(result) {
                            if (result) {
                                self.aspectList.set(newAspectId, newAspect);
                            }
                        });
                        suicideHook();
                    }
                }
            );
            newAspectPopup.open();
        });
        buttonDiv.append(addNewAspectButton);

        return Widget.block([Html.div(this.aspectDivStyle,this.aspectList.draw()), buttonDiv]);

    }
},
    function(aspectDivStyle, aspectListStyle, initialAspects, newProcess, editProcess, removeProcess) {
        var self = this;
        this.aspectList = new MapAspectListWidget(aspectListStyle, editProcess, removeProcess);
        if (initialAspects.length > 0) {
            this.newAspectCounter = initialAspects[initialAspects.length - 1].id + 1;
        } else {
            this.newAspectCounter = 0;
        }
        this.aspectDivStyle = any(aspectDivStyle, "UIAspectsListDiv");

        if (exists(initialAspects)) {
            each(initialAspects, function(aspect){
                self.aspectList.set(aspect.id, $O(aspect));
            });
        }

        this.newProcess = any(newProcess, aspectListNothing);
     }
);
