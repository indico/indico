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

              // If popup alredy shown do nothing
             if (self.popupActive || self.materialMenuOpen) {
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

         _getRightSideDecorators: function()
         {
             return Html.span({});
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
            _blockDescription: function(block, event) {
                var self = this;

                this.titleDiv = Html.div({className: 'timetableBlockTitle', style: {fontWeight: this.eventData.fontWeight}}, this.eventData.title);
                // If it's a session slot it might have a slot title that should be
                // added to the title
                if (this.eventData.slotTitle && this.eventData.slotTitle !== "") {
                    this.titleDiv.append(": " + this.eventData.slotTitle);
                }

                this.titleWrapper = Html.div({}, this._getRightSideDecorators(), this.titleDiv);

                this.div = Html.div({style: { width: '100%', height: '100%'}}, this.titleWrapper);

                if (this.compactMode) {
                    this.timeDiv = Html.div('timetableBlockTimeDiscreet', this.eventData.startDate.time.substring(0,5) +' - '+ this.eventData.endDate.time.substring(0,5));
                    this.div.insert(this.timeDiv);
                } else {
                    this.timeDiv = Html.div({className: 'timetableBlockTime'}, this.eventData.startDate.time.substring(0,5) +' - '+ this.eventData.endDate.time.substring(0,5));

                    this.locationDiv  = Html.div('timetableBlockLocation');
                    var addComma = false;
                    if (this.eventData.room) {
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

                var classTable = {
                    'Session': 'timetableSession',
                    'Contribution': 'timetableContribution',
                    'Break': 'timetableBreak'
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
                   this.block.dom.style.cursor = 'pointer';
                   this.block.observeClick(function(e) { self.openPopup(e); });
                   highlightWithMouse(this.div, this.block);
                   showWithMouse(this.div, this.arrows);
               }

               return this.block;
           },
            postDraw: function(hook) {
                var self = this;
                var title = this.eventData.title;

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

                // If nothin has been drawn do nothing
                if (!parentDivHeight) {
                    return;
                }

                // If no space for location and time info then hide the divs
                if (this.compactMode && parentDivWidth < 200) {
                    this.timeDiv.dom.style.display = 'none';
                }
                if (!this.compactMode) {
                    var locationMaxWidth = parentDivWidth  - 20;

                    // Hide the time if there are not enough space
                    if (this.timeDiv.dom.offsetWidth + 8 >= parentDivWidth) {
                        this.timeDiv.dom.style.display = 'none';
                    }
                    else if (contentWidth() >= parentDivWidth) {
                        this.timeDiv.dom.style.display = 'none';
                    } else {
                        locationMaxWidth -= this.timeDiv.dom.offsetWidth;
                    }

                    this.locationDiv.dom.style.maxWidth = pixels(locationMaxWidth);

                    // Presenters information should not take more than half of the space of the block
                    if (this.presentersDiv && this.presentersDiv.dom.offsetWidth > parentDivWidth / 2) {
                        this.presentersDiv.dom.style.display = 'none';
                    }
                }

                // If content height <= div height then nothing needs to be done
                if (contentHeight() <= parentDivHeight) {
                    return;
                }

                // Try to remove the location info, and set title font weight to non bold,
                // if this works then we're done otherwisestart to truncate the title as well.
                if (this.timeDiv.dom.style.display == 'none') {
                    this.locationDiv.dom.style.display = 'none';
                }

                if (contentHeight() <= parentDivHeight) {
                    return;
                }

                // Truncate title based on a ratio: div height / content height
                this.titleDiv.set(this.truncateTitle(Math.ceil(this.eventData.title.length * ((parentDivHeight) / contentHeight())), title));

                var step = Math.ceil(parentDivWidth / 40);
                while (contentHeight() > parentDivHeight && title.length > step) {
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
                    'Contribution': 'timetableContribution',
                    'Break': 'timetableBreak'
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


         this.arrows = Html.div({style: {cssFloat: 'right', padding: '2px'}}, arrowUp, arrowDown);
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

    _getGeneralInfo: function() {
        var self = this;

        var infoContentDiv = Html.div({className: 'timetablePopupInfoContent'});

        infoContentDiv.append(this._getTime());

        if (self.eventData.room) {
            infoContentDiv.append(Html.strong({style:{fontStyle: 'normal'}}, 'Room: '));
            infoContentDiv.append(self.eventData.room);
            infoContentDiv.append(Html.br());
        }

        if (self.eventData.location) {
            infoContentDiv.append(Html.strong({style:{fontStyle: 'normal'}}, 'Location: '));
            infoContentDiv.append(self.eventData.location);
            infoContentDiv.append(Html.br());
        }

        // If it's a contribtion add speaker information
        if (self.eventData.entryType == 'Contribution') {
            var speakers = Html.span();
            var i = 0;
            each(self.eventData.presenters, function(p) {
                speakers.append(i++ > 0 ? ', ' : '' + p.name);
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
            url = Indico.Urls.SessionDisplay + '?sessionId=' + self.eventData.sessionId + '&confId=' + self.eventData.conferenceId;
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
                contributions.append(Html.tr({}, Html.td('timetablePopupContributionTime', self.eventData.r ? '-' : value.startDate.time.substr(0,5)),
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

    _getTime: function() {
        var self = this;

        var editLink = Html.a({className: 'fakeLink', style: {marginLeft: '10px'}}, '[edit]');
        var timeDiv = Html.div({},
                               this.eventData.startDate.time.substring(0,5) + ' - ' +
                               this.eventData.endDate.time.substring(0,5), editLink);

        var startEndTimeField = IndicoUI.Widgets.Generic.dateStartEndTimeField(
                this.eventData.startDate.time.substring(0,5),
                this.eventData.endDate.time.substring(0,5));

        var parameterManager = new IndicoUtil.parameterManager();

        parameterManager.add(startEndTimeField.startTimeField, 'time', false);
        parameterManager.add(startEndTimeField.endTimeField, 'time', false,
                             function(value) {
                                 var sTime = translate(parseTime(startEndTimeField.startTimeField.get()), zeropad).join('');
                                 var eTime = translate(parseTime(value), zeropad).join('');
                                 if (eTime <= sTime) {
                                     return "End time should be after start time!";
                                 }
                             });

        var saveButton = Html.button({}, 'Save');
        saveButton.observeClick(function() {

            if (!parameterManager.check()) {
                return;
            }

            var startDate = clone(self.eventData.startDate);
            var endDate = clone(self.eventData.startDate);

            startDate.time = startEndTimeField.accessor.get('startTime');
            endDate.time = startEndTimeField.accessor.get('endTime');

            self.managementActions.editEntryStartEndDate(Util.formatDateTime(startDate, IndicoDateTimeFormats.Server),
                                                         Util.formatDateTime(endDate, IndicoDateTimeFormats.Server),
                                                         self.eventData,
                                                         rescheduleCheckbox.get());
            self.close();
        });
        var cancelButton = Html.button({}, 'Cancel');
        cancelButton.observeClick(function() {
            timeEditDiv.dom.style.display = 'none';
            timeDiv.dom.style.display = 'block';
        });

        var rescheduleCheckbox = Html.checkbox({style:{marginRight: '5px', verticalAlign: 'middle'}});

        var timeEditDiv = Html.div({style: {display: 'none', fontSize: '9pt'}},
                Html.div({style: {cssFloat: 'right'}}, saveButton, " ", cancelButton),
            startEndTimeField.element,
            Html.div({style: {marginTop: '5px'}}, rescheduleCheckbox, $T('Shift later entries')));


        editLink.observeClick(function() {
            // make sure the edit div is at least as high as the timeDiv
            // to avoid a small 'jump' in the balloon popup
            timeEditDiv.dom.style.display = 'block';
            //timeEditDiv.dom.style.height = pixels(timeDiv.dom.offsetHeight);
            timeDiv.dom.style.display = 'none';
        });


        return Html.div('timetablePopupTimeDiv', timeDiv, timeEditDiv);

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

            menuItems[$T('Interval timetable')] = function() {
                self.managementActions.switchToIntervalTimetable(self.eventData.id);
                self.close();
            };
            menuItems[$T('Interval properties')] = function() {
                self.managementActions.editSessionSlot(self.eventData);
                self.close();
            };
            if (!self.managementActions.isSessionTimetable) {
                menuItems[$T('Session properties')] = self.managementActions.editEntry(self.eventData);
            }

            editLink.observeClick(function() {
                var menu = new PopupMenu(menuItems, [editLink], 'timetableManagementPopupList', true, true);
                var pos = editLink.getAbsolutePosition();
                menu.open(pos.x + editLink.dom.offsetWidth + 2, pos.y + editLink.dom.offsetHeight + 2);
            });

        } else if (self.eventData.entryType == 'Contribution') {
            editLink = Html.a({
                className: 'fakeLink',
                style: {fontWeight: 'bold'},
                href: self.managementActions.editEntry(self.eventData)
            }, $T("Edit"));
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
                self.managementActions.moveEntryContrib(self.eventData);
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


        var ttLink = Html.a({className: 'fakeLink'}, "View and edit current interval timetable");
        ttLink.observeClick(function() {
            self.managementActions.switchToIntervalTimetable(self.eventData.id);
            self.close();
        });
        contributionsDiv.append(Html.div({style: {marginTop: '10px', fontWeight: 'bold'}}, ttLink));

        return contributionsDiv;
    }
    },
     function(timetable, block, eventData, blockDiv, closeHandler, managementActions) {
         this.block = block;
         this.managementActions = managementActions;
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

             var scaleDiv = Html.div({style:
                                      {
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

                 scaleDiv.append(Html.div({style:
                                           {
                                               position: 'absolute',
                                               top: pixels(px),
                                               width: pixels(this.width),
                                               height: hour==last?'20px':scale[n+1][1]-px,
                                               borderTop: '1px solid #E8E8E8',
                                               fontSize: '11px'}}, zeropad(hour)+':00'));
             }

             return scaleDiv;
         },

         _drawWholeDayBlocks: function(data, blocks) {
             var self = this;

             var wholeDayBlockDiv = Html.div({style:
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

             self.blocks = [];

             each(blocks, function(blockData) {

                 var nCol = groups[blockData.group][1];

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

             this.postDraw();

             return height + wholeDayBlocks.dom.offsetHeight;
         },

         setPrintableVersion: function(printableVersion) {
             this.printableVersion = printableVersion;
             this.redraw();
         },

         postDraw: function() {
             each(this.blocks, function(block) { block.postDraw(); });
         },

         /*
          * Sets the color for all session blocks belonging to the
          * session with sessionId
          */
         setSessionBlockColors: function (sessionId, textColor, bgColor) {
             var self = this;

             each(this.blocks, function(block) {
                 if (block.eventData.entryType == 'Session' && block.eventData.sessionId == sessionId) {
                     block.setColors(textColor, bgColor);
                 }
             });
         },

         flatten: function(data) {
             var result = {};
             each(data, function(entry, key) {
                 // sessions that are not poster sessions will be
                 // 'converted' to contributions
                 if (entry.entryType == 'Session' && !entry.isPoster) {
                     each(entry.entries, function(subentry, subkey) {
                         result[subkey] = clone(subentry);
                         result[subkey].color = entry.color;
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

                 // Format the day string
                 var d = day.substring(6,8);
                 var m = day.substring(4,6);
                 var strDate =  d + '/' + m + '/' + day.substring(0,4);
                 var nDate = new Date();
                 setDate(nDate, parseDate(strDate));
                 var dayStr = Indico.Data.WeekDays[nDate.getDay()].substring(0,3)+' '+d+'/'+m;

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
            var height = 100+TimetableDefaults.topMargin+TimetableDefaults.bottomMargin;
            this.wrappingElement.setStyle('height', pixels(height + (this.printableVersion ? 0 : 100))); // +100 to have margin for the tabs

            var blocks = this._posterBlocks(dayData);

            this.canvas.set(Html.div({style: {position: 'relative'}}, blocks));

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
                var entryInfo = Html.div({},blockData.title );
                var timeDiv = Html.div("posterBlockTime", blockData.startDate.time.substring(0,5) +' - '+ blockData.endDate.time.substring(0,5));
                var block = Html.div({className:'posterEntry'},
                    entryTools,
                    entryInfo,
                    Html.div({},timeDiv));
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
    }
);
