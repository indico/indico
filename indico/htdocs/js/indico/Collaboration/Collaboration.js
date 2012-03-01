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
    var popup = new ErrorPopup(title, errors, Html.span("messageAfterErrors", afterMessage));
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
 * @param {object} values The values of the input nodes of the form. This is needed because checks
 *                        on some fields depend on values of others.
 */
type("CSParameterManager", [], {

    __addComponent: function(component) {
        var self = this;

        var name;
        var componentToAdd;
        if (component.ErrorAware) {
            name = component.getName();
            componentToAdd = component;
        } else if (isDom(component)){
            name = component.name;
            componentToAdd = $E(component);
        } else {
            return;
        }
        var checkData = this.checks[name];

        if (exists(checkData)) {
            var customCheckFunction = checkData[2];
            if (exists(customCheckFunction)) {
                this.parameterManager.add(componentToAdd, checkData[0], checkData[1], function(value){
                    var errors = checkData[2](value, self.values);
                    if (errors.length == 0) {
                        return null;
                    } else {
                        return CSErrorList(errors);
                    }
                });
            } else {
                this.parameterManager.add(componentToAdd, checkData[0], checkData[1]);
            }
        }
    },

    /**
     * Adds component(s) to the inner parameter manager, looking for what checks should be done
     * in the corresponding plugin code.
     * @param {object} formNodes An array of nodes or ErrorAware components.
     *                           For example, an array of nodes can be obtained with
     *                           var formNodes = IndicoUtil.findFormFields(containerElement)
     */
    add: function(components) {
        var self = this;

        if(!isArrayOrListable(components)) {
            components = [components];
        }
        each(components, function(component) {
            self.__addComponent(component);
        });
    },

    /**
     * Executes check() on the inner parameterManager
     */
    check: function() {
        return this.parameterManager.check();
    }
},
    function(pluginName, values) {
        this.parameterManager = new IndicoUtil.parameterManager();
        this.values = values;
        this.checks = codes[pluginName].checkParams();
    }
);


var formatDateStringCS = function(dateString) {
    var dt = dateString.split(' ')
    return (dt[0] + ' at ' + dt[1]);
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
    IndicoUI.Effect.highLightBackground($E("bookingRow" + booking.id), highlightColor, 3000);
    var existingInfoRow = $E("infoRow" + booking.id);
    if (existingInfoRow != null) {
        IndicoUI.Effect.highLightBackground($E("infoRow" + booking.id), highlightColor, 3000);
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

        var firstCell = Html.td();
        headRow.append(firstCell);

        var typeCell = Html.td({className: "collaborationTitleCellNarrow"});
        var typeSpan = Html.span({style:{fontSize: "medium"}}, "Type");
        typeCell.set(typeSpan);
        headRow.append(typeCell);

        var statusCell = Html.td({className: "collaborationTitleCell"});
        var span3 = Html.span({style:{fontSize: "medium"}}, "Status");
        statusCell.set(span3);
        headRow.append(statusCell);

        var infoCell = Html.td({className: "collaborationTitleCell"});
        var infoSpan = Html.span({style:{fontSize: "medium"}}, "Info");
        infoCell.set(infoSpan);
        headRow.append(infoCell);

        var actionsCell = Html.td({className: "collaborationTitleCell", colspan: 10, colSpan: 10});
        var actionsSpan = Html.span({style:{fontSize: "medium"}}, "Actions");
        actionsCell.set(actionsSpan);
        headRow.append(actionsCell);

        var lastCell = Html.td({width: "100%", colspan: 1, colSpan: 1})
        headRow.append(lastCell);
    }
};

var refreshStartAllStopAllButtons = function() {
    var startShouldAppear = false;
    var stopShouldAppear = false;

    var length = bookings.length.get();
    if (length > 1) {
        var nCanStart = 0;
        var nCanStop = 0;
        var typesStart = {};
        var typesStop = {};
        var nTypesStart = 0;
        var nTypesStop = 0;

        for (i=0; i < length; i++) {
            booking = bookings.item(i);
            if (booking.hasStart && booking.canBeStarted) {
                if (booking.hasStartStopAll) {
                    nCanStart++;
                }
                if (!(booking.type in typesStart)) {
                    typesStart[booking.type] = true;
                    nTypesStart++;
                }
            }
            if (booking.hasStop && booking.canBeStopped) {
                if (booking.hasStartStopAll) {
                    nCanStop++;
                }
                if (!(booking.type in typesStop)) {
                    typesStop[booking.type] = true;
                    nTypesStop++;
                }
            }
        };

        startShouldAppear = nTypesStart > 1 || nCanStart > 1 ;
        stopShouldAppear = nTypesStop > 1 || nCanStop > 1 ;
    }

    if (startShouldAppear) {
        IndicoUI.Effect.appear($E('startAll'), 'inline');
    } else {
        IndicoUI.Effect.disappear($E('startAll'));
    }

    if (stopShouldAppear) {
        IndicoUI.Effect.appear($E('stopAll'), 'inline');
    } else {
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

    var cellShowInfo;
    if (pluginHasFunction(booking.type, "showInfo")) {
        cellShowInfo = Html.td({className : "collaborationCellNarrow"});
        showInfoButton = IndicoUI.Buttons.customImgSwitchButton(
            showInfo[booking.id],
            Html.img({
                alt: "Show info",
                src: imageSrc("itemExploded"),
                className: "centeredImg"
            }),
            Html.img({
                alt: "Hide info",
                src: imageSrc("currentMenuItem"),
                className: "centeredImg"
            }),
            booking, showBookingInfo, showBookingInfo
        );
        cellShowInfo.set(showInfoButton);
    } else {
        cellShowInfo = Html.td();
    }
    row.append(cellShowInfo);

    var typeCell = Html.td({className : "collaborationCellNarrow"});
    var typeSpan = Html.span({style:{fontSize:"medium"}}, booking.type);
    typeCell.set(typeSpan);
    row.append(typeCell);

    var statusCell = Html.td({className : "collaborationCell"});
    var statusSpan = Html.span("statusMessage " + booking.statusClass, booking.statusMessage);
    statusCell.append(statusSpan);
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
        statusCell.append(checkStatusButton);
    }

    row.append(statusCell);

    var cellCustom;
    if (pluginHasFunction(booking.type, "customText")) {
        cellCustom = Html.td({className : "collaborationCell"});
        cellCustom.dom.innerHTML = codes[booking.type].customText(booking);
    } else {
        cellCustom = Html.td();
    }
    row.append(cellCustom);

    var cellEditRemove = Html.td({className : "collaborationCell"});
    var editButton = Widget.link(command(function(){edit(booking);}, IndicoUI.Buttons.editButton()));
    if (booking.canBeDeleted) {
        var removeButton = Widget.link(command(function(){remove(booking);}, IndicoUI.Buttons.removeButton()));
    } else {
        var removeButton = IndicoUI.Buttons.removeButton(true);
    }
    cellEditRemove.append(editButton);
    cellEditRemove.append(removeButton);
    row.append(cellEditRemove);

    var cellButtons = Html.td({className : "collaborationCellNarrow"});;

    if (booking.hasConnect){
        if (booking.canBeConnected) {
            var connectButton = Widget.link( command(function(){connect(booking);} ,IndicoUI.Buttons.playButtonText($T("Connect ") + booking.linkVideoRoomLocation, "left" )) );
            cellButtons.append(connectButton);
        }
    }

    if (booking.hasStart) {
        if (booking.canBeStarted) {
            if(booking.hasConnect){
                var align="";
                if (booking.canBeConnected){
                    align = "right";
                }
                var playButton = Widget.link( command(function(){start(booking);} , IndicoUI.Buttons.playButtonText($T("Start desktop"), align) ) );
            }else{
                var playButton = Widget.link( command(function(){start(booking);} , IndicoUI.Buttons.playButton(false)) );
            }

        } else {
            var playButton = IndicoUI.Buttons.playButton(true);
        }
        cellButtons.append(playButton);
    }

    if (booking.hasStop) {
        var cellStop = Html.td({className : "collaborationCellNarrow"});
        if (booking.canBeStopped) {
            var stopButton = Widget.link( command(function(){stop(booking);} , IndicoUI.Buttons.stopButton(false) ) );
        } else {
            var stopButton = IndicoUI.Buttons.stopButton(true);
        }
        cellButtons.append(stopButton);
    }

    row.append(cellButtons);


    //var cellMail = Html.td({className : "collaborationCellNarrow"});
    //cellMail.set(Html.img({src: imageSrc("mail_big"), style: {'verticalAlign': 'middle', marginLeft: '3px', marginRight: '3px'}}));
    //row.append(cellMail);

    if (booking.hasAcceptReject && userIsAdmin) {
        var cellAccept = Html.td({className : "collaborationCellNarrow"});

        if (booking.acceptRejectStatus !== true) { // Hides the accept button if already accepted.
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
        }

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

            if (booking.acceptRejectStatus !== true) { // Hides the accept button if already accepted.
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
            }

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
    if (booking.isAllowMultiple) {
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
                        refreshStartAllStopAllButtons();
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
                    refreshStartAllStopAllButtons();
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
 * -Function that will be called when the user presses the "Connect" button of a booking.
 * -If the booking's plugin has defined a "checkConnect" function, it will be called to verify (locally)
 * that the booking can be connected. If the booking cannot connect, nothing happens (other than what
 * the "checkConnect" function wants to do in that case, like popping up an alert).
 * -If the booking's plugin has set "requiresServerCallForConnect" to true, the server is notified
 * of the booking connect. The server can then take appropiate actions, or change the booking object.
 * -The "connectBookingLocal" function will be called in any case (this function will verify if there should be a local action).
 * @param {object} booking The booking object corresponding to the "connect" button that was pressed.
 */
var connectBooking = function(booking, conferenceId) {

    if (!pluginHasFunction(booking.type, "checkConnect") || codes[booking.type].checkConnect(booking)) {

        if (booking.requiresServerCallForConnect) {
            var killProgress = IndicoUI.Dialogs.Util.progress("Connecting...");
            indicoRequest(
                'collaboration.connectCSBooking',
                {
                    conference: conferenceId,
                    bookingId: booking.id
                },
                function(result,error) {
                    if (!error) {
                        if (result.error){
                            killProgress();
                            codes[booking.type].errorHandler('connect', result, booking);
                        }
                        else {
                            connectBookingLocal(result);
                            killProgress();
                            new AlertPopup($T("Success"), $T("The room ") + booking.linkVideoRoomLocation  + $T(" has been conected to the Vidyo room.") ).open();
                            refreshBooking(result);
                        }
                    } else {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
            );
        } else {
            connectBookingLocal(booking);
        }
    }
};

/**
 * Function called to execute the local action when connecting a booking.
 * It will verify that the booking's plugin has an actual client-side action configured,
 * that the booking is authorized to connect.
 * Then the "cinnect" Javascript function of the booking will be called, passing the booking object and its corresponding iframe
 * in case it is needed for something (loading an URL to send a message / download Koala / etc ).
 */
var connectBookingLocal = function(booking) {
    if (booking.requiresClientCallForConnect && booking.permissionToConnect) {
        codes[booking.type].connect(booking, frames["iframeTarget" + booking.id]);
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
                    codes[booking.type].errorHandler('checkStatus', result, booking);
                } else {
                    refreshBooking(result);
                    if (pluginHasFunction(booking.type, 'postCheckStatus')) {
                        codes[booking.type].postCheckStatus(result);
                    }
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


    var popup = new ConfirmPopup(title, null, function(confirmed) {
        if(!confirmed) {
            return;
        }
        var killProgress = IndicoUI.Dialogs.Util.progress("Rejecting booking...");
        var reason = this.textarea.get();

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
    }, 'OK', 'Cancel Rejection');

    popup.draw = function() {
        var self = this;
        var span1 = Html.span('', "Please write the reason of your rejection (short):");
        this.textarea = Html.textarea({style:{marginTop: '5px', marginBottom: '5px'}, id: "rejectionTextarea", rows: 3, cols: 30});
        var span2 = Html.span('', "The reason will be displayed to the user.");

        this.content = Widget.block([span1, Html.br(), this.textarea, Html.br(), span2]);
        return this.ConfirmPopup.prototype.draw.call(this);
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
var refreshBookingM = function(booking, doHighlight) {
    doHighlight = any(doHighlight, true);
    var index = getBookingIndexById(booking.id);
    hideAllInfoRows(false);
    bookings.removeAt(index);
    bookings.insert(booking, index+"");
    showAllInfoRows(false);
    if (doHighlight) {
        hightlightBookingM(booking);
    }
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
    var newCell = Html.td({id: "infoCell" + booking.id, colspan: 16, colSpan: 16, className : "collaborationInfoCell"});
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
        var infoHTML = codes[booking.type].showInfo(booking);
        if (isString(infoHTML)) {
            existingInfoCell.dom.innerHTML = infoHTML;
        } else if(infoHTML.XElement) {
            existingInfoCell.set(infoHTML);
        }
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
 * Mouseover help popup for the 'Keep booking synchronized with event' advanced option, in case it is disabled.
 */

var sanitizationError = function(invalidFields) {
    each(invalidFields, function(fieldName) {
        var fields = $N(fieldName);
        each(fields, function(field){
            IndicoUtil.markInvalidField(field, $T("Tags in the <tag> form are not allowed. Please remove any '<' and '>' characters."));
        });
    });
}

/**
 * -A modal dialog will emerge to request the booking parameters to the user.
 * -The dialog will change depending on the plugin that has been selected / type of the booking being edited.
 * -The necessary HTML for each plugin is taken from the 'forms' dictionary.
 * -The booking parameters input by the user are retrieved with the "IndicoUtil.getFormValues" function.
 *  -If modifying a booking, the already existing parameters will be taken from the booking object, and they will appear in the form
 *  thanks to the "IndicoUtil.setFormValues" function.
 * -If the plugin has defined a "checkParams" function, this function is called before actually sending the booking to the server.
 *  If the function finds any errors, another modal dialog displays them and the booking cannot be added to the server.
 * -If the booking is actually sent to the server, 2 things can occur:
 *    +there have been no problems, so the booking is added to the 'bookings' watchlist, so the table is updated, and an iframe is created.
 *    +there have been problems, an exception message will appear.
 *
 * @param {string} popupType A string whose value should be 'create' or 'edit'
 * @param {string} bookingType The type of the booking being created / edited.
 * @param {object} booking If 'create' mode, leave to null. If 'edit' mode, the booking object
 * @param {string} conferenceId the conferenceId of the current event
 */
type ("BookingPopup", ["ExclusivePopupWithButtons"],
    {
        switchToBasicTab: function() {
            if (this.tabControl.getSelectedTab() === 'Advanced') {
                this.tabControl.setSelectedTab('Basic');
            }
        },

        _onOpen: function() {
            this.ExclusivePopup.prototype._onOpen.call(this);
            $('#dateSyncHelpImg').qtip({
                content :   $T("This option ensures that if a manager changes the event's dates," +
                               "this booking's dates change accordingly.")});
        },

        draw: function() {
            var self = this;

            // We get the form HTML
            this.basicTabForm = Html.div();
            this.basicTabForm.dom.innerHTML = forms[self.bookingType][0];

            this.advancedTabForm = Html.div();
            this.advancedTabForm.dom.innerHTML = forms[self.bookingType][1];

            // We scan the input nodes inside the dialog
            this.components = IndicoUtil.findFormFields(this.basicTabForm, this.advancedTabForm);

            // We initialize the parameter manager in order to make checks on the fields
            this.__buildParameterManager();

            var width = 600;
            if (pluginHasFunction(self.bookingType, "getPopupWidth")) {
                var width = codes[self.bookingType].getPopupWidth();
                width = width > 400 ? width : 400;
            }

            this.tabControl = new JTabWidget([[$T("Basic"), this.basicTabForm], [$T("Advanced"), this.advancedTabForm]], width);

            return this.ExclusivePopupWithButtons.prototype.draw.call(this, this.tabControl.draw());
        },

        _getButtons: function() {
            var self = this;
            return [
                [$T('Save'), function() {
                    self.__save();
                }],
                [$T('Cancel'), function() {
                    self.close();
                }]
            ];
        },

        afterDraw: function() {

            // If we are modifying a booking, we put the booking's values the dialog's input fields
            if (this.popupType === 'edit') {
                IndicoUtil.setFormValues(this.components, this.booking.bookingParams);
            }

            if (this.popupType === 'edit' && !this.booking.canBeNotifiedOfEventDateChanges) {
                if (exists($E('dateSyncCheckBox'))) {
                    $E('dateSyncCheckBox').dom.disabled = true;
                    $E('dateSyncCheckBox').dom.className = 'disabled';
                }
            }
            this.tabControl.heightToTallestTab();
            this.postDraw();

            // We put calendar widgets on the date fields
            this.__drawCalendarWidgets();
        },

        /**
         * Adds a HTML node or an ErrorAware widget to the parameter manager
         */
        addComponent: function(component) {
            this.components.push(component);
            this.parameterManager.add(component);
        },

        __save: function(){
            var self = this;

            IndicoUtil.getFormValues(this.components, this.values);

            // We check if there are errors
            var checkOK = true;
            if (this.needsCheck) {
                checkOK = this.parameterManager.check();
            }

            // If there are no errors, the booking is sent to the server
            if (checkOK) {
                var onSaveResult = true;
                if (pluginHasFunction(self.bookingType, "onSave")) {
                    onSaveResult = codes[this.bookingType].onSave(this.values);
                }

                if (onSaveResult) {
                    var killProgress = IndicoUI.Dialogs.Util.progress($T("Saving your booking..."));

                    if (this.popupType === 'create') {
                        indicoRequest(
                            'collaboration.createCSBooking',
                            {
                                conference: this.conferenceId,
                                type: this.bookingType,
                                bookingParams: this.values
                            },
                            function(result,error) {
                                if (!error) {
                                    // If the server found no problems, a booking object is returned in the result.
                                    // We add it to the watchlist and create an iframe.
                                    if (result.error) {
                                        killProgress();
                                        self.switchToBasicTab();
                                        if (result._type === 'CSSanitizationError') {
                                            sanitizationError(result.invalidFields);
                                        } else {
                                            codes[self.bookingType].errorHandler('create', result);
                                        }
                                    } else {
                                        hideAllInfoRows(false);
                                        showInfo[result.id] = true; // we initialize the show info boolean for this booking
                                        bookings.append(result);
                                        showAllInfoRows(false);
                                        addIFrame(result);
                                        refreshStartAllStopAllButtons();
                                        refreshTableHead();
                                        if (pluginHasFunction(self.bookingType, 'postCreate')) {
                                            codes[self.bookingType].postCreate(result);
                                        }
                                        killProgress();
                                        hightlightBookingM(result);
                                        self.close();

                                    }
                                } else {
                                    killProgress();
                                    IndicoUtil.errorReport(error);
                                }
                            }
                        );

                    } else if (this.popupType === 'edit') {
                        indicoRequest(
                            'collaboration.editCSBooking',
                            {
                                conference: self.conferenceId,
                                bookingId: self.booking.id,
                                bookingParams: self.values
                            },
                            function(result,error) {
                                if (!error) {
                                    if (result.error) {
                                        killProgress();
                                        self.switchToBasicTab();
                                        if (result._type === 'CSSanitizationError') {
                                            sanitizationError(result.invalidFields);
                                        } else {
                                            codes[self.bookingType].errorHandler('edit', result, self.booking);
                                        }
                                    } else {
                                        if (pluginHasFunction(self.bookingType, 'postEdit')) {
                                            codes[self.bookingType].postEdit(result);
                                        }
                                        showInfo[result.id] = true;
                                        refreshBooking(result);
                                        killProgress();
                                        self.close();
                                    }
                                } else {
                                    killProgress();
                                    IndicoUtil.errorReport(error);
                                }
                            }
                        );
                    }
                }
            } else { // Parameter manager detected errors
                this.switchToBasicTab();
            }
        },

        __buildParameterManager: function() {
            this.needsCheck = pluginHasFunction(this.bookingType, "checkParams");

            if (this.needsCheck) {
                this.parameterManager = new CSParameterManager(this.bookingType, this.values);
                this.parameterManager.add(this.components);
            } else {
                this.parameterManager = null;
            }

        },

        __drawCalendarWidgets: function() {

            if (pluginHasFunction(this.bookingType, "getDateFields")) {
                var fieldList = codes[this.bookingType].getDateFields();
                var fieldDict = {};
                each(fieldList, function(name){
                    fieldDict[name] = true;
                });
                each(this.components, function(node){
                    if (node.name in fieldDict) {
                        IndicoUI.Widgets.Generic.input2dateField($E(node), true, null)
                    }
                });
            }
        }
    },

    /**
     * Constructor
     */
    function(popupType, pluginType, booking, conferenceId) {
        this.popupType = popupType;
        this.bookingType = pluginType;
        if (popupType === 'create') {
            var title = pluginType + " booking creation";
        } else if (popupType === 'edit') {
            this.booking = booking;
            var title = this.bookingType + ' booking modification';
        }
        this.conferenceId = conferenceId;
        this.ExclusivePopupWithButtons(title);

        // We initialize the dictionary where the values sent to the server
        // will be sent on save
        this.values = {};

        this.extraComponents = [];
    }
);

var checkPermissions = function(pluginName, action) {
    if(!hasCreatePermissions[pluginName]){
        var psupport = videoServiceSupport[pluginName]?videoServiceSupport[pluginName]:pluginName + " support.";
        new WarningPopup($T("User has not permissions"),
                $T("You do not have enough permissions to " + action + " " + pluginName + " bookings. " +
                 "If you think that you should have permissions please contact " + psupport) ).open();
        return false;
        }
    return true;
};

/**
 * Function that will be called when the user presses the "Create" button.
 * Will use the 'BookingPopup' class.
 * @param {string} pluginName a string with the type of booking being created ('EVO', 'CERNMCU', ...)
 * @param {string} conferenceId the conferenceId of the current event
 */
var createBooking = function(pluginName, conferenceId) {

    if (!checkPermissions(pluginName, $T("create"))) {
        return false;
    }

    var popup = new BookingPopup('create', pluginName, null, conferenceId);
    popup.open();

    if (pluginHasFunction(pluginName, "onCreate")) {
        codes[pluginName].onCreate(popup);
    }
    popup.afterDraw();

    return true;
}

/**
 * Function that will be called when the user presses the "Edit" button of a booking.
 * Will use the 'BookingPopup' class. Checks the plugin to see whether or not it has a
 * deferred object, that is whether it should postpone the display of the popup until
 * all AJAX requests have been completed.
 * @param {object} booking The booking object corresponding to the "edit" button that was pressed.
 * @param {string} conferenceId the conferenceId of the current event
 */
var editBooking = function(booking, conferenceId) {

    if (!checkPermissions(booking.type, $T("edit"))) {
        return false;
    }

    var popup = new BookingPopup('edit', booking.type, booking, conferenceId);
    popup.open();

    if (pluginHasFunction(booking.type, "onEdit")) {
        codes[booking.type].onEdit(booking, popup);
    }
    popup.afterDraw();
}

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

    if (!checkPermissions(booking.type, $T("delete"))) {
        return false;
    }

    var confirmHandler = function(confirm) { if (confirm) {

        var killProgress = IndicoUI.Dialogs.Util.progress($T("Removing your booking..."));

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
                        codes[booking.type].errorHandler('remove', result, booking);
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
    }};

    IndicoUI.Dialogs.Util.confirm($T("Remove booking"),
            Html.div({style:{paddingTop:pixels(10), paddingBottom:pixels(10), width:pixels(400)}}, $T("Are you sure you want to remove that ") + booking.type + $T(" booking?"),Html.br(), Html.span({width:'100px'},$T("Please be aware that by deleting this ") + booking.type + $T(" booking, all bookings which are cloned from it will also be deleted as a result."))),
            confirmHandler);
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
    var length = bookings.length.get();
    var startedTypes = {};
    var warningsGiven = {};

    for (var i=0; i < length; i++) {
        var booking = bookings.item(i);

        if (startedTypes[booking.type]) {
            if (!(warningsGiven[booking.type])) {
                var popup = new AlertPopup("Booking start", Html.span({},"Multiple " + booking.type + " bookings cannot start at the same time,",
                        Html.br(),
                        "so we just started the first one."));
                popup.open();
                warningsGiven[booking.type] = true;
            }
        } else {
            setTimeout("start(bookings.item(" + i + "))", i*1000);
        }

        if (!booking.hasStartStopAll) {
            startedTypes[booking.type] = true;
        }

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
  //Check if there are buttons to withdraw, modify or send. If not, it means it
    // is not a "request" collaboration plugin.
    if (exists($E('withdraw'+name+'Top'))) {
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
    }
};

var sendRequest = function(pluginName, conferenceId) {

    // We retrieve the values from the form
    var formNodes = IndicoUtil.findFormFields($E(pluginName + 'Form'))
    var values = IndicoUtil.getFormValues(formNodes);

    var needsCheck = pluginHasFunction (pluginName, "checkParams");
    var parameterManager;
    if (needsCheck) {
        parameterManager = new CSParameterManager(pluginName, values);
        parameterManager.add(formNodes);
    }

    // We check if there are errors
    var checkOK = true;
    if (needsCheck) {
        checkOK = parameterManager.check();
    }

    // If there are no errors, the booking is sent to the server
    if (checkOK) {
        var killProgress = IndicoUI.Dialogs.Util.progress($T("Sending your request..."));
        var commonHandler = function(result,error) {
            if (!error) {
                if (result.error) {
                    killProgress();
                    if (result._type === 'CSSanitizationError') {
                        sanitizationError(result.invalidFields);
                    } else {
                        if (exists(singleBookings[pluginName])) {
                            codes[pluginName].errorHandler('edit', result, singleBookings[pluginName]);
                        } else {
                            codes[pluginName].errorHandler('create', result);
                        }
                    }
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
        CSErrorPopup($T("Errors detected"), allErrors, $T("The corresponding fields have been marked in red."));
    }
};

var withdrawRequest = function(pluginName, conferenceId) {

    if (exists(singleBookings[pluginName])) {
        var self = this;
        var title = $T("Withdraw request");

        var popup = new ConfirmPopup(title, $T('Are you sure you want to withdraw the request?'), function(confirmed) {
            if(!confirmed) {
                return;
            }
            var killProgress = IndicoUI.Dialogs.Util.progress($T("Withdrawing your request..."));

            indicoRequest(
                'collaboration.removeCSBooking',
                {
                    conference: conferenceId,
                    bookingId: singleBookings[pluginName].id
                },
                function(result,error) {
                    killProgress();
                    if (!error) {
                        if (result.error) {
                            if (result._type === 'CSSanitizationError') {
                                sanitizationError(result.invalidFields);
                            } else {
                                codes[pluginName].errorHandler('remove', result, singleBookings[pluginName]);
                            }
                        } else {
                            // If the server found no problems, we remove the booking from the watchlist and remove the corresponding iframe.
                            removeIFrame(singleBookings[pluginName]);
                            singleBookings[pluginName] = null;
                            refreshPlugin(pluginName);
                            if (pluginHasFunction(pluginName, 'clearForm')) {
                                codes[pluginName]['clearForm']()
                            }
                            if (pluginHasFunction(pluginName, 'postDelete')) {
                                codes[pluginName].postDelete(result);
                            }
                        }
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
            );
        }, 'Withdraw', 'Cancel');
        popup.open();
    }
};

var buildShowHideButton = function(pluginName) {
    var showHideButton = IndicoUI.Buttons.customTextSwitchButton(
        true,
        $T("Show"),
        $T("Hide"),
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

/*
 * editSpeakerEmail is used to popup a window when the event manager wants
 * to edit the email of the speaker who needs to sign the Electronical Agreement
 */
type("EditSpeakerEmail", ["ExclusivePopupWithButtons"],{
        _getButtons: function() {
            var self = this;
            return [
                [$T('Save'), function() {
                    var method;
                    if (self.confType == 'simple_event') {
                        method = 'collaboration.setEmailChair';
                    }
                    else {
                        method = 'collaboration.setEmailSpeaker';
                    }

                    var newEmail = $('#emailField').val();
                    if (Util.Validation.isEmailAddress(newEmail) || newEmail == '') {
                        indicoRequest(
                            method,
                            {
                                conference: self.confId,
                                contribution: self.contId,
                                spkId: self.spkId,
                                value: newEmail
                            },
                            function(result, error){
                                //killProgress();
                                if (error) {
                                    IndicoUtil.errorReport(error);
                                } else {
                                    window.location.reload();
                                }
                            }
                        );
                        self.close();
                    }
                    else {
                        //Popup saying that email format is unvalid
                        IndicoUI.Dialogs.Util.alert($T("Input Error"), $T("Invalid Email Address Format"));
                    }
                }],
                [$T('Cancel'), function() {
                    self.close();
                }]
            ];
        },

        _drawWidget: function(){
            var self = this;
            var div = Html.div("", $T("Email Address of "+self.fullName));

            var text = Html.input('text', {style:{width:'100%'}}, value=self.email);
            text.setAttribute('id', 'emailField');
            return Html.div({}, div, text);
        },

        draw: function(){
            return this.ExclusivePopupWithButtons.prototype.draw.call(this, this._drawWidget());
        }
    },
    function(confType, fullName, spkId, email, confId, contId){
        var self = this;

        self.confType = confType;
        self.fullName = fullName;
        self.spkId = spkId;
        self.email = email;
        self.confId = confId;
        self.contId = contId;

        this.ExclusivePopupWithButtons($T("Edit Email Address"));
    }
);

type("UploadElectronicAgreementPopup", ["ExclusivePopupWithButtons"],{

        _getButtons: function(){
            var self = this;

            return [
                [$T('Upload'), function() {
                    if (self.pm.check()){
                        self.killProgress = IndicoUI.Dialogs.Util.progress($T('Uploading...'));
                        $(self.form.dom).submit();
                    }
                }],
                [$T('Cancel'), function() {
                    self.close();
                }]
            ];
        },

        _drawWidget: function(){
            var self = this;

            var info = Html.div({style: {textAlign: 'left', fontStyle: 'italic', color: '#881122', marginTop: '10px'}},
                    $T('Please upload the Paper Agreement here.'));

            this.file = Html.input('file', {id:'fileUpload', name: 'file', file:'*.pdf'});
            self.pm.add(this.file, 'text', false);

            this.frameId = Html.generateId();
            this.form = Html.form(
                    {
                        method: 'post',
                        id: "uploadForm",
                        action: self.uploadAction
                    },
                    info,
                    this.file,
                    Html.input('hidden', {name:'spkUniqueId'}, self.spkUniqueId));

            $(this.form.dom).ajaxForm({
                dataType: 'json',
                iframe: true,
                /*
                complete: function() {
                    self.killProgress();
                },
                */
                success: function(resp) {
                    if (resp.status == 'ERROR') {
                        self.killProgress();
                        IndicoUtil.errorReport(resp.info);
                    }
                    else {
                        location.reload();
                    }
                }
            });

            return Html.div({}, this.form);
        },

        draw: function(){
            return this.ExclusivePopupWithButtons.prototype.draw.call(this, this._drawWidget());
        },

    },
    function(confId, spkUniqueId, uploadAction) {
       var self = this;
       self.confId = confId;
       self.spkUniqueId = spkUniqueId;
       self.uploadAction = uploadAction;
       self.pm = new IndicoUtil.parameterManager();
       this.ExclusivePopupWithButtons($T("Upload the Paper Agreement"));
    }
);

type("SpeakersEmailPopup", ["BasicEmailPopup"],{

        _getButtons: function() {
            var self = this;
            return [
                [$T('Send'), function() {
                    var killProgress = IndicoUI.Dialogs.Util.progress($T("Sending..."));
                    indicoRequest(
                        "collaboration.sendElectronicAgreement",
                        {
                            conference: self.confId,
                            uniqueIdList: self.uniqueIdList,
                            from: $E("fromEmailAddress"),
                            content: self.rtWidget.get(),
                        },
                        function(result, error){
                            killProgress();
                            if (error) {
                                IndicoUtil.errorReport(error);
                                self.close();
                            } else {
                                if(result == "url_error"){
                                    IndicoUI.Dialogs.Util.alert($T("Email Format Error"), $T("The {url} field is missing in your email. This is a mandatory field thus, this email cannot be sent."));
                                }else if(result == "talkTitle_error"){
                                    IndicoUI.Dialogs.Util.alert($T("Email Format Error"), $T("The {talkTitle} field is missing in your email. This is a mandatory field thus, this email cannot be sent."));
                                }else{
                                    self.close();
                                    var divs = $('<div/>');
                                    $('<div/>').html($T("Email sent successfully!")).appendTo(divs);
                                    $('<div/>').html($T("The email has been sent to:")).appendTo(divs);
                                    $('<div/>').text(result).appendTo(divs);
                                    informationPopup(divs);
                                }
                            }
                        }
                    );
                }],
                [$T('Cancel'), function() {
                    self.close();
                }]
            ];
        },

    _drawFromAddress: function(){
        var self = this;
        // drop down list with senders
        optionList = Array();
        for(var i in self.fromList){
            optionList.push(Html.option({value: self.fromList[i]}, "Indico Mailer <"+self.fromList[i]+">"));
        }
        var selectFromAddress = Html.select({id:"fromEmailAddress"}, optionList);

        var fromField = Html.tr({},
                Html.td({width:"15%"}, Html.span({}, $T("From:"))),
                Html.td({width:"85%"}, selectFromAddress)
        );

        return Html.table({width:"95%", style:{margin:"20px"}}, fromField);
    },

    _drawToAddress: function(){
        return null;
    },

    draw: function(){
        return this.ExclusivePopupWithButtons.prototype.draw.call(this, this._drawWidget());
    },

    _drawSubject: function(){
        return null;
    }

},
    function(confTitle, confId, uniqueIdList, fromList, subject, defaultText, legends){
        var self = this;
        self.uniqueIdList = uniqueIdList;
        self.fromList = fromList;
        self.sendFunction=function(){
            indicoRequest(
                "collaboration.sendElectronicAgreement",
                {
                    conference : self.confId,
                    uniqueIdList: self.uniqueIdList,
                    from: $E("fromEmailAddress"),
                    content: self.rtWidget.get()
                },
                function(result, error){
                    if (error) {
                        IndicoUtil.errorReport(error);
                        self.close();
                    } else {
                        if(result == "url_error"){
                            IndicoUI.Dialogs.Util.alert($T("Email Format Error"), $T("The {url} field is missing in your email. This is a mandatory field thus, this email cannot be sent."));
                        }else if(result == "talkTitle_error"){
                            IndicoUI.Dialogs.Util.alert($T("Email Format Error"), $T("The {talkTitle} field is missing in your email. This is a mandatory field thus, this email cannot be sent."));
                        }else{
                            self.close();
                            span1 = Html.div({}, $T("Email sent successfully !"));
                            span2 = Html.div({}, $T("The Electronic Agreement email has been sent to:"));
                            span3 = Html.div({}, $T(""+result));

                            informationPopup(Html.div({}, span1, span2, span3), null);
                        }
                    }
                }
            );
            //self.close();
        };
        title = $T("Send Email to Speakers");
        this.BasicEmailPopup(title, confTitle, confId, subject, defaultText, legends);
    }
);

//Information popup, will print an information and redirect to the redirectionLink when click on OK
var informationPopup = function(information, redirectionLink) {
    (new AlertPopup($T("Confirmation"), information, function() {
        window.location = redirectionLink || window.location.href;
    })).open();
};

var makeMeModerator = function(videoLink, confId, bookingId, successFunction) {
    $E(videoLink).set(progressIndicator(true,true));
    jsonRpc(Indico.Urls.JsonRpcService, "collaboration.makeMeModerator",
            { confId: confId,
              bookingId: str(bookingId) },
            function(result, error){
                  if (exists(error)) {
                      IndicoUtil.errorReport(error);
                  } else if (exists(result.error) && result.error) {
                      $('.ui-tooltip').qtip('hide');
                      new WarningPopup($T("Cannot become moderator"), result.userMessage).open();
                  } else {
                      successFunction(videoLink, result);
                  }
    });
};

var successMakeModerator = function(videoLink, result){
    $(videoLink).parent().parent().html(result.bookingParams.owner["name"]);
    var bookingPopup = $(videoServiceInfo[result.id]);
    bookingPopup.find("#"+$T("Moderator")).html(Html.div({},result.bookingParams.owner["name"]).dom);
    videoServiceInfo[result.id] = $(bookingPopup).wrap('<div/>').parent().html();
};

var successMakeEventModerator = function(videoLink, result){
    $(videoLink).parent().parent().html(Html.div({}, result.bookingParams.owner["name"]).dom);
};

var drawBookingPopup = function (videoInformation, confId, bookingId, displayModeratorLink) {
    var divWrapper = Html.div({className:"videoServiceInlinePopup"});
    for(section in videoInformation){
        var leftCol = Html.div({className:"leftCol"}, videoInformation[section]["title"]);
        var rightCol = Html.div({className:"rightCol", id: videoInformation[section]["title"]});
        for(line in videoInformation[section]["lines"]){
            rightCol.append(Html.div({}, videoInformation[section]["lines"][line]));
        }
        for(line in videoInformation[section]["linkLines"]){
            rightCol.append(Html.div({}, Html.input("text",{onClick: '$(this).select();'}, videoInformation[section]["linkLines"][line][1])));
        }
        if(videoInformation[section]["title"] == $T("Moderator") && displayModeratorLink){
            var link = Html.a({href:'#', onClick:'makeMeModerator(this,'+confId+','+bookingId+', successMakeModerator)'},$T("Make me moderator"));
            rightCol.append(Html.div({}, " ", link));
        }
        divWrapper.append(Html.div({className: "lineWrapper"}, leftCol, rightCol));
    }
    return $(divWrapper.dom).wrap("<div/>").parent().html();
};

var acceptElectronicAgreement = function(confId, authKey, redirectionLink) {
    var killProgress = IndicoUI.Dialogs.Util.progress($T("Accepting Electronic Agreement..."));
    indicoRequest(
            'collaboration.acceptElectronicAgreement',
            {
                confId: confId,
                authKey: authKey
            },
            function(result,error) {
                if (!error) {
                    killProgress();
                    informationPopup($T("The acceptance of the agreement has been successfully recorded."), redirectionLink);
                } else {
                    killProgress();
                    IndicoUtil.errorReport(error);
                }
            }
        );
};

var rejectElectronicAgreement = function(confId, authKey, redirectionLink) {
    var popup = new ExclusivePopupWithButtons($T('Reason for rejection'), positive, false, false, true);

    popup._getButtons = function() {
        var self = this;
        return [
            [$T('OK'), function() {
                var reason = self.textarea.get() || $T('No reason specified');

                var killProgress = IndicoUI.Dialogs.Util.progress($T("Rejecting Electronic Agreement..."));
                indicoRequest(
                    'collaboration.rejectElectronicAgreement',
                    {
                        confId: confId,
                        reason: reason,
                        authKey: authKey
                    },
                    function(result,error) {
                        killProgress();
                        if (!error) {
                            self.close();
                            informationPopup($T("The rejection of the agreement has been successfully recorded."), redirectionLink);
                        } else {
                            IndicoUtil.errorReport(error);
                        }
                    }
                );
            }],
            [$T('Cancel Rejection'), function() {
                self.close();
            }]
        ];
    }

    popup.draw = function(){
        var span1 = Html.span('', $T("Please write the reason of your rejection (short):"));
        this.textarea = Html.textarea({style:{marginTop: '5px', marginBottom: '5px'}, id: "rejectionTextarea", rows: 3, cols: 30});
        var span2 = Html.span('', $T("The reason will be displayed to the administrators."));

        return this.ExclusivePopupWithButtons.prototype.draw.call(this, Widget.block([span1, Html.br(), this.textarea, Html.br(), span2, Html.br()]));
    };

    popup.open();
};
