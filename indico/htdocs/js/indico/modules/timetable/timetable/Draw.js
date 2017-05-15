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
             self._drawPopup(event);
         },

         createMaterialMenu: function(attachments, triggerElement, closeHandler) {
             var menuItems = {},
                 sections = {'': {content: menuItems, description: ''}};

            $.each(attachments.files, function(i, attachment) {
                menuItems["material" + attachment.download_url] = {
                    action: attachment.download_url,
                    display: attachment.title ,
                    description: attachment.description};
            });

            $.each(attachments.folders, function(i, folder) {
                var sectionItems = {},
                    section = folder.title;

                $.each(folder.attachments, function(i, attachment) {
                    sectionItems["material" + attachment.download_url] = {
                        action: attachment.download_url,
                        display: attachment.title ,
                        description: attachment.description
                    };
                });
                sections[section] = {content: sectionItems, description: folder.description };

            });
            return new SectionPopupMenu(sections, [triggerElement], null, null, true, closeHandler);
         },

         getMaterialMenu: function (attachments) {
            var root = $('<ul class="material_list"/>');

            each(attachments.files, function(attachment) {
                var resource_html = $('<li/>').append(
                    $('<a/>').attr('href', attachment.download_url).text(attachment.title));
                root.append(resource_html);
            });

            each(attachments.folders, function(folder) {
                var resources = $('<ul class="resource_list"/>');
                each(folder.attachments, function(attachment) {
                    var resource_html = $('<li/>').append(
                        $('<a/>').attr('href', attachment.download_url).text(attachment.title));
                    resources.append(resource_html);
                });
                var material_html = $('<li/>').append($('<h3/>').append(folder.title), resources);
                root.append(material_html);
            });
            return root;
         },

         createMaterialButton: function(attachments) {
             var self = this;

             var button = Html.a('i-link entry-attachments');
             var $button = $(button.dom);
             $button.qtip({
                 content: {
                     text: self.getMaterialMenu(attachments)
                 },
                 show: {
                     event: false
                 },
                 hide: {
                     event: 'unfocus'
                 },
                 events: {
                     show: function() {
                         $button.addClass('open').trigger('indico:closeAutoTooltip');
                     },
                     hide: function() {
                         $button.removeClass('open');
                     }
                 },
                 position: {
                     my: 'top right',
                     at: 'bottom left'
                 },
                 style: {
                     classes: 'material_tip'
                 },
                 suppress: false
             }).on('click', function(evt) {
                 evt.stopPropagation();
                 $(this).qtip('show');
             }).attr('title', $T.gettext("Show materials")).data('qtip-position', 'right');

             return button;
         },

         _getRightSideDecorators: function() {
             return Html.span({});
         },

         _formatConveners: function(conveners) {
             if (conveners) {
                 return _.map(_.sortBy(conveners, _.property('displayOrderKey')), _.property('name')).join(', ');
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

                this.titleWrapper = Html.div({}, this.titleDiv);

                this.div = Html.div({className: 'entry-content', style: { width: '100%', height: '100%'}}, this.titleWrapper);

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
                        var firstPresenter = self.eventData.presenters[0];
                        this.presentersDiv = Html.div({className: 'timetableBlockPresenters'});
                        this.presentersDiv.append(firstPresenter.name);
                        if (self.eventData.presenters.length > 1) {
                            this.presentersDiv.append(' ' + $T('et al.'));
                        }
                        this.titleWrapper.insert(this.presentersDiv);
                    }

                    // Add material menu
                    if (!self.managementActions && self.eventData.attachments && self.eventData.attachments.files) {
                        this.titleWrapper.insert(this.createMaterialButton(this.eventData.attachments));
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

                this.block.set(this._getRightSideDecorators(), this._blockDescription());

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
                   $(this.block.dom).on('click', '.entry-content', function(e) {
                       if (!self.timetable.getTimetableDrawer().eventsDisabled) {
                           $(this).trigger('tt_block.balloon', e);
                       }
                   });
                   highlightWithMouse(this.div, this.block);
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
                this.titleWrapper.dom.style.paddingTop = '15px';
                if (this.compactMode) {
                    this.timeDiv.dom.style.paddingTop = '15px';
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
                if (self.eventData.attachments && self.eventData.attachments.files) {
                    this.titleWrapper.insert(this.createMaterialButton(this.eventData.attachments));
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

function loadBalloonContent(self, api, editable) {
    var entryId = self.eventData.scheduleEntryId ? self.eventData.scheduleEntryId : self.eventData.id.substring(1);
    var url = editable ? Indico.Urls.Timetable.entries.info.manage : Indico.Urls.Timetable.entries.info.display;
    var urlParams = {
       'confId': self.eventData.conferenceId,
       'entry_id': entryId
    };
    if (self.timetable.isSessionTimetable) {
        urlParams.session_id = self.eventData.sessionId;
    }

    $.ajax({
        url: build_url(url, urlParams)
    })
    .then(function(content) {
        // Set the tooltip content upon successful retrieval
        api.set('content.text', content.html);
        var $content = api.elements.content;

        function hideBalloon() {
            /* Make sure the balloon's qTip is hidden. qTip2 will trigger the hide event callbacks with the cached
             * event when hide() is called. Sometimes the cached event happens to be a mouseleave event which will
             * prevent the qTip from closing. To ensure the qTip is always closed we are changing the type of that
             * event to one that will not be prevented. */
            api.cache.event.type = 'click';
            api.hide();
        }

        if (editable) {
            var qtipId = $content.closest('.qtip').data('qtip-id');
            var $balloonQtip = $('[data-hasqtip=' + qtipId + ']');
            var closeBalloon = false;
            $content.find('.js-edit-time').ajaxqbubble({
                url: build_url(Indico.Urls.Timetable.entries.editTime, urlParams),
                qBubbleOptions: {
                    style: {
                        classes: 'balloon-time-qtip'
                    },
                    position: {
                        at: 'top center',
                        my: 'bottom center',
                    },
                    events: {
                        hidden: function() {
                            if (closeBalloon) {
                                $balloonQtip.qbubble('hide');
                            }
                        }
                    }
                },
                qtipConstructor: function(element, qtipOptions) {
                    $balloonQtip.qbubble('createNested', element, qtipOptions);
                },
                onClose: function(data) {
                    handleNotifications(data);
                    if (data) {
                        self.timetable._updateDay(data.update);
                        /* Since the entry update creates a new div we can't
                         * easily reposition the balloon on the timetable entry. */
                        closeBalloon = true;
                    }
                }
            });

            $content.on('indico:confirmed', '.js-delete', function(evt) {
                evt.preventDefault();
                self.managementActions.deleteEntry(self.eventData);
            })
            .on('ajaxDialog:closed', '.js-manage-attachments, .js-manage-subcontribs', function(e) {
                api.set('content.text', function(evt, api) {
                    loadBalloonContent(self, api, editable);
                });
            })
            .on('ajaxDialog:loadError', '.js-move, .js-edit', function(evt, xhr) {
                if (xhr.status == 404) {
                    evt.preventDefault();
                    handleErrorResponse(xhr);
                }
            });

            $content.find('.js-switch-to-interval').on('click', function() {
                self.managementActions.switchToIntervalTimetable(self.eventData.id);
            });

            $content.find('.js-edit').on('click', function() {
                var extraParams = $(this).data('extra-params');
                ajaxDialog({
                    trigger: this,
                    url: build_url(Indico.Urls.Timetable.entries.edit, $.extend({}, urlParams, extraParams)),
                    title: $(this).data('title'),
                    onClose: function(data) {
                        if (data) {
                            handleNotifications(data);
                            self.timetable._updateDay(data.update);
                        }
                    }
                });
            });

            $content.find('.js-move').on('click', function() {
                var urlArgs = {
                    confId: self.eventData.conferenceId,
                    entry_id: self.eventData.scheduleEntryId
                };
                if (self.timetable.isSessionTimetable) {
                    urlArgs.session_id = self.timetable.contextInfo.sessionId;
                }
                ajaxDialog({
                    url: build_url(Indico.Urls.Timetable.entries.move, urlArgs),
                    data: {'day': self.timetable.currentDay},
                    title: $T.gettext("Move entry"),
                    subtitle: $(this).data('subtitle'),
                    trigger: this,
                    onClose: function(data) {
                        if (data) {
                            self.managementActions.moveToSession(self.eventData, data, true, null);
                        }
                    }
                });
            });

            var $picker = $content.find('.palette-picker');
            $picker.palettepicker({
                availableColors: $picker.data('palette'),
                selectedColor: $picker.data('initial-color'),
                onSelect: function(background, text) {
                    $.ajax({
                        url: $picker.data('href'),
                        method: $picker.data('method'),
                        data: JSON.stringify({'colors': {'text': text, 'background': background}}),
                        dataType: 'json',
                        contentType: 'application/json',
                        complete: IndicoUI.Dialogs.Util.progress(),
                        error: handleAjaxError,
                        success: function(data) {
                            self.managementActions._addEntries(data.entries);
                        }
                    });
                },
                qtipConstructor: function(element, qtipOptions) {
                    var qtipId = $picker.closest('.qtip').data('qtip-id');
                    $('[data-hasqtip=' + qtipId + ']').qbubble('createNested', element, qtipOptions);
                }
            });

        }
        $content.find('.js-hide-balloon').on('click', hideBalloon);
        // Change the target of the qTip position in order to open it at the mouse position
        $content.closest('.qtip').trigger('qbubble:ajaxload');
    }, function(xhr, status, error) {
        if (xhr.status == 404) {
            handleErrorResponse(xhr);
            api.set('content.text', $T.gettext('This timetable entry does not exist anymore. Please refresh the page.'));
        }
    });

    return $T.gettext('Loading...');
}

function handleErrorResponse(xhr) {
    cornerMessage({
        message: $T.gettext('This timetable entry does not exist anymore. Please refresh the page.'),
        actionLabel: $T.gettext('Refresh'),
        actionCallback: function() {
            location.reload();
        },
        duration: 10000,
        class: 'error'
    });
}

function drawBalloon(self, evt, editable) {
    var timetableBlock = $(self.div.dom);
    var entryId = self.eventData.scheduleEntryId ? self.eventData.scheduleEntryId : self.eventData.id.substring(1);

    if ($('html').data('static-site')) {
        var url;
        if (self.eventData.entryType == 'Session') {
            url = build_url(Indico.Urls.Sessions.display_session, {
                'confId': self.eventData.conferenceId,
                'session_id': self.eventData.sessionId
            });
        } else if (self.eventData.entryType == 'Contribution') {
            url = build_url(Indico.Urls.Contributions.display_contribution, {
                'confId': self.eventData.conferenceId,
                'contrib_id': self.eventData.contributionId}
            );
        } else {
            return;
        }
        location.href = url;
    } else {
        var isBreak = self.eventData.entryType == 'Break';

        timetableBlock.qbubble({
            id: entryId.toString(),
            content: {
                text: function(evt, api) {
                    return loadBalloonContent(self, api, editable);
                }
            },
            show: {
                ready: true
            },
            hide: {
                event: 'unfocus',
                fixed: true
            },
            events: {
                hide: function(evt, api) {
                    if (evt.originalEvent.type == 'mouseleave') {
                        evt.preventDefault();
                    }
                },
                render: function(e, api) {
                    api.elements.target.on('click', function() {
                        api.hide();
                    });
                },
            },
            position: {
                at: 'top center',
                my: 'bottom center',
                target: [evt.pageX, evt.pageY],
                adjust: {
                    mouse: false
                },
                effect: false
            },
            style: {
                classes: 'balloon-qtip ' + (editable ? 'edit-mode' : 'display-mode') + (isBreak ? ' no-details' : '')
            }
        });
    }
}

type("TimetableBlockDisplayMixin",[],
     {
         _drawPopup: function(evt) {
            drawBalloon(this, evt, false);
         }

     });


type("TimetableBlockManagementMixin", ["DragAndDropBlockMixin"],
    {
        _drawPopup: function(evt) {
            drawBalloon(this, evt, true);
        },

        _getRightSideDecorators: function() {
            return this.arrows;
        },

        _drawArrows: function() {
            var self = this;
            var arrowUp = $('<a>', {class: 'i-link icon-collapse'});
            var arrowDown = $('<a>', {class: 'i-link icon-expand'});

            if (self.eventData.canSwapUp) {
                arrowUp.attr('title', $T.gettext('Move up'));
                arrowUp.on('click', function() {
                    self.managementActions.swapEntry(self.eventData, 'up');
                });
            } else {
                arrowUp.addClass('disabled');
            }

            if (self.eventData.canSwapDown) {
                arrowDown.attr('title', $T.gettext('Move down'));
                arrowDown.on('click', function() {
                    self.managementActions.swapEntry(self.eventData, 'down');
                });
            } else {
                arrowDown.addClass('disabled');
            }

            if (self.eventData.canSwapDown || self.eventData.canSwapUp) {
                this.arrows = Html.div({className: 'entry-arrows'}, arrowUp.get(0), arrowDown.get(0));
            }
        }
    },
    function() {
        var isParallel = this.timetable.isSessionTimetable ? this.eventData.isParallelInSession
                                                           : this.eventData.isParallel;

        if (!isParallel && (!this.timetable.isTopLevel || this.timetable.canManageBlocks)) {
            this._drawArrows();
        }
        this.DragAndDropBlockMixin();
    }
);

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
             return this.eventData.friendlyId >= 0 ? this.eventData.friendlyId + " - " + title : title;
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
            data = _.sortBy(data, function(d) { return [d.startDate.date, d.startDate.time, d.title]; });
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

                function createEditLink(blockData) {
                    var link = $('<a>', {
                        class: 'i-link icon-edit',
                        title: $T.gettext("Edit"),
                        data: {
                            title: $T.gettext("Edit poster"),
                            confId: blockData.conferenceId,
                            timetableEntryId: blockData.scheduleEntryId
                        }
                    }).on('click', function(evt, params) {
                        var $this = $(this);
                        var urlArgs = {
                           'confId': $this.data('confId'),
                           'entry_id': $this.data('timetableEntryId')
                        };
                        if (self.timetable.isSessionTimetable) {
                            urlArgs.session_id = self.timetable.contextInfo.sessionId;
                        }
                        ajaxDialog({
                            trigger: this,
                            url: build_url(Indico.Urls.Timetable.entries.edit, urlArgs),
                            title: $this.data('title'),
                            onClose: function(data) {
                                if (data) {
                                    handleNotifications(data);
                                    self.timetable._updateDay(data.update);
                                }
                            }
                        });
                    });

                    return Html.$(link);
                }

                function createProtectionLink(blockData) {
                    var link = $('<a>', {
                        class: 'i-link icon-shield',
                        title: $T.gettext("Manage protection"),
                        data: {
                            title: $T.gettext("Manage poster protection"),
                            confId: blockData.conferenceId,
                            contribId: blockData.contributionId
                        }
                    }).on('click', function(evt) {
                        var $this = $(this);
                        var urlArgs = {
                           'confId': $this.data('confId'),
                           'contrib_id': $this.data('contribId'),
                        };
                        ajaxDialog({
                            trigger: this,
                            url: build_url(Indico.Urls.Timetable.contributions.protection, urlArgs),
                            title: $this.data('title'),
                            onClose: function(data) {
                                if (data && data.entries) {
                                    self.managementActions._addEntries(data.entries);
                                }
                            }
                        });
                    });

                    return Html.$(link);
                }

                function createDeleteLink(blockData) {
                    var tooltipText, dialogTitle, dialogText;
                    if (self.timetable.eventInfo.isConference) {
                        tooltipText = $T.gettext("Unschedule");
                        dialogTitle = $T.gettext("Unschedule poster");
                        dialogText = $T.gettext("Are you sure you want to unschedule the poster?");
                    } else {
                        tooltipText = $T.gettext("Delete");
                        dialogTitle = $T.gettext("Delete poster");
                        dialogText = $T.gettext("Are you sure you want to delete the poster?");
                    }
                    var link = $('<a>', {
                        class: 'i-link icon-remove',
                        title: tooltipText,
                        data: {
                            title: dialogTitle,
                            confirm: dialogText
                        }
                    }).on('click', function(evt) {
                        confirmPrompt($(this).data('confirm'), $(this).data('title')).then(function() {
                            self.managementActions.deleteEntry(blockData);
                        });
                    });

                    return Html.$(link);
                }

                var entryTools = Html.div({className: 'group right'});
                if (!self.timetable.isSessionTimetable || self.timetable.canManageContribs) {
                    entryTools.append(createEditLink(blockData));
                    entryTools.append(createProtectionLink(blockData));
                }
                if (self.timetable.eventInfo.isConference || self.timetable.canManageContribs) {
                    entryTools.append(createDeleteLink(blockData));
                }
                var entryInfo = Html.div({},blockData.friendlyId + " - " + blockData.title );
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

(function() {
    'use strict';

    $(document).on('qbubble:ajaxload', '.balloon-qtip.display-mode:not(.no-details)', function() {
        var $description = $(this).find('.description');
        $description.on('click', function(e) {
            var newTab = e.which == 2;  // Middle click
            var url = $(this).data('displayHref');
            if (newTab) {
                window.open(url, '_blank');
            } else {
                window.location.href = url;
            }
        });
    });
})();
