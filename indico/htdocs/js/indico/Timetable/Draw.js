type("TimetableBlock", [],
     {
         _blockDescription: function(block, event) {
             var self = this;

             this.titleDiv = Html.div({className: 'timetableBlockTitle'}, this.eventData.title);

             this.div = Html.div({style: { width: '100%', height: '100%'}}, this.titleDiv);

             if (!self.printableVersion) {
                 this.div.dom.style.cursor = 'pointer';
             }


             if (!this.compactMode) {
                 this.timeDiv = Html.div({className: 'timetableBlockTime'}, this.eventData.startDate.time.substring(0,5) +' - '+ this.eventData.endDate.time.substring(0,5));
                 this.locationDiv = Html.div({className: 'timetableBlockLocation'}, this.eventData.room, Html.br(), this.eventData.location);
                 this.div.append(this.timeDiv);
                 this.div.append(this.locationDiv);
             } else {
                 this.timeDiv = Html.div({className: 'timetableBlockTimeDiscreet', style: {color: self.printableVersion ? 'black' : ''}}, this.eventData.startDate.time.substring(0,5) +' - '+ this.eventData.endDate.time.substring(0,5));
                 this.div.insert(this.timeDiv);
             }

             this.div.observeClick(function(e) {
                 // No popups in printable version
                 if (self.printableVersion) {
                     return;
                 }

                 // If popup alredy shown do nothing
                 if (self.popupActive) {
                     return;
                 }

                 self.popupActive = true;
                 self.div.dom.style.cursor = 'default';

                 var cursor = getMousePointerCoordinates(e);

                 var popup = new TimetableBlockPopup(self.eventData, self.div, function() {
                     self.div.dom.style.cursor = 'pointer';
                     self.popupActive = false;
                     return self.popupAllowClose;
                 },function(color) {
                     var parent = self.div.getParent();
                     parent.setStyle('backgroundColor', color);
                 });
                 popup.open(cursor.x, cursor.y);
             });

             return this.div;
         },

         draw: function(leftPos, width) {

             var classTable = {
                 'Session': 'timetableSession',
                 'Contribution': 'timetableContribution',
                 'Break': 'timetableBreak'
             };

             return Html.div({style:
                              {
                                  position: 'absolute',
                                  top: pixels(this.blockData.start),
                                  height: pixels(this.blockData.end-this.blockData.start-3),
                                  backgroundColor: this.printableVersion ? 'white' : this.eventData.color,
                                  borderColor: this.printableVersion ? 'black' : '',
                                  left: pixels(leftPos),
                                  width: pixels(width-3),
                                  borderBottomStyle: this.blockData.unfinished?'dashed':''
                              },
                              className: 'timetableBlock ' + classTable[this.eventData.entryType]
                             }, this._blockDescription());
         },
         postDraw: function() {
             var self = this;
             var title = this.eventData.title;

	     // sets the highlighting effect
	     highlightWithMouse(this.div, this.div.getParent());

             // Returns the total height of the divs in the block
             var contentHeight = function() {
                 var h = 0;
                 if (!self.compactMode) {
                     h = self.locationDiv.dom.offsetHeight + self.margin;
                 }

                 return self.titleDiv.dom.offsetHeight + h;
             };
             var contentWidth = function() {
                 return self.timeDiv.dom.offsetWidth + self.locationDiv.dom.offsetWidth + 2*self.margin;
             };

             // Truncates the title to the size numChars
             // If truncate is < 0 remove numChar characters
             var truncateTitle = function(numChars) {
                 if (numChars >= title.length) {
                     return title;
                 }

                 if (numChars < 0) {
                     // Never truncate more than the length of  the string
                     if (-numChars >= title.length) {
                         return title;
                     } else {
                         numChars = title.length + numChars;
                     }
                 }

                 title = title.substring(0, numChars) + "...";
                 self.titleDiv.set(title);
                 return title;
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
                 if (this.timeDiv.dom.offsetWidth + 8 >= parentDivWidth) {
                     this.timeDiv.dom.style.display = 'none';
                     this.locationDiv.dom.style.display = 'none';
                 }
                 else if (contentWidth() >= parentDivWidth) {
                     this.timeDiv.dom.style.display = 'none';
                 }
             }

             // If content height <= div height then nothing needs to be done
             if (contentHeight() <= parentDivHeight) {
                 return;
             }

             // Truncate title based on a ratio: div height / content height
             truncateTitle(Math.ceil(this.eventData.title.length * ((parentDivHeight) / contentHeight())));

             var step = Math.ceil(parentDivWidth / 20);
             while (contentHeight() > parentDivHeight && title.length > step) {
                 truncateTitle(-step);
             }

         }
     },
     function(eventData, blockData, compactMode, printableVersion){
         this.compactMode = compactMode;
         this.eventData = eventData;
         this.blockData = blockData;
         this.margin = TimetableDefaults.blockMargin;
         this.popupActive = false;
         this.popupAllowClose = true;
         this.printableVersion = any(printableVersion, false);
     }
    );

type("TimetableColorPicker", ["PopupDialog"], {
    draw: function(x, y) {
        var self = this;

        var colors = ['#c6e1c1', '#f4ca88', '#f9ad90', '#e8f4cb', '#cbdef4', '#d5d5d5', 'brown', 'black', 'violet'];
        var tbody = Html.tbody({});
        var tr;
        var i = 0;
        each(colors, function(c) {
            if (i++ % 3 == 0) {
                tr = Html.tr();
                tbody.append(tr);
            }
            var colorBlock = Html.div({className: 'timetableColorPickerBlock', style: {backgroundColor: c, cursor: 'pointer'}});
            colorBlock.observeEvent('mouseover', function() {
                self.tmpColor = colorBlock.dom.style.backgroundColor;
                if (self.tmpColor === ''){
                    return;
                }

                var bgColor = colorBlock.dom.style.backgroundColor;
                var s = bgColor.match(/rgb\((\d+), (\d+), (\d+)\)/);
                if (!s) {
                    s = bgColor.match(/#(..)(..)(..)/);
                    if (!s)
                        return;

                    s[1] = parseInt('0x'+s[1],16);
                    s[2] = parseInt('0x'+s[2],16);
                    s[3] = parseInt('0x'+s[3],16);
                }
                s[1] = Math.floor(s[1]*1.05);
                s[2] = Math.floor(s[2]*1.05);
                s[3] = Math.floor(s[3]*1.05);
                colorBlock.setStyle('backgroundColor', 'rgb(' + s[1] + ',' + s[2] + ',' + s[3] + ')');
            });
            colorBlock.observeEvent('mouseout', function(event) {
                colorBlock.setStyle('backgroundColor', self.tmpColor);
            });
            colorBlock.observeClick(function (e) {
                self.colorClickHandler(c);
                self.close();
            });
            tr.append(Html.td({}, colorBlock));
        });

        this.div.append(Html.table({}, tbody));
        return this.PopupDialog.prototype.draw.call(this, this.div, x, y);
    },
    open: function() {
        var pos = this.colorPickerElement.getAbsolutePosition();
        return this.PopupDialog.prototype.open.call(this, pos.x-20, pos.y+20);
    }
},
     function(colorPickerElement, colorClickHandler, closeHandler) {
         this.colorPickerElement = colorPickerElement;
         this.colorClickHandler = colorClickHandler;
         this.div = Html.div('timetableColorPicker');
         this.PopupDialog(this.div, colorPickerElement, closeHandler);
     });

type("TimetableBlockPopup", ["BalloonPopup"], {
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
        
        if (self.managmenetMode) {
            var menuBar = this.createManagementMenuBar();
        } else {
            var menuBar = this.createDisplayMenuBar()
        }
        if (menuBar) {
            div.append(menuBar);
        }
        
        var infoDiv = this.createInfoDiv();
        div.append(infoDiv);
        
        var contributions = this.createContributionList()
        if (contributions) {
            div.append(contributions);
            div.dom.style.width = pixels(this.popupWidth + 50);
        }

        return div;
    },

    createInfoDiv: function() {
        var self = this;
        
        var infoContentDiv = Html.div({className: 'timetablePopupInfoContent'});
        
        infoContentDiv.append(Html.div({className: 'timetablePopupTimeDiv'},
                              self.eventData.startDate.time.substring(0,5) + ' - ' + 
                              self.eventData.endDate.time.substring(0,5)));
        
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

        // If it's a contribtion the add speakers information
        if (self.eventData.entryType == 'Contribution') {
            var speakers = Html.span();
            var i = 0;
            each(self.eventData.presenters, function(p) {
                speakers.append(i++ > 0 ? ', ' : '' + p.name);
                if (p.affiliation && p.affiliation != '') {
                    speakers.append(Html.em({style: {fontSize: '9pt'}}, ' (' + p.affiliation + ')'));
                }
            });
            if (i > 0) {
                infoContentDiv.append(Html.strong({style:{fontStyle: 'normal'}}, 'Presenter(s): '));
                infoContentDiv.append(speakers);
            }
        }

        // Add the description and if it's too long cut it down
        var desc = self.eventData.description;
        if (desc && desc != '') {
            infoContentDiv.append(Html.span({style: {display: 'block', marginTop: pixels(5)}},
                                  desc.length > 200 ? desc.substr(0, 200) + '...' : desc));
        }

        return Html.div({className: 'timetablePopupInfoWrapper'}, infoContentDiv);
    },
    
    createManagementMenuBar: function() {
        var self = this;
        
        // The admin menu
        var colorSelector = Html.div({style: {display: 'inline', cursor: 'pointer'}}, 'Color: ',
                            Html.div({className: 'timetableColorPickerBlock',
                                style: {display: 'inline', backgroundColor: self.eventData.color}},
                            Html.img({src: 'images/0.png', width: '15', height: '5'})));

        // Handles the color selector
        colorSelector.observeClick(function(e) {
            // If open just close it
            if (self.colorPickerOpen) {
                self.colorPicker.close();
                self.colorPickerOpen = false;
                return;
            }

            self.colorPicker = new TimetableColorPicker(colorSelector, function(color) {
                self.colorPickerOpen = false;
                self.colorClickHandler(color);
            }, function() { self.colorPickerOpen = false; return true; });
            // Make sure that clicking in the color picker div doesn't close
            // balloon popup
            self.addNonCloseTriggeringElement(self.colorPicker.div);
            self.colorPicker.open();
            self.colorPickerOpen = true;
        });

        var href = '';
        if (self.eventData.entryType == 'Contribution') {
            href = Indico.Urls.ContributionModification + '?confId=' + self.eventData.conferenceId + '&contribId=' + self.eventData.contributionId;
        } else {
            href = Indico.Urls.SessionModification + '?confId=' + self.eventData.conferenceId + '&sessionId=' + self.eventData.sessionId;
        }
        var modifyLink = Html.a({'href': href, className: 'timetablePopupAdminLink'}, "Modify");

        return Html.div({className: 'managementMenuBar'}, Html.div({}, modifyLink, " | ", colorSelector));
    },

    createDisplayMenuBar: function() {
        var self = this;
        
        // There is only a need for a menu bar when we show contribution or session
        if (self.eventData.entryType != 'Contribution' && self.eventData.entryType != 'Session') {
            return null;
        }

        var exportLink = Html.a('dropDownMenu fakeLink', "Export");

        exportLink.observeClick(function () {
            var menuItems = {};
            if (self.eventData.entryType == 'Contribution') {
                var urlParams = '?contribId=' + self.eventData.contributionId + '&confId=' + self.eventData.conferenceId
                menuItems["PDF file"] = Indico.Urls.ContribToPDF + urlParams;
                menuItems["Calendar"] = Indico.Urls.ContribToiCal + urlParams;
                menuItems["XML"] = Indico.Urls.ContribToXML + urlParams;
            } else if (self.eventData.entryType == 'Session') {
                var urlParams = '?showSessions=' + self.eventData.sessionId + '&confId=' + self.eventData.conferenceId
                menuItems["PDF timetable"] = Indico.Urls.ConfTimeTablePDF + urlParams;

                urlParams = '?sessionId=' + self.eventData.sessionId + '&confId=' + self.eventData.conferenceId
                menuItems["Calendar"] = Indico.Urls.SessionToiCal + urlParams;
            }

            var exportMenu = new PopupMenu(menuItems, [exportLink], null, true, true);
            var pos = exportLink.getAbsolutePosition();
            exportMenu.open(pos.x + exportLink.dom.offsetWidth, pos.y + exportLink.dom.offsetHeight);
        });
        
        var url = "#";
        if (self.eventData.entryType == 'Contribution') {
            url = Indico.Urls.ContributionDisplay + '?contribId=' + self.eventData.contributionId + '&confId=' + self.eventData.conferenceId;
        } else if (self.eventData.entryType == 'Session') {
            url = Indico.Urls.SessionDisplay + '?sessionId=' + self.eventData.sessionId + '&confId=' + self.eventData.conferenceId;
        }
        var viewLink = Html.a({'href': url}, "View details");

        return Html.div({className: 'menuBar'}, Html.div({}, viewLink, "|", exportLink));
    },
    
    createContributionList: function() {
        var self = this;
        
        var contributions = Html.tbody({});
        var contributionsDiv = Html.div({className: 'timetablePopupContributions'}, "Contributions");

        var contribs = [];
        each(this.eventData.entries, function(value, key) {
            if (value.entryType == 'Contribution') {
                contribs.push(value);
            }
        });
        
        if (contribs.length == 0)
            return null;
        
        contribs.sort(function(a,b) {
            if (a.startDate.time > b.startDate.time) {
                return 1;
            }
            return -1;
        });
        var i = 0;
        each(contribs, function(value) {
            if (++i < 6) {
                var link = Html.a({href: Indico.Urls.ContributionDisplay + '?sessionId=' + value.sessionId + '&contribId=' + value.contributionId + '&confId=' + value.conferenceId, style: {fontWeight: 'normal'}}, value.title);
                contributions.append(Html.tr({}, Html.td('timetablePopupContributionTime', self.eventData.isPoster ? '-' : value.startDate.time.substr(0,5)),
                                             Html.td('timetablePopupContributionTitle', link)));
            }
        });
        if (i >= 6) {
            contributions.append(Html.tr({}, Html.td({}), Html.td({}, Html.span({style: {fontSize: '9pt', fontWeight: 'normal', fontStyle: 'italic', color: '#444444'}}, '' + (i - 5) + ' more contribution(s)...'))));
        }
        contributionsDiv.append(Html.table({style: {marginTop: pixels(5)}}, contributions));

        detailsLink = Html.div({style: {marginTop: pixels(5), marginLeft: pixels(5)}}, Html.span({className: "fakeLink", style: {fontStyle: 'italic', fontWeight: 'normal'}}, contribs.length >= 6 ? "View all contributions" : "View contribution list"));
        contributionsDiv.append(detailsLink);

        detailsLink.observeClick(function (e) {
            self.close();
            var popup = new ContributionsPopup(self.eventData, contribs, function() {self.popupAllowClose = true; return true;});
            popup.open();
        });
        
        //timetableLink = Html.div({style: {marginTop: pixels(5), marginLeft: pixels(5)}}, Html.span({className: "fakeLink", style: {fontStyle: 'italic', fontWeight: 'normal'}}, "View timetable"));
        //contributionsDiv.append(timetableLink);

        //timetableLink.observeClick(function (e) {
        //    self.close();
        //    var popup = new TimetablePopup(self.eventData, contribs, function() {self.popupAllowClose = true; return true;});
        //    popup.open();
        //});
        
        return contributionsDiv;
    }
    },
     function(eventData, blockDiv, closeHandler, colorClickHandler, managementMode) {
         this.eventData = eventData;
         this.triggerElement = blockDiv;
         this.popupWidth = 300;
         this.colorClickHandler = colorClickHandler;
         this.colorPickerOpen = false;

         this.managementMode = any(managementMode, false);

         this.BalloonPopup(this.createContent(), blockDiv, closeHandler);
     }
    );

type("ContributionsPopup", ["ExclusivePopup"], {

    draw: function() {
        var self = this;
        var table = Html.tbody({});
        each(this.contributions, function(contrib) {
            var time = Html.div({style: {paddingTop: pixels(7), marginRight: pixels(3), fontSize: '9pt', fontWeight: 'bold'}}, self.eventData.isPoster ? '' : contrib.startDate.time.substr(0,5));
            var link = Html.a({href: Indico.Urls.ContributionDisplay + '?sessionId=' + contrib.sessionId + '&contribId=' + contrib.contributionId + '&confId=' + contrib.conferenceId}, contrib.title);
            var title = Html.div({style: {color: '#444444', width: pixels(self.width), padding: pixels(5), fontSize: '11pt'}}, link);

            var infoDiv = Html.div({style: {width: pixels(self.width), border: '1px solid rgb(234, 234, 234)', marginBottom: pixels(10), marginLeft: pixels(5), padding: pixels(5), backgroundColor: 'rgb(248, 248, 248)',color: '#444444', fontSize: '9pt'}});

            var showFullDescLink = Html.a({style: {cursor: 'pointer', fontWeight: 'bold', fontSize: '9pt', fontStyle: 'italic'}}, ' Show full description');
            var hideFullDescLink = Html.a({style: {cursor: 'pointer', fontWeight: 'bold', fontSize: '9pt', fontStyle: 'italic'}}, ' Hide full description');
            var shortDesc = Html.span({style: {display: 'block'}}, contrib.description.substr(0, 250) + '... ', showFullDescLink);
            var longDesc = Html.span({style: {display: 'none'}}, contrib.description, hideFullDescLink);

            if (contrib.description && contrib.description != '') {
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
                    if (p.affiliation && p.affiliation != '') {
                        speakers.append(Html.em({style: {fontSize: '9pt'}}, ' (' + p.affiliation + ')'));
                    }
                });

                infoDiv.append(speakers);
            }

            if (contrib.room && contrib.room != '') {
                var room = Html.span({style: {marginTop: pixels(3), display: 'block'}}, Html.strong({}, 'Room: '), contrib.room);
                infoDiv.append(room);
            }

            if (contrib.location && contrib.location != '') {
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
         this.contributions = contributions;
         this.eventData = eventData;
         this.width = 500;

         this.ExclusivePopup('Contribution details', closeHandler, true, true);
     }
    );

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

         this.ExclusivePopup('This is going to show the timatable for a session', closeHandler);
     }
    );



type("TimetableDrawer", ["LookupTabWidget"],
     {

         _titleTemplate : function(text) {
             if (text == 'all')
                 return 'All days';

             var day = text.substring(6,8);
             var month = text.substring(4,6);

             var strDate =  day + '/' + month + '/' + text.substring(0,4);

             var nDate = new Date();
             setDate(nDate, parseDate(strDate));

             return Indico.Data.WeekDays[nDate.getDay()].substring(0,3)+' '+day+'/'+month;

         },

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

                 scaleDiv.append(Html.div({style:
                                           {
                                               position: 'absolute',
                                               top: pixels(px),
                                               width: pixels(this.width),
                                               height: hour==last?'20px':scale[n+1][1]-px,
                                               borderTop: '1px solid #E8E8E8',
                                               fontSize: '8pt'                                                 }}, zeropad(hour)+':00'));
             }

             return scaleDiv;
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

                 var eventData = data[blockData.id];

                 var block;

                 if (blockData.collapsed || (blockData.end - blockData.start < TimetableDefaults.layouts.proportional.values.pxPerHour)) {
                     block = new TimetableBlock(eventData, blockData, true, self.printableVersion);
                 } else {
                     block = new TimetableBlock(eventData, blockData, false, self.printableVersion);
                 }
                 self.blocks.push(block);
                 blockDiv.append(block.draw(leftPos, colWidth));

             });

             return blockDiv;
         },

         setLayout: function(layout) {
             this.layoutChooser.set(layout);
         },

         redraw: function(day) {
             if (this.blockRedraw) {
                 return;
             }

             var day = any(day, this.day);
             if (day == 'all') {
                 this.redrawAllDays();
                 return;
             }

             var dayFiltered = this.applyFilters(this.data[day]);

             if (this.detail.get() == 'contribution') {
                 dayFiltered = this.flatten(dayFiltered);
             }

             var dayData = this.layoutChooser.get().drawDay(dayFiltered);
             var height = dayData[0]+TimetableDefaults.topMargin+TimetableDefaults.bottomMargin;
             this.wrappingElement.setStyle('height', pixels(height + (this.printableVersion ? 0 : 100))); // +100 to have margin for the tabs

             // Only do if not all days are drawn
             this.canvas.set([this._drawGrid(dayData[1]),
                              this._drawBlocks(dayFiltered, dayData[2], dayData[3])]);

             this.postDraw();

             return height;
         },

         setPrintableVersion: function(printableVersion) {
             this.printableVersion = printableVersion;
             this.redraw();
         },

         postDraw: function() {
             each(this.blocks, function(block) { block.postDraw(); });
             this.LookupTabWidget.prototype.postDraw.call(this);
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
                     });
                 } else {
                     result[key] = entry;
                 }
             });

             return result;
         },

         drawDay: function(day) {
             this.day = day;

             this.blockRedraw = true;
             this.updateFilters(day);
             this.blockRedraw = false;

             this.redraw(day);

             return this.canvas;
         },

         drawAllDays: function() {
             this.day = 'all';

             this.blockRedraw = true;
             this.updateFilters('all');
             this.blockRedraw = false;

             this.redrawAllDays();

             return this.canvas;
         },

         redrawAllDays: function() {
             var self = this;
             var days = [];
             // Add the elements to an array and sort it based on date
             each(this.data['all'], function(value, key) {
                 if (key != 'all') {
                     value['date'] = key;
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
                 delete value['date'];
                 var h = self.redraw(day);

                 // Copy all the elements in canvas
                 var elements = translate(self.canvas.dom.childNodes, function(value) {return $E(value);});
                 var dayCanvas = Html.div({style: {position: 'relative', height: pixels(h)}}, elements);

                 // Add a div containing the date
                 var headerStyle = {width: pixels(self.width-10)}; // substract the padding
                 if (self.printableVersion) {
                     headerStyle['textAlign'] = 'center';
                     headerStyle['borderBottom'] = '0';
                 } else if (firstDay) {
                     headerStyle['marginTop'] = '0';
                     headerStyle['paddingTop'] = '0';
                 }
                 header = Html.div({className: 'timetableHeader', style: headerStyle}, self._titleTemplate(day));
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
         }
     },
     function(data, width, wrappingElement, detailLevel, extraButtons) {


         var self = this;

         this.wrappingElement = wrappingElement;
         this.canvas = Html.div('canvas'); // TODO: remove canvas
         this.filterList = new WatchList();
         this.data = data;
         // This is used to draw all days
         this.data.all = this.data;
         this.blocks = [];
         this.width = width;
         // Prevents redraw when set to true
         this.blockRedraw = false;
         // Used to switch between normal and printable version
         this.printableVersion = false;

         // layoutKey -> layoutManager map
         this.layoutChooser =  new Chooser(map(TimetableDefaults.layouts,
                                               function(value, key) {
                                                   return value.manager;
                                               }));

         this.detail = new WatchValue();
         this.layout = new WatchValue();

         // default layout is 'proportional'
         this.layout.set('proportional');
         this.layoutChooser.set('proportional');
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

         // Set the initial tab to today's date if exists
         var today = new Date();
         var todayStr = IndicoUtil.formatDate2(today);
         var initialTab = -1;
         while (exists(data[todayStr])) {
             today.setDate(today.getDate()-1);
             todayStr = IndicoUtil.formatDate2(today);
             initialTab++;
         }
         // if today not found, set initial tab to the first one
         if (initialTab == -1) {
             initialTab = 0;
         }

         var sortedKeys = keys(this.data);
         sortedKeys.sort();
         
         // Extra buttons such as print and filter, displayed in tab widget
         var extraButtons = any(extraButtons, []);
         
         // the widget consists in a "rich" tab widget, where
         // each tab is a day
         this.LookupTabWidget( translate(sortedKeys, function(key) {
             return [key, function() {
                 // each time one tab is clicked,
                 // drawDay is called over a different day
                 if (key == 'all') {
                     return self.drawAllDays();
                 } else {
                     return self.drawDay(key);
                 }
             }];
         }), this.width, 100, initialTab, extraButtons);

         this.detail.observe(function(value) {
             self.redraw();
         });

         this.layout.observe(function(value) {
             self.layoutChooser.set(value);
             self.redraw();
         });
     });

