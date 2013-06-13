/**
 * Function used by the importer plugin to create importer dialog.
 * @param timetable Timetable object used to specify import destination
 */
function createImporterDialog(timetable){
    new ImportDialog(timetable);
};

/**
  * Namespace for importer utility functions and variables.
  */
ImporterUtils = {
     /**
      * Possible extensions for resources
      */
     resourcesExtensionList : {'pdf' : 1, 'doc' : 1, 'docx' : 1, 'ppt' : 1},

     /**
      * Maps importer name into report number system name
      */
     reportNumberSystems: {"invenio" : "cds",
                           "dummy" : "Dummy"},

     /**
      * Short names of the months.
      */
     shortMonthsNames : [$T("Jan"),
                         $T("Feb"),
                         $T("Mar"),
                         $T("Apr"),
                         $T("May"),
                         $T("Jun"),
                         $T("Jul"),
                         $T("Aug"),
                         $T("Sep"),
                         $T("Oct"),
                         $T("Nov"),
                         $T("Dec")],
    /**
     * Converts minutes to the hour string (format HH:MM).
     * If minutes are greater than 1440 (24:00) value '00:00' is returned.
     * @param minutes Integer containing number of minutes.
     * @return hour string.
     */
     minutesToTime: function(minutes) {
        if(minutes <= 1440)
            return ((minutes - minutes % 60)/ 60 < 10 ? "0" + (minutes  - minutes % 60) / 60:(minutes  - minutes % 60) / 60)
                     + ":" + (minutes % 60 < 10 ? "0" + minutes % 60:minutes % 60);
        else
            return '00:00';
    },

    /**
     * Standard sorting function comparing start times of events.
     * @param a first event.
     * @param b second event.
     * @return true if the first event starts later than the second. If not false.
     */
    compareStartTime: function (a, b){
        return a.startDate.time > b.startDate.time;
    },

    /**
     * Returns array containing sorted keys of the dictionary.
     * @param dict Dictionary to be sorted.
     * @param sortFunc Function comparing keys of the dictionary.
     * @return Array containg sorted keys.
     */
    sortedKeys: function(dict, sortFunc){
        var array = [];
        each(dict, function(item){
            array.push(item);
        });
        return array.sort(sortFunc);
    },
    /**
     * Checks if a dictionary contains empty person data.
     */
    isPersonEmpty: function(person){
        return person && (person.firstName || person.familyName);
    },

    /**
     * Handles multiple Indico requests. Requests are sent to the server sequentially.
     * When a request is finished the next one is sent to the server.
     * @param reqList List of dictionaries. Each element of the list represents a single request.
     * Each request has a following format {'method' : nameOfTheMetod(string), 'args': dictionaryOfArguments}
     * @param successCallback Function executed after every successful request.
     * @param errorCallback Function executed after every failed request.
     * @param finalCallback Function executed after finishing all requests.
     */
    multipleIndicoRequest: function(reqList, successCallback, errorCallback, finalCallback){
        if( reqList.length > 0 )
            indicoRequest( reqList[0]["method"], reqList[0]["args"], function(result, error){
                if( result && successCallback)
                    successCallback(result);
                if( error && errorCallback)
                    errorCallback(error);
                reqList.splice(0,1);
                ImporterUtils.multipleIndicoRequest(reqList, successCallback, errorCallback, finalCallback);
            });
        else if( finalCallback )
            finalCallback();
    }
};

/**
 * Imitates dictionary with keys ordered by the time element insertion.
 */
type("QueueDict", [],{
            /**
             * Inserts new element to the dictionary. If element's value is null removes an element.
             * @param key element's key
             * @param value element's value
             */
            set: function(key, value) {
                var existed = false;
                for( i in this.keySequence )
                    if( key == this.keySequence[i] ){
                        existed = true;
                        if(value != null)
                            this.keySequence[i] = value;
                        else
                            this.keySequence.splice(i,1);
                    }
                if( !existed )
                    this.keySequence.push(key);
                this.dict[key] = value;
            },
            /**
             * Gets list of keys. The list is sorted by an element insertion time.
             */
            getKeys: function(){
                return this.keySequence;
            },
            /**
             * Gets elements with the specified key.
             */
            get: function(key){
                return this.dict[key];
            },
            /**
             * Gets list of values. The list is sorted by an element insertion time.
             */
            getValues: function(){
                var tmp = []
                for( index in this.keySequence )
                    tmp.push(this.get(this.keySequence[index]));
                return tmp;

            },
            /**
             * Returns number of elements in the dictionary.
             */
            getLength: function(){
                return this.keySequence.length;
            },
            /**
             * Removes all elements from the dictionary
             */
            clear: function(){
                this.keySequence = [];
                this.dict = {};
            },
            /**
             * Moves the key one position towards the begining of the key list.
             */
            shiftTop: function(idx){
                if( idx > 0 ){
                    var tmp = this.keySequence[idx];
                    this.keySequence[idx] = this.keySequence[idx - 1];
                    this.keySequence[idx - 1] = tmp;
                }
            },
            /**
             * Moves the key one position towards the end of the key list.
             */
            shiftBottom: function(idx){
                if( idx < this.keySequence.length - 1 ){
                    var tmp = this.keySequence[idx];
                    this.keySequence[idx] = this.keySequence[idx + 1];
                    this.keySequence[idx + 1] = tmp;
                }
            }
        },
        /**
         * Creates an empty dictionary.
         */
        function(){
            this.keySequence = [];
            this.dict = {};
        }
);


type("ImportDialog", ["ExclusivePopupWithButtons", "PreLoadHandler"],
        {
            _preload:[
                      /**
                       * Loads a list of importers from the server.
                       */
                      function(hook){
                          var self = this;
                          indicoRequest('importer.getImporters',{},
                                  function(result, error){
                                        if(!error)
                                            self.importers = result;
                                        hook.set(true);
                          });
                      }
            ],
            /**
             * Hides importer list and timetable list and shows information to type a new query.
             */
            _hideLists: function(){
                this.importerList.hide();
                this.timetableList.hide();
                this.emptySearchDiv.show();
            },
            /**
             * Shows importer list and timetable list and hides information to type a new query.
             */
            _showLists: function(){
                this.importerList.show();
                this.timetableList.refresh();
                this.timetableList.show();
                this.emptySearchDiv.hide();
            },
            /**
             * Draws the content of the dialog.
             */
            drawContent : function(){
                var self = this;
                var search = function() {
                        self.importerList.search(query.dom.value, importFrom.dom.value, 20, [function(){
                            self._showLists();
                        }]);
                    };
                var searchButton = Html.input('button',{}, $T('search'));
                searchButton.observeClick(search);
                var importFrom = Html.select({});
                for( importer in this.importers )
                    importFrom.append(Html.option({value:importer}, this.importers[importer]));
                var query = Html.input('text', {});
                query.observeEvent('keypress', function(event){
                    if( event.keyCode == 13 )
                        search();
                });

                this.emptySearchDiv = new PresearchContainer(this.height, function(){
                    self._showLists();
                });
                /**
                 * Enables insert button whether some elements are selected at both importer and timetable list
                 */
                var _observeInsertButton =  function(){
                    if(self.importerList.getSelectedList().getLength() > 0 && self.timetableList.getSelection() )
                        self.insertButton.disabledButtonWithTooltip('enable');
                    else
                        self.insertButton.disabledButtonWithTooltip('disable');

                };
                this.importerList = new ImporterList([],
                        {"height" : this.height - 80, "width" : this.width / 2 - 20, "cssFloat" : "left"},
                        'entryList', 'entryListSelected', true, _observeInsertButton);
                this.timetableList = new TableTreeList(this.topTimetable,
                        {"height" : this.height - 80, "width" : this.width / 2 - 20, "cssFloat" : "right"},
                        'treeList', 'treeListDayName', 'treeListEntry', true, _observeInsertButton);
                return Html.div({},
                        Html.div({className:'importDialogHeader', style:{width:pixels(this.width * 0.9)}}, query, searchButton, $T(" in "), importFrom),
                        this.emptySearchDiv.draw(), this.importerList.draw(), this.timetableList.draw());
            },
            _getButtons: function() {
                var self = this;
                return [
                    [$T('Proceed...'), function() {
                        var destination = self.timetableList.getSelection();
                        var entries = self.importerList.getSelectedList();
                        var importer = self.importerList.getLastImporter();
                        new ImporterDurationDialog(entries, destination,  self.confId, self.timetable, importer, function(redirect) {
                            if(!redirect) {
                                self._hideLists();
                                self.timetableList.clearSelection();
                                self.importerList.clearSelection();
                                self.emptySearchDiv.showAfterSearch();
                            } else {
                                self.close();
                            }
                        });
                    }],
                    [$T('Close'), function() {
                        self.close();
                    }]
                ];
            },
            draw: function(){
                this.insertButton = this.buttons.eq(0);
                this.insertButton.disabledButtonWithTooltip({
                    tooltip: $T('Please select contributions to be added and their destination.'),
                    disabled: true
                });
                return this.ExclusivePopupWithButtons.prototype.draw.call(this, this.drawContent());
            }
        },
        /**
         * Importer's main tab. Contains inputs for typing a query and select the importer type.
         * After making a query imported entries are displayed at the left side of the dialog, while
         * at the right side list of all entries in the event's timetable will be shown. User can add
         * new contributions to the timetable's entry by simply selecting them and clicking at 'proceed'
         * button.
         * @param timetable Indico timetable object. If it's undefined constructor will try to fetch
         * window.timetable object.
         */
        function(timetable){
            var self = this;
            this.ExclusivePopupWithButtons($T("Import Entries"));
            this.timetable = timetable?timetable:window.timetable;
            this.topTimetable = this.timetable.parentTimetable?this.timetable.parentTimetable:this.timetable
            this.confId = this.topTimetable.contextInfo.id;
            this.height = document.body.clientHeight - 200;
            this.width = document.body.clientWidth - 200;
            this.importers;
            this.PreLoadHandler(
                    this._preload,
                    function() {
                        self.open();
                    });
            this.execute();
        }
);

type("PresearchContainer",[],
        {
            /**
             * Shows a widget.
             */
            show: function(){
                this.contentDiv.dom.style.display = 'block';
            },
            /**
             * Hides a widget.
             */
            hide: function(){
                this.contentDiv.dom.style.display = 'none';
            },
            /**
             * Changes a content of the widget. It should be used after making a first successful import.
             */
            showAfterSearch: function(){
                this.firstSearch.dom.style.display = 'none';
                this.afterSearch.dom.style.display = 'inline';
            },
            draw: function(){
                this.firstSearch = Html.span({style:{display:"inline"}},$T("Please type your search phrase and press 'search'."));
                var hereLink = Html.span({className: 'fakeLink'}, $T("here"));
                hereLink.observeClick(this.afterSearchAction);
                this.afterSearch = Html.span({style:{display:"none"}},$T("Your entries were inserted "), Html.span({style:{fontWeight:'bold'}}, $T("successfully")), $T(". Please specify a new query or click "), hereLink, $T(" to see the previous results."));
                this.contentDiv = Html.div({className:'presearchContainer', style:{"height" : pixels(this.height - 130)}}, this.firstSearch, this.afterSearch);
                return this.contentDiv;
            }
        },
        /**
         * A placeholder for importer and timetable list widgets. Contains user's tips about what to do right now.
         * @param widget's height
         * @param function executed afer clicking 'here' link.
         */
        function(height, afterSearchAction){
            this.height = height;
            this.afterSearchAction = afterSearchAction;
        });

type("ImporterDurationDialog",["ExclusivePopupWithButtons", "PreLoadHandler"],
        {
            _preload: [
                    /**
                     * Fetches the default start time of the first inserted contribution.
                     * Different requests are used for days, sessions and contributions.
                     */
                    function(hook){
                        var self = this;
                        //If the destination is a contribution, simply fetch the contribution's start time.
                        if( this.destination.entryType == 'Contribution' ) {
                            self.info.set("startTime", this.destination.startDate.time.substr(0,5));
                            hook.set(true);
                        }
                        else {
                            var method;
                            if( this.destination.entryType == 'Day' )
                                method = 'schedule.event.getDayEndDate';
                            if( this.destination.entryType == 'Session' )
                                method = 'schedule.slot.getDayEndDate';
                            indicoRequest(method, {'confId' : this.confId,
                                                   'sessionId' : this.destination.sessionId,
                                                   'slotId' : this.destination.sessionSlotId,
                                                   'selectedDay': this.destination.startDate.date.replace(/-/g,'/')},
                                                   function(result, error){
                                                       if(!error)
                                                           self.info.set("startTime", result.substr(11,5));
                                                       hook.set(true);
                                                   });
                        }
                    }
            ],

            drawContent: function(){
                var durationField = Html.input('text', {}, this.destination.contribDuration?this.destination.contribDuration:20);
                var timeField = Html.input('text', {});
                var redirectCheckbox = Html.input('checkbox', {});

                this.parameterManager.add(durationField, 'unsigned_int', false);
                this.parameterManager.add(timeField, 'time', false);

                $B(this.info.accessor("duration"), durationField);
                $B(timeField, this.info.accessor("startTime"));
                $B(this.info.accessor("redirect"), redirectCheckbox);

                return IndicoUtil.createFormFromMap([
                            [$T("Duration time of every inserted contribution:"), durationField],
                            [$T("Start time of the first contribution:"), timeField],
                            [$T("Show me the destination:"), redirectCheckbox]
                         ]);
            },
            /**
             * Returns an insert method name based on the destintion type.
             */
            _extractMethod: function(){
                switch (this.destination.entryType){
                    case "Day":
                        return "schedule.event.addContribution";
                    case "Contribution":
                        return "contribution.addSubContribution";
                    case "Session":
                        return "schedule.slot.addContribution";
                    default:
                        return null;
                }
            },
            /**
             * Returns an url of the destination's timetable.
             */
            _extractRedirectUrl: function() {
                switch (this.destination.entryType){
                    case "Day":
                        return build_url(Indico.Urls.ConfModifSchedule, {confId: this.confId}, this.destination.startDate.date.replace(/-/g, ''));
                    case "Contribution":
                        return build_url(Indico.Urls.SubcontrModif, {contribId: this.destination.contributionId, confId: this.confId});
                    case "Session":
                        return build_url(Indico.Urls.ConfModifSchedule, {confId: this.confId}, this.destination.startDate.date.replace(/-/g, '') + '.' + this.destination.id);
                    default:
                        return null;
                }
            },

            _getButtons: function() {
                var self = this;
                return [
                    [$T('Insert'), function() {
                        if(!self.parameterManager.check()) {
                            return;
                        }
                        //Converts string containing contribution's start date(HH:MM) into a number of minutes.
                        //Using parseFloat because parseInt('08') = 0.
                        var time = parseFloat(self.info.get('startTime').split(':')[0]) * 60 + parseFloat(self.info.get('startTime').split(':')[1]);
                        var duration = parseInt(self.info.get('duration'));
                        var method = self._extractMethod();
                        //If last contribution finishes before 24:00
                        if( time + duration * self.entries.getLength() <= 1440) {
                            var killProgress = IndicoUI.Dialogs.Util.progress();
                            var date = self.destination.startDate.date.replace(/-/g,'/');
                            var args = [];
                            each(self.entries.getValues(), function(entry){
                                entry = entry.getAll();
                                var timeStr = ImporterUtils.minutesToTime(time);
                                args.push({'method' : method,
                                           'args' : {'conference' : self.confId,
                                                     'duration' : duration,
                                                     'title' : entry.title?entry.title:"Untitled",
                                                     'sessionId' : self.destination.sessionId,
                                                     'slotId' : self.destination.sessionSlotId,
                                                     'contribId' : self.destination.contributionId,
                                                     'startDate' : date + " " + timeStr,
                                                     'keywords' : [],
                                                     'authors':ImporterUtils.isPersonEmpty(entry.primaryAuthor)?[entry.primaryAuthor]:[],
                                                     'coauthors' : ImporterUtils.isPersonEmpty(entry.secondaryAuthor)?[entry.secondaryAuthor]:[],
                                                     'presenters' : ImporterUtils.isPersonEmpty(entry.speaker)?[entry.speaker]:[],
                                                     'roomInfo' : {},
                                                     'field_content': entry.summary,
                                                     'reportNumbers': entry.reportNumbers?
                                                             [{'system': ImporterUtils.reportNumberSystems[self.importer], 'number': entry.reportNumbers}]:[],
                                                     'materials': entry.materials}
                                });
                                time += duration;
                            });
                            var successCallback = function(result){
                                if(exists(result.slotEntry) && self.timetable.contextInfo.id == result.slotEntry.id){
                                    self.timetable._updateEntry(result, result.id);
                                } else{
                                    var timetable = self.timetable.parentTimetable?self.timetable.parentTimetable:self.timetable;
                                    timetable._updateEntry(result, result.id);
                                }
                            };
                            var errorCallback = function(error){
                                if(error){
                                    IndicoUtil.errorReport(error);
                                }
                            };
                            var finalCallback = function(){
                                if(self.successFunction)
                                    self.successFunction(self.info.get('redirect'));
                                if(self.info.get('redirect'))
                                    window.location = self._extractRedirectUrl();
                                self.close();
                                killProgress();
                            };
                            ImporterUtils.multipleIndicoRequest(args, successCallback , errorCallback, finalCallback);
                        }
                        else {
                            new WarningPopup("Warning", "Some contributions will end after 24:00. Please modify start time and duration.").open();
                        }
                    }],
                    [$T('Cancel'), function() {
                        self.close();
                    }]
                ];

            },
            draw: function(){
                return this.ExclusivePopupWithButtons.prototype.draw.call(this, this.drawContent());
            }
        },
        /**
         * Dialog used to set the duration of the each contribution and the start time of the first on.
         * @param entries List of imported entries
         * @param destination Place into which entries will be inserted
         * @param confIf Id of the current conference
         * @param timetable Indico timetable object of the current conference.
         * @param importer Name of the used importer.
         * @param successFunction Function executed after inserting events.
         */
        function(entries, destination, confId, timetable, importer, successFunction){
            var self = this;
            this.ExclusivePopupWithButtons($T('Adjust entries'));
            this.confId = confId;
            this.entries = entries;
            this.destination = destination;
            this.timetable = timetable;
            this.successFunction = successFunction;
            this.importer = importer;
            this.parameterManager = new IndicoUtil.parameterManager();
            this.info = new WatchObject();
            this.PreLoadHandler(
                    this._preload,
                    function() {
                        self.open();
                    });
            this.execute();
        }
);

type("ImporterListWidget", ["SelectableListWidget"],
        {
            /**
             * Removes all entries from the list
             */
            clearList: function(){
                this.SelectableListWidget.prototype.clearList.call(this);
                this.recordDivs = [];
            },
            /**
             * Removes all selections.
             */
            clearSelection: function(){
                this.SelectableListWidget.prototype.clearSelection.call(this);
                this.selectedObserver(this.selectedList);
            },
            /**
             * Returns number of entries in the list.
             */
            getLength: function(){
                return this.recordDivs.length;
            },
            /**
             * Returns the last query.
             */
            getLastQuery: function(){
                return this.lastSearchQuery;
            },
            /**
             * Returns the name of the last used importer.
             */
            getLastImporter: function(){
                return this.lastSearchImporter;
            },
            /**
             * Returns true if it's possible to import more entries, otherwise false.
             */
            isMoreToImport: function(){
                return this.moreToImport;
            },
            /**
             * Base search method. Sends a query to the importer.
             * @param query A query string send to the importer
             * @param importer A name of the used importer.
             * @param size Number of fetched objects.
             * @param successFunction Method executed after successful request.
             * @param callbacks List of methods executed after request (doesn't matter if successful).
             */
            _searchBase: function(query, importer, size, successFunc, callbacks) {
                var self = this;
                var killProgress = IndicoUI.Dialogs.Util.progress();
                indicoRequest("importer.import",
                        {'importer': importer,
                         'query': query,
                         // One more entry is fetched to be able to check if it's possible to fetch
                         // more entries in case of further requests.
                         'size': size + 1},
                         function(result, error) {
                             if(!error && result && successFunc)
                                 successFunc(result);
                             each(callbacks, function(callback){
                                 callback();
                             });
                             killProgress();
                         });
                //Saves last request data
                this.lastSearchImporter = importer;
                this.lastSearchQuery = query;
                this.lastSearchSize = size;
            },
            /**
             * Clears the list and inserts new imported entries.
             * @param query A query string send to the importer
             * @param importer A name of the used importer.
             * @param size Number of fetched objects.
             * @param callbacks List of methods executed after request (doesn't matter if successful).
             */
            search: function(query, importer, size, callbacks){
                var self = this;
                var successFunc = function(result){
                    self.clearList();
                    var importedRecords = 0;
                    self.moreToImport = false;
                    for( record in result ){
                        //checks if it's possible to import more entries
                        if(size == importedRecords++){
                            self.moreToImport = true;
                            break;
                        }
                        self.set(record, $O(result[record]));
                    }
                }
                this._searchBase(query, importer, size, successFunc, callbacks);
            },
            /**
             * Adds more entries to the current list. Uses previous query and importer.
             * @param size Number of fetched objects.
             * @param callbacks List of methods executed after request (doesn't matter if successful).
             */
            append: function(size, callbacks){
                var self = this;
                var lastLength = this.getLength();
                var successFunc = function(result){
                    var importedRecords = 0;
                    self.moreToImport = false;
                    for( record in result ){
                        // checks if it's possible to import more entries
                        if(lastLength + size == importedRecords){
                            self.moreToImport = true;
                            break;
                        }
                        // Some entries are already in the list so we don't want to insert them twice.
                        // Entries with indexes greater or equal lastLength - 1 are not yet in the list.
                        if(lastLength - 1 < importedRecords)
                            self.set(record, $O(result[record]));
                        ++importedRecords;
                    }
                }
                this._searchBase(this.getLastQuery(), this.getLastImporter(), this.getLength() + size, successFunc, callbacks);
            },
            /**
             * Extracts person's name, surname and affiliation
             */
            _getPersonString: function(person){
                return person.firstName + " " + person.familyName +
                    (person.affiliation? " (" + person.affiliation + ")" : "");
            },
            /**
             * Draws sequence number attached to the item div
             */
            _drawSelectionIndex: function(){
                var self = this;
                var selectionIndex = Html.div({className:'entryListIndex', style:{display:'none', cssFloat:'left'}});
                //Removes standard mouse events to enable custom right click event
                var stopMouseEvent = function(event){
                    event.cancelBubble=true;
                    if (event.preventDefault)
                        event.preventDefault();
                    else
                        event.returnValue= false;
                    return false;
                };
                selectionIndex.observeEvent('contextmenu',stopMouseEvent);
                selectionIndex.observeEvent('mousedown',stopMouseEvent);
                selectionIndex.observeEvent('click',stopMouseEvent);
                selectionIndex.observeEvent('mouseup',function(event){
                    //Preventing event propagation
                    event.cancelBubble=true;
                    if (event.which == null)
                        /* IE case */
                        var button = event.button == 1 ? "left" : "notLeft";
                    else
                        /* All others */
                        var button= event.which == 1 ? "left" : "notLeft";
                    var idx = parseInt(selectionIndex.dom.innerHTML.substr(0, selectionIndex.dom.innerHTML.length - 2) - 1);
                    if( button == "left")
                        self.selectedList.shiftTop(idx);
                    else
                        self.selectedList.shiftBottom(idx);
                    self.observeSelection(self.selectedList);
                });
                return selectionIndex;
            },
            /**
             * Converts list of materials into a dictionary
             */
            _convertMaterials: function(materials){
                var materialsDict = {};
                each(materials, function(mat){
                    if(!materialsDict[mat.name])
                        materialsDict[mat.name] = [];
                    materialsDict[mat.name].push(mat.url);
                });
                return materialsDict;
            },
            /**
             * Converts resource link into a name.
             */
            _getResourceName: function(resource){
                var splittedName = resource.split('.');
                if(splittedName[splittedName.length - 1] in ImporterUtils.resourcesExtensionList)
                    return splittedName[splittedName.length - 1];
                else
                    return 'resource';
            },
            /**
             * Draws a div containing entry's data.
             */
            _drawItem : function(record) {
                var self = this;
                var recordDiv = Html.div({})
                var key = record.key;
                var record = record.get();
                // Empty fields are not displayed.
                if ( record.get("reportNumbers") ){
                    var reportNumber = Html.div({}, Html.em({},$T("Report number(s)")), ":");
                    each(record.get("reportNumbers"), function(id){
                        reportNumber.append(" " + id);
                    });
                    recordDiv.append(reportNumber);
                }
                if ( record.get("title") )
                    recordDiv.append(Html.div({}, Html.em({},$T("Title")), ": ", record.get("title")));
                if ( record.get("meetingName") )
                    recordDiv.append(Html.div({}, Html.em({},$T("Meeting")), ": ", record.get("meetingName")));
                // Speaker, primary and secondary authors are stored in dictionaries. Their property have to be checked.
                if( ImporterUtils.isPersonEmpty(record.get("primaryAuthor")))
                    recordDiv.append(Html.div({}, Html.em({},$T("Primary author")), ": ", this._getPersonString(record.get("primaryAuthor"))));
                if( ImporterUtils.isPersonEmpty(record.get("secondaryAuthor")))
                    recordDiv.append(Html.div({}, Html.em({},$T("Secondary author")), ": ", this._getPersonString(record.get("secondaryAuthor"))));
                if( ImporterUtils.isPersonEmpty(record.get("speaker")))
                    recordDiv.append(Html.div({}, Html.em({},$T("Speaker")), ": ", this._getPersonString(record.get("speaker"))));
                if( record.get("summary") ){
                    var summary = record.get("summary");
                    //If summary is too long it need to be truncated.
                    if( summary.length < 200 )
                        recordDiv.append(Html.div({}, Html.em({},$T("Summary")), ": " ,summary));
                    else{
                        var summaryBeg = Html.span({},summary.substr(0,200));
                        var summaryEnd = Html.span({style:{display:'none'}},summary.substr(200));
                        var showLink = Html.span({className:'fakeLink'}, $T(" (show all)"));
                        showLink.observeClick(function(evt){
                            summaryEnd.dom.style.display = "inline";
                            showLink.dom.style.display = "none";
                            hideLink.dom.style.display = "inline";
                            //Preventing event propagation
                            evt.cancelBubble=true;
                            //Recalculating position of the selection number
                            self.observeSelection(self.selectedList);
                        });
                        var hideLink = Html.span({className:'fakeLink', style:{display:'none'}}, $T(" (hide)"));
                        hideLink.observeClick(function(evt){
                            summaryEnd.dom.style.display = "none";
                            showLink.dom.style.display = "inline";
                            hideLink.dom.style.display = "none";
                            //Preventing event propagation
                            evt.cancelBubble=true;
                            //Recalculating position of the selection number
                            self.observeSelection(self.selectedList);
                        });
                        var sumamaryDiv = Html.div({}, Html.em({},$T("Summary")), ": " ,summaryBeg, showLink, summaryEnd, hideLink)
                        recordDiv.append(sumamaryDiv);
                    }
                }
                if( record.get("place") ){
                    recordDiv.append(Html.div({}, Html.em({},$T("Place")), ": ", record.get("place")));
                }
                if ( record.get("materials") ){
                    record.set("materials", this._convertMaterials(record.get("materials")));
                    var materials = Html.div({}, Html.em({},$T("Materials")), ":");
                    for(mat in record.get("materials")){
                        var materialType = Html.div({}, mat + ":");
                        each(record.get("materials")[mat], function(resource){
                            var link = Html.a({href:resource, target: "_new"},self._getResourceName(resource));
                            link.observeClick(function(evt){
                                //Preventing event propagation
                                evt.cancelBubble=true;
                            });
                            materialType.append(" ");
                            materialType.append(link);
                        });
                        materials.append(materialType);
                    }
                    recordDiv.append(materials);
                }
                recordDiv.append(this._drawSelectionIndex());
                this.recordDivs[key] = recordDiv;
                return recordDiv;
            },
            /**
             * Observer function executed when selection is made. Draws a number next to the item div, which
             * represents insertion sequence of entries.
             */
            observeSelection: function(list){
                var self = this;
                //Clears numbers next to the all divs
                for( entry in this.recordDivs){
                    var record = this.recordDivs[entry];
                    record.dom.lastChild.style.display = 'none';
                    record.dom.lastChild.innerHTML = '';
                }
                var seq = 1;
                var self = this;
                each(list.getKeys(), function(entry){
                    var record = self.recordDivs[entry];
                    record.dom.lastChild.style.display = 'block';
                    record.dom.lastChild.style.top = pixels(-(record.dom.clientHeight + 23) / 2);
                    record.dom.lastChild.innerHTML = seq;
                    switch( seq ) {
                        case 1:
                            record.dom.lastChild.innerHTML += $T('st');
                            break;
                        case 2:
                            record.dom.lastChild.innerHTML += $T('nd');
                            break;
                        case 3:
                            record.dom.lastChild.innerHTML += $T('rd');
                            break;
                        default:
                            record.dom.lastChild.innerHTML += $T('th');
                            break;
                    }
                    ++seq;
                });
            }
        },
        /**
         * Widget containing a list of imported contributions. Supports multiple selections of results and
         * keeps selection order.
         * @param events List of events to be inserted during initialization.
         * @param listStyle Css class name of the list.
         * @param selectedStyle Css class name of a selected element.
         * @param customObserver Function executed while selection is made.
         */
        function(events, listStyle, selectedStyle, customObserver){
            var self = this;
            // After selecting/deselecting an element two observers are executed.
            // The first is a default one, used to keep selected elements order.
            // The second one is a custom observer passed in the arguments list.
            var observer = function(list) {
                this.observeSelection(list);
                if(customObserver)
                    customObserver(list);
            }
            this.SelectableListWidget(observer, false, listStyle, selectedStyle);
            this.selectedList = new QueueDict();
            this.recordDivs = {};
            for( record in events )
                this.set(record, $O(events[record]));
        });

type("ImporterList", [],
        {
            /**
             * Show the widget.
             */
            show: function(){
                this.contentDiv.dom.style.display = 'block';
            },
            /**
             * Hides the widget.
             */
            hide: function(){
                this.contentDiv.dom.style.display = 'none';
            },
            /**
             * Returns list of the selected entries.
             */
            getSelectedList: function(){
                return this.importerWidget.getSelectedList();
            },
            /**
             * Removes all entries from the selection list.
             */
            clearSelection: function(){
                this.importerWidget.clearSelection();
            },
            /**
             * Returns last used importer.
             */
            getLastImporter: function(){
                return this.importerWidget.getLastImporter();
            },
            /**
             * Changes widget's header depending on the number of results in the list.
             */
            handleContent: function(){
                if( this.descriptionDiv && this.emptyDescriptionDiv) {
                    if( this.importerWidget.getLength() == 0) {
                        this.descriptionDiv.dom.style.display = 'none';
                        this.emptyDescriptionDiv.dom.style.display = 'block';
                        this.moreEntriesDiv.dom.style.display = 'none';
                    } else {
                        this.entriesCount.dom.innerHTML = this.importerWidget.getLength() == 1?
                                $T("1 entry was found. "):this.importerWidget.getLength() + $T(" entries were found. ");
                        this.descriptionDiv.dom.style.display = 'block';
                        this.emptyDescriptionDiv.dom.style.display = 'none';
                        if( this.importerWidget.isMoreToImport() )
                            this.moreEntriesDiv.dom.style.display = 'block';
                        else
                            this.moreEntriesDiv.dom.style.display = 'none';
                    }
                }
            },
            /**
             * Adds handleContent method to the callback list. If callback list is empty, creates a new one
             * containing only handleContent method.
             * @return list with inserted handleContent method.
             */
            _appendCallbacks: function(callbacks){
                var self = this;
                if( callbacks )
                    callbacks.push(function(){self.handleContent()});
                else
                    callbacks = [function(){self.handleContent()}];
                return callbacks;
            },
            /**
             * Calls search method from ImporterListWidget object.
             */
            search: function(query, importer, size, callbacks){
                this.importerWidget.search(query, importer, size, this._appendCallbacks(callbacks));
            },
            /**
             * Calls append method from ImporterListWidget object.
             */
            append: function(size, callbacks){
                this.importerWidget.append(size, this._appendCallbacks(callbacks));
            },
            draw: function(){
                var importerDiv = this._drawImporterDiv();
                this.contentDiv = Html.div({className:'entryListContainer'}, this._drawHeader(), importerDiv);
                for ( style in this.style ){
                    this.contentDiv.setStyle(style, this.style[style]);
                    if(style == 'height')
                        importerDiv.setStyle('height', this.style[style] - 76); //76 = height of the header
                }
                if( this.hidden )
                    this.contentDiv.dom.style.display = 'none';
                return this.contentDiv;
            },
            _drawHeader: function(){
                this.entriesCount = Html.span({},'0');
                this.descriptionDiv = Html.div({className:'entryListDesctiption'},this.entriesCount, $T("Please select the results you want to insert."));
                this.emptyDescriptionDiv = Html.div({className:'entryListDesctiption'},$T("No result were found. Please change the search phrase."));
                return Html.div({}, Html.div({className:'entryListHeader'}, $T("Step 1: Search results:")), this.descriptionDiv, this.emptyDescriptionDiv);
            },
            _drawImporterDiv: function(){
                var self = this;
                this.moreEntriesDiv = Html.div({className:'fakeLink', style:{paddingBottom:pixels(15), textAlign:'center', clear: 'both', marginTop: pixels(15)}},$T("more results"));
                this.moreEntriesDiv.observeClick(function(){
                    self.append(20);
                });
                return Html.div({style:{overflow:'auto'}}, this.importerWidget.draw(), this.moreEntriesDiv);
            }
        },
        /**
         * Encapsulates ImporterListWidget. Adds a header depending on the number of entries in the least.
         * Adds a button to fetch more entries from selected importer.
         * @param events List of events to be inserted during initialization.
         * @param style Dictionary of css styles applied to the div containing the list. IMPORTANT pass 'height'
         * attribute as an integer not a string, because some further calculations will be made.
         * @param listStyle Css class name of the list.
         * @param selectedStyle Css class name of a selected element.
         * @param hidden If true widget will not be displayed after being initialized.
         * @param observer Function executed while selection is made.
         */
        function( events, style, listStyle, selectedStyle, hidden, observer ){
            this.importerWidget = new ImporterListWidget(events, listStyle, selectedStyle, observer);
            this.style = style;
            this.hidden = hidden;
        });

type("TimetableListWidget",["ListWidget"],
        {
            /**
             * Highlights selected entry and calls an observer method.
             */
            setSelection: function(selected, div){
                if(this.selectedDiv){
                    this.selectedDiv.dom.style.fontWeight = "normal";
                    this.selectedDiv.dom.style.boxShadow = "";
                    this.selectedDiv.dom.style.MozBoxShadow = "";
                }
                if(this.selected != selected) {
                    this.selectedDiv = div;
                    this.selected = selected;
                    this.selectedDiv.dom.style.fontWeight = "bold";
                    this.selectedDiv.dom.style.boxShadow = "3px 3px 15px #000000";
                    this.selectedDiv.dom.style.MozBoxShadow = "3px 3px 15px #000000";
                } else {
                    this.selected = null;
                    this.selectedDiv = null;
                }
                if( this.observeSelection )
                    this.observeSelection();
            },
            /**
             * Deselects current entry.
             */
            clearSelection: function(){
                if(this.selectedDiv){
                    this.selectedDiv.dom.style.backgroundColor = "";
                }
                this.selected = null;
                this.selectedDiv = null;
                if( this.observeSelection )
                    this.observeSelection();
            },
            /**
             * Returns selected entry
             */
            getSelection: function(){
                return this.selected;
            },
            /**
             * Recursive function drawing timetable hierarchy.
             * @param item Entry to be displayed
             * @param level Recursion level. Used to set margins properly.
             */
            _drawItem : function( item, level ) {
                var self = this;
                level = level?level:0;
                // entry is a Day
                switch(item.entryType){
                    case 'Contribution':
                        item.color = "#F8F2E8";
                        item.textColor = "#000000";
                    case 'Session':
                        var titleDiv = Html.div({className:"treeListEntry", style:{backgroundColor: item.color, color: item.textColor}},
                                item.title + (item.startDate && item.endDate?" (" + item.startDate.time.substr(0,5) + " - " + item.endDate.time.substr(0,5) + ")":""));
                        var entries = ImporterUtils.sortedKeys(item.entries, ImporterUtils.compareStartTime);
                        break;
                    case 'Break':
                        if( this.displayBreaks ){
                            var titleDiv = Html.div({className:"treeListEntry", style:{backgroundColor: item.color, color: item.textColor}},
                                    item.title + (item.startDate && item.endDate?" (" + item.startDate.time.substr(0,5) + " - " + item.endDate.time.substr(0,5) + ")":""));
                            var entries = ImporterUtils.sortedKeys(item.entries, ImporterUtils.compareStartTime);
                            break;
                        } else
                            return null;
                    case undefined:
                        item.entryType = 'Day';
                        item.startDate = {date : item.key.substr(0,4) + "-" + item.key.substr(4,2) + "-" + item.key.substr(6,2)}
                        item.color = "#FFFFFF";
                        item.textColor = "#000000";
                        var titleDiv = Html.div({className:"treeListDayName"},
                                item.key.substr(6,2) + " " + ImporterUtils.shortMonthsNames[parseFloat(item.key.substr(4,2)) - 1] +
                                " " + item.key.substr(0,4));
                        var entries = ImporterUtils.sortedKeys(item.get().getAll(), ImporterUtils.compareStartTime);
                        break;
                }
                titleDiv.observeClick(function(){
                    self.setSelection(item, titleDiv);
                });
                var itemDiv = Html.div({style:{marginLeft:pixels(level * 20), clear:"both", padding:pixels(5)}}, titleDiv);
                var entriesDiv = Html.div({style:{display:"none"}});
                //Draws subentries
                for(entry in entries)
                    entriesDiv.append(this._drawItem(entries[entry], level + 1));
                //If there are any subentries, draws buttons to show/hide them on demand.
                if(entries.length) {
                    titleDiv.append(this._drawShowHideButtons(entriesDiv));
                    itemDiv.append(entriesDiv);
                }
                return itemDiv;
            },
            /**
             * Attaches buttons to the dom object which hide/show it when clicked.
             */
            _drawShowHideButtons: function(div){
                var self = this;
                var showButton = Html.img({src:imageSrc("collapsd.png"), style:{display:'block'}});
                var hideButton = Html.img({src:imageSrc("exploded.png"), style:{display:"none"}});
                showButton.observeClick(function(evt){
                    div.dom.style.display = "block";
                    showButton.dom.style.display = "none";
                    hideButton.dom.style.display = "block";
                    evt.cancelBubble=true;
                });
                hideButton.observeClick(function(evt){
                    div.dom.style.display = "none";
                    showButton.dom.style.display = "block";
                    hideButton.dom.style.display = "none";
                    evt.cancelBubble=true;
                });
                return Html.div({className: 'expandButtonsDiv'},showButton, hideButton)
            },
            /**
             * Inserts entries from the timetable inside the widget.
             */
            _insertFromTimetable: function(){
                var self = this;
                var timetableData = this.timetable.getData();
                each(this.timetable.sortedKeys, function(day){
                    self.set(day, $O(timetableData[day]));
                });
            },
            /**
             * Clears the list and inserts entries from the timetable inside the widget.
             */
            refresh: function(){
                this.clear();
                this._insertFromTimetable();
            }
        },
        /**
         * Draws event's timetable as a hierarchical expandable list.
         * @param timetable Indico timetable object to be drawn
         * @param listStyle Css class name of the list.
         * @param dayStyle Css class name of day entries.
         * @param eventStyle Css class name of session and contributions entries.
         * @param observeSelection Funtcion executed after changing selection state.
         * @param displayBreaks If true breaks will be displayed in the list. If false breaks are hidden.
         */
        function(timetable, listStyle, dayStyle, eventStyle, observeSelection, displayBreaks){
            this.timetable = timetable;
            this.displayBreaks = displayBreaks;
            this.observeSelection = observeSelection;
            var self = this;
            this.ListWidget(listStyle);
            this._insertFromTimetable();
        });

type("TableTreeList",[],
        {
            /**
             * Show the widget.
             */
            show: function(){
                this.contentDiv.dom.style.display = 'block';
            },
            /**
             * Hides the widget
             */
            hide: function(){
                this.contentDiv.dom.style.display = 'none';
            },
            /**
             * Returns selected entry. TimetableListWidget method wrapper.
             */
            getSelection: function(){
                return this.timetableList.getSelection();
            },
            /**
             * Deselects current entry. TimetableListWidget method wrapper.
             */
            clearSelection: function(){
                return this.timetableList.clearSelection();
            },
            /**
             * Highlights selected entry and calls an observer method. TimetableListWidget method wrapper.
             */
            setSelection: function(selected, div){
                return this.timetableList.setSelection(selected, div);
            },
            /**
             * Clears the list and inserts entries from the timetable inside the widget.
             */
            refresh: function(){
                this.timetableList.refresh()
            },
            draw: function(){
                this.contentDiv = Html.div({className:'treeListContainer'},Html.div({className:'treeListHeader'}, $T("Step 2: Choose destination:")),
                        Html.div({className:'treeListDescription'},$T("Please select the place in which the contributions will be inserted.")));
                var treeDiv = Html.div({style:{overflow:'auto'}}, this.timetableList.draw());
                for ( style in this.style ){
                    this.contentDiv.setStyle(style, this.style[style]);
                    if(style == 'height')
                        treeDiv.setStyle('height', this.style[style] - 76);
                }
                this.contentDiv.append(treeDiv);
                if( this.hidden )
                    this.contentDiv.dom.style.display = 'none';
                return this.contentDiv;
            }
        },
        /**
         * Draws event's timetable as a hierarchical expandable list.
         * @param timetable Indico timetable object to be drawn
         * @param style Dictionary of css styles applied to the div containing the list. IMPORTANT pass 'height'
         * attribute as an integer not a string, because some further calculations will be made.
         * @param listStyle Css class name of the list.
         * @param dayStyle Css class name of day entries.
         * @param eventStyle Css class name of session and contributions entries.
         * @param observer Funtcion executed after changing selection state.
         */
        function( timetable, style, listStyle, dayStyle, eventStyle, hidden, observer ){
            this.timetableList = new TimetableListWidget(timetable, listStyle, dayStyle, eventStyle, observer)
            this.style = style;
            this.hidden = hidden;
        });
