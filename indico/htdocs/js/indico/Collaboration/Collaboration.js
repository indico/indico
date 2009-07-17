/* ------------------------------ UTILITY / HELPER FUNCTIONS -------------------------------*/

// COMMON FUNCTIONS
// They require the following JS variables defined in the template:
// -codes (a dictionary like the one in ConfModifCollaboration.tpl)
// -eventLoadTime & clientLoadTime (see ConfModifCollaboration.tpl)
// And the following divs defined:
// 'iframes' : here will be stored the iframes for loading pages, Java Web Start apps etc.
//

/**
 * Color to be used when highlighting the background of a row to indicate a change happened
 */
var highlightColor = "#FFFF88";

/**
 * Utility function to display a popup with errors.
 * Useful for notifying the user of input mistakes when writing the booking parameters.
 * @param {Array of String} errors An Array of strings with the errors to display.
 */
var CSErrorPopup = function (title, errors, afterMessage) {
    var popup = new ErrorPopup(Html.span("errorTitle", title), errors, Html.span("messageAfterErrors", afterMessage));
    popup.open();
};

/**
 * Utility function to build an error list.
 * @param {Array of String} errors An Array of strings with the errors to display.
 * @return An Html.span() if there is only 1 error, an Html.ul() if there are more.
 */
var CSErrorList = function(errors, style) {
    if (!exists(style)) {
        style = "errorList"
    }
    var errorList;
    if (errors.length > 1) {
        errorList = Html.ul("errorList")
        each(errors, function(e) {
            errorList.append(Html.li('', e));
        });
    } else {
        errorList = Html.span({}, errors[0]);
    }
    return errorList;
};

/**
 * Utility function to add an iframe inside the 'iframes' div element, given a booking.
 * The booking id is used to name the iframe.
 * Each booking will have a corresponding iframe that will be using when, for example, loading an URL,
 * or downloading the EVO client...
 * @param {object} booking A booking object.
 */
var addIFrame = function(booking) {
    var iframeName = "iframeTarget" + booking.id;
    var iframe = Html.iframe({id: iframeName, name: iframeName, src:"", style:{display: "block"}});
    $E('iframes').append(iframe);
};

/**
  * Utility function to remove an iframe inside the 'iframes' div element, given a booking.
  * The booking id is used to find the iframe to remove.
  * @param {object} booking A booking object.
  */
var removeIFrame = function(booking) {
    var iframeName = "iframeTarget" + booking.id;
    $E('iframes').remove($E(iframeName));
};

/**
 * Utility function that returns true if the given plugin has a function in the "codes" object with the given name.
 * @param {String} pluginName The name of the plugin. Example: EVO, DummyPlugin
 * @param {String} functionName The name of the function. Example: start, stop, checkParams.
 * @return {boolean} true if the given plugin has a function in the "codes" object with the given name, false otherwise.
 */
var pluginHasFunction = function(pluginName, functionName) {
    return !(codes[pluginName][functionName] === undefined)
};

/**
 * Utility function that calls a function defined by a plugin inside JSCode.js and returns the value.
 * @param {String} pluginName The name of the plugin.
 * @param {String} functionName The name of the function.
 * @param {??} arguments Stuff that will be passed to the function
 * @return {??} Stuff returned by the function.
 */
var callFunction = function(pluginName, functionName, arguments) {
    if (pluginHasFunction(pluginName, functionName)) {
        return codes[pluginName][functionName](arguments);
    }
};

/**
 * Utility function to be used by plugins.
 * It returns if a date is in the past or not,
 * provided the date is expressed in the same timezone as the event.
 */
var beforeNow = function(date) {
    var elapsedSinceLoad = new Date().getTime() - clientLoadTime.getTime();
    var eventNow = new Date()
    eventNow.setTime(eventLoadTime.getTime() + elapsedSinceLoad);
    return date < eventNow;
};

/**
 * Builds a parameter manager to verify a form's parameter
 * @param {String} pluginName The name of the plugin that the form belongs to.
 * @param {Array of nodes} formNodes An array of nodes such as the one that can be obtained with
 *                                   var formNodes = IndicoUtil.findFormFields(containerElement)
 * @param {object} values The values of the input nodes of the form. This is needed because checks
 *                        on some fields depend on values of others.
 * @return The parameterManager object so that we can call parameterManager.check() later.
 */
var buildParameterManager = function(pluginName, formNodes, values) {
    var parameterManager = new IndicoUtil.parameterManager();
    var checks = codes[pluginName].checkParams();
    each(formNodes, function(node){
        var checkData = checks[node.name]
        if (exists(checkData)) {
            var customCheckFunction = checkData[2];
            if (exists(customCheckFunction)) {
                parameterManager.add($E(node), checkData[0], checkData[1], function(value){
                    var errors = checkData[2](value, values);
                    if (errors.length == 0) {
                        return null;
                    } else {
                        return CSErrorList(errors);
                    }
                });
            } else {
                parameterManager.add($E(node), checkData[0], checkData[1]);
            }
        }
    });
    return parameterManager;
};

var formatDateStringCS = function(dateString) {
    return (dateString.substring(0,10) + ' at ' + dateString.substring(11, 16));
};

var formatDateTimeCS = function(date) {
    return date.date + ' at ' + date.time.substring(0,5);
};

// MULTIPLE-BOOKING TYPE FUNCTIONS
// They require the following variables defined:
// -bookings: a WatchList of bookings. See ConfModifCollaborationMultipleBookings.tpl

/**
 * Dictionary that maps booking ids to the state of the booking info text that can be shown or hidden.
 * true: currently shown, false: currently hidden.
 */
var showInfo = {};



/**
 * Highlights a booking row during 3 seconds, in yellow color,
 * in order to let the user see which booking was just created or modified.
 */
var hightlightBookingM = function(booking) {
    IndicoUI.Effect.highLightBackground("bookingRow" + booking.id, highlightColor, 3000);
    var existingInfoRow = $E("infoRow" + booking.id);
    if (existingInfoRow != null) {
        IndicoUI.Effect.highLightBackground("infoRow" + booking.id, highlightColor, 3000);
    }
};


var refreshTableHead = function() {
    var length = bookings.length.get();
    var headRow = $E('tableHeadRow');
    if (length == 0) {
        var cell = Html.td();
        cell.set(Html.span('','Currently no bookings have been created'));
        headRow.set(cell);
    } else {
        headRow.clear();

        var cell2 = Html.td({className: "collaborationTitleCell"})
        var span2 = Html.span({style:{fontSize: "medium"}}, "Type");
        cell2.set(span2);
        headRow.append(cell2);

        var cell3 = Html.td({className: "collaborationTitleCell"})
        var span3 = Html.span({style:{fontSize: "medium"}}, "Status");
        cell3.set(span3);
        headRow.append(cell3);

        var cell4 = Html.td({className: "collaborationTitleCell"})
        var span4 = Html.span({style:{fontSize: "medium"}}, "Info");
        cell4.set(span4);
        headRow.append(cell4);

        var cell5 = Html.td({className: "collaborationTitleCell", colspan: 10, colSpan: 10})
        var span5 = Html.span({style:{fontSize: "medium"}}, "Actions");
        cell5.set(span5);
        headRow.append(cell5);
    }
};

var refreshStartAllStopAllButtons = function() {
    var length = bookings.length.get();
    if (length > 1) {
        var nCanStart = 0;
        var nCanStop = 0;
        for (i=0; i < length; i++) {
            booking = bookings.item(i);
            if (booking.hasStart && booking.canBeStarted) {
                nCanStart++;
            }
            if (booking.hasStop && booking.canBeStopped) {
                nCanStop++;
            }
        };
        if (nCanStart > 1) {
            IndicoUI.Effect.appear($E('startAll'), 'inline');
        }
        if (nCanStop > 1) {
            IndicoUI.Effect.appear($E('stopAll'), 'inline');
        }
    } else {
        IndicoUI.Effect.disappear($E('startAll'));
        IndicoUI.Effect.disappear($E('stopAll'));
    }
};

/* ------------------------------ Booking templates -------------------------------*/

// Require the following variable defined:
// -userIsAdmin (boolean)

/**
 * Builds a table row element from a booking object, pickled from an Indico's CSBooking object
 * @param {Object} booking A booking object.
 * @return {XElement} an Html.row() XElement with the row representing the booking.
 */
var bookingTemplateM = function(booking) {

    var row = Html.tr({id: "bookingRow" + booking.id});

    var cell2 = Html.td({className : "collaborationCell", style: {textAlign: 'center'}});
    var span = Html.span({style:{fontSize:"medium"}}, booking.type);
    cell2.set(span);
    row.append(cell2);

    var cell3 = Html.td({className : "collaborationCell"});
    var span = Html.span("statusMessage " + booking.statusClass, booking.statusMessage);
    cell3.append(span);
    if (booking.hasCheckStatus) {
        var checkStatusButton = Widget.link(command(
            function() {checkStatus(booking);} ,
            Html.img({
                alt: "Check Booking Status",
                title: "Check Booking Status",
                src: imageSrc("reload"),
                style: {
                    'verticalAlign': 'middle'
                }
            })
        ));
        cell3.append(checkStatusButton);
    }

    row.append(cell3);

    var cellCustom;
    if (pluginHasFunction(booking.type, "customText")) {
        cellCustom = Html.td({className : "collaborationCell"});
        cellCustom.dom.innerHTML = codes[booking.type].customText(booking);
    } else {
        cellCustom = Html.td();
    }
    row.append(cellCustom);

    var cellShow;
    if (pluginHasFunction(booking.type, "showInfo")) {
        cellShow = Html.td({className : "collaborationCell"});
        showInfoButton = IndicoUI.Buttons.customImgSwitchButton(
            false,
            Html.img({
                alt: "Show info",
                src: imageSrc("info"),
                className: "centeredImg"
            }),
            Html.img({
                alt: "Hide info",
                src: imageSrc("info"),
                className: "centeredImg"
            }),
            booking, showBookingInfo, showBookingInfo
        );
        cellShow.set(showInfoButton);
    } else {
        cellShow = Html.td();
    }
    row.append(cellShow);

    var cellEdit = Html.td({className : "collaborationCellNarrow"});
        editButton = Widget.link(command(function(){
            edit(booking);
        },
        IndicoUI.Buttons.editButton()));
    cellEdit.set(editButton);
    row.append(cellEdit);

    var cellRemove = Html.td({className : "collaborationCellNarrow"});
        removeButton = Widget.link(command(function(){
            remove(booking);
        },
        IndicoUI.Buttons.removeButton()));
    cellRemove.set(removeButton);
    row.append(cellRemove);

    var cellStart;
    if (booking.hasStart) {
        var cellStart = Html.td({className : "collaborationCell"});
        if (booking.canBeStarted) {
            var playButton = Widget.link( command(function(){start(booking);} , IndicoUI.Buttons.playButton(false) ) );
        } else {
            var playButton = IndicoUI.Buttons.playButton(true);
        }
        cellStart.set(playButton);
    } else {
        var cellStart = Html.td();
    }
    row.append(cellStart);


    if (booking.hasStop) {
        var cellStop = Html.td({className : "collaborationCellNarrow"});
        if (booking.canBeStopped) {
            var stopButton = Widget.link( command(function(){stop(booking);} , IndicoUI.Buttons.stopButton(false) ) );
        } else {
            var stopButton = IndicoUI.Buttons.stopButton(true);
        }
        cellStop.set(stopButton);
        row.append(cellStop);
    };

    if (booking.hasAcceptReject && userIsAdmin) {
        var cellAccept = Html.td({className : "collaborationCell"});
        var acceptButton = Widget.link(command(
            function() {accept(booking);} ,
            Html.img({
                alt: "Accept Booking",
                title: "Accept Booking",
                src: imageSrc("accept"),
                style: {
                    'verticalAlign': 'middle'
                }
            })
        ));
        cellAccept.set(acceptButton);
        row.append(cellAccept);

        var cellReject = Html.td({className : "collaborationCellNarrow"});
        var rejectButton = Widget.link(command(
            function() {reject(booking);} ,
            Html.img({
                alt: "Reject Booking",
                title: "Reject Booking",
                src: imageSrc("reject"),
                style: {
                    'verticalAlign': 'middle'
                }
            })
        ));
        cellReject.set(rejectButton);
        row.append(cellReject);
    };

    return row;
};


var bookingTemplateS = function(booking) {

    var list = Html.ul({id:"bookingUl" + booking.id, className: "singleBooking"})

    var liState = Html.li("singleBooking")
    var span = Html.span("statusMessage " + booking.statusClass, booking.statusMessage);
    liState.append(span);
    if (booking.hasCheckStatus) {
        var checkStatusButton = Widget.link(command(
            function() {checkStatus(booking);} ,
            Html.img({
                alt: "Check Booking Status",
                title: "Check Booking Status",
                src: imageSrc("reload"),
                className: "centeredImg"
            })
        ));
        liState.append(checkStatusButton);
    };
    list.append(liState);

    if (pluginHasFunction(booking.type, "customText")) {
        var text = codes[booking.type].customText(booking);
        if (text) {
            var customTextDiv = Html.div('singleBookingCustomText');
            customTextDiv.dom.innerHTML = text;
        }
        var liInfo = Html.li("singleBooking", customTextDiv);
        list.append(liInfo);
    }

    if (booking.hasStart || booking.hasStop || (booking.hasAcceptReject && userIsAdmin)) {
        var liActions = Html.li("singleBooking");

        if (booking.hasStart) {
            if (booking.canBeStarted) {
                var playButton = Widget.link( command(function(){start(booking);} , IndicoUI.Buttons.playButton(false) ) );
            } else {
                var playButton = IndicoUI.Buttons.playButton(true);
            }
            liActions.append(Html.div("actionButton", playButton));
        }

        if (booking.hasStop) {
            if (booking.canBeStopped) {
                var stopButton = Widget.link( command(function(){stop(booking);} , IndicoUI.Buttons.stopButton(false) ) );
            } else {
                var stopButton = IndicoUI.Buttons.stopButton(true);
            }
            liActions.append(Html.div("actionButton", stopButton));
        }



        if (booking.hasAcceptReject && userIsAdmin) {
            var acceptButton = Widget.link(command(
                function() {accept(booking);} ,
                Html.img({
                    alt: "Accept Booking",
                    title: "Accept Booking",
                    src: imageSrc("accept"),
                    style: {
                        'verticalAlign': 'middle'
                    }
                })
            ));
            liActions.append(Html.div("actionButton", acceptButton));

            var rejectButton = Widget.link(command(
                function() {reject(booking);} ,
                Html.img({
                    alt: "Reject Booking",
                    title: "Reject Booking",
                    src: imageSrc("reject"),
                    style: {
                        'verticalAlign': 'middle'
                    }
                })
            ));
            liActions.append(Html.div("actionButton", rejectButton));
        };

        list.append(liActions);
    }

    return list;
};

/* ------------------------------ FUNCTIONS TO BE CALLED WHEN USER EVENTS HAPPEN -------------------------------*/

// COMMON FUNCTIONS

/**
 * Refreshes the display of a booking.
 * Depending of the type of booking, it will call in turn
 * refreshBookingM (for bookings of plugins who allow multiple bookings) or
 * refreshBookingS (for bookings of plugins who allow only one booking)
 */
var refreshBooking = function(booking) {
    if (booking.allowMultiple) {
        refreshBookingM(booking);
    } else {
        refreshBookingS(booking);
    }
};

/**
 * -Function that will be called when the user presses the "Start" button of a booking.
 * -If the booking's plugin has defined a "checkStart" function, it will be called to verify (locally)
 * that the booking can be started. If the booking cannot start, nothing happens (other than what
 * the "checkStart" function wants to do in that case, like popping up an alert).
 * -If the booking's plugin has set "requiresServerCallForStart" to true, the server is notified
 * of the booking start. The server can then take appropiate actions, or change the booking object, for example the permissionToStart flag.
 * -The booking object is replaced by a new booking object with same id and same booking parameters (but maybe some flags will be different).
 * -The "startBookingLocal" function will be called in any case (this function will verify if there should be a local action).
 * @param {object} booking The booking object corresponding to the "start" button that was pressed.
 */
var startBooking = function(booking, conferenceId) {

    if (!pluginHasFunction(booking.type, "checkStart") || codes[booking.type].checkStart(booking)) {

        if (booking.requiresServerCallForStart) {
            var killProgress = IndicoUI.Dialogs.Util.progress("Starting...");
            indicoRequest(
                'collaboration.startCSBooking',
                {
                    conference: conferenceId,
                    bookingId: booking.id
                },
                function(result,error) {
                    if (!error) {
                        startBookingLocal(result);
                        refreshBooking(result);
                        killProgress();
                    } else {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
            );
        } else {
            startBookingLocal(booking);
        }
    }
};

/**
 * Function called to execute the local action when starting a booking.
 * It will verify that the booking's plugin has an actual client-side action configured,
 * that the booking is authorized to start.
 * Then the "start" Javascript function of the booking will be called, passing the booking object and its corresponding iframe
 * in case it is needed for something (loading an URL to send a message / download Koala / etc ).
 */
var startBookingLocal = function(booking) {
    if (booking.requiresClientCallForStart && booking.permissionToStart) {
        codes[booking.type].start(booking, frames["iframeTarget" + booking.id]);
    }
};

/**
 * -Function that will be called when the user presses the "Stop" button of a booking.
 * -If the booking's plugin has set "requiresServerCallForStop" to true, the server is notified
 * of the booking stop. The server can then take appropiate actions,
 * or change the booking object, for example the permissionToStop flag.
 * -The booking object is replaced by a new booking object with same id and same booking parameters (but maybe some flags will be different).
 * -The "stopBookingLocal" function will be called in any case (this function will verify if there should be a local action).
 * @param {object} booking The booking object corresponding to the "stop" button that was pressed.
 */
var stopBooking = function(booking, conferenceId) {

    if (booking.requiresServerCallForStop) {
        var killProgress = IndicoUI.Dialogs.Util.progress("Stopping...");
        indicoRequest(
            'collaboration.stopCSBooking',
            {
                conference: conferenceId,
                bookingId: booking.id
            },
            function(result,error) {
                if (!error) {
                    stopBookingLocal(result);
                    refreshBooking(result);
                    killProgress();
                } else {
                    killProgress();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    } else {
        stopBookingLocal(booking);
    }
};


/**
* Function called to execute the local action when stopping a booking.
* It will verify that the booking's plugin has an actual client-side action configured,
* that the booking is authorized to stop.
* Then the "stop" Javascript function of the booking will be called, passing the booking object and its corresponding iframe
* in case it is needed for something.
*/
var stopBookingLocal = function(booking) {
    if (booking.requiresClientCallForStop && booking.permissionToStop) {
        codes[booking.type].stop(booking, frames["iframeTarget" + booking.id]);
    }
};

/**
 * Function called when the user presses the "Check Status" button of a booking.
 * The booking will be refreshed after its status has been updated.
 */
var checkBookingStatus = function(booking, conferenceId) {

    var killProgress = IndicoUI.Dialogs.Util.progress("Checking status...");
    indicoRequest(
        'collaboration.checkCSBookingStatus',
        {
            conference: conferenceId,
            bookingId: booking.id
        },
        function(result,error) {
            if (!error) {
                if (result.error) {
                    killProgress();
                    codes[booking.type].errorHandler('checkStatus', result);
                } else {
                    refreshBooking(result);
                    killProgress();
                }
            } else {
                killProgress();
                IndicoUtil.errorReport(error);
            }
        }
    );

};

var acceptBooking = function(booking, conferenceId) {
    var killProgress = IndicoUI.Dialogs.Util.progress("Accepting booking...");
    indicoRequest(
        'collaboration.acceptCSBooking',
        {
            conference: conferenceId,
            bookingId: booking.id
        },
        function(result,error) {
            if (!error) {
                refreshBooking(result);
                killProgress();
            } else {
                killProgress();
                IndicoUtil.errorReport(error);
            }
        }
    );
};

var rejectBooking = function(booking, conferenceId) {

    var title = "Reason for rejection";


    var popup = new ExclusivePopup(title, function(){return true;});

    popup.draw = function(){
        var self = this;
        var span1 = Html.span('', "Please write the reason of your rejection (short):");
        var textarea = Html.textarea({style:{marginTop: '5px', marginBottom: '5px'}, id: "rejectionTextarea", rows: 3, cols: 30});
        var span2 = Html.span('', "The reason will be displayed to the user.");

        // We construct the "ok" button and what happens when it's pressed
        var okButton = Html.button('', "OK");
        okButton.observeClick(function() {
            var killProgress = IndicoUI.Dialogs.Util.progress("Rejecting booking...");
            var reason = textarea.get();

            indicoRequest(
                'collaboration.rejectCSBooking',
                {
                    conference: conferenceId,
                    reason: reason,
                    bookingId: booking.id
                },
                function(result,error) {
                    if (!error) {
                        refreshBooking(result);
                        killProgress();
                    } else {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
            );
            self.close();
        });

        // We construct the "cancel" button and what happens when it's pressed (which is: just close the dialog)
        var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, "Cancel Rejection");
        cancelButton.observeClick(function(){
            self.close();
        });

        var buttonDiv = Html.div({style:{textAlign:"center", marginTop:pixels(10)}}, okButton, cancelButton)

        return this.ExclusivePopup.prototype.draw.call(this, Widget.block([span1, Html.br(), textarea, Html.br(), span2, Html.br(), buttonDiv]));
    };

    popup.open();
};

//MULTIPLE-BOOKING TYPE FUNCTIONS
//They require the following variables defined:
//-bookings: a WatchList of bookings. See ConfModifCollaborationMultipleBookings.tpl
//They require the following DOM elements defined:
//-bookingsTableBody : a tbody where the booking rows will appear

/**
 * Requests the list of bookings from the server,
 * and put them into the "bookings" watchlist.
 * As a consequence the bookings table where 1 booking = 1 row is initialized.
 */
var displayBookings = function() {

    var killProgress = IndicoUI.Dialogs.Util.progress("Loading list of bookings...");
    // We bind the watchlist and the table through the template
    bind.element($E("bookingsTableBody"), bookings, bookingTemplateM);
    each(bookings, function(booking) {
        addIFrame(booking);
    });
    refreshStartAllStopAllButtons();
    refreshTableHead();
    killProgress();
};

/**
 * Given a booking id, it returns the index of the booking with that id in the "var bookings = $L();" object.
 * Example: bookings is a Watchlist of booking object who ids are [1,2,10,12].
 *          getBookingIndexById('10') will return 2.
 * @param {String} id The id of a booking object.
 * @return {int} the index of the booking object with the given id, inside the watchlist "bookings".
 */
var getBookingIndexById = function(id) {
    for (var i=0; i < bookings.length.get(); i++) {
        booking = bookings.item(i);
        if (booking.id == id) {
            return i;
        }
    }
};

/**
* Utility function to "refresh" the display of a booking that has been changed.
* Since just changing the object doesn't notify the watchlist of the change, we have to remove and insert it.
* @param {object} booking A booking object that has to be inside the 'bookings' watchlist.
*/
var refreshBookingM = function(booking) {
    var index = getBookingIndexById(booking.id);
    hideAllInfoRows(false);
    bookings.removeAt(index);
    bookings.insert(booking, index+"");
    showAllInfoRows(false);
    hightlightBookingM(booking);
};

/**
 * Hides the information text of a booking by removing its row from the table
 */
var hideInfoRow = function (booking) {
    var existingInfoRow = $E("infoRow" + booking.id);
    if (existingInfoRow != null) {
        IndicoUI.Effect.disappear(existingInfoRow);
        $E('bookingsTableBody').remove(existingInfoRow);
    } //otherwise ignore
};

/**
 * Shows the information text of a booking by adding its row to the table and updating it
 */
var showInfoRow = function(booking) {
    var newRow = Html.tr({id: "infoRow" + booking.id, display: "none"});
    var newCell = Html.td({id: "infoCell" + booking.id, colspan: 10, colSpan: 10, className : "collaborationInfoCell"});
    newRow.append(newCell);
    var nextRowDom = $E('bookingRow'+booking.id).dom.nextSibling;
    if (nextRowDom) {
        $E('bookingsTableBody').dom.insertBefore(newRow.dom, nextRowDom);
    } else {
        $E('bookingsTableBody').append(newRow);
    }
    updateInfoRow(booking);
    IndicoUI.Effect.appear(newRow, '');
};

/**
 * Sets the HTML inside the information text of a booking
 */
var updateInfoRow = function(booking) {
    var existingInfoCell = $E("infoCell" + booking.id);
    if (existingInfoCell != null) { // we update
        var infoHTML = codes[booking.type].showInfo(booking)
        existingInfoCell.dom.innerHTML = infoHTML;
    } //otherwise ignore
};

/**
 * Hides all of the information rows
 * @param {boolean} markAsHidden If true, the rows will be marked as hidden in the showInfo object
 */
var hideAllInfoRows = function(markAsHidden) {
    bookings.each(function(booking) {
        hideInfoRow(booking);
        if (markAsHidden) {
            showInfo[booking.id] = false;
        }
    });
};

/**
 * Hides all of the information rows
 * @param {boolean} showAll If true, all the rows will be shown. Otherwise, only those marked as shown in the showInfoObject
 */
var showAllInfoRows = function(showAll) {
    bookings.each(function(booking) {
        if (showAll || showInfo[booking.id]) {
            showInfoRow(booking);
            showInfo[booking.id] = true;
        }
    });
};

/**
 * -Function that will be called when the user presses the "Create" button.
 * -A modal dialog will emerge to request the booking parameters to the user.
 *  The dialog will change depending on the plugin that has been selected.
 * -The necessary HTML for each plugin is taken from the 'forms' dictionary.
 * -The booking parameters input by the user are retrieved with the "IndicoUtil.getFormValues" function.
 * -If the plugin has defined a "checkParams" function, this function is called before actually sending the booking to the server.
 *  If the function finds any errors, another modal dialog displays them and the booking cannot be added to the server.
 * -If the booking is actually sent to the server, 2 things can occur:
 *    +there have been no problems, so the booking is added to the 'bookings' watchlist, so the table is updated, and an iframe is created.
 *    +there have been problems, an exception message will appear.
 */
var createBooking = function(pluginName, conferenceId) {

    var selectedPlugin = getSelectedPlugin();

    var popup = new ExclusivePopup(null, function(){return true;});

    popup.draw = function() {
        var self = this;

        // We get the form HTML
        var form = Html.div();
        form.dom.innerHTML = forms[pluginName];

        // If this kind of booking can be notified of date changes, we offer a checkbox (checked by default)
        if (canBeNotifiedOnDateChanges[pluginName]) {
            var dateCheckBox = Html.checkbox({id : "dateCheckBox", name:"notifyOnDateChanges", value:"notifyOnDateChanges"});
            var dateLabel = Html.label({}, "Change this booking's dates if the event's dates change");
            dateLabel.dom.htmlFor = "dateCheckBox";
            var dateChangeDiv = Html.div({style : {display: "block", marginTop:pixels(10), fontWeight:"normal"}}, dateCheckBox, dateLabel);
            dateCheckBox.dom.checked = true;
            form.append(dateChangeDiv);
        }

        var formNodes = IndicoUtil.findFormFields(form);
        var values = {}

        if (pluginHasFunction(pluginName, "getDateFields")) {
            var fieldList = codes[pluginName].getDateFields();
            var fieldDict = {};
            each(fieldList, function(name){
                fieldDict[name] = true;
            });
            each(formNodes, function(node){
                if (node.name in fieldDict) {
                    IndicoUI.Widgets.Generic.input2dateField($E(node), true, null)
                }
            });
        }

        var needsCheck = pluginHasFunction (selectedPlugin, "checkParams");
        var parameterManager;
        if (needsCheck) {
            parameterManager = buildParameterManager(selectedPlugin, formNodes, values);
        }

        // We construct the "ok" button and what happens when it's pressed
        var saveButton = Html.button(null, "Save");
        saveButton.observeClick(function(){

            // We retrieve the values from the form
            IndicoUtil.getFormValues(formNodes, values);

            // We check if there are errors
            var checkOK = true;
            if (needsCheck) {
                checkOK = parameterManager.check();
            }

            // If there are no errors, the booking is sent to the server
            if (checkOK) {
                var killProgress = IndicoUI.Dialogs.Util.progress("Saving your booking...");

                var saveOk = true;
                if (pluginHasFunction(pluginName, "onSave")) {
                    saveOk = codes[pluginName].onSave(values);
                }

                if (saveOk) {
                    indicoRequest(
                        'collaboration.createCSBooking',
                        {
                            conference: conferenceId,
                            type: selectedPlugin,
                            bookingParams: values
                        },
                        function(result,error) {
                            if (!error) {
                                // If the server found no problems, a booking object is returned in the result.
                                // We add it to the watchlist and create an iframe.
                                if (result.error) {
                                    killProgress();
                                    codes[pluginName].errorHandler('create', result);
                                } else {
                                    hideAllInfoRows(false);
                                    bookings.append(result);
                                    showAllInfoRows(false);
                                    addIFrame(result);
                                    showInfo[result.id] = false; // we initialize the show info boolean for this booking
                                    refreshStartAllStopAllButtons();
                                    refreshTableHead();
                                    killProgress();
                                    hightlightBookingM(result);
                                    self.close();

                                    if (pluginHasFunction(pluginName, 'postCreate')) {
                                        codes[pluginName].postCreate(result);
                                    }
                                }
                            } else {
                                killProgress();
                                self.close();
                                IndicoUtil.errorReport(error);
                            }
                        }
                    );
                } else { // saveOk = false
                    killProgress();
                }
            }
        });

        // We construct the "cancel" button and what happens when it's pressed (which is: just close the dialog)
        var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, "Cancel");
        cancelButton.observeClick(function(){
            self.close();
        });

        var buttonDiv = Html.div({style:{textAlign:"center", marginTop:pixels(10)}}, saveButton, cancelButton)

        return this.ExclusivePopup.prototype.draw.call(this, Widget.block([form, buttonDiv]));
    };

    popup.open();

    if (pluginHasFunction(pluginName, "onCreate")) {
        codes[pluginName].onCreate();
    }
};

/**
 * -Function that will be called when the user presses the "Remove" button for a plugin.
 * -A modal dialog will emerge to request permission to remove the booking.
 * -2 things can occur:
 *    +there have been no problems in removing the booking, so the booking is removed from the 'bookings' watchlist,
 *    so the table is updated, and an iframe is deleted.
 *    +there have been problems, an exception message will appear.
 * @param {object} booking The booking object corresponding to the "remove" button that was pressed.
 */
var removeBooking = function(booking, conferenceId) {

    var title = "Remove booking";

    var popup = new ExclusivePopup(title, function(){return true;});

    popup.draw = function(){
        var self = this;
        var span = Html.span("", "Are you sure you want to remove that " + booking.type + " booking?");

        // We construct the "ok" button and what happens when it's pressed
        var okButton = Html.button(null, "Remove");
        okButton.observeClick(function() {
            var killProgress = IndicoUI.Dialogs.Util.progress("Removing your booking...");

            indicoRequest(
                'collaboration.removeCSBooking',
                {
                    conference: conferenceId,
                    bookingId: booking.id
                },
                function(result,error) {
                    if (!error) {
                        // If the server found no problems, we remove the booking from the watchlist and remove the corresponding iframe.
                        if (result && result.error) {
                            killProgress();
                            codes[booking.type].errorHandler('remove', result);
                        } else {
                            hideAllInfoRows(false);
                            bookings.removeAt(getBookingIndexById(booking.id))
                            showAllInfoRows(false);
                            removeIFrame(booking);
                            refreshStartAllStopAllButtons();
                            refreshTableHead();

                            if (pluginHasFunction(booking.type, 'postDelete')) {
                                codes[booking.type].postDelete(result);
                            }
                        }
                        killProgress();
                    } else {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
            );
            self.close();
        });

        // We construct the "cancel" button and what happens when it's pressed (which is: just close the dialog)
        var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, "Cancel");
        cancelButton.observeClick(function(){
            self.close();
        });

        var buttonDiv = Html.div({style:{textAlign:"center", marginTop:pixels(10)}}, okButton, cancelButton)

        return this.ExclusivePopup.prototype.draw.call(this, Widget.block([span, Html.br(), buttonDiv]));
    };
    popup.open();
};


/**
 * -Function that will be called when the user presses the "Edit" button of a booking.
 * -A modal dialog will emerge to request the new booking parameters to the user.
 *  The dialog will change depending on the plugin that has been selected.
 * -The necessary HTML for each plugin is taken from the 'forms' dictionary.
 * -The already existing parameters will be taken from the booking object, and they will appear in the form
    thanks to the "IndicoUtil.setFormValues" function.
 * -If the plugin has defined a "checkParams" function, this function is called before actually sending the booking to the server.
 *  If the function finds any errors, another modal dialog displays them and the booking cannot be added to the server.
 * -If the booking is actually sent to the server, 2 things can occur:
 *    +there have been no problems, so the booking is "refreshed" in the 'bookings' watchlist, so the table is updated.
 *    +there have been problems, an exception message will appear.
 * @param {object} booking The booking object corresponding to the "remove" button that was pressed.
 */
var editBooking = function(booking, conferenceId) {

    var popup = new ExclusivePopup(null, function(){return true;});

    popup.draw = function(){
        var self = this;

        // We get the form HTML and set the existing object values into the form
        var form = Html.div();
        form.dom.innerHTML = forms[booking.type];

        // If this kind of booking can be notified of date changes, we offer a checkbox (checked by default)
        if (booking.canBeNotifiedOfEventDateChanges) {
            var dateCheckBox = Html.checkbox({id : "dateCheckBox", name:"notifyOnDateChanges", value:"notifyOnDateChanges"});
            var dateLabel = Html.label({}, "Change this booking's dates if the event's dates change");
            dateLabel.dom.htmlFor = "dateCheckBox";
            var dateChangeDiv = Html.div({style : {display: "block", marginTop:pixels(10), fontWeight:"normal"}}, dateCheckBox, dateLabel);
            dateCheckBox.dom.checked = true;

            form.append(dateChangeDiv);
        }

        var formNodes = IndicoUtil.findFormFields(form);
        var values = {}

        if (pluginHasFunction(booking.type, "getDateFields")) {
            var fieldList = codes[booking.type].getDateFields();
            var fieldDict = {};
            each(fieldList, function(name){
                fieldDict[name] = true;
            });
            each(formNodes, function(node){
                if (node.name in fieldDict) {
                    IndicoUI.Widgets.Generic.input2dateField($E(node), true, null)
                }
            });
        }

        IndicoUtil.setFormValues(formNodes, booking.bookingParams);

        var needsCheck = pluginHasFunction (booking.type, "checkParams");
        var parameterManager;
        if (needsCheck) {
            parameterManager = buildParameterManager(booking.type, formNodes, values);
        }

        // We construct the "save" button and what happens when it's pressed
        var saveButton = Html.button(null, "Save");
        saveButton.observeClick(function() {

            // We retrieve the values from the form
            IndicoUtil.getFormValues(formNodes, values);

            // We check if there are errors
            var checkOK = true;
            if (needsCheck) {
                checkOK = parameterManager.check();
            }

            // If there are no errors, the booking is sent to the server
            if (checkOK) {
                var killProgress = IndicoUI.Dialogs.Util.progress("Saving your booking...");

                var saveOk = true;
                if (pluginHasFunction(booking.type, "onSave")) {
                    saveOk = codes[booking.type].onSave(values);
                }

                if (saveOk) {
                    indicoRequest(
                        'collaboration.editCSBooking',
                        {
                            conference: conferenceId,
                            bookingId: booking.id,
                            bookingParams: values
                        },
                        function(result,error) {
                            if (!error) {
                                if (result.error) {
                                    killProgress();
                                    codes[booking.type].errorHandler('edit', result);
                                } else {
                                    refreshBooking(result);
                                    killProgress();
                                    self.close();
                                    if (pluginHasFunction(booking.type, 'postEdit')) {
                                        codes[pluginName].postEdit(result);
                                    }
                                }

                            } else {
                                killProgress();
                                self.close();
                                IndicoUtil.errorReport(error);
                            }
                        }
                    );
                } else { // saveOk = false
                    killProgress();
                }
            }
        });

        // We construct the "cancel" button and what happens when it's pressed (which is: just close the dialog)
        var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, "Cancel");
        cancelButton.observeClick(function(){
            self.close();
        });

        var buttonDiv = Html.div({style:{textAlign:"center", marginTop:pixels(10)}}, saveButton, cancelButton)

        return this.ExclusivePopup.prototype.draw.call(this, Widget.block([form, buttonDiv]));
    };
    popup.open();

    if (pluginHasFunction(booking.type, "onEdit")) {
        codes[booking.type].onEdit(booking);
    }
};

/**
 * -Function that will be called when the user presses the "Show" button of a booking.
 * -A new row will be created in the table of bookings in order to show this information.
 * -Drawback: the row will be destroyed when a new booking is added or a booking is edited.
 */
var showBookingInfo = function(booking) {
    if (showInfo[booking.id]) { // true if info already being shown
        hideInfoRow(booking);
    } else { // false if we have to show it
        showInfoRow(booking);
    }
    showInfo[booking.id] = !showInfo[booking.id];
};

/**
 * Function that will be called when the user presses the "Start All" button.
 * It will be equivalent to pressing each of the bookings' "Start" button in intervals of 1 second.
 */
var startAll = function(){
    var length = bookings.length.get()
    for (var i=0; i < length; i++) {
        setTimeout("start(bookings.item(" + i + "))", i*1000);
    }
};

/**
 * Function that will be called when the user presses the "Stop All" button.
 * It will be equivalent to pressing each of the bookings' "Stop" button in intervals of 1 second.
 */
var stopAll = function(){
    var length = bookings.length.get()
    for (var i=0; i < length; i++) {
        setTimeout("stop(bookings.item(" + i + "))", i*1000);
    }
};

//SINGLE-BOOKING TYPE FUNCTIONS
//They require the following variables defined:
//-singleBookings: a dictionary pluginName -> booking. See ConfModifCollaborationSingleBookings.tpl
//And the following DOM elements defined:
//-for each plugin: a div called XXXXDiv where XXXX is the plugin name (see ConfModifCollaborationSingleBookings.tpl)
//-for each plugin: a div called XXXXInfo where XXXX is the plugin name (see ConfModifCollaborationSingleBookings.tpl), inside XXXXDiv
//-for each plugin: a div called XXXXForm where XXXX is the plugin name (see ConfModifCollaborationSingleBookings.tpl), inside XXXXDiv

var refreshBookingS = function(booking) {
    $E(booking.type + 'Info').set(bookingTemplateS(booking));
};

var refreshPlugin = function(name) {
    if (exists(singleBookings[name])) {
        refreshBookingS(singleBookings[name]);
        var formNodes = IndicoUtil.findFormFields($E(name + 'Form'));
        IndicoUtil.setFormValues(formNodes, singleBookings[name].bookingParams);
        IndicoUI.Effect.appear($E('withdraw'+name+'Top'), 'inline');
        IndicoUI.Effect.appear($E('withdraw'+name+'Bottom'), 'inline');
        IndicoUI.Effect.appear($E('modify'+name+'Top'), 'inline');
        IndicoUI.Effect.appear($E('modify'+name+'Bottom'), 'inline');
        IndicoUI.Effect.disappear($E('send'+name+'Top'));
        IndicoUI.Effect.disappear($E('send'+name+'Bottom'));
    } else {
        IndicoUI.Effect.disappear($E('withdraw'+name+'Top'));
        IndicoUI.Effect.disappear($E('withdraw'+name+'Bottom'));
        IndicoUI.Effect.disappear($E('modify'+name+'Top'));
        IndicoUI.Effect.disappear($E('modify'+name+'Bottom'));
        IndicoUI.Effect.appear($E('send'+name+'Top'), 'inline');
        IndicoUI.Effect.appear($E('send'+name+'Bottom'), 'inline');
        $E(name + 'Info').clear();
    }
};

var sendRequest = function(pluginName, conferenceId) {

    // We retrieve the values from the form
    var formNodes = IndicoUtil.findFormFields($E(pluginName + 'Form'))
    var values = IndicoUtil.getFormValues(formNodes);

    var needsCheck = pluginHasFunction (pluginName, "checkParams");
    var parameterManager;
    if (needsCheck) {
        parameterManager = buildParameterManager(pluginName, formNodes, values);
    }

    // We check if there are errors
    var checkOK = true;
    if (needsCheck) {
        checkOK = parameterManager.check();
    }

    // If there are no errors, the booking is sent to the server
    if (checkOK) {
        var killProgress = IndicoUI.Dialogs.Util.progress("Sending your request...");
        var commonHandler = function(result,error) {
            if (!error) {
                if (result.error) {
                    killProgress();
                    codes[pluginName].errorHandler(exists(singleBookings[pluginName]) ? 'edit' : 'create', result)
                } else {
                 // If the server found no problems, a booking object is returned in the result.
                    // We add it to the watchlist and create an iframe.
                    singleBookings[pluginName] = result;
                    refreshPlugin(pluginName);
                    addIFrame(result);
                    killProgress();
                    if (exists(singleBookings[pluginName])) {
                        if (pluginHasFunction(pluginName, 'postEdit')) {
                            codes[pluginName].postEdit(result);
                        }
                    } else {
                        if (pluginHasFunction(pluginName, 'postCreate')) {
                            codes[pluginName].postCreate(result);
                        }
                    }

                }
            } else {
                killProgress();
                IndicoUtil.errorReport(error);
            }
        }

        if (exists(singleBookings[pluginName])) {
            indicoRequest(
                'collaboration.editCSBooking',
                {
                    conference: conferenceId,
                    bookingId: singleBookings[pluginName].id,
                    bookingParams: values
                },
                commonHandler
            );
        } else {
            indicoRequest(
                'collaboration.createCSBooking',
                {
                    conference: conferenceId,
                    type: pluginName,
                    bookingParams: values
                },
                commonHandler
            );
        }
    } else {
        var allErrors = [];
        var checks = codes[pluginName]["checkParams"]();
        each(checks, function(value, key){
            customCheckFunction = value[2];
            if (exists(customCheckFunction)) {
                var errors = customCheckFunction(values[key], values);
                each (errors, function(error){
                    allErrors.push(error);
                });
            }
        });
        // If there are problems, we show them
        CSErrorPopup("Errors detected", allErrors, "The corresponding fields have been marked in red");
    }
};

var withdrawRequest = function(pluginName, conferenceId) {

    if (exists(singleBookings[pluginName])) {
        var self = this;
        var title = "Withdraw request";

        var popup = new ExclusivePopup(title, function(){return true;});
        popup.draw = function(){
            var self = this;
            var span = Html.span("", "Are you sure you want to withdraw the request?");

            // We construct the "ok" button and what happens when it's pressed
            var okButton = Html.button(null, "Withdraw");
            okButton.observeClick(function() {
                var killProgress = IndicoUI.Dialogs.Util.progress("Withdrawing your request...");

                indicoRequest(
                    'collaboration.removeCSBooking',
                    {
                        conference: conferenceId,
                        bookingId: singleBookings[pluginName].id
                    },
                    function(result,error) {
                        if (!error) {
                            if (result.error) {
                                killProgress();
                                codes[pluginName].errorHandler('remove', result)
                            } else {
                                // If the server found no problems, we remove the booking from the watchlist and remove the corresponding iframe.
                                removeIFrame(singleBookings[pluginName]);
                                singleBookings[pluginName] = null;
                                refreshPlugin(pluginName);
                                if (pluginHasFunction(pluginName, 'clearForm')) {
                                    codes[pluginName]['clearForm']()
                                }
                                killProgress();
                                if (pluginHasFunction(pluginName, 'postDelete')) {
                                    codes[pluginName].postDelete(result);
                                }
                            }
                        } else {
                            killProgress();
                            IndicoUtil.errorReport(error);
                        }
                    }
                );
                self.close();
            });

            // We construct the "cancel" button and what happens when it's pressed (which is: just close the dialog)
            var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, "Cancel");
            cancelButton.observeClick(function(){
                self.close();
            });

            var buttonDiv = Html.div({style:{textAlign:"center", marginTop:pixels(10)}}, okButton, cancelButton)

            return this.ExclusivePopup.prototype.draw.call(this, Widget.block([span, Html.br(), buttonDiv]));
        }
        popup.open();
    }
};

var buildShowHideButton = function(pluginName) {
    var showHideButton = IndicoUI.Buttons.customTextSwitchButton(
        true,
        "Show",
        "Hide",
        null,
        function() {IndicoUI.Effect.appear($E(pluginName + "Div"), '');},
        function() {IndicoUI.Effect.disappear($E(pluginName + "Div"), '');}
    );
    $E(pluginName + "showHide").set(showHideButton);
};

var loadBookings = function() {
    for (var i=0; i < singlePluginNames.length; i++) {
        var name = singlePluginNames[i];
        refreshPlugin(name);
    }
};