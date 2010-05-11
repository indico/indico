type("ShowConcurrentEvents", ["ExclusivePopup", "PreLoadHandler"], {
    _preload: [
        function(hook){
            var killProgress = IndicoUI.Dialogs.Util.progress();
            var self = this;
            var concurrentEventsSvc = indicoSource('event.showConcurrentEvents', self.args);

            concurrentEventsSvc.state.observe(function(state) {
                if (state == SourceState.Loaded) {
                    self.concurrentEvents = $O(concurrentEventsSvc);
                    hook.set(true);
                    killProgress();
                }
            });
        }
    ],

    draw: function() {
        var self = this;

        if (self.concurrentEvents.isEmpty()){
            return this.ExclusivePopup.prototype.draw.call(this, "No events in that date");
        }

        var table = Html.table({style:{borderSpacing: pixels(0)}});
        var tBody = Html.tbody();
        table.set(tBody);

        var row0 = Html.tr({});

        var cell0 = Html.td({style:{verticalAlign:"top", align:"left", fontWeight: "bold"}});
        cell0.set($T("Category"));
        row0.append(cell0);

        var cell1 = Html.td({style:{verticalAlign:"top", align:"left", fontWeight: "bold"}});
        cell1.set($T("Events"));
        row0.append(cell1);

        tBody.append(row0);

        var pair = true;

        each(self.concurrentEvents, function(eventsList, categ){

            var confListUL = Html.ul({style:{listStyleType: "none", padding:pixels(0), paddingBottom:pixels(8), margin:pixels(0)}});
            each(eventsList, function(eventObj) {

                var evtTxt = [Html.span({},eventObj[0]), Html.span({style:{fontSize: pixels(10)}}, " (" + $T("from") + " " + eventObj[1] + " " + $T("to") + " " + eventObj[2] + ", " + $T("tz") + ": " + eventObj[3] + ")")];

                confListUL.append(Html.li({}, evtTxt));

            });
            categSpan = Html.span({style:{fontSize:pixels(12)}}, categ);

            if (pair) {
                color = "#F5F5F5";
            }else {
                color = "#FFFFFF";
            }
            pair = !pair;
            var row1 = Html.tr({style:{backgroundColor:color}});

            var cell0 = Html.td({style:{paddingRight:pixels(30), verticalAlign:"top", align:"left"}});
            cell0.set(categSpan);
            row1.append(cell0);

            var cell1 = Html.td({style:{verticalAlign:"top", align:"left"}});
            cell1.set(confListUL);
            row1.append(cell1);

            tBody.append(row1);

        });

        return this.ExclusivePopup.prototype.draw.call(this, table);

    }
},

     function(args) {
         var self = this;
         if (args) {
             this.args = args;
             this.PreLoadHandler(
                 self._preload,
                 function() {
                     self.open();
                 }
             );

             this.ExclusivePopup($T("Concurrent Events sorted by category:"), function() {
                 self.close();
             });
         }
     }

    );


type("CategoryChooserListWidget", ["RemoteListWidget"], {

    /**
     * drawContent is a method that is called from RemoteWidget when the source changes.
     *
     * adds the results of the request to the list.
     *
     */
    drawContent: function() {
        var self = this;
        if (exists(self.owner)) {
            if (!this.source.get().accessAllowed) {
                var popup = new ErrorPopup($T("Access forbidden"), [$T("You do not have sufficient permissions to access that category")], "");
                popup.open();
            }
            self.owner.update(this.source.get().parentCateg, this.source.get().currentCateg);
        }
        return this.RemoteListWidget.prototype.drawContent.call(this);
    },

    getList: function() {
        return this.source.get().categList;
    },

    /**
     * _drawItem is a method that it's called from ListWidget
     *
     */
    _drawItem: function(pair) {
            var self = this;
            /*var pr = null;
            if (pair.get().protected) {
                pr = Html.span("protected", " (protected)")
            }*/
            var numSubcat = null;
            if (!pair.get().final) {
                numSubcat = Html.em({}, " ("+pair.get().subcatLength+$T(" subcategories)"));
            }
            var itemDiv = Html.div({}, pair.get().title, numSubcat);
            //-- Highlight the chosen one --
            if (pair.get().final) {
                itemDiv.setStyle('fontWeight', 'bold');
                if(self.categId == pair.get().id) {
                    itemDiv.setStyle('backgroundColor', '#FFF6DF');
                }
            }
            itemDiv.observeClick(function() {
                if (pair.get().final) {
                    self._returnChoice(pair.get());
                }else{
                    self.args.categId = pair.get().id;
                    self.source.refresh();
                }
            });
            return itemDiv;
    },

    _returnChoice: function(categ) {
        if (!this.creationControl) {
            this.owner.closeHandler(categ, 'public');
        } else {
            var self = this;
            self.killProgress = IndicoUI.Dialogs.Util.progress();
            var src = indicoSource("category.canCreateEvent", {"categId":categ.id});
            self.resultCateg = categ;
            src.state.observe(function(value) {
                if (value == SourceState.Loaded) {
                    if (self.owner) {
                        if (!src.get()["canCreate"]) {
                            var popup = new ErrorPopup($T("Creation forbidden"), [$T("You do not have permissions to create events in that category")], "");
                            popup.open();
                        }else{
                            self.owner.closeHandler(self.resultCateg, src.get()["protection"]);
                        }
                        self.killProgress();
                    }
                }
            });
        }
    }

},
     function(categId, owner, creationControl) {
         var self = this;
         self.owner = owner;
         this.categId = categId;
         this.args = {"categId":this.categId};
         this.creationControl = creationControl;

         this.RemoteListWidget("CategoryList", 'category.getCategoryList', this.args);
     }

);

type("CategoryChooserWidget", [], {

    /**
     * Udpates the title with a new category and stores the new current categ (used by go to parent category).
     */
    update: function(parentCateg, currentCateg) {
        this.parentCateg = parentCateg;
        this.currentCateg = currentCateg;
        this.categTitleDiv.set(currentCateg.title);
        this.drawBreadcrumb();
    },

    closeHandler: function(categ, protection) {
        this.handler(categ, protection);
    },

    drawBreadcrumb: function(){
        this.breadcrumbs.clear();
        if (!this.currentCateg.breadcrumb) {
            return;
        }
        for (var i=0; i<this.currentCateg.breadcrumb.length; i++) {
            cat = this.currentCateg.breadcrumb[i];
            if ((i+1) == this.currentCateg.breadcrumb.length) {
                this.breadcrumbs.append(cat);
            }else {
                this.breadcrumbs.append(cat);
                var breadcrumbArrow = Html.img({
                    src: imageSrc("breadcrumbArrow"),
                    alt: '>',
                    title: ''
                    });
                this.breadcrumbs.append(breadcrumbArrow);
            }
        }
    },

    draw: function() {
        var self = this;

        self.catListWidget = new CategoryChooserListWidget(this.currentCateg.id, this, this.creationControl);

        this.categTitleDiv = Html.div("categoryTitle", this.currentCateg.title);

        var goBackLink = Html.a({href: '#', style: {fontSize: '17px'}}, $T('Go to parent category') );
        goBackLink.observeClick(function(e) {
            self.catListWidget.args.categId = self.parentCateg.id;
            self.catListWidget.source.refresh();
        });
        var buttonsDiv = Html.span("CategoryListButtons", goBackLink);

        var toolBar = Html.div({}, buttonsDiv, this.categTitleDiv);

        this.breadcrumbs = Html.span("pathWithoutLinks",null);
        this.drawBreadcrumb();

        return Html.div({}, toolBar, this.breadcrumbs, Html.div("CategoryListDiv", self.catListWidget.draw()));
    }

    },
     function(categ, handler, creationControl) {
         this.currentCateg = categ;
         this.parentCateg = categ;
         this.handler = handler;
         this.creationControl = creationControl;
    }

);

type("CategoryChooser", ["ExclusivePopup"], {

    draw: function() {
        var self = this;

        var handler = function(categ, protection) {
            self.categ = categ;
            self.protection = protection
            self.close();
            self.categoryChooserHandler(categ, protection);
        };
        var catChooserWidget = new CategoryChooserWidget(self.categ, handler, self.creationControl);

        return this.ExclusivePopup.prototype.draw.call(
            this,
            Html.div({ style: {width:pixels(640), height:pixels(480)} }, catChooserWidget.draw()));

    }
    },

    /**
     *
     * categoryChooserHandler is a function that will be executed when
     * a category is chosen.
     *
     */
     function(categ, categoryChooserHandler, creationControl) {
         var self = this;
         this.categ = categ;
         this.categoryChooserHandler = categoryChooserHandler;
         this.creationControl = creationControl;

         this.ExclusivePopup($T("Category chooser:"), function() {
             self.close();
         });

     }

);
