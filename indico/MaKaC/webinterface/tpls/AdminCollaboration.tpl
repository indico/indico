<div class="container">
<div class="categoryTitle">
    ${ _("Video Services Overview")}
</div>
<div class="CADiv">
    <div class="CATopBanner">
        <ul class="CAIndexList">
        <label>Select Video Service Index:</label>&nbsp;
        <% lastIndex = len(Indexes) - 1 %>
        % for i, index in enumerate(Indexes):
            <% indexName = index.getName() %>
            <li>
                % if i == lastIndex:
                    <% additionalStyle = 'style="border-right\x3a 0px;"' %>
                % else:
                    <% additionalStyle = '' %>
                % endif
                <a id="index_${indexName}" onclick="indexSelectedObs('${indexName}', false)" class="CAIndexUnselected" ${additionalStyle} >
                    ${ indexName[0].upper() + indexName[1:] }
                </a>
            </li>
        % endfor
        </ul>
    </div>

    <div class="CALeftPane">
        <div class="CASortByDiv">
            <span class="CAFormattingSpan">${ _("View by:")} </span>
            <a class="CAViewByLink" id="conferenceTitleViewBy" onclick="viewByObs('conferenceTitle')">${ _("Event Title")}</a>
            <a class="CAViewByLink" id="conferenceStartDateViewBy" onclick="viewByObs('conferenceStartDate')">${ _("Event Start Date")}</a>
            <a class="CAViewByLink" id="creationDateViewBy" onclick="viewByObs('creationDate')">${ _("Creation Date")}</a>
            <a class="CAViewByLink" id="modificationDateViewBy" onclick="viewByObs('modificationDate')">${ _("Modification Date")}</a>
            <a class="CAViewByLink" id="startDateViewBy" onclick="viewByObs('startDate')">${ _("Booking Start Date")}</a>
        </div>
        <div class="CASortByDiv">
            <span class="CAFormattingSpan">${ _("Order:")} </span>
            <a class="CAViewByLink" id="ascendingViewBy" onclick="orderByObs('ascending')">${ _("Ascending")}</a>
            <a class="CAViewByLink" id="descendingViewBy" onclick="orderByObs('descending')" >${ _("Descending")}</a>
        </div>
        <div id="dateFilter">
            <div class="CAPaneHeader">
                Date Range
            </div>
            <div>
                % if InitialFromDays:
                    <% checked1 = '' %>
                    <% checked2 = 'checked' %>
                % else:
                    <% checked1 = 'checked' %>
                    <% checked2 = '' %>
                % endif
                <input type="radio" name="dateFilterType" id="sinceToDateRadio" onclick="updateDateFilterType()" class="CARadio" ${ checked1 } />
                <span class="CAFormattingSpan">${ _("Since")}</span><span id="sinceDateContainer"></span>
                ${ _("to")} <span id="toDateContainer"></span>
                <span class="CAMinMaxKeySuggestion">${ _("Please input dates") }</span>
            </div>
            <div style="padding-top: 5px">
                <input type="radio" name="dateFilterType" id="fromToDaysRadio" onclick="updateDateFilterType()" class="CARadio" ${ checked2 } />
                <span class="CAFormattingSpan">${ _("From")}</span> <input type="text" size="3" id="fromDays" name="fromDays" onkeypress="updateFilterButton()" value="${ InitialFromDays }"/>
                ${ _("days ago to")} <input type="text" size="3" id="toDays" name="toDays" onkeypress="updateFilterButton()" value="${ InitialToDays }"/>
                ${ _("days in the future") }
                <span class="CAMinMaxKeySuggestion">${ _("Please input integers") }</span>
            </div>
        </div>
        <div id="titleFilter" style="padding-top: 5px">
            <div class="CAPaneHeader">
                Title Filter
            </div>
            <div>
                <span class="CAFormattingSpan">${ _("From")}</span> <input type="text" size="13" id="fromTitle" name="fromTitle" onkeypress="updateFilterButton()" value="${ InitialFromTitle }"/>
                ${ _("to")} <input type="text" size="13" id="toTitle" name="toTitle" onkeypress="updateFilterButton()" value="${ InitialToTitle }"/>
                <span class="CAMinMaxKeySuggestion">${ _("Please input a conference title or the beginning of it") }</span>
            </div>
        </div>
    </div>

    <div class="CARightPane">
        <div id="CAShowOnlyPendingDiv">
            <span class="CAFormattingSpan">${ _("Show only pending:")}</span>
            % if InitialOnlyPending:
                <% checked = 'checked' %>
            % else:
                 <% checked = '' %>
            % endif
            <input type="checkbox" id="pendingCB" name="pendingCB" onchange="updateFilterButton()" ${checked }/>
        </div>
        <div>
          <span class="CAFormattingSpan">${ _("Restrict to category id:")}</span>
          <input type="text" size="5" id="categoryId" name="categoryId" onkeypress="updateFilterButton()" value="${ InitialCategoryId }"/>
        </div>
        <div>
          <span class="CAFormattingSpan">${ _("Restrict to conference id:")}</span>
         <input type="" name="" value="" type="text" size="5" id="conferenceId" name="conferenceId" onkeyup="confIdObs()" onkeypress="updateFilterButton()" value="${ InitialConferenceId }"/>
        </div>
        <div>
          <span class="CAFormattingSpan">${ _("Results per page:")}</span>
          <input type="text" id="resultsPerPage" name="resultsPerPage" size="5" onkeypress="updateFilterButton()" value="${ InitialResultsPerPage }"/>
        </div>
    </div>

    <div class="CABottomBanner">
        <div class="CAStaticURLDiv">
            <span class="fakeLink" id="CAStaticURLLink">
                ${ _("Static URL for this result")}
            </span>
            <div id="CAStatucURLContentContainer">
                <div id="CAStaticURLContent">
                    <div>${ _("You can use this link for bookmarks:")}</div>
                    <input readonly="readonly" type="text" id="staticURL" name="staticURL" />
                </div>
            </div>
        </div>
        <input type="button" id="filterButton" name="filterButton" value="${ _("Refresh")}" onclick="refresh()"/>
        ${ _("This list can have bookings of the following type(s):")} <span class="pluginNames" id="indexPluginTypes"></span>
    </div>
</div>

<div>
    <div class = "CAResultsDiv">
        <span id="resultsMessage">${ _("(Results will appear here)")}</span>
        <div id="resultsInfo" style="display:none;">
            <div class="CATotalInIndexDiv">
                <span id="totalInIndex"></span><span>&nbsp;${ _("bookings in this index.") }</span>
            </div>
            <div class="CANResultsDiv">
                <span>Query returned&nbsp;</span><span id="nBookings"></span><span>&nbsp;${ _("bookings.") }</span>
            </div>
        </div>
        <table cellpadding="0" cellspacing="0" class="CAResultsTable" id ="results">
        </table>
    </div>
    <div id="pageNumberList">
    </div>
</div>
<script type="text/javascript">

var bookings = ${ jsonEncode (InitialBookings) };
var nBookings = ${ InitialNumberOfBookings }
var totalInIndex = ${ InitialTotalInIndex }
var nPages = ${ InitialNumberOfPages };

var indexNames = ${[index.getName() for index in Indexes]};
var indexInformation = ${ jsonEncode(IndexInformation)};
var viewBy = ['conferenceTitle','conferenceStartDate', 'creationDate','modificationDate','startDate'];

var queryParams = {
    indexName: '',
    showOnlyPending: ${ jsonEncode(InitialOnlyPending) },
    filterByOnlyPending: true,
    conferenceId: '${ InitialConferenceId }',
    categoryId: '${ InitialCategoryId }',
    sinceDate: '${ InitialSinceDate }',
    toDate: '${ InitialToDate }',
    fromDays: '${ InitialFromDays }',
    toDays: '${ InitialToDays }',
    fromTitle: '${ InitialFromTitle }',
    toTitle: '${ InitialToTitle }',
    viewBy: '',
    orderBy: '',
    resultsPerPage: '${ InitialResultsPerPage }',
    page: '${ InitialPage }'
}

var dateParameterManager = new IndicoUtil.parameterManager();
var resultsPerPageParameterManager = new IndicoUtil.parameterManager();

var codes = {
${ ",\n". join(['"' + pluginName + '" \x3a ' + code for pluginName, code in JSCodes.items()]) }
}

var buildIndexTooltips = function() {
    for (var i=0; i<indexNames.length; i++) {
        $E('index_' + indexNames[i]).dom.onmouseover = function(event) {
            IndicoUI.Widgets.Generic.tooltip(this, event, '<div style="padding:5px">' + $T("Plugins in this index:") + '<br \/>' +
                    indexInformation[this.id.substring(6)].plugins.join(", ") +
                    '<\/div>');
        }
    }
}

var alertNoIndexSelected = function() {
    var popup = new AlertPopup($T("No index selected"), Html.span({},$T("Please select an index name")), Html.br(),
            Html.span(indexNames.join(', ')));
    popup.open();
}

var indexSelectedObs = function(selectedIndexName, firstTime) {

    for (var i=0; i<indexNames.length; i++) {
        var name = indexNames[i];
        if(name == selectedIndexName) {
            $E('index_' + name).dom.className = "CAIndexSelected";
        } else {
            $E('index_' + name).dom.className = "CAIndexUnselected";
        }
    }

    $E('indexPluginTypes').set(indexInformation[selectedIndexName].plugins.join(", "));
    queryParams.indexName = selectedIndexName;

    var hasViewByStartDate = indexInformation[selectedIndexName].hasViewByStartDate;
    var hasShowOnlyPending = indexInformation[selectedIndexName].hasShowOnlyPending;

    if (hasViewByStartDate || selectedIndexName == 'RecordingRequest' || selectedIndexName == 'WebcastRequest') {
        IndicoUI.Effect.appear($E('startDateViewBy'));
    } else {
        IndicoUI.Effect.disappear($E('startDateViewBy'));
        if (queryParams.viewBy == 'startDate'){
            queryParams.viewBy = 'modificationDate';
        }
    }

    if (hasShowOnlyPending) {
        IndicoUI.Effect.appear($E('CAShowOnlyPendingDiv'), 'inline');
        queryParams.filterByOnlyPending = true;
    } else {
        IndicoUI.Effect.disappear($E('CAShowOnlyPendingDiv'));
        queryParams.filterByOnlyPending = false;
    }

    if (!firstTime) {
        refresh();
    };
}

var viewByObs = function(viewBySelected, firstTime) {
    for (var i=0; i<viewBy.length; i++) {
        var name = viewBy[i];
        if (viewBySelected == name) {
            $E(name + 'ViewBy').dom.className = "CAViewBySelected";
        } else {
            $E(name + 'ViewBy').dom.className = "CAViewByUnselected";
        }
    }

    if ((endsWith(queryParams.viewBy, 'Date') || firstTime) && viewBySelected == 'conferenceTitle') {
        if (!(firstTime && bookings)) {
            $E('fromTitle').set('');
            $E('toTitle').set('');
        }
        IndicoUI.Effect.disappear($E('dateFilter'));
        IndicoUI.Effect.appear($E('titleFilter'));
        orderByObs('ascending', true); // we put true because we don't want to trigger another request
    }
    if (endsWith(viewBySelected, 'Date') && (queryParams.viewBy == 'conferenceTitle' || firstTime)) {
        if (!(firstTime && bookings)) {
            $E('sinceDate').set('');
            $E('toDate').set('');
            $E('fromDays').set('');
            $E('toDays').set('');
        }
        IndicoUI.Effect.disappear($E('titleFilter'));
        IndicoUI.Effect.appear($E('dateFilter'));
        orderByObs('descending', true); // we put true because we don't want to trigger another request
    }

    queryParams.viewBy = viewBySelected;

    if (!firstTime) {
        refresh();
    };
}

var updateDateFilterType = function() {
    if ($E('sinceToDateRadio').dom.checked) {
        $E('fromDays').dom.disabled = true;
        $E('toDays').dom.disabled = true;
        $E('sinceDate').dom.disabled = false;
        $E('toDate').dom.disabled = false;
    } else {
        $E('sinceDate').dom.disabled = true;
        $E('toDate').dom.disabled = true;
        $E('fromDays').dom.disabled = false;
        $E('toDays').dom.disabled = false;
    }
}

var orderByObs = function(orderBySelected, firstTime) {

    if (orderBySelected == 'ascending') {
        $E('ascendingViewBy').dom.className = "CAViewBySelected";
        $E('descendingViewBy').dom.className = "CAViewByUnselected";
    } else if (orderBySelected == 'descending') {
        $E('ascendingViewBy').dom.className = "CAViewByUnselected";
        $E('descendingViewBy').dom.className = "CAViewBySelected";
    }

    queryParams.orderBy = orderBySelected;

    if (!firstTime) {
        refresh();
    };
}

var confIdObs = function() {
    $E('categoryId').dom.disabled = ($E('conferenceId').get() != '')
}

var updateFilterButton = function() {
    $('#filterButton').attr('value', $T("Apply Filter"));
}

var refresh = function() {
    if (!queryParams.indexName) {
        alertNoIndexSelected();
    } else {
        applyFilter();
        query();
    }
}

var applyFilter = function(){

    queryParams.showOnlyPending = $E('pendingCB').dom.checked;
    queryParams.conferenceId = $E('conferenceId').get();
    queryParams.categoryId = $E('categoryId').get();
    if (endsWith(queryParams.viewBy, 'Date')) {
        queryParams.fromTitle = '';
        queryParams.toTitle = '';
        if ($E('sinceToDateRadio').dom.checked) {
            queryParams.fromDays = '';
            queryParams.toDays = '';
            queryParams.sinceDate = $E('sinceDate').get();
            queryParams.toDate = $E('toDate').get();
        } else {
            queryParams.sinceDate = '';
            queryParams.toDate = '';
            queryParams.fromDays = $E('fromDays').get();
            queryParams.toDays = $E('toDays').get();
        }
    } else {
        queryParams.sinceDate = '';
        queryParams.toDate = '';
        queryParams.fromDays = '';
        queryParams.toDays = '';
        queryParams.fromTitle = $E('fromTitle').get();
        queryParams.toTitle = $E('toTitle').get();
    }
    queryParams.resultsPerPage = $E('resultsPerPage').get();
    queryParams.page = 1;
    $E('filterButton').dom.value = $T('Refresh');

}

var query = function() {

    if (endsWith(queryParams.viewBy, 'Date') && !dateParameterManager.check()) {
        return;
    }
    if (!resultsPerPageParameterManager.check()) {
        return;
    }

    var killProgress = IndicoUI.Dialogs.Util.progress($T("Retrieving the data..."));
    updateStaticURL();

    indicoRequest(
        'collaboration.bookingIndexQuery',
        {
            indexName : queryParams.indexName,
            viewBy : queryParams.viewBy,
            orderBy : queryParams.orderBy,
            sinceDate : queryParams.sinceDate,
            toDate : queryParams.toDate,
            fromDays : queryParams.fromDays,
            toDays : queryParams.toDays,
            fromTitle : queryParams.fromTitle,
            toTitle : queryParams.toTitle,
            onlyPending : queryParams.filterByOnlyPending && queryParams.showOnlyPending,
            conferenceId : queryParams.conferenceId,
            categoryId : queryParams.categoryId,
            page: queryParams.page,
            resultsPerPage: queryParams.resultsPerPage
        },
        function(result,error) {
            if (!error) {
                bookings = result.results;
                nBookings = result.nBookings;
                totalInIndex = result.totalInIndex;
                nPages = result.nPages;
                updateList();
                killProgress();
            } else {
                killProgress();
                IndicoUtil.errorReport(error);
            }
        }
    );

}

var updateStaticURL = function() {
    var url = '${ BaseURL }' +
              '?queryOnLoad=true' +
              '&page=' + queryParams.page +
              '&resultsPerPage=' + queryParams.resultsPerPage +
              '&indexName=' + queryParams.indexName +
              '&onlyPending=' + queryParams.showOnlyPending +
              '&conferenceId=' + queryParams.conferenceId +
              '&categoryId=' + queryParams.categoryId +
              '&viewBy=' + queryParams.viewBy +
              '&orderBy=' + queryParams.orderBy;
    if (queryParams.sinceDate) {
        url = url + '&fromDate=' + queryParams.sinceDate + '&toDate=' + queryParams.toDate;
    } else if (queryParams.fromDays) {
        url = url + '&fromDays=' + queryParams.fromDays + '&toDays=' + queryParams.toDays;
    } else if (queryParams.fromTitle) {
        url = url + '&fromTitle=' + queryParams.fromTitle + '&toTitle=' + queryParams.toTitle;
    }

    $('#staticURL').attr('value', url);
    $('#staticURLLink').attr('href', url);
}

/** Static URL qTip event handler **/
$('#CAStaticURLLink').qtip({
    content: {
        text: function() { return $('#CAStatucURLContentContainer').html(); }
    },
    position: {
        my: 'bottom middle',
        at: 'top right'
    },
    hide: {
        event: 'unfocus',
        fixed: true,
        effect: function() {
            $(this).fadeOut(300);
        }
    },
    style: {
        classes: 'ui-tooltip-rounded ui-tooltip-shadow ui-tooltip-light'
    }
}, {
    beforeRender: updateStaticURL()
});

var buildVideoServicesDisplayUrl = function(conference){
    return (conference.type === 'conference' ? Indico.Urls.ConfCollaborationDisplay : Indico.Urls.ConferenceDisplay ) + '?confId=' + conference.id;
};

var confTitleGroupTemplate = function(group, isFirst){
    var conference = group[0];
    var bookings = group[1];

    var result = Html.tbody({},
        Html.tr({}, Html.td({className : 'ACBookingGroupTitle', colspan: 10, colSpan: 10},
            Html.a({className : 'ACConfLink', href : buildVideoServicesDisplayUrl(conference)},
                    Html.span('ACConfTitle', conference.title),
                    Html.span('ACConfId', ' (ID: ' + conference.id + ') '),
                    Html.span('ACConfDates', conference.startDate.date + (conference.startDate.date != conference.endDate.date? ' - ' + conference.endDate.date : ''))
                   ))));
    each(bookings, function(booking){
        result.append(confTitleBookingTemplate(booking));
    });

    return result;
}

var confTitleBookingTemplate = function(booking) {
    var row = Html.tr("ACBookingLine");

    var cell = Html.td('ACBookingFirstCell', Html.span('', booking.type));
    row.append(cell);

    var cell = Html.td('ACBookingCellNoWrap', Html.span(booking.statusClass, booking.statusMessage));
    row.append(cell);

    var cell = Html.td('ACBookingCellNoWrap', $T("Last modification:") + formatDateTimeCS(booking.modificationDate) );
    row.append(cell);

    if (pluginHasFunction(booking.type, 'customText')) {
        var cell = Html.td('ACBookingCell', codes[booking.type].customText(booking, 'conferenceTitle') );
        row.append(cell);
    } else {
        row.append(Html.td());
    }

    var cell = Html.td('ACBookingCellNoWrap', Html.a({href: booking.modificationURL}, 'Change'),
                                              Html.span('horizontalSeparator', '|'),
                                              Html.a({href: buildVideoServicesDisplayUrl(booking.conference)}, $T('Event Display')));
    row.append(cell);

    return row;
}

var dateBookingTemplate = function(booking, viewBy) {
    var row = Html.tr("ACBookingLine");

    var time = null;
    if (viewBy === "creationDate") {
        time = booking.creationDate.time.substring(0,5);
    } else if (viewBy === "modificationDate") {
        time = booking.modificationDate.time.substring(0,5);
    } else if (viewBy === "startDate" || viewBy === "conferenceStartDate") {
        time = (booking.bookingParams.startDate.length === 0)
               ? '' : Util.parseDateTime(booking.bookingParams.startDate,
                       IndicoDateTimeFormats.Default).time.substring(0, 5);
    }

    var cell = Html.td('ACBookingFirstCell ACBookingTime', time);
    row.append(cell);

    var cell = Html.td('ACBookingCellNoWrap', Html.span({}, booking.type));
    row.append(cell);

    var cell = Html.td('ACBookingCellNoWrap', Html.span(booking.statusClass, booking.statusMessage));
    row.append(cell);

    var cell = Html.td('ACBookingCell', Html.span({}, $T("In event: ")), Html.span({}, booking.conference.title));
    row.append(cell);

    if (pluginHasFunction(booking.type, 'customText')) {
        var cell = Html.td('ACBookingCell', codes[booking.type].customText(booking, viewBy) );
        row.append(cell);
    } else {
        row.append(Html.td());
    }

    var cell = Html.td('ACBookingCellNoWrap', Html.a({href: booking.modificationURL}, $T('Change')),
            Html.span('horizontalSeparator', '|'),
            Html.a({href: buildVideoServicesDisplayUrl(booking.conference)}, $T('Event Display')));
    row.append(cell);

    return row;
}

var dateGroupTemplate = function(group, isFirst, viewBy) {
    var date = group[0];
    var bookings = group[1];

    var result = Html.tbody({},
            Html.tr({}, Html.td({className : 'ACBookingGroupTitle', colspan: 10, colSpan: 10},
                Html.span({}, date)
            )));
    each(bookings, function(booking){
        result.append(dateBookingTemplate(booking, viewBy));
    });

    return result;
}

var updateList = function() {
    updateResults();
    updatePageNumberList();
}

var updateResults = function() {

    $E('results').clear();

    if (nBookings < 1) {
        $E('resultsMessage').set($T("No results found"));
        IndicoUI.Effect.appear($E('resultsMessage'));
        IndicoUI.Effect.disappear($E('resultsInfo'));
    } else {
        IndicoUI.Effect.disappear($E('resultsMessage'));
        IndicoUI.Effect.appear($E('resultsInfo'));
        $E('totalInIndex').set(totalInIndex);
        $E('nBookings').set(nBookings);
        for (var i = 0; i < bookings.length; i++) {
            group = bookings[i];
            if (queryParams.viewBy == 'conferenceTitle') {
                $E('results').append(confTitleGroupTemplate(group, i == 0))
            } else {
                $E('results').append(dateGroupTemplate(group, i == 0, queryParams.viewBy))
            }
        }
    }
}

var updatePageNumberList = function() {
    pf.setNumberOfPages(nPages);
    pf.selectPage(queryParams.page);
}

var pageSelectedHandler = function(page) {
    queryParams.page = page;
    query();
}

var pf = new PageFooter('${ InitialNumberOfPages }', '${ InitialPage }', 4, pageSelectedHandler)

IndicoUI.executeOnLoad(function(){

    var sinceDate = IndicoUI.Widgets.Generic.dateField(true, {id:'sinceDate'});
    $E('sinceDateContainer').set(sinceDate);
    sinceDate.set(${ InitialSinceDate });
    sinceDate.observeEvent("keypress", function (e) { updateFilterButton(); });
    var toDate = IndicoUI.Widgets.Generic.dateField(true, {id:'toDate'});
    $E('toDateContainer').set(toDate);
    toDate.set(${ InitialToDate });
    toDate.observeEvent("keypress", function (e) { updateFilterButton(); });

    buildIndexTooltips();
    confIdObs();
    viewByObs('${InitialViewBy }', true);
    updateDateFilterType();
    % if InitialOrderBy:
        orderByObs('${ InitialOrderBy }', true);
    % endif
    % if InitialIndex:
        indexSelectedObs('${ InitialIndex }', true);
    % endif
    updateStaticURL();

    $E('pageNumberList').set(pf.draw());

    dateParameterManager.add(sinceDate, 'datetime', true);
    dateParameterManager.add($E('toDate'), 'datetime', true);

    resultsPerPageParameterManager.add($E('resultsPerPage'), 'int', false, function(value) {
        if (value < 1) {
            return $T("Please input number higher than 0");
        }
    })

    if (bookings) {
        updateResults();
    }
    $('body').delegate('#staticURL', 'click', function(e){
        $(this).select();});
});
</script>
