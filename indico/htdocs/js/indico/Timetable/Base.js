var TimetableDefaults = {
    topMargin: 30,
    bottomMargin: 40,
    leftMargin: 70,
    resolution: 10,
    menuWidth: 150,
    blockMargin: 4,         // Margin used inside timetable blocks
    layouts: {'compact': {name: "Compact",
                          values : {
                              pxPerHour: 50,
                              pxPerSpace: 2,
                              minPxPerBlock: 35
                          },
                          manager: new CompactLayoutManager()},

              'proportional': {name: 'Proportional',
                               values : {
                                   pxPerHour: 50,
                                   minPxPerBlock: 25
                               },
                               manager: new ProportionalLayoutManager()
                              }
             },
    filters: {'session': {name: $T('Session'),
                          filter: new SessionFilter()},
              'room': {name: $T('Room'),
                       filter: new RoomFilter()}}
};

type("TimeTable", ["IWidget"],
     {
         draw: function() {
             return this.IWidget.prototype.draw.call(this,
                                                     Html.div({style:{width: pixels(this.width)}},
                                                              this.timetableDrawer.draw(),
                                                              Widget.block(this.menuChooser)));
         },
         
         filterSetup: function() {
             var self = this;
             this.filter = new TimeTableFilter(this.timetableDrawer, function () {
                 // When closed restore the filter button color
                 self.filterButtonContainer.dom.style.background = "";
                 return true;
             });
             this.filter.draw();
         },
         
         functionButtons: function() {
             var self = this;

             var printButton = Html.div('printButtonWhite', $T('Print'));
             var linkButton = Html.div('linkButtonWhite', $T('Link'));

             var filterButton = {'btn': Html.div('filterButtonWhite', $T('Filter')),
                                 'onclick': function(btnContainer) {
                                     // Save the container so that the filter button background
                                     // color can be restored when filter is closed
                                     self.filterButtonContainer = btnContainer
                                     self.filter.toggle();
                                     var state = self.filter.state.get();
                                     btnContainer.dom.style.background = state ? "#A5A5A5" : "";
                                 }
             };
             
             return [{'btn': printButton, 'onclick': function(){self.print()}},
                     filterButton];
         },

         postDraw: function() {
             this.timetableDrawer.postDraw();
         },

         filterMenu: function() {
             var self = this;

             var filterLink = Html.a({href: '#'}, $T("Filter"));
             this.filterMenu = new TimetableFilterMenu(filterLink, self.timetableDrawer);

             filterLink.observeClick(function(e) {
                 var pos = filterLink.getAbsolutePosition();
                 self.filterMenu.open(pos.x + filterLink.dom.offsetWidth, pos.y);
                 return false;
             });

             return Html.ul({className: "inner", style: {display: 'none'}},
                            Html.li("menuConfMiddleCell",
                                    filterLink));
         },

         layoutMenu: function() {
             var self = this;

             var layoutLink = Html.a({href: '#'}, $T("Layout"));
             this.layoutMenu = new TimetableLayoutMenu(layoutLink, self.timetableDrawer);

             layoutLink.observeClick(function(e) {
                 var pos = layoutLink.getAbsolutePosition();
                 //              e.preventDefault();
                 self.layoutMenu.open(pos.x + layoutLink.dom.offsetWidth, pos.y);
                 return false;
             });

             return Html.ul({className: "inner", style: {display: 'none'}},
                            Html.li("menuConfMiddleCell",
                                    layoutLink));
         },
         printMenu: function() {
             var self = this;

             var printLink = Html.a({href: '#'}, $T("Printable version"));
             printLink.observeClick(function(e) {

                 self.print();

             });

             return Html.ul({className: "inner", style: {display: 'none'}},
                            Html.li("menuConfMiddleCell",
                                    printLink));
         },
         print: function() {
             var self = this;

             //self.timetableDrawer.setPrintableVersion(true);

             // Close any open menu otherwise they will
             // stay open when going back from print view
             self.filterMenu.close();
             self.layoutMenu.close();

             var bodyPadding = $E(document.body).dom.style.padding;
             var timetableElements = translate(self.timetableDrawer.canvas.dom.childNodes, function(value) {return $E(value);});
             var elements = translate($E(document.body).dom.childNodes, function(value) {return $E(value);});

             var goBackLink = Html.a({href: '#', style: {fontSize: '13pt'}}, 'Go back');
             var printLink = Html.a({href: '#', style: {fontSize: '13pt'}}, 'Print');
             var showColors = Html.checkbox();
             var showColorsSpan = Html.span({style: {fontSize: '10pt'}}, showColors, 'Show colors');

             var links = Html.span({style: {cssFloat: 'right'}}, printLink, ' | ', goBackLink);

             var headerStyle = {padding: '0px 5px 5px 5px',
                 borderBottom: '1px solid black',
                 textAlign: 'center',
                 width: pixels(self.timetableDrawer.width)};
             var header = Html.div({className: 'timetableHeader', style: headerStyle}, links, 
                 Html.span({style: {cssFloat: 'left'}}, self.timetableDrawer._titleTemplate(self.timetableDrawer.day)), showColorsSpan);

             goBackLink.observeClick(function(e) {
                 self.timetableDrawer.setPrintableVersion(false);
                 $E(document.body).setStyle('padding', bodyPadding);
                 $E(document.body).set(elements);
                 
             });
             showColors.observeClick(function(e) {
                 alert(showColors.get());
                 self.timetableDrawer.setPrintableVersion(false);
                 $E(document.body).set(header, timetableDiv);
             });
             printLink.observeClick(function(e) {
                 window.print();
             });
             var timetableDiv = Html.div({style: {paddingTop: pixels(20), position: 'relative'}}, timetableElements)
             $E(document.body).set(header, timetableDiv);
             $E(document.body).setStyle('padding', pixels(30));
         }

     },
     function(data, width, wrappingElement, detailLevel, adminMode)
     {
         var self = this;

         this.width = width;
         this.timetableDrawer = new TimetableDrawer(data, width, wrappingElement, detailLevel, this.functionButtons());
         this.adminMode = any(adminMode, false);
         this.filterSetup();
     });