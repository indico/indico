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

             //All elements currently being dragged
             /* We don't want to trigger the popup
              if something is being dragged by the mouse */
             var draggingElements = $('.ui-draggable-dragging');

              // If popup alredy shown do nothing
             if (self.popupActive || self.materialMenuOpen ||
                 (draggingElements.length > 0)) {

                 return;
             }

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
                 sections[section] = menuItems;
                 each(value.resources, function(item) {
                     var name = item.name;
                     // set the URL instead of the title, if there's no title
                     menuItems[name ? name : item.url] = item.url;
                 });
             });

             var menu = new SectionPopupMenu(sections, [triggerElement], null, null, true, closeHandler);

             return menu;
         },
         createMaterialButton: function(material) {
             var self = this;

             this.materialMenuOpen = false;

             var button = Html.div('timetableBlockMaterial');
             button.observeClick(function(e) {
                 self.materialMenuOpen = true;

                 self.closePopup();

                 // use this style as long as the menu is open
                 button.dom.className = "timetableBlockMaterial timetableBlockMaterialActive";

                 var menu = self.createMaterialMenu(material, button, function () {
                     // Restores the button style when menu is closed
                     button.dom.className = "timetableBlockMaterial";
                     self.materialMenuOpen = false;
                     return true;
                 });

                 var pos = button.getAbsolutePosition();
                 menu.open(pos.x + 20, pos.y + 18);
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
                         return conv.firstName + ' ' +
                             conv.familyName;
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

                this.block = Html.div({style:
                        {
                            position: 'absolute',
                            top: pixels(this.topPos),
                            height: pixels(this.height),
                            backgroundColor: this.printableVersion ? 'white' : this.eventData.color,
                            color: this.printableVersion ? 'black' : this.eventData.textColor,
                            borderColor: this.printableVersion ? 'black' : '',
                            left: pixels(this.leftPos),
                            width: pixels(this.width-3),
                            borderBottomStyle: this.blockData.unfinished?'dashed':''
                        },
                                       className: 'timetableBlock ' + classTable[this.eventData.entryType]
                                      }, this._blockDescription()
               );

              self.makeDraggable(self.block, self.eventData);
              self.makeResizable(self.block, self.eventData);

              //When you drop something on a session timeBlock.
              if(this.eventData.entryType == 'Session') {
                self.makeMoveDroppable(self.block, self.eventData);
              }

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
                     self.openPopup(e);
                   });
                   highlightWithMouse(this.div, this.block);
                   showWithMouse(this.div, this.arrows);
               }
               return this.block;
            },

          makeResizable: function(block, eventData) {
            var self = this;
            var originalHeight = $(block.dom).height();
            $(block.dom).data('originalheight', originalHeight);
            var currentEndHour = null;
            var currentStartHour = null;

            var resizable = $(block.dom).resizable({
              containment: $('#timetableDiv'),
              maxWidth: $(block.dom).width(),
              minWidth: $(block.dom).width(),

              resize: function(event, ui) {
                //Array of the form [hour] = '..position().top' (relative to timetable)
                var hourLines = self.timetable.timetableDrawer.hourLinesArray;
                var mouseTop = event.pageY;

                var curBestDiff = Number.MAX_VALUE;
                var curHour = null;
                var diff = null;

                //This loop extracts the hour you're resizing on.
                //"The older for loop" is much faster than jQuery by the way
                for(i in hourLines) {
                  if(hourLines[i] != undefined) {

                    // If you pull the resize "edge" where there is
                    // no hourLine div
                    if(!($("#hourLine_"+i).length > 0)) {
                      return;
                    }

                    diff = (mouseTop - $("#hourLine_"+i).offset().top);
                    if((diff > 0) && (diff < curBestDiff)) {
                      curBestDiff = diff;
                      curHour = i;
                    }
                  }
                }

                //returns array, with array[0] = ending hour, array[1] = ending minute (rounded to closest 5-divisible)
                var gridTime = self.timetable.getTimetableDrawer().fetchTimeDragOnHour($(block.dom), $("#hourLine_"+curHour), curHour, "end");
                if(gridTime != null) {
                  currentStartHour = gridTime[0];
                  currentEndHour = gridTime[1];
                }
                return;
              },
              stop: function(event, ui) {
                $('.dragTip').hide();
                self.timetable.getTimetableDrawer().releaseResizeOnHour(currentStartHour, currentEndHour, eventData, block);
              }
            });
          },

          makeDraggable: function(block, eventData) {
            var self = this;

            var originalWidth = $(block.dom).width();
            var originalHeight = $(block.dom).height();

            /* Resize timeblock if nedeed */
            var maxCol = self.timetable.getTimetableDrawer().maxCol;
            var newWidth = (Math.round($('#timetableDiv').width()/(maxCol)));

            var heightThreshold = 450;
            var heightChange = (originalHeight > heightThreshold);
            var newHeight =  (heightChange) ? heightThreshold : originalHeight;

            var widthChange = (!(newWidth == originalWidth));

            var draggable = $(block.dom).draggable({
              //Center the mouse in the middle of the block while dragging
              cursorAt: {
                left: ((newWidth == undefined) ? 0 : Math.round(newWidth/2)),
                top: Math.round(newHeight/2) },
              containment: $('#timetableDiv'),
              revert: 'invalid',
              start: function() {
                /* Resize timeblock if nedeed */
                maxCol = self.timetable.getTimetableDrawer().maxCol;
                newWidth = (maxCol > 1) ? Math.round($('#timetableDiv').width()/(maxCol)) : originalWidth;

                $(block.dom).width(newWidth);
                $(block.dom).height(newHeight);

                //(fulhack) Ugly hack [Begin] on jQuery to make the changed width come in to effect while dragging
                $(this).data('draggable').helperProportions.width = newWidth;
                $(this).data('draggable').helperProportions.height = newHeight;
                $(this).data('draggable')._setContainment();
                //Ugly hack [End]

                self.timetable.getTimetableDrawer().createDragToolTip();

                var pos = $(block.dom).position();
                draggable.data('initialPosition', pos);
              },
              stop: function() {
                //reset original width
                if(widthChange || heightChange) {
                  $(block.dom).animate({
                    width: originalWidth,
                    height: originalHeight
                  });
                }
                $('.dragTip').remove();
              },
              drag: function(event) {
              }});

            draggable.data('blockInfo', block);
            draggable.data('eventData', eventData);
          },

          /* This is the function that take care of time block drops
            ON a session */
          makeMoveDroppable: function(block, eventData) {
            var self = this;

            function isSession(ui) {
              return ($(ui.draggable).hasClass("timetableSession"));
            }

            function isTouchingWall(ui) {
             var ret = (($(ui.draggable).position().left == 0)
                        || ($(ui.draggable).position().left ==
                         ($('#timetableDiv').width()-$(ui.draggable).width())));
              return ret;
            };

            $(block.dom).droppable({
              drop: function( event, ui ) {
                $('.dragTip').remove();

                //If a session is dropped on top do nothing.
                if(isSession(ui)) {
                  return;
                }

                /* If the dragged block dropped to the left most side,
                 * or the right most side (touches left/right wall)
                 * AND..
                 * the drop is handled by the drop-on-session-handler (since we're inside here now...)
                 * THEN
                 * handle it as a normal "HourLine drop". */

                if(isTouchingWall(ui)) {
                    $('.ui-droppable').droppable('enable');
                    var ttDrawer = self.timetable.getTimetableDrawer();
                    ttDrawer.releaseDragOnHour(ui, ttDrawer.curStartHour, ttDrawer.curStartMinute);
                    return;
                }

                var blockInfo = $(ui.draggable).data('blockInfo');
                var blockEventData = $(ui.draggable).data('eventData');

                var moveEntryDialog = new MoveEntryDialog(
                  self.managementActions,
                  self.timetable,
                  eventData.entryType,
                  eventData.sessionId,
                  eventData.sessionSlotId,
                  timetable.currentDay,
                  eventData.scheduleEntryId,
                  eventData.conferenceId,
                  eventData.startDate.date);

                var chosenValue = eventData.sessionId + ':' + eventData.sessionSlotId;

                var initialPosition = $(ui.draggable).data('initialPosition');

                //Store Undo data
                // TODO - not functioning at the moment
                //self.timetable.getTimetableDrawer().enableUndo("drop", blockEventData);

                moveEntryDialog.handleBlockMove(blockEventData, chosenValue);

                // Non-instanced call, which fails on self.slotId inside the indicoRequest, inside moveEntryDialog(...)
                /* MoveEntryDialog.prototype.handleBlockMove.call(self, blockEventData,
                  chosenValue, self.managementActions); */

                return;
              },
              greedy: true,
              tolerance: 'intersect',
              activate: function() {
                $(block.dom).css('border', '2px solid green');
              },
              deactivate: function() {
                $(block.dom).css('border', '');
              },
              over: function(event, ui) {
                /* If you touch the wall while also
                 * over a session - show that session with the style of
                 * "not current drop target"
                 *
                 */
                  function(event) {
                    if(isTouchingWall(ui)) {
                      $('.ui-droppable').droppable('enable');
                    }
                  };

                if(isSession(ui) || isTouchingWall(ui)) {
                  return;
                }

                $('.dragTip').hide();
                $('.ui-droppable').not(this).droppable('disable');
              },
              out: function(event, ui) {
                if(isSession(ui)) {
                  return;
                }
                $('.dragTip').show();
                $('.ui-droppable').not(this).droppable('enable');
              },
           });
          },

            postDraw: function(hook) {
                var self = this;
                var title = this._getTitle();

                // Returns the total height of the divs in the block
                var contentHeight = function() {
                    var h = 0;
                    if (!self.compactMode) {
                        locationHeight = self.locationDiv.dom.style.display != 'none' ? self.locationDiv.dom.offsetHeight : 0;
                        timeHeight = self.timeDiv.dom.style.display != 'none' ? self.timeDiv.dom.offsetHeight : 0;

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
                if (contentHeight() <= parentDivHeight) {
                    return;
                }

                // Try to remove the location info, and set title font weight to non bold,
                // if this works, then we're done. Otherwise, start to truncate the title as well.
                if (this.timeDiv.dom.style.display == 'none') {
                    this.locationDiv.dom.style.display = 'none';
                }

                if (contentHeight() <= parentDivHeight) {
                    return;
                }

                //Calculates the the width of title, presenters and possible arrows
                var topContentWidth = function() {
                    var width = 2 * self.margin;
                    if(self.titleDiv)
                        width += self.titleDiv.dom.offsetWidth;
                    if(self.presentersDiv)
                        width += self.presentersDiv.dom.offsetWidth;

                    return width;
                }

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

                block = Html.div({style: {
                            backgroundColor: this.printableVersion ? 'white' : this.eventData.color,
                            color: this.printableVersion ? 'black' : this.eventData.textColor,
                            borderColor: this.printableVersion ? 'black' : '',
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

type("TimetableBlockManagementMixin",[],
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
            //Using plural if there are multiple conveners
            infoContentDiv.append(
                Html.div('roomPopupTitle',
                            (self.eventData.conveners.length > 1)?
                            $T('Conveners'):
                            $T('Convener'), ': '));

            infoContentDiv.append(self._formatConveners(this.eventData.conveners));
            infoContentDiv.append(Html.br());
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

    _getMenuBar: function() {
        var self = this;

        // There is only a need for a menu bar when we show contribution or session
        if (self.eventData.entryType != 'Contribution' && self.eventData.entryType != 'Session') {
            return null;
        }

        var bar = Html.div({});

        var url = "#";
        if (self.eventData.entryType == 'Contribution') {
            url = Indico.Urls.ContributionDisplay + '?contribId=' + self.eventData.contributionId + '&confId=' + self.eventData.conferenceId;
        } else if (self.eventData.entryType == 'Session') {
            url = Indico.Urls.SessionDisplay + '?sessionId=' + self.eventData.sessionId +
                    '&confId=' + self.eventData.conferenceId + '#' + self.timetable.currentDay;
        }
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
                urlParams = '?contribId=' + self.eventData.contributionId + '&confId=' + self.eventData.conferenceId;
                menuItems.PDF = Indico.Urls.ContribToPDF + urlParams;
                menuItems.Calendar = Indico.Urls.ContribToiCal + urlParams;
                menuItems.XML = Indico.Urls.ContribToXML + urlParams;
            } else if (self.eventData.entryType == 'Session') {
                urlParams = '?showSessions=' + self.eventData.sessionId + '&confId=' + self.eventData.conferenceId;
                menuItems["PDF timetable"] = Indico.Urls.ConfTimeTablePDF + urlParams;

                urlParams = '?sessionId=' + self.eventData.sessionId + '&confId=' + self.eventData.conferenceId;
                menuItems.Calendar = Indico.Urls.SessionToiCal + urlParams;
            }

            var exportMenu = new PopupMenu(menuItems, [exportLink], null, true, true);
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
            var popup = new ContributionsPopup(self.eventData, contribs, function() {self.popupAllowClose = true; return true;});
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
                    href: Indico.Urls.ContributionDisplay + '?sessionId=' + value.sessionId + '&contribId=' + value.contributionId + '&confId=' + value.conferenceId,
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
                self.saveRoomLocationFunction()
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
                    this.eventData.endDate.time.substring(0,5));

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

                menuItems[$T('Block timetable')] = function() {
                    self.managementActions.switchToIntervalTimetable(self.eventData.id);
                    self.close();
                };
                menuItems[$T('Block properties')] = function() {
                    self.managementActions.editSessionSlot(self.eventData);
                    self.close();
                };
                if (!self.managementActions.isSessionTimetable) {
                    menuItems[$T('Session properties')] = self.managementActions.editEntry(self.eventData);
                    menuItems[$T('Session protection')] = self.managementActions.editEntryProtection(self.eventData);
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
                menuItems[$T('Contribution properties')] = self.managementActions.editEntry(self.eventData);
                menuItems[$T('Contribution protection')] = self.managementActions.editEntryProtection(self.eventData);
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
                    return false;
                });
            }
            menu.insert(editLink);


            // Move Entry link, only available for contribs and breaks
            if (self.eventData.entryType != 'Session') {
                menu.insert(" | ");

                moveEntryLink = Html.a('fakeLink', Html.span({}, $T("Move")));
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

            roomLocationDiv = Html.div({},Html.div('roomPopupTitle', 'Room: '),
                    self.eventData.room, Html.br(), Html.div('roomPopupTitle', 'Location: '),
                    self.eventData.location, Html.img({src: imageSrc("edit_16.png")}));

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
                                                                       Indico.Data.DefaultLocation,
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

type("ContributionsPopup", ["ExclusivePopup"], {

    draw: function() {
        var self = this;
        var table = Html.tbody({});
        each(this.contributions, function(contrib) {
            var time = Html.div({style: {paddingTop: pixels(7), marginRight: pixels(3), fontSize: '12px', fontWeight: 'bold'}}, self.eventData.isPoster ? '' : contrib.startDate.time.substr(0,5));
            var link = Html.a({href: Indico.Urls.ContributionDisplay + '?sessionId=' + contrib.sessionId + '&contribId=' + contrib.contributionId + '&confId=' + contrib.conferenceId}, contrib.title);
            var title = Html.div({style: {color: '#444444', width: pixels(self.width), padding: pixels(5), fontSize: '15px'}}, link);

            var infoDiv = Html.div({style: {width: pixels(self.width), border: '1px solid rgb(234, 234, 234)', marginBottom: pixels(10), marginLeft: pixels(5), padding: pixels(5), backgroundColor: 'rgb(248, 248, 248)',color: '#444444', fontSize: '12px'}});

            var showFullDescLink = Html.a({style: {cursor: 'pointer', fontWeight: 'bold', fontSize: '12px', fontStyle: 'italic'}}, ' Show full description');
            var hideFullDescLink = Html.a({style: {cursor: 'pointer', fontWeight: 'bold', fontSize: '12px', fontStyle: 'italic'}}, ' Hide full description');
            var shortDesc = Html.span({style: {display: 'block'}}, contrib.description.substr(0, 250) + '... ', showFullDescLink);
            var longDesc = Html.span({style: {display: 'none'}}, contrib.description, hideFullDescLink);

            if (contrib.description && contrib.description !== '') {
                if (contrib.description.length <= 250) {
                    longDesc.setStyle('display', 'block');
                    hideFullDescLink.setStyle('display', 'none');
                    infoDiv.append(longDesc);
                } else {
                    infoDiv.append(longDesc);
                    infoDiv.append(shortDesc);
                }
            }

            if (contrib.presenters.length > 0) {
                var speakers = Html.span({style: {marginTop: pixels(5), display: 'block'}}, Html.strong({}, 'Presenter(s): '));

                var i = 0;
                each(contrib.presenters, function(p) {
                    speakers.append(i++ > 0 ? ', ' : '' + p.name);
                    if (p.affiliation && p.affiliation !== '') {
                        speakers.append(Html.em({style: {fontSize: '12px'}}, ' (' + p.affiliation + ')'));
                    }
                });

                infoDiv.append(speakers);
            }

            if (contrib.room && contrib.room !== '') {
                var room = Html.span({style: {marginTop: pixels(3), display: 'block'}}, Html.strong({}, 'Room: '), contrib.room);
                infoDiv.append(room);
            }

            if (contrib.location && contrib.location !== '') {
                var location = Html.span({style: {marginTop: pixels(3), display: 'block'}}, Html.strong({}, 'Location: '), contrib.location);
                infoDiv.append(location);
            }

            showFullDescLink.observeClick(function(e) {
                shortDesc.setStyle('display', 'none');
                longDesc.setStyle('display', 'block');
            });
            hideFullDescLink.observeClick(function(e) {
                shortDesc.setStyle('display', 'block');
                longDesc.setStyle('display', 'none');
            });

            // Hide the infoDiv if it's empty
            if (infoDiv.dom.innerHTML === "") {
                infoDiv.dom.style.display = 'none';
            }

            table.append(Html.tr({}, Html.td({style:{verticalAlign: 'top'}}, time), Html.td({}, title, infoDiv)));
        });
        this.innerHTML = Html.table({style: {marginBottom: pixels(10)}}, table).dom.innerHTML;
        return this.ExclusivePopup.prototype.draw.call(this, Html.table({style: {marginBottom: pixels(10)}}, table));
    },
    postDraw: function(){
        this.ExclusivePopup.prototype.postDraw.call(this);
    }
    },
     function(eventData, contributions, closeHandler) {

         this.contributions = $L(contributions);
         this.contributions.sort(IndicoSortCriteria.StartTime);

         this.eventData = eventData;
         this.width = 500;

         this.ExclusivePopup('Contribution details', closeHandler, true, true);
     }
    );

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

type("TimetableDrawer", ["IWidget"],
     {

         _minuteDifference: function(time1, time2) {
             var t1 = parseInt(time1.substring(0,2), 10)*60 + parseInt(time1.substring(3,6), 10);
             var t2 = parseInt(time2.substring(0,2), 10)*60 + parseInt(time2.substring(3,6), 10);

             return t2 - t1;
         },

         _drawGrid: function(scale) {
           var scaleDiv = Html.div({style: {
             position:'relative',
             top: pixels(TimetableDefaults.topMargin)
           }});

             last = scale[scale.length-1][0];

             for (var n=0; n < scale.length; ++n){
                 hour = scale[n][0];
                 px = scale[n][1];

                 if (scale[n].length > 2) {
                   scaleDiv.append(Html.div({style:
                     {
                         position: 'absolute',
                         top: pixels(px),
                         width: pixels(this.width),
                         height: hour==last?'20px':scale[n+1][1]-px,
                         borderTop: '1px dotted red',
                         fontSize: '11px'}}));
                     continue;
                 }

               var hourLineDiv = Html.div({id: 'hourLine_'+parseInt(hour), className: 'hourLine', style:
                                           { position: 'absolute',
                                           top: pixels(px),
                                           width: pixels(this.width),
                                           height: hour==last?'20px':scale[n+1][1]-px,
                                           borderTop: '1px solid #E8E8E8',
                                           fontSize: '11px'}}, zeropad(hour)+':00');
               this._makeHourLineDroppable(hourLineDiv, parseInt(hour));

               this.hourLinesArray[hour] = px;

               scaleDiv.append(hourLineDiv);
             }
             return Html.div({}, this.layoutChooser.get().getHeader(this.width), scaleDiv);
         },


       createDragToolTip: function() {
         /*A dragging "tooltip" line that follows wherever a timeblock
          * is being dragged and displays the current start time
          * at that current dragging position.  */
           $('#timetableDiv').append($('<div class="dragTip"></div>'));
       },


         _calculateRelativeMinuteOffset: function(position, hour) {
             //If the current hour does not have an hourLine div
             if(($("#hourLine_"+hour).position() == null)) {
                 return null;
             }

             var hourTop = $("#hourLine_"+hour).position().top;
             var hourHeight = $("#hourLine_"+hour).height();

             var offsetHeight = (position - hourTop);

             var minute = Math.floor((offsetHeight/hourHeight) * 59);
             return ((minute > 60) || (minute < 0))? null : minute;
         },

       _makeHourLineDroppable: function(hourDiv, hour) {
         var self = this;

         var checkpoints = self.layoutChooser.get().checkpoints;

         ///* Just a small function to pick out smallest + largest value...
         var maxMinExtract = function(operator, list) {

           var significantValue = (operator == "min") ? (Number.MAX_VALUE) : null;
           _(keys(list)).each(function(x) {
             //We're actually only interested in the value x for these checkpoints
             if(operator == "max") {
               significantValue = (x > significantValue) ? x : significantValue;
             } else if(operator == "min") {
               significantValue = (x < significantValue) ? x : significantValue;
             }
             });
           return significantValue;
         };

         //Extract the hours from the strings of the form: HHMMSS
         var dayStartHour = parseInt(new String(maxMinExtract("min", checkpoints)).substring(0,2));
         var dayEndHour = parseInt(new String(maxMinExtract("max", checkpoints)).substring(0,2));

         self.dayEndHour = (dayEndHour == 24) ? 00 : dayEndHour;
         self.dayStartHour = dayStartHour;

         var isDisallowedTime = function(ui, hourCompare) {
           /* IF its outside the timetable div topside OR before day-start-hour OR
            * past midnight, when the day ends prior to 00:00 */
           return ($(ui.draggable).offset().top < $(hourDiv.dom).offset().top)
             || (hourCompare < dayStartHour) || ((dayEndHour == 0) && (hourCompare > 0));
         };

         //"unique" name for each drag-handler per hourLine
         var thisDragSpaceName = ("drag."+hour);

         //These variables are used below
         var startHour = null;
         var startMinute = null;

         $(hourDiv.dom).droppable({
           drop: function(event, ui) {
             if(isDisallowedTime(ui, startHour)) {
               self.revertBlockPos(ui.draggable);
               return;
             }

             self.releaseDragOnHour(ui, startHour, startMinute);
           },
           tolerance: 'touch',
           over: function(event, ui) {
             $(ui.draggable).bind(thisDragSpaceName, function(newEvent, newUi) {
               if(isDisallowedTime(ui, hour)) {
                 return;
               }

               var gridTime = self.fetchTimeDragOnHour(ui.draggable, hourDiv.dom, hour, "start");

               //null means that the drag is not allowed
               if((gridTime == null)) {
                 return;
               }
               startHour = gridTime[0];
               startMinute = gridTime[1];
               self.curStartHour = startHour;
               self.curStartMinute = startMinute;

               });
           },
           out: function(event, ui) {
             if(thisDragSpaceName != null) {
               $(ui.draggable).unbind(thisDragSpaceName);
             }
             $('.dragTip').hide();
           }
           });
       },

       /* This function determines what hour + minute the time block
        * should start at for the current dragging pixel position in the timetable.
        * This function is used by over:, in _makeHourLineDroppable
        * Args:
        * ui is the same one that drop(ui,events) is using.
        * hour = the current "hourLineDiv" being dragged upon
        *
        * significantEdge = start or end, whichever is being used to measure with
        * (start = dragging, end = resizing..)
        *
        * Returns an array, where array[0] = startHour, array[1] = startMinute
        * */
       fetchTimeDragOnHour: function(draggingBlock, hourDiv, hour, significantEdge) {
         var self = this;

         var setToolTipPos = function(newTop) {
           //Sets the drag-tooltip at the current dragging/resizing position
           $('.dragTip').offset({
             left: $('.dragTip').offset().left,
             top: newTop
           });
         };

         var dragTipTop = null;
         try {
           //If we're DRAGGING, and the dragTip is already created...
           dragTipTop = $(draggingBlock).offset().top;
         } catch (Exception) {
           dragTipTop = 0;
           dragTipTop = $(draggingBlock).offset().top;
           setToolTipPos(dragTipTop);
         }

         //Top left Position of the current hourLine div
         var hourPos = $(hourDiv).position();

         var blockPosTop = $(draggingBlock).position().top;
         var blockHeight = $(draggingBlock).height();
         var hourLowerLeftCorner = (hourPos.top+$(hourDiv).height());
         var hourTopLeftCorner = (hourPos.top);

         //Difference of time block and hour block in height
         var diffBlockTopLine = blockPosTop - hourTopLeftCorner;

         var startHour = hour;
         var startMinute = self._calculateRelativeMinuteOffset(blockPosTop, startHour);

         var endHour = hour;

         var blockEnd = (blockPosTop+blockHeight);
         endMinute = self._calculateRelativeMinuteOffset(blockEnd, endHour);

         if(!($('.dragTip').length > 0)) {
           self.timetable.getTimetableDrawer().createDragToolTip();
         }

         var gridTime = null;
         //significantEdge is set by the caller of this whole function
         // It represents the significant edge to measure with of a time block
         //That is, if youre resizing, then it will be "end"
         //Dragging --> "start"
         if(significantEdge == "start") {
           setToolTipPos($(draggingBlock).offset().top);
           //Returns closest 5-minute-divisible, hour and minute in an array
           gridTime = self.round5(startHour, startMinute);
         } else if(significantEdge == "end") {
           setToolTipPos($(draggingBlock).offset().top+blockHeight);
           gridTime = self.round5(startHour, endMinute);
         }

         if(gridTime == null) {
           return null;
         }

         if($('.dragTip').length > 0) {
           $('.dragTip').show();
           $('.dragTip').html(gridTime[0]+":"+gridTime[1]);
         }

         return gridTime;
       },

       enableUndo: function(undoLabel, currentEventData, shifted) {
         var undoArrayInfo = new Array();
         undoArrayInfo[0] = undoLabel;

         //Copying original values before they get modified
         undoArrayInfo[1] = currentEventData.startDate.date;
         undoArrayInfo[2] = currentEventData.startDate.time;
         undoArrayInfo[3] = currentEventData.endDate.date;
         undoArrayInfo[4] = currentEventData.endDate.time;
         undoArrayInfo[5] = currentEventData.duration;
         undoArrayInfo[6] = currentEventData.entryType;
         undoArrayInfo[7] = currentEventData.conferenceId;

         //If shifting entries was enabled
         undoArrayInfo[8] = shifted;
         //Also keep a reference to the soon-to-be modified eventData
         undoArrayInfo[9] = currentEventData;
         $(window).data('undo', undoArrayInfo);
         this.drawUndoDiv();
       },

       undoLastAction: function() {
         var self = this;
         var undoArrayInfo = $(window).data('undo');
         var undoLabel = undoArrayInfo[0];

         //[**] Fetch stored values for undo

         //String of the form "HH:MM:SS"
         var startDate = new Object();
         startDate.date = undoArrayInfo[1];
         startDate.time = undoArrayInfo[2];

         var endDate = new Object();
         endDate.date = undoArrayInfo[3];
         endDate.time = undoArrayInfo[4];

         var duration = undoArrayInfo[5];
         var entryType = undoArrayInfo[6];
         var conferenceId = undoArrayInfo[7];

         var shifted = undoArrayInfo[8];

         var currentEventData = undoArrayInfo[9];

         //[**] end

         /* conferenceId and entryType is cleared it seems at some point when
          * running editEntryStartEndDate on the original... hmm...
          *  - so here the values are just re-assigned from the original (stored PRIOR to calling editEntrySt...) */
         currentEventData.entryType = entryType;
         currentEventData.conferenceId = conferenceId;

         var startDT = new Date((Util.dateTimeIndicoToJS(startDate)).getTime());
         var endDT = new Date((Util.dateTimeIndicoToJS(endDate)).getTime());

         if((undoLabel == "placementChange") || (undoLabel == "resize")) {
           self.managementActions.editEntryStartEndDate(Util.formatDateTime(startDT, IndicoDateTimeFormats.Server),
             Util.formatDateTime(endDT, IndicoDateTimeFormats.Server), currentEventData, $(window).data('shiftIsPressed'));
         } else if(undoLabel == "drop") {
           // Here goes code to handle drop undo
           // However I didnt have time to find a reasonable way

             // Something in the right direction below (debug/test)
           /*
           var moveEntryDiag = new MoveEntryDialog(
             self.managementActions,
             self.timetable,
             currentEventData.entryType,
             currentEventData.sessionId,
             currentEventData.sessionSlotId,
             self.timetable.currentDay,
             currentEventData.scheduleEntryId,
             currentEventData.conferenceId,
             currentEventData.startDate.date);

           var chosenValue = currentEventData.sessionId;
           moveEntryDiag.handleBlockMove(currentEventData, chosenValue+":0", self.managementActions);
            */
         }

         $(window).data('undo', undefined);
         $('#undoDiv').remove();
         return;
       },

       /* A "button" that appears after an action is performed */
       drawUndoDiv: function() {
         //If it isnt drawn already
         if(!($('#undoDiv').length > 0)) {
           var self = this;
           var undoLink = Html.a({}, "Undo last action");
           undoLink.observeClick(
             function(e) {
               self.undoLastAction();
             });

           var undoDiv =
             Html.div({
             id: 'undoDiv',
             className: 'undoDiv',
               style: {
                 padding: '5px',
                 background: '#FFF',
                 border: '3px solid black',
                 position: 'fixed',
                 bottom: '0px',
                 left: '50%'
               }}, undoLink);
           $('#timetableDiv').append(undoDiv.dom);
         }
       },

       /* The function to execute when a drop occurs ON an hour.
        * The argument ui is the same one that drop(ui,events) is using.
        *
        * startHour is the hour where it is being dropped (0 to 23)
        * startMinute is the minute where it is being dropped, a 5-divisible in the range 0-55
        * startHour and startMinute is determined by fetchTimeDragOnHour(..)
        *
        * This function is used by drop:, in _makeHourLineDroppable
        */
       releaseDragOnHour: function(ui, startHour, startMinute) {
         var self = this;
         $('.dragTip').remove();

         if((startMinute == null) || (startHour == 00)) {
           self.revertBlockPos(ui.draggable);
           return false;
         }

           //originalEventData is used for the undo functionality
           var eventData = $(ui.draggable).data('eventData');

           //Store Undo data
           self.enableUndo("placementChange", eventData, $(window).data('shiftIsPressed'));

           eventData.startDate.time = startHour+":"+startMinute+":00";

           var startDT = Util.dateTimeIndicoToJS(eventData.startDate);
           var endDT = new Date(startDT.getTime() + eventData.duration*60000);

           //If it doesnt end on the same day, revert drag
           if(endDT.getDay() > startDT.getDay()) {
             self.revertBlockPos(ui.draggable);
             return false;
           }

         self.managementActions.editEntryStartEndDate(Util.formatDateTime(eventData.startDate, IndicoDateTimeFormats.Server),
                                                      Util.formatDateTime(endDT, IndicoDateTimeFormats.Server), eventData, $(window).data('shiftIsPressed'));

         return true;
       },

       releaseResizeOnHour: function(endHour, endMinute, eventData, block) {
         var self = this;
         self.enableUndo("resize", eventData);

         eventData.endDate.time = endHour+":"+endMinute+":00";
         var endDT = Util.dateTimeIndicoToJS(eventData.endDate);
         var startDT = Util.dateTimeIndicoToJS(eventData.startDate);

         // HERE GOES CODE TO LIMIT RESIZE FOR THE CURRENT DAY ONLY
         //If it doesnt end on the same day, revert drag
         /*
         if((self.dayEndHour == 0) && (false))  {
           self.revertBlockHeight(block);
           return false;
         }
          */

         self.managementActions.editEntryStartEndDate(Util.formatDateTime(eventData.startDate, IndicoDateTimeFormats.Server),
           Util.formatDateTime(endDT, IndicoDateTimeFormats.Server),
           eventData, false);

         //Store Undo-data
         return true;
       },

       revertBlockHeight: function(block) {
         $(block.dom).animate({
         height: $(block.dom).data('originalheight')
           });
       },

       /* Returns a draggable to its initial position */
       revertBlockPos: function(draggable) {
         var initPos = $(draggable).data('initialPosition');

         $(draggable).animate({
           left: initPos.left,
           top: initPos.top
         });
         $('.dragTip').remove();
       },

       round5: function (hour, minute) {

         //Rounds the number to the closest 5-divisible,..
         //Also appends padding to the number, such that 0 = 00, 1 = 01...
         closestFive = (minute % 5) >= 2.5 ? parseInt(minute / 5) * 5 + 5 : parseInt(minute / 5) * 5;
         var newHour = ((minute > 55) && (closestFive == 60)) ? (hour+1) : hour;
         var timeArray = new Array();
         if(newHour > 23) {
           return null;
         }
         timeArray[0] = zeropad(newHour);
         timeArray[1] = zeropad((closestFive == 60) ? 00 : closestFive);
         return timeArray;
       },

       /* Since javascripts mod (%) function/operator can't
        * properly handle negative numbers here's a real one */
       properModulus: function(num, modn) {
         return ((num%modn)+modn)%modn;
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

             self.blocks = []

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

                 var empty = true;

                 for (b in eventData.entries) {
                     empty = false;
                     break;
                 }
                 compactMode = false;
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
                 self.blocks.push(block);
             });

             return blockDiv;
         },

         setLayout: function(layout) {
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

             var dayData = this.layoutChooser.get().drawDay(dayFiltered, 'session', this.startTime, this.endTime);
             var height = dayData[0]+TimetableDefaults.topMargin+TimetableDefaults.bottomMargin;
             this.wrappingElement.setStyle('height', pixels(height + (this.printableVersion ? 0 : 100))); // +100 to have margin for the tabs

             var grid = this._drawGrid(dayData[1]);
             var blocks = this._drawBlocks(dayFiltered, dayData[2], dayData[3]);
             var wholeDayBlocks = this._drawWholeDayBlocks(dayFiltered, dayData[4]);

             // Only do if not all days are drawn
             this.canvas.set([wholeDayBlocks, Html.div({style: {position: 'relative'}}, grid, blocks)]);
             var totalHeight = height + wholeDayBlocks.dom.offsetHeight;

             this.canvas.dom.style.height = pixels(totalHeight);

             this.postDraw();

             return totalHeight;
         },

         setPrintableVersion: function(printableVersion) {
             this.printableVersion = printableVersion;
             this.redraw();
         },

         postDraw: function() {
             each(this.blocks, function(block) { block.postDraw(); });
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
                         result[subkey].textColor = entry.textColor;
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
                     funcToCall.call(self, arg);
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
         }
     },
     function(timetable, width, wrappingElement, detailLevel, extraButtons, loadingIndicator, managementMode, managementActions, defaultLayout) {


         var self = this;

         this.hourLinesArray = new Array();

         this.wrappingElement = wrappingElement;
         this.canvas = Html.div({});
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

                var editLink = Html.a('fakeLink', "Edit");
                editLink.observeClick(function() {
                    window.location = self.managementActions.editEntry(blockData);
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

        postDraw: function() {

        },

        setData: function(data, day, isPoster) {
            this.isPoster = isPoster;
            this.day = day;
            if (this.isPoster) {
                this.setLayout('poster');
            } else {
                this.setLayout('compact');
            }
            this.TimetableDrawer.prototype.setData.call(this, data);
        }
    },
    function(data, canvas, width, wrappingElement, extraButtons, loadingIndicator, managementMode, managementActions) {
        this.TimetableDrawer(data, canvas, width, wrappingElement, 'session', extraButtons, loadingIndicator, managementMode, managementActions, data.isPoster?'poster':null);
        this.wrappingElement = data.parentTimetable.timetableDrawer.wrappingElement;

    }
);
