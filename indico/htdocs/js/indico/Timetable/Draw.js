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

type("TimetableBlockBase", [],
     {
        truncateTitle: function(numChars, title) {
            if (numChars >= title.length) {
                return title;
            }

            if (numChars < 0) {
                // Never truncate more than the length of  the string
                if (-numChars >= title.length) {
                    return title;
                }

                // Since we add 3 periods in the end truncating 3 or less chars
                // doen't result in shortening the string. Force it to be <= -4
                if (numChars >= -3) {
                    numChars = -4;
                }

                numChars = title.length + numChars;
            }

            title = title.substring(0, numChars) + "...";
            return title;
        },

         openPopup: function(event) {
             var self = this;
             self.popupActive = true;
             self.div.dom.style.cursor = 'default';
             var cursor = getMousePointerCoordinates(event);

             this.popup = self._drawPopup();

             this.popup.open(cursor.x, cursor.y);
         },

         closePopup: function() {
             var self = this;

              // If popup not open shown do nothing
             if (!self.popupActive) {
                 return;
             }

             this.popup.close();
         },

         createMaterialMenu: function(material, triggerElement, closeHandler) {
             var sections = {};
             each(material, function(value) {
                 var section = value.title;
                 var menuItems = {};
                 sections[section] = {content: menuItems, description: value.description };
                 each(value.resources, function(item) {
                     var name = item.name;
                     // set the URL instead of the title, if there's no title
                     menuItems["material" + item.url] = {
                         action: item.url,
                         display: name ? name : item.url,
                         description: item.description};
                 });
             });
             return new SectionPopupMenu(sections, [triggerElement], null, null, true, closeHandler);
         },

         getMaterialMenu: function (materials) {
             var root = $('<ul class="material_list"/>');
             each(materials, function(material) {
                 var resources = $('<ul class="resource_list"/>');
                 each(material.resources, function(resource) {
                     var resource_html = $('<li/>').append(
                         $('<a/>').attr('href', resource.url).text(
                             resource.name ? resource.name : resource.url));
                     resources.append(resource_html);
                 });
                 var material_html = $('<li/>').append($('<h3/>').append(material.title), resources);
                 root.append(material_html);
             });
             return root;
         },

         createMaterialButton: function(material) {
             var self = this;

             var button = Html.div('timetableBlockMaterial');
             button.observeClick(function(e) {
                 stopPropagation(e);
                 self.closePopup();
                 // use this style as long as the menu is open
                 button.dom.className = "timetableBlockMaterial timetableBlockMaterialActive";
                 $(".timetableBlockMaterialActive").qtip({
                         content: {
                             text: self.getMaterialMenu(material)
                         },
                         show: {
                             event: 'click'
                         },
                         hide: {
                             event: 'unfocus'
                         },
                         position: {
                             my: 'top right',
                             at: 'bottom left'
                         },
                         events: {
                             hide: function(event, api) {
                                 // Restores the button style when menu is closed
                                 button.dom.className = "timetableBlockMaterial";
                             }
                         },
                         style: {
                             classes: 'material_tip'
                         }
                 });
                 $(".timetableBlockMaterialActive").qtip().show();
             });

             return button;
         },

         _getRightSideDecorators: function() {
             return Html.span({});
         },

         _formatConveners: function(conveners) {
             if (conveners) {
                 return translate(
                     conveners,
                     function(conv) {
                         return conv.name;
                     }).join(', ');
             } else {
                 return '';
             }
         }

     },
     function(timetable){

         this.timetable = timetable;
         this.popupActive = false;
         this.popupAllowClose = true;
     }
);

type("TimetableBlockNormal", ["TimetableBlockBase"],
        {
            _getTitle: function(){
                var title = this.eventData.title;

                if (this.eventData.slotTitle && this.eventData.slotTitle !== "") {
                    title += ": " + this.eventData.slotTitle;
                }
                return title;
            },

            _blockDescription: function(block, event) {
                var self = this;

                this.titleDiv = Html.div({className: 'timetableBlockTitle', style: {fontWeight: this.eventData.fontWeight}}, this._getTitle());

                this.titleWrapper = Html.div({}, this._getRightSideDecorators(), this.titleDiv);

                this.div = Html.div({style: { width: '100%', height: '100%'}}, this.titleWrapper);

                if (this.compactMode) {
                    this.timeDiv = Html.div('timetableBlockTimeDiscreet', this.eventData.startDate.time.substring(0,5) +' - '+ this.eventData.endDate.time.substring(0,5));
                    this.div.insert(this.timeDiv);
                } else {
                    if (this.eventData.startDate.time == this.eventData.endDate.time) {
                        this.timeDiv = Html.div({className: 'timetableBlockTime'}, this.eventData.startDate.time.substring(0,5));
                    } else {
                        this.timeDiv = Html.div({className: 'timetableBlockTime'}, this.eventData.startDate.time.substring(0,5) +' - '+ this.eventData.endDate.time.substring(0,5));
                    }

                    this.locationDiv  = Html.div('timetableBlockLocation');
                    var addComma = false;
                    if (this.eventData.room && this.timetable.getTimetableDrawer().layoutChooser.get().shouldShowRoom()) {
                        this.locationDiv.append(this.eventData.room);
                        addComma = true;
                    }
                    if (this.eventData.location) {
                        this.locationDiv.append(addComma ? ', ' : '');
                        this.locationDiv.append(this.eventData.location);
                    }

                    // If it's a contribution add the speakers information
                    if (self.eventData.presenters && self.eventData.presenters.length > 0) {
                        this.presentersDiv = Html.div({className: 'timetableBlockPresenters'});
                        this.presentersDiv.append(self.eventData.presenters[0].name);
                        if (self.eventData.presenters.length > 1) {
                            this.presentersDiv.append($T(' et al.'));
                        }
                        this.titleWrapper.insert(this.presentersDiv);
                    }

                    // Add material menu
                    if (!self.managementActions && self.eventData.material && self.eventData.material.length > 0) {
                        this.titleWrapper.insert(this.createMaterialButton(this.eventData.material));
                    }

                    //this.titleWrapper.insert(this.createManageButton());

                    //Add converner's info
                    this.convenerDiv = Html.div(
                        'timetableBlockConvener',
                        self._formatConveners(this.eventData.conveners));

                    this.div.append(this.convenerDiv);
                    this.div.append(this.timeDiv);
                    this.div.append(this.locationDiv);
                }

                return this.div;
            },

            redraw: function() {
                this.block.clear();
                this.block.set(this._blockDescription());
            },

            draw: function(leftPos, width) {
                var self = this;

                this.leftPos = leftPos;
                this.width = width;
                this.height = this.blockData.end-this.blockData.start-3;
                this.topPos = this.blockData.start;

              //To disable dragging while outside management mode
              var blockIsDraggable = ((this.detailLevel != "session") && (this.detailLevel != "contribution"));

              var additionalClasses = 'ui-draggable ui-resizable';

              var contributionClass = (blockIsDraggable) ? 'timetableContribution '+additionalClasses : 'timetableContribution';
              var breakClass = (blockIsDraggable) ? 'timetableBreak '+additionalClasses : 'timetableBreak';
              var sessionClass = (blockIsDraggable) ? 'timetableSession '+additionalClasses : 'timetableSession';
              var classTable = {
                'Session': sessionClass,
                'Contribution': contributionClass,
                'Break': breakClass
             };

                $(this.block.dom).css({
                    position: 'absolute',
                    top: pixels(this.topPos),
                    height: pixels(this.height),
                    'background-color': this.eventData.color,
                    color: this.eventData.textColor,
                    left: pixels(this.leftPos),
                    width: pixels(this.width-3),
                    'border-bottom-style': this.blockData.unfinished?'dashed':''
                });

                $(this.block.dom).addClass('timetableBlock ' +
                                           classTable[this.eventData.entryType]);

                this.block.set(this._blockDescription());

               // This is a special case, when users shows contribution details it doesn't
               // apply to poster sessions. Instead add some grpahical elements to indicate
               // that this sessions contains several contributions.
               if (this.detailLevel == 'contribution' && this.eventData.isPoster && this.height > 30) {

                   var pileDiv = this.createPileEffect();
                   pileDiv.dom.onmouseover = function(){ };
                   var numContribs = 0;
                   each(this.eventData.entries, function(value, key) {
                       if (value.entryType == 'Contribution') {
                           numContribs++;
                       }
                   });
                   pileDiv.dom.onmouseover = function(event) {
                       if (self.popupActive) {
                           return;
                       }
                       IndicoUI.Widgets.Generic.tooltip(pileDiv.dom, event, "<div style='padding:3px'>" +
                           $T('This poster session has ') + numContribs + $T(' contribution(s).') + "<br / >" +
                           $T('Please click for more information.') + "</div>");
                   };
               }

               if (!self.printableVersion) {
                   $(this.block.dom).click(function(e) {
                       if (!self.timetable.getTimetableDrawer().eventsDisabled) {
                           $(this).trigger('tt_block.balloon', e);
                       }
                   });
                   highlightWithMouse(this.div, this.block);
                   showWithMouse(this.div, this.arrows);
               }
               return this.block;
            },

            _postDraw: function() {
            },

            postDraw: function(hook) {
                var self = this;
                var title = this._getTitle();

                // Returns the total height of the divs in the block
                var contentHeight = function() {
                    var h = 0;
                    if (!self.compactMode) {
                        var locationHeight = self.locationDiv.dom.style.display != 'none' ? self.locationDiv.dom.offsetHeight : 0;
                        var timeHeight = self.timeDiv.dom.style.display != 'none' ? self.timeDiv.dom.offsetHeight : 0;

                        h = Math.max(locationHeight, timeHeight);
                    }

                    return self.titleDiv.dom.offsetHeight + h;
                };
                var contentWidth = function() {
                    return self.timeDiv.dom.offsetWidth + self.locationDiv.dom.offsetWidth + 2*self.margin;
                };

                var parentDivHeight = this.div.dom.parentNode.offsetHeight;
                var parentDivWidth = this.div.dom.parentNode.offsetWidth;

                // If nothing has been drawn do nothing
                if (!parentDivHeight) {
                    return;
                }

                // If no space for location and time info then hide the divs
                if (this.compactMode && parentDivWidth < 200) {
                    this.timeDiv.dom.style.display = 'none';
                }
                if (!this.compactMode) {
                    var locationMaxWidth = parentDivWidth  - 20;

                    // Hide the time if there is not enough space
                    if (this.timeDiv.dom.offsetWidth + 8 >= parentDivWidth) {
                        this.timeDiv.dom.style.display = 'none';
                    }
                    // If at this point the width of the content fits but the height of the content
                    // is bigger than the height of the parent div, it is probably because the
                    // location takes more than one line in the block. For this edge case we force
                    // the hiding of the time div so that the location div takes only one line.
                    else if (contentWidth() >= parentDivWidth || contentHeight() >= parentDivHeight) {
                        this.timeDiv.dom.style.display = 'none';
                    } else {
                        locationMaxWidth -= this.timeDiv.dom.offsetWidth;
                    }

                    this.locationDiv.dom.style.maxWidth = locationMaxWidth > 0 ?
                        pixels(locationMaxWidth) : '0px';

                    // After modifying the location width, the content of the location might be expaneded
                    // on two lines. Therefore, we should re-check if there is enought space for the time.
                    if (contentWidth() >= parentDivWidth || contentHeight() >= parentDivHeight) {
                        this.timeDiv.dom.style.display = 'none';
                        this.locationDiv.dom.style.maxWidth = pixels(parentDivWidth  - 20);
                    }

                    // Presenters information should not take more than half of the space of the block
                    if (this.presentersDiv && this.presentersDiv.dom.offsetWidth > parentDivWidth / 2) {
                        this.presentersDiv.dom.style.display = 'none';
                    }

                    // Convener information should not take more than half of the space of the block
                    // if not truncate the string.
                    if (this.convenerDiv && this.convenerDiv.dom.offsetWidth > parentDivWidth / 2) {
                        var newLength = parentDivWidth / 2 / this.convenerDiv.dom.offsetWidth * this.convenerDiv.get().length;
                        this.convenerDiv.set(this.truncateTitle(newLength - 1, this.convenerDiv.get()));
                    }

                    // If checks if height of the cell is enough to paint convener's name.
                    if (this.convenerDiv && this.convenerDiv.dom.offsetHeight + contentHeight() > parentDivHeight) {
                        this.convenerDiv.dom.style.display = 'none';
                    }
                }

                // If content height <= div height then nothing needs to be done
                if (contentHeight() > parentDivHeight) {
                    // Try to remove the location info, and set title font weight to non bold,
                    // if this works, then we're done. Otherwise, start to truncate the title as well.
                    if (this.timeDiv.dom.style.display == 'none') {
                        this.locationDiv.dom.style.display = 'none';
                    }

                    if (contentHeight() > parentDivHeight) {
                        // Calculates the the width of title, presenters and possible arrows
                        var topContentWidth = function() {
                            var width = 2 * self.margin;
                            if(self.titleDiv)
                                width += self.titleDiv.dom.offsetWidth;
                            if(self.presentersDiv)
                                width += self.presentersDiv.dom.offsetWidth;

                            self._postDraw();
                            return width;
                        };

                        // Truncate title based on a ratio: div height / content height
                        title = this.truncateTitle(Math.ceil(title.length * ((parentDivHeight) / contentHeight())), title);
                        this.titleDiv.set(title);
                        //String will be shorten by the value of 'step'
                        var step = 2;
                        //Truncating the title since it can be displayed in a single line
                        // title !== "..." avoids the endless loop
                        while (title !== "..." && contentHeight() > parentDivHeight && topContentWidth() > parentDivWidth * 0.8) {
                            title = this.truncateTitle(-step, title);
                            this.titleDiv.set(title);
                        }
                    }
                }

                this._postDraw();
                return null;
            },
            createPileEffect: function() {
                var self = this;
                var pileEffect = Html.div({style: { position: 'absolute', top: '3px', left: '0', width: pixels(this.width-3)}}, Html.div({},
                        Html.div('timetableBlock timetableBlockPileEffect'),
                        Html.div('timetableBlock timetableBlockPileEffect'),
                        Html.div('timetableBlock timetableBlockPileEffect')
                    ));

                this.div.insert(pileEffect);
                this.titleWrapper.dom.style.paddingTop = '20px';
                if (this.compactMode) {
                    this.timeDiv.dom.style.paddingTop = '20px';
                }

                return pileEffect;
            },
            setColors: function(textColor, bgColor) {
                this.block.dom.style.backgroundColor = bgColor;
                this.block.dom.style.color = textColor;
            }

        },
     function(timetable, eventData, blockData, compactMode, printableVersion, detailLevel){
         this.TimetableBlockBase(timetable);
         this.compactMode = compactMode;
         this.eventData = eventData;
         this.blockData = blockData;
         this.margin = TimetableDefaults.blockMargin;
         this.printableVersion = printableVersion;
         this.detailLevel = detailLevel;
         this.arrows = Html.span({});
         this.block = Html.div({});

         var self = this;
         $(this.block.dom).bind('tt_block.balloon', function(event, originalEvent){
             if (!self.popupActive) {
                 self.openPopup(originalEvent);
             }
         })
        }
   );


type("TimetableBlockWholeDayBase", ["TimetableBlockBase"],
        {
            _blockDescription: function(block, event) {
                var self = this;

                this.titleDiv = Html.div({className: 'timetableBlockTitle', style: {fontWeight: this.eventData.fontWeight}}, this.eventData.title);
                this.titleWrapper = Html.div({}, this._getRightSideDecorators(), this.titleDiv);

                this.div = Html.div({style: { width: '100%', height: '100%'}}, this.titleWrapper);

                this.timeDiv = Html.div('timetableBlockTimeDiscreet', this.eventData.startDate.time.substring(0,5) +' - '+ this.eventData.endDate.time.substring(0,5));
                this.div.insert(this.timeDiv);

                // Add material menu
                if (self.eventData.material && self.eventData.material.length > 0) {
                    this.titleWrapper.insert(this.createMaterialButton(this.eventData.material));
                }

                return this.div;
            },

            draw: function() {
                var self = this;

                var classTable = {
                    'Session': 'timetableSession',
                    'Contribution': 'timetableContribution ',
                    'Break': 'timetableBreak '
                };

                var block = Html.div({style: {
                            backgroundColor: this.eventData.color,
                            color: this.eventData.textColor,
                            maxHeight : '30px',
                            margin : '2px 0',
                            overflow : 'hidden'
                        },
                        className: 'timetableBlock ' + classTable[this.eventData.entryType]
                    }, this._blockDescription()
                );

                if (!self.printableVersion) {
                    block.dom.style.cursor = 'pointer';
                  block.observeClick(function(e) { self.openPopup(e); });
                    highlightWithMouse(this.div, block);
                    showWithMouse(this.div, this.arrows);
                }

                return block;
            },
            postDraw: function() {

            }
        },
     function(timetable, eventData, blockData){
         this.TimetableBlockBase(timetable);

         this.eventData = eventData;
         this.blockData = blockData;
         this.margin = TimetableDefaults.blockMargin;
         this.arrows = Html.span({});
     }
   );


type("TimetableBlockDisplayMixin",[],
     {
         _drawPopup: function() {
             var self = this;

             return new TimetableBlockPopup(
                 this.timetable,
                 this.eventData,
                 this.div,
                 function() {
                     self.div.dom.style.cursor = 'pointer';
                     self.popupActive = false;
                     return self.popupAllowClose;
                 },
                 function(color) {
                     var parent = self.div.getParent();
                     parent.setStyle('backgroundColor', color);
                 }
             );
         }

     });

type("TimetableBlockManagementMixin", ["DragAndDropBlockMixin"],
     {
         _drawPopup: function() {

             var self = this;
             return new TimetableBlockPopupManagement(
                 this.timetable,
                 this,
                 this.eventData,
                 this.div,
                 function() {
                         self.div.dom.style.cursor = 'pointer';
                         self.popupActive = false;
                         return self.popupAllowClose;
                     },
                 this.managementActions);
         },

         _getRightSideDecorators: function()
         {
             return this.arrows;
         }

     },
     function() {
         var arrowUp = Html.img({src: imageSrc('arrow_up'), title: $T('Move up')});
         var arrowDown = Html.img({src: imageSrc('arrow_down'), style:{paddingLeft: '5px'}, title: $T('Move down')});

         var self = this;

         arrowUp.observeClick(
             function(event) {
                 self.managementActions.moveEntryUpDown(self.eventData, true);
                 if (event.stopPropagation) {
                     event.stopPropagation();
                 } else {
                     event.cancelBubble = true;
                 }
                 return false;
             });

         arrowDown.observeClick(
             function(event) {
                 self.managementActions.moveEntryUpDown(self.eventData, false);
                 if (event.stopPropagation) {
                     event.stopPropagation();
                 } else {
                     event.cancelBubble = true;
                 }
                 return false;
             });


         this.arrows = Html.div({},
                             Html.div({className: "ttentryArrowsBackground"}),
                             Html.div({className: "ttentryArrows"}, arrowUp, arrowDown));
         this.DragAndDropBlockMixin();
     });

type("TimetableBlockWholeDayDisplay", ["TimetableBlockWholeDayBase", "TimetableBlockDisplayMixin"],
     {
     },
     function(timetable, eventData, blockData) {
         this.TimetableBlockWholeDayBase(timetable, eventData, blockData);
     });

type("TimetableBlockWholeDayManagement", ["TimetableBlockWholeDayBase", "TimetableBlockManagementMixin"],
     {
     },
     function(timetable, eventData, blockData, managementActions) {
         this.TimetableBlockWholeDayBase(timetable, eventData, blockData);
         this.managementActions = managementActions;
         this.TimetableBlockManagementMixin();

         this._getRightSideDecorators = TimetableBlockManagementMixin.prototype._getRightSideDecorators;
         this._postDraw = TimetableBlockManagementMixin.prototype._postDraw;
     });


type("TimetableBlockNormalDisplay", ["TimetableBlockNormal", "TimetableBlockDisplayMixin"],
     {
     },
     function(timetable, eventData, blockData, compactMode, printableVersion, detailLevel)
     {
         this.TimetableBlockNormal(timetable, eventData, blockData, compactMode, printableVersion, detailLevel);
     });

type("TimetableBlockNormalManagement", ["TimetableBlockNormal", "TimetableBlockManagementMixin"],
     {
         _getTitle: function(){
             var title = this.TimetableBlockNormal.prototype._getTitle.call(this);

             if (this.eventData.entryType == "Session") {
                 return this.eventData.sessionId + " - " + title;
             } else if (this.eventData.entryType == "Contribution") {
                 return this.eventData.contributionId + " - " + title;
             }

             return title;
         }
     },
     function(timetable, eventData, blockData, compactMode, printableVersion, detailLevel, managementActions)
     {
         this.TimetableBlockNormal(timetable, eventData, blockData, compactMode, printableVersion, detailLevel);
         this.managementActions = managementActions;
         this.TimetableBlockManagementMixin();

         this._getRightSideDecorators = TimetableBlockManagementMixin.prototype._getRightSideDecorators;
         this._postDraw = TimetableBlockManagementMixin.prototype._postDraw;
     });

type("TimetableBlockPopup", ["BalloonPopup", "TimetableBlockBase"], {
    createContent: function() {
       var self = this;

        var div = Html.div({className: 'timetablePopup', style: {width: pixels(this.popupWidth)}});

        // Truncate title if longer than 90 chars
        var title = self.eventData.title;
        if (title.length > 90) {
            title = title.substring(0, 87) + '...';
        }

        var titleDiv = Html.div({className: 'title'}, title);
        div.append(titleDiv);


        if (self.eventData.entryType != 'Session' &&
            exists(self.eventData.sessionSlotId)) {
            var session = self.timetable.eventInfo.sessions[self.eventData.sessionId];
            var belongsToDiv = Html.div(
                'balloonSubtitle',
                $T('inside'),' ',
                Html.span({style:{fontWeight:'bold'}},session.title));
            div.append(belongsToDiv);
        }

        var menuBar = this._getMenuBar();
        div.append(menuBar);

        var infoDiv = this._getGeneralInfo();
        div.append(infoDiv);

        var contributions = this._getContributionInfo();
        if (contributions) {
            div.append(contributions);
            div.dom.style.width = pixels(this.popupWidth + 50);
        }

        return div;
    },

    _getRoomLocationInfo: function() {
        var roomLocationInfo = Html.div({});

        if (this.eventData.room) {
            roomLocationInfo.append(Html.div('roomPopupTitle', 'Room: '));
            roomLocationInfo.append(this.eventData.room);
            roomLocationInfo.append(Html.br());
        }

        if (this.eventData.location) {
            roomLocationInfo.append(Html.div('roomPopupTitle', 'Location: '));
            roomLocationInfo.append(this.eventData.location);
            roomLocationInfo.append(Html.br());
        }
        return roomLocationInfo;
    },

    _getTimeLocationInfo: function() {
      return Html.div({}, this._getTime(), this._getRoomLocationInfo());
    },

    _getGeneralInfo: function() {
        var self = this;

        var infoContentDiv = Html.div({className: 'timetablePopupInfoContent'});

        infoContentDiv.append(this._getTimeLocationInfo());

        if(self.eventData.conveners &&
           self.eventData.conveners.length > 0)
        {
            var convenersDiv = Html.div({className: 'timeLocationDiv'});
            //Using plural if there are multiple conveners
            convenersDiv.append(
                Html.div('roomPopupTitle',
                            (self.eventData.conveners.length > 1)?
                            $T('Conveners'):
                            $T('Convener'), ': '));

            convenersDiv.append(self._formatConveners(this.eventData.conveners));
            convenersDiv.append(Html.br());
            infoContentDiv.append(convenersDiv);
        }

        // If it's a contribtion add speaker information
        if (self.eventData.entryType == 'Contribution') {
            var speakers = Html.span();
            var i = 0;
            each(self.eventData.presenters, function(p) {
                speakers.append((i++ > 0 ? '; ' : '') + p.name);
                if (p.affiliation && p.affiliation !== '') {
                    speakers.append(Html.em({style: {fontSize: '12px'}}, ' (' + p.affiliation + ')'));
                }
            });
            if (i > 0) {
                infoContentDiv.append(Html.strong({style:{fontStyle: 'normal'}}, 'Presenter(s): '));
                infoContentDiv.append(speakers);
            }
        }

        // Add the description and if it's too long cut it down
        var desc = self.eventData.description;
        if (desc && desc !== '') {
            infoContentDiv.append(Html.span({style: {display: 'block', marginTop: pixels(5)}},
                                  desc.length > 200 ? desc.substr(0, 200) + '...' : desc));
        }

        return Html.div({className: 'timetablePopupInfoWrapper'}, infoContentDiv);
    },

    _getTime: function() {
        return Html.div({className: 'timetablePopupTimeDiv'},
                        this.eventData.startDate.time.substring(0,5) + ' - ' +
                        this.eventData.endDate.time.substring(0,5));
    },

    _getExportPopup: function(method, params){
        var self = this;
        var killProgress = IndicoUI.Dialogs.Util.progress();
           jsonRpc(Indico.Urls.JsonRpcService, method,
                params,
                function(result, error){
                    killProgress();
                    if (exists(error)) {
                        IndicoUtil.errorReport(error);
                    } else {

                        var popup = new ExclusivePopup($T('Export to Calendar'), null, true, true);

                        popup.draw = function() {
                            this.ExclusivePopup.prototype.draw.call(this, result);
                            exportPopups[self.eventData.uniqueId].showContent();
                            exportPopups[self.eventData.uniqueId].showPopup();
                        };
                        popup.open();
                    }
            });
        // Ensure that progress popup is closed for offline conference generation
        killProgress();
    },

    _getMenuBar: function() {
        var self = this;

        // There is only a need for a menu bar when we show contribution or session
        if (self.eventData.entryType != 'Contribution' && self.eventData.entryType != 'Session') {
            return null;
        }

        var bar = Html.div({});
        var url = self.eventData.url;
        var viewLink = Html.a({'href': url}, "View details");
        bar.append(viewLink);

        if (self.eventData.material && self.eventData.material.length > 0) {
            var materialLink = Html.a('dropDownMenu fakeLink', "Material");
            materialLink.observeClick(function(e) {
                var menu = self.createMaterialMenu(self.eventData.material, materialLink);

                var pos = materialLink.getAbsolutePosition();
                menu.open(pos.x + materialLink.dom.offsetWidth + 2, pos.y + materialLink.dom.offsetHeight + 2);
            });
            bar.append("|");
            bar.append(materialLink);
        }


        var exportLink = Html.a('dropDownMenu fakeLink', "Export");
        exportLink.observeClick(function () {
            var menuItems = {};
            var urlParams;
            if (self.eventData.entryType == 'Contribution') {
                urlParams = {
                    contribId: self.eventData.contributionId,
                    confId: self.eventData.conferenceId
                };
                menuItems["PDF"] = {action: self.eventData.pdf, display: $T('PDF')};
                menuItems["Calendar" + self.eventData.uniqueId] = {
                    action: function() {
                        self._getExportPopup("schedule.api.getContribExportPopup", {
                            confId: self.eventData.conferenceId,
                            contribId: self.eventData.contributionId
                        });
                    },
                    display: $T('Calendar')
                };
                menuItems["XML"] = {action: build_url(Indico.Urls.ContribToXML, urlParams), display: $T('XML')};
            } else if (self.eventData.entryType == 'Session') {
                menuItems["PDFtimetable"] = {action: self.eventData.pdf, display: $T('PDF timetable')};
                menuItems["Calendar" + self.eventData.uniqueId] = {
                    action: function() {
                        self._getExportPopup("schedule.api.getSessionExportPopup", {
                            confId: self.eventData.conferenceId,
                            sessionId: self.eventData.sessionId
                        });
                    },
                    display: $T('Calendar')
                };
            }

            this.exportMenu = new PopupMenu(menuItems, [exportLink], null, true, true);
            var pos = exportLink.getAbsolutePosition();
            exportMenu.open(pos.x + exportLink.dom.offsetWidth + 2, pos.y + exportLink.dom.offsetHeight + 2);
        });
        bar.append("|");
        bar.append(exportLink);

        return Html.div('menuBar', bar);
    },

    _getContributionInfo: function() {
        var self = this;

        var contributionsDiv = this._getContributionList(6, true);

        if (!contributionsDiv) {
            return null;
        }

        var detailsLink = Html.div({style: {marginTop: pixels(5), marginLeft: pixels(5)}}, Html.span({className: "fakeLink", style: {fontStyle: 'italic', fontWeight: 'normal'}}, "View contribution list"));
        contributionsDiv.append(detailsLink);

        detailsLink.observeClick(function (e) {
            self.close();
            var contribs = [];
            each(self.eventData.entries, function(value, key) {
                if (value.entryType == 'Contribution') {
                    contribs.push(value);
                }
            });
            var popup = new ContributionsPopup(("Contribution details"),contribs, self.eventData.isPoster, false, function() {self.popupAllowClose = true; return true;}, true);
            popup.open();
        });


        /*
         * A timetable link for viewing the content of a session.
         * Needs some work on the TimetablePopup dialog
         */

        /*timetableLink = Html.div({style: {marginTop: pixels(5), marginLeft: pixels(5)}}, Html.span({className: "fakeLink", style: {fontStyle: 'italic', fontWeight: 'normal'}}, "View timetable"));
        contributionsDiv.append(timetableLink);

        timetableLink.observeClick(function (e) {
            self.close();
            var popup = new TimetablePopup(self.eventData, contribs, function() {self.popupAllowClose = true; return true;});
            popup.open();
        });
        */

        return contributionsDiv;
    },
    /*
     * Builds a list of contributions.
     */
    _getContributionList: function(maxNumContribs, links) {
        var self = this;

        var contributionsDiv = Html.div({className: 'timetablePopupContributions'}, "Contributions");

        var contributions = Html.tbody({});
        var contribs = [];
        each(this.eventData.entries, function(value, key) {
            if (value.entryType == 'Contribution') {
                contribs.push(value);
            }
        });

        if (contribs.length === 0) {
            return null;
        }

        contribs.sort(function(a,b) {
            if (a.startDate.time > b.startDate.time) {
                return 1;
            }
            return -1;
        });
        var i = 0;
        each(contribs, function(value) {
            if (++i <= maxNumContribs) {
                var element = links ? Html.a({
                    href: value.url,
                    style: {fontWeight: 'normal'}},
                    value.title) :
                    Html.span({}, value.title);
                contributions.append(Html.tr({}, Html.td('timetablePopupContributionTime', self.eventData.r || self.eventData.isPoster ? '' : value.startDate.time.substr(0,5)),
                                             Html.td('timetablePopupContributionTitle', element)));
            }
        });
        if (i > maxNumContribs) {
            contributions.append(Html.tr({}, Html.td({}), Html.td({}, Html.span({style: {fontSize: '12px', fontWeight: 'normal', fontStyle: 'italic', color: '#444444'}}, '' + (i - maxNumContribs) + ' more contribution(s)...'))));
        }
        contributionsDiv.append(Html.table({style: {marginTop: pixels(5)}}, contributions));

        return contributionsDiv;
    }
    },
     function(timetable, eventData, blockDiv, closeHandler) {
         this.timetable = timetable;
         this.eventData = eventData;
         this.triggerElement = blockDiv;
         this.popupWidth = 300;

         this.BalloonPopup(this.createContent(), blockDiv, closeHandler);
     }
);


type("TimetableBlockPopupManagement", ["TimetableBlockPopup"],
{
        _getTimeLocationInfo: function() {
            var self = this;
            var timeDiv = Html.div('timeLocationDiv', this._getTime());
            var locationDiv = Html.div('timeLocationDiv', this._getRoomLocationInfo());

            var saveButton = Html.input('button', {}, 'Save');
            var cancelButton = Html.input('button', {}, 'Cancel');

            var buttonsDiv = Html.div({style:{textAlign:'center', display:'none', padding:'5px'}}, saveButton, cancelButton);

            saveButton.observeClick(function(){
                self.saveRoomLocationFunction();
                if (self.saveTimeFunction()) {
                    self.close();
                }
            });

            cancelButton.observeClick(function(){
                buttonsDiv.dom.style.display = 'none';
                timeDiv.dom.className = 'timeLocationDiv';
                locationDiv.dom.className = 'timeLocationDiv';
                self.stopEditingTimeFunction();
                self.stopEditingRoomLocationFunction();
            });

            timeDiv.observeClick(function(){
                self.editTimeFunction();
                buttonsDiv.dom.style.display = 'block';
                timeDiv.dom.className = '';
            });

            locationDiv.observeClick(function(){
                self.editRoomLocationFunction();
                buttonsDiv.dom.style.display = 'block';
                locationDiv.dom.className = '';
            });

            return Html.div({}, timeDiv, locationDiv, buttonsDiv);
        },

        _getTime: function() {
            var self = this;

            var timeDiv = Html.div({},
                                   Html.div('roomPopupTitle', 'Duration: '),
                                   this.eventData.startDate.time.substring(0,5) + ' - ' +
                                   this.eventData.endDate.time.substring(0,5),
                                   Html.img({src: imageSrc("edit_16.png")}));

            this.startEndTimeField = IndicoUI.Widgets.Generic.dateStartEndTimeField(
                    this.eventData.startDate.time.substring(0,5),
                    this.eventData.endDate.time.substring(0,5), {style: {width: '50px'}}, {style: {width: '50px'}});

            this.startEndTimeField.accessor.set('date', this.eventData.startDate.date);

            var parameterManager = new IndicoUtil.parameterManager();

            parameterManager.add(this.startEndTimeField.startTimeField, 'time', false);
            parameterManager.add(this.startEndTimeField.endTimeField, 'time', false,
                                 function(value) {
                                     var sTime = translate(parseTime(self.startEndTimeField.startTimeField.get()), zeropad).join('');
                                     var eTime = translate(parseTime(value), zeropad).join('');
                                     if (eTime == sTime &&
                                         self.eventData.entryType == "Break") {
                                         // this is so that we allow
                                         // zero-sized breaks
                                         // do nothing
                                     } else if (eTime <= sTime) {
                                         return "End time should be after start time!";
                                     }
                                 });

            this.saveTimeFunction = function() {
                if (!parameterManager.check()) {
                    return false;
                }

                var startDate = clone(self.eventData.startDate);
                var endDate = clone(self.eventData.startDate);

                startDate.time = self.startEndTimeField.accessor.get('startTime');
                endDate.time = self.startEndTimeField.accessor.get('endTime');

                self.managementActions.editEntryStartEndDate(Util.formatDateTime(startDate, IndicoDateTimeFormats.Server),
                                                             Util.formatDateTime(endDate, IndicoDateTimeFormats.Server),
                                                             self.eventData,
                                                             rescheduleCheckbox.get());

                return true;
            };

            this.editTimeFunction = function() {
                timeEditDiv.dom.style.display = 'block';
                timeDiv.dom.style.display = 'none';
            };

            this.stopEditingTimeFunction = function() {
                timeEditDiv.dom.style.display = 'none';
                timeDiv.dom.style.display = 'block';
                this.startEndTimeField.accessor.set('startTime', this.eventData.startDate.time.substring(0,5));
                this.startEndTimeField.accessor.set('endTime', this.eventData.endDate.time.substring(0,5));
                rescheduleCheckbox.dom.checked = false;
            };

            var rescheduleCheckbox = Html.checkbox({style:{marginRight: '5px', verticalAlign: 'middle'}});

            var timeEditDiv = Html.div({style: {display: 'none'}},
                Html.div('roomVerticalWidgetTitle', 'Duration'),
                Html.div({},self.startEndTimeField.element),
                Html.div({style: {marginTop: '5px'}}, rescheduleCheckbox, $T('Shift later entries')));

            return Html.div({}, timeDiv, timeEditDiv);

        },
        _getMenuBar: function() {
            var self = this;

            var menu = Html.div({className: 'menuBar managementMenuBar'});

            var deleteLink = Html.a('fakeLink', "Delete");
            deleteLink.observeClick(function() {
                self.managementActions.deleteEntry(self.eventData);
                self.close();
            });
            menu.insert(deleteLink);
            menu.insert(" | ");

            var editLink;

            if (self.eventData.entryType == 'Session') {
                // If it's a session the show the edit menu
                editLink = Html.a({className: 'dropDownMenu', style: {fontWeght: 'bold'}}, $T('Edit'));
                var menuItems = {};

                menuItems["blockProperties"] = { action: function() {
                    self.managementActions.editSessionSlot(self.eventData);
                    self.close();
                }, display: $T('Basic edition')};
                if (!self.managementActions.isSessionTimetable) {
                    menuItems["sessionProperties"] = {action: self.managementActions.editEntry(self.eventData), display: $T('Full session edition')};
                    menuItems["sessionProtection"] = {action: self.managementActions.editEntryProtection(self.eventData), display: $T('Edit protection')};
                }

                editLink.observeClick(function() {
                    var menu = new PopupMenu(menuItems, [editLink], 'timetableManagementPopupList', true, true);
                    var pos = editLink.getAbsolutePosition();
                    menu.open(pos.x + editLink.dom.offsetWidth + 2, pos.y + editLink.dom.offsetHeight + 2);
                });

                var addInterval = Html.a('fakeLink', $T("Add block"));
                addInterval.observeClick(function() {
                    self.managementActions.addSessionSlot(self.eventData);
                    self.close();
                });
                menu.insert(addInterval);
                menu.insert(" | ");

            } else if (self.eventData.entryType == 'Contribution') {
                editLink = Html.a({className: 'dropDownMenu', style: {fontWeght: 'bold'}}, $T('Edit'));
                var menuItems = {};
                menuItems['contributionProperties'] = {action: function() {
                    self.managementActions.editContribution(self.eventData);
                    self.close();
                }, display: $T('Basic edition')};
                menuItems["contributionFullEdition"] = {action: self.managementActions.editEntry(self.eventData), display: $T('Full edition')};
                menuItems["contributionProtection"] = {action: self.managementActions.editEntryProtection(self.eventData), display: $T('Edit protection')};
                editLink.observeClick(function() {
                    var menu = new PopupMenu(menuItems, [editLink], 'timetableManagementPopupList', true, true);
                    var pos = editLink.getAbsolutePosition();
                    menu.open(pos.x + editLink.dom.offsetWidth + 2, pos.y + editLink.dom.offsetHeight + 2);
                });
            } else {
                // event is a Break

                editLink = Html.a({
                    className: 'fakeLink',
                    style: {fontWeight: 'bold'},
                    href: '#'
                }, $T("Edit"));

                editLink.observeClick(function() {
                    self.managementActions.editEntry(self.eventData);
                    self.close();
                    return false;
                });
            }
            menu.insert(editLink);


            // Move Entry link, only available for contribs and breaks
            if (self.eventData.entryType != 'Session') {
                menu.insert(" | ");

                var moveEntryLink = Html.a('fakeLink', Html.span({}, $T("Move")));
                moveEntryLink.observeClick(function(){
                  self.close();
                  self.managementActions.moveEntry(self.eventData);
                });

                menu.insert(moveEntryLink);

            }

            if (self.eventData.entryType == 'Session') {
                // Handles the color picker
                var colorPicker = new ColorPicker([], true, this.eventData.color, this.eventData.textColor);
                var colorPickerLink = colorPicker.getLink(function () {
                    self.addNonCloseTriggeringElement(colorPicker.getCanvas());
                    return true;
                });

                colorPicker.observe(function(colors) {
                    self.managementActions.changeSessionColors(self.eventData, colors.bgColor, colors.textColor);
                });
                menu.append(Html.a({}, colorPickerLink));
            }


            return menu;
        },

        _getContributionInfo: function() {
            var self = this;

            if (this.eventData.entryType !== 'Session') {
                return null;
            }

            var contributionsDiv = this._getContributionList(4, false);

            if (!contributionsDiv) {
                contributionsDiv = Html.div({className: 'timetablePopupContributions'}, Html.em({style: {fontWeight: 'normal'}}, $T('This session is empty...')));
            }


            var ttLink = Html.a({className: 'fakeLink'}, "View and edit this block timetable");
            ttLink.observeClick(function() {
                self.managementActions.switchToIntervalTimetable(self.eventData.id);
                self.close();
            });
            contributionsDiv.append(Html.div({style: {marginTop: '10px', fontWeight: 'bold'}}, ttLink));

            return contributionsDiv;
        },

        _getRoomLocationInfo: function() {
            var self = this;
            this._setInfo();
            this._setParentInfo();

            var roomLocationDiv = Html.div({},Html.div('roomPopupTitle', 'Location: '),
                    self.eventData.location, Html.br(), Html.div('roomPopupTitle', 'Room: '),
                    self.eventData.room, Html.img({src: imageSrc("edit_16.png")}), Html.br());

            this.editRoomLocationFunction = function(e){
                roomLocationDiv.dom.style.display = 'none';
                roomEditorDiv.dom.style.display = 'block';
            };

            this.saveRoomLocationFunction = function() {
                self.managementActions.editRoomLocation(self.roomEditor.info.accessor('room').get(),self.roomEditor.info.accessor('location').get(), self.eventData);
                return true;
            };

            this.stopEditingRoomLocationFunction = function() {
                roomLocationDiv.dom.style.display = 'block';
                roomEditorDiv.dom.style.display = 'none';
                self.roomEditor.locationChooser.set(self.eventData.location);
                self.roomEditor.roomChooser.set(self.eventData.room);
                self.roomEditor.inheritCheckbox.set(self.eventData.inheritRoom && self.eventData.inheritLoc)
            };

            var parentName = {
                Event: $T('event'),
                Contribution: $T('contribution'),
                SessionContribution: $T('contribution'),
                Session: $T('session'),
                SessionSlot: $T('session')
            }[this.info.get('parentType')];

            this.roomEditor = new RoomBookingVerticalReservationWidget(Indico.Data.Locations,
                                                                       this.info,
                                                                       this.parentInfo,
                                                                       nullRoomInfo(this.info),
                                                                       [],
                                                                       null,
                                                                       this.bookedRooms,
                                                                       this.timetableData,
                                                                       this.startEndTimeField.accessor,
                                                                       this.eventData.id,
                                                                       parentName);

            var roomEditorDiv = Html.div({id:'roomEditor'},this.roomEditor.draw());
            roomEditorDiv.dom.style.display = 'none';

            return Html.div({},roomLocationDiv, roomEditorDiv);
        },

        clickTriggersClosing: function(target) {
            //dirty way of finding dropdown list's elements
            if(target.dom.className.indexOf('bottomLine') != -1 || target.dom.parentNode.parentNode.className == 'optionBoxAdd')
                return false;
            else
                return this.PopupDialog.prototype.clickTriggersClosing.call(this, target);
        },

        _setParentInfo: function() {
            var parent;
            if(this.managementActions.session)
                parent = this.managementActions.session;
            else
                parent = this.managementActions.eventInfo;

            this.info.set('parentType', parent.entryType || 'Event');
            this.parentInfo = new WatchObject();
            this.parentInfo.set('room',parent.room);
            this.parentInfo.set('location',parent.location);
        },

        _setInfo: function() {
            this.info = new WatchObject();
            if(!this.eventData.inheritRoom)
                this.info.set('room',this.eventData.room);
            if(!this.eventData.inheritLoc)
                this.info.set('location',this.eventData.location);
        },

        postDraw: function() {
            this.roomEditor.postDraw();
        }
    },
     function(timetable, block, eventData, blockDiv, closeHandler, managementActions) {
         this.block = block;
         this.managementActions = managementActions;
         this.bookedRooms = managementActions.eventInfo.bookedRooms;
         this.timetableData = timetable.parentTimetable?timetable.parentTimetable.getData():timetable.getData();
         this.TimetableBlockPopup(timetable, eventData, blockDiv, closeHandler);
     });

/*
 * An exclusive popup for showing the timetable of a session.
 * Is functional but needs more work in order to be useful.
 */
type("TimetablePopup", ["ExclusivePopup"], {

    draw: function() {
        var self = this;

        var div = Html.div({style: {padding: pixels(30)}});

        var timetable = new TimeTable({"20090617": {"s420": this.eventData}} ,710, div, 'contribution', false);
        div.set(timetable.draw());
        timetable.postDraw();

        return this.ExclusivePopup.prototype.draw.call(this, Html.div({style: {marginBottom: pixels(10)}}, div));
    }
},
     function(eventData, contributions, closeHandler) {
         this.contributions = contributions;
         this.eventData = eventData;
         this.width = 500;

         this.ExclusivePopup('Session timetable', closeHandler);
     }
    );

type("TimetableDrawer", ["IWidget", "DroppableTimetableMixin"],
     {

         _minuteDifference: function(time1, time2) {
             var t1 = parseInt(time1.substring(0,2), 10)*60 + parseInt(time1.substring(3,6), 10);
             var t2 = parseInt(time2.substring(0,2), 10)*60 + parseInt(time2.substring(3,6), 10);

             return t2 - t1;
         },

         _drawGrid: function(scale) {

           var scaleDiv = Html.div({
               id: 'timetable_grid',
               style: {
                   position:'relative',
                   top: pixels(TimetableDefaults.topMargin)
               }});

             var last = scale[scale.length-1][0];

             for (var n=0; n < scale.length; ++n){
                 var hour = scale[n][0];
                 var px = scale[n][1];

                 if (scale[n].length > 2) {
                   scaleDiv.append(Html.div({style:
                     {
                         position: 'absolute',
                         top: pixels(px),
                         width: pixels(this.width),
                         height: hour==last?'0px':scale[n+1][1]-px,
                         borderTop: '1px dotted red',
                         fontSize: '11px'}}));
                     continue;
                 }

                 var hourLineDiv = Html.div({id: 'hourLine_' + parseInt(hour), className: 'hourLine', style:
                                             { top: pixels(px),
                                               width: pixels(this.width),
                                               height: hour == last ? '20px' : scale[n + 1][1] - px}
                                            }, zeropad(hour) + ':00');

                 this.make_droppable($(hourLineDiv.dom), parseInt(hour));

                 scaleDiv.append(hourLineDiv);
             }
             return Html.div({}, this.layoutChooser.get().getHeader(this.width), scaleDiv);
         },

         _drawWholeDayBlocks: function(data, blocks) {
             var self = this;

             var wholeDayBlockDiv =
               Html.div({style:
                         {
                           position:'relative',
                           marginTop: pixels(TimetableDefaults.topMargin),
                           top: pixels(10),
                           marginLeft: pixels(TimetableDefaults.leftMargin),
                           marginRight: pixels(TimetableDefaults.rightMargin)
                         }
                        });

             self.wholeDayBlocks = [];

             var blockAdded = false;
             each(blocks, function(blockData) {
                 var eventData = data[blockData.id];

                 var block;
                 if (self.managementMode) {
                     block = new TimetableBlockWholeDayManagement(self.timetable, eventData, blockData, self.managementActions);
                 } else {
                     block = new TimetableBlockWholeDayDisplay(self.timetable, eventData, blockData);
                 }
                 wholeDayBlockDiv.append(block.draw(0, 100));
                 blockAdded = true;
             });

             return blockAdded ? wholeDayBlockDiv : Html.div({});
         },

         _drawBlocks: function(data, blocks, groups) {
             var self = this;
             var colN = 0;

             var blockDiv = Html.div({style:
                                      {
                                          position:'relative',
                                          top: pixels(TimetableDefaults.topMargin)
                                      }
                                     });
             this.blocks = [];
             this._blockMap = {};

             each(blocks, function(blockData) {

                 var nCol = self.layoutChooser.get().getNumColumnsForGroup(groups[blockData.group]);
                 self.maxCol = ((self.maxCol == null) || (self.maxCol < nCol)) ? nCol : self.maxCol;

                 var colWidth = Math.floor((self.width-TimetableDefaults.leftMargin) / nCol);

                 var leftPos = TimetableDefaults.leftMargin + colWidth*blockData.assigned;

                 var width;
                 if (parseInt(blockData.assigned, 10) == (nCol-1)) {
                     // If last colument make sure the blocks spans all the way to the end
                     // of the timetable. Makes sure that the right margin is always aligned.
                     width = self.width - leftPos - TimetableDefaults.rightMargin;
                 } else {
                     width = colWidth;
                 }

                 var eventData = data[blockData.id];
                 var block;
                 var compactMode = false;
                 // For now don't use the compact mode. Activating it makes short entries displaying less
                 // information in the block (only time and title).
                 //if (blockData.collapsed || (blockData.end - blockData.start < TimetableDefaults.layouts.proportional.values.pxPerHour))
                 //    compactMode = true;

                 if (self.managementMode) {
                     block = new TimetableBlockNormalManagement(self.timetable, eventData, blockData, compactMode, self.printableVersion, self.detail.get(), self.managementActions);

                 } else {
                     block = new TimetableBlockNormalDisplay(self.timetable, eventData, blockData, compactMode, self.printableVersion, self.detail.get());
                 }
                 blockDiv.append(block.draw(leftPos, width));
                 self._blockMap[blockData.id] = block.block.dom;
                 self.blocks.push(block);
             });

             return blockDiv;
         },

         setLayout: function(layout) {
             this.layout.set(layout);
             this.layoutChooser.set(layout);
         },

         redraw: function(day) {

             if (this.preventRedraw) {
                 return;
             }

             this.timetable.redrawLegend();

             day = any(day, this.day);
             if (day == 'all') {
                 this.redrawAllDays();
                 return;
             }

             var dayFiltered = this.applyFilters(this.data[day]);

             if (this.detail.get() == 'contribution') {
                 dayFiltered = this.flatten(dayFiltered);
             }

             var dayData = this.layoutChooser.get().drawDay(dayFiltered, 'session', this.startTime, this.endTime, this.managementMode);
             var height = dayData[0] + TimetableDefaults.topMargin + TimetableDefaults.bottomMargin;
             this.wrappingElement.setStyle('height', pixels(height + (this.printableVersion ? 0 : 100))); // +100 to have margin for the tabs

             this.grid.length = 0;
             $.merge(this.grid, dayData[1]);

             var gridElems = this._drawGrid(this.grid);
             var blocks = this._drawBlocks(dayFiltered, dayData[2], dayData[3]);
             var wholeDayBlocks = this._drawWholeDayBlocks(dayFiltered, dayData[4]);

             // Only do if not all days are drawn
             this.canvas.set([wholeDayBlocks, Html.div({style: {position: 'relative'}}, gridElems, blocks)]);
             var totalHeight = height + wholeDayBlocks.dom.offsetHeight;

             this.canvas.dom.style.height = pixels(totalHeight);

             this.postDraw();

             $('body').trigger('timetable_redraw', this);

             return totalHeight;
         },

         setPrintableVersion: function(printableVersion) {
             this.printableVersion = printableVersion;
             this.redraw();
         },

         postDraw: function() {
             each(this.blocks, function(block) {
                 if (exists(block.postDraw)) {
                     block.postDraw();
                 }
                 });
         },

         flatten: function(data) {
             var result = {};
             each(data, function(entry, key) {
                 // sessions that are not poster sessions will be
                 // 'converted' to contributions
                 if (entry.entryType == 'Session' && !entry.isPoster && keys(entry.entries).length > 0) {
                     each(entry.entries, function(subentry, subkey) {
                         result[subkey] = clone(subentry);
                         result[subkey].color = subentry.entryType == 'Break' ? subentry.color:entry.color;
                         result[subkey].textColor = subentry.entryType == 'Break' ? subentry.textColor:entry.textColor;
                     });
                 } else {
                     result[key] = entry;
                 }
             });

             return result;
         },

         flatten2: function(data) {

             return data;
         },

         drawDay: function(day) {
             this.day = day;

             this.preventRedraw = true;
             this.updateFilters(day);
             this.preventRedraw = false;

             this.setLoading(true, this.redraw, day);

             return this.canvas;
         },

         drawAllDays: function() {
             this.day = 'all';

             this.preventRedraw = true;
             this.updateFilters('all');
             this.preventRedraw = false;

             this.setLoading(true, this.redrawAllDays);

             return this.canvas;
         },

         redrawAllDays: function() {
             var self = this;

             var days = [];
             // Add the elements to an array and sort it based on date
             each(this.data.all, function(value, key) {
                 if (key != 'all') {
                     value.date = key;
                     days.push(value);
                 }
             });
             days.sort(function(a,b) {
                 if (a.date > b.date) {
                     return 1;
                 }
                 return -1;
             });

             var div = Html.div({});
             var height = 0;
             var headerHeight = 0;

             // Retrieve the header height by adding it to the dom tree and then
             // removing it... is there a better way?
             var header = Html.div({className: 'timetableHeader', style: {visibility: 'hidden'}}, 'Test');
             self.wrappingElement.append(header);
             headerHeight = header.dom.offsetHeight + 20; // 20 is the top margin
             self.wrappingElement.remove(header);

             var firstDay = true;
             each(days, function(value) {
                 var day = value.date;
                 delete value.date;
                 var h = self.redraw(day);

                 // Copy all the elements in canvas
                 var elements = translate(self.canvas.dom.childNodes, function(value) {return $E(value);});
                 var dayCanvas = Html.div({style: {position: 'relative', height: pixels(h)}}, elements);

                 // Add a div containing the date
                 var headerStyle = {width: pixels(self.width-10)}; // substract the padding
                 if (self.printableVersion) {
                     headerStyle.textAlign = 'center';
                     headerStyle.borderBottom = '0';
                 } else if (firstDay) {
                     headerStyle.marginTop = '0';
                 }

                 var nDate = Util.parseJSDateTime(day, IndicoDateTimeFormats.Ordinal);
                 var dayStr = Indico.Data.WeekDays[nDate.getDay()].substring(0,3)+' '+nDate.getDate()+'/'+(nDate.getMonth()+1);

                 header = Html.div({className: 'timetableHeader', style: headerStyle}, dayStr);
                 div.append(header);
                 // Add the timetable canvas
                 div.append(dayCanvas);

                 // Increase total height with this day's height + height of div containing the date
                 height += h + headerHeight;

                 firstDay = false;
             });
             // The extra margin added to the height, if not printable version
             // then the height of the tabs needs to be added
             var margin = 30 + (self.printableVersion ? 0 : 100);
             self.wrappingElement.setStyle('height', pixels(height + margin));

             this.canvas.set(div);

             return this.canvas;
         },

         setWidth: function(width) {
             this.width = width;
         },

         applyFilters: function(data) {

             var result = {};
             var self = this;

             each(data, function(event, key) {
                 var show = true;
                 self.filterState.each(function(value, filterName) {
                     if (value) {
                         var filter = TimetableDefaults.filters[filterName].filter;
                         if (!filter.apply(event)) {
                             show = false;

                         }
                     }
                 });
                 if (show) {
                     result[key] = event;
                 }
             });

             return result;
         },
         updateFilters: function() {
             var self = this;

             self.filterState.each(function(value, filterName) {
                 if (value) {
                     TimetableDefaults.filters[filterName].filter.setData(self.data, self.day);
                 }
             });
         },
         /*
          * Since the loading indicator needs to be shown before the rest of the code
          * is executed a small timeout is added before calling the funcToCall.
          */
         setLoading: function(loading, funcToCall, arg) {
             var self = this;
             funcToCall = any(funcToCall, function () {} );
             this.loading += loading ? 1 : -1;

             if (this.loading > 0) {
                 this.loadingIndicator.dom.style.visibility = 'visible';
                 setTimeout(function() {
                     // call redraw function
                     funcToCall.call(self, arg);
                     $('body').trigger('timetable_ready', self.timetable);
                     self.setLoading(false);
                 }, 100);
             } else {
                 this.loadingIndicator.dom.style.visibility = 'hidden';
                 this.loading = 0;
             }
         },
         setData: function(data, startTime, endTime) {
             this.startTime = startTime;
             this.endTime = endTime;
             this.data = data;
             this.redraw();
         },
         toggleEvents: function(value) {
             if (value === undefined) {
                 this.eventsDisabled = !this.eventsDisabled;
             } else {
                 this.eventsDisabled = !value;
             }
         }

     },
     function(timetable, width, wrappingElement, detailLevel, extraButtons, loadingIndicator, managementMode, managementActions, defaultLayout) {

         var self = this;

         this.grid = [];
         this.wrappingElement = wrappingElement;
         this.canvas = Html.div({'id': 'timetable_canvas'});
         this.filterList = new WatchList();
         this.data = timetable.data;
         this.timetable = timetable;
         this.blocks = [];
         this.width = width;
         // Prevents redraw when set to true
         this.preventRedraw = false;
         // Used to switch between normal and printable version
         this.printableVersion = false;

         // layoutKey -> layoutManager map
         this.layoutChooser =  new Chooser(map(TimetableDefaults.layouts,
                                               function(value, key) {
                                                   return value.manager;
                                               }));

         this.detail = new WatchValue();
         this.layout = new WatchValue();
         // if greater > 0 the timetable is loading
         this.loading = 0;
         this.loadingIndicator = loadingIndicator;


         this.managementMode = managementMode;
         this.managementActions = managementActions;

         // default layout is 'compact'
         this.layout.set(any(defaultLayout, 'compact'));
         this.layoutChooser.set(any(defaultLayout, 'compact'));
         // default detail level is 'session'
         this.detail.set(any(detailLevel, 'session'));
         this.eventsDisabled = false;

         var filterState = map(TimetableDefaults.filters,
             function(value, key) {
                 // simultaneously, set the data for the filters
                 //value.filter.setData(data);
                 return true;
             });

         // create a filterName -> filterObject list
         this.filterState = $O(filterState);

         this.detail.observe(function(value) {
             if (!self.preventRedraw) {
                 self.setLoading(true, self.redraw);
             }
         });

         this.layout.observe(function(value) {
             self.layoutChooser.set(value);
             if (!self.preventRedraw) {
                 self.setLoading(true, self.redraw);
             }
         });

         this.DroppableTimetableMixin();
     });



type("IntervalTimetableDrawer", ["TimetableDrawer"],
    {
        posterRedraw: function() {
            // TO USE: in a future interval timetable for display mode.
            //var dayFiltered = this.applyFilters(this.data[this.day]);
            //var dayData = this.layoutChooser.get().drawDay(dayFiltered);
            var dayData = this.layoutChooser.get().drawDay(this.data[this.day]);
            var blocks = this._posterBlocks(dayData);
            this.canvas.set(Html.div({style: {position: 'relative'}}, blocks));

            var height = this.canvas.dom.clientHeight + 50 + TimetableDefaults.topMargin+TimetableDefaults.bottomMargin;

            this.wrappingElement.setStyle('height', pixels(height + (this.printableVersion ? 0 : 100))); // +100 to have margin for the tabs

            this.postDraw();

            return height;
        },

        redraw:function() {
            if (this.isPoster) {
                return this.posterRedraw();
            }else {
                return this.TimetableDrawer.prototype.redraw.call(this);
            }
        },

        _posterBlocks: function(data) {
            var self = this;

            var blockDiv = Html.div({style:
                                     {
                                         position:'relative',
                                         top: pixels(TimetableDefaults.topMargin)
                                     }
                                    });

            self.blocks = [];
            var topPx = 0;
            each(data, function(blockData, id) {

                var editLink = Html.a({className: 'dropDownMenu', style: {fontWeight: 'bold'}}, $T('Edit'));
                var menuItems = {};
                menuItems["blockProperties"] = { action: function() {self.managementActions.editContribution(blockData);}, display: $T('Basic edition')};
                menuItems["contributionFullEdition"] = {action: self.managementActions.editEntry(blockData), display: $T('Full edition')};
                menuItems["contributionProtection"] = {action: self.managementActions.editEntryProtection(blockData), display: $T('Edit protection')};
                editLink.observeClick(function() {
                    var menu = new PopupMenu(menuItems, [editLink], 'timetableManagementPopupList', true, true);
                    var pos = editLink.getAbsolutePosition();
                    menu.open(pos.x + editLink.dom.offsetWidth + 2, pos.y + editLink.dom.offsetHeight + 2);
                });

                var deleteLink = Html.a('fakeLink', "Delete");
                deleteLink.observeClick(function() {
                    self.managementActions.deleteEntry(blockData);
                });


                var entryTools = Html.div({style:{cssFloat: "right"}},editLink," | ",deleteLink);
                var entryInfo = Html.div({},blockData.contributionId + " - " + blockData.title );
                var block = Html.div({className:'posterEntry'},
                    entryTools,
                    entryInfo,
                    Html.div({}));
                blockDiv.append(block);
                self.blocks.push(block);
            });

            return blockDiv;
        },

        setData: function(data, day, isPoster) {
            this.isPoster = isPoster;
            this.day = day;
            if (this.isPoster) {
                this.setLayout('poster');
            } else {
                this.setLayout(this.layout.get());
            }
            this.TimetableDrawer.prototype.setData.call(this, data);
        }
    },
     function(data, width, wrappingElement, extraButtons, loadingIndicator, managementMode, managementActions, layout) {
         this.TimetableDrawer(data, width, wrappingElement, 'session', extraButtons, loadingIndicator, managementMode, managementActions, data.isPoster?'poster':'proportional');
        this.wrappingElement = data.parentTimetable.timetableDrawer.wrappingElement;

    }
);
