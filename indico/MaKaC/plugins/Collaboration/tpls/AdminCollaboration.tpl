<div class="container">
<div class="categoryTitle">
    ${ _("Video Services Overview")}
</div>
<div class="CRLDiv CADiv">
    <div class="CATopBanner">
        <ul class="CAIndexList">
        <label>Select Video Service Index:</label>&nbsp;
        % for index in Indexes:
            % if index == None:
            <li class="grey">|</li>
            % else:
            <li>
                <a data-index="${index}">
                    ${index[0].upper() + index[1:]}
                </a>
            </li>
            % endif
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
                <span class="CAFormattingSpan">${ _("Since")}</span><input type="text" id="sinceDate" value="${InitialSinceDate}" />
                ${ _("to")} <input type="text" id="toDate" value="${InitialToDate}" />
                <a href="#" id="today_button">Today</a>
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
</div>
<script type="text/javascript">

//hack for IE
var STATUS_MESSAGE = {};
STATUS_MESSAGE[null] = $T('Pending approval');
STATUS_MESSAGE[true] = $T('Accepted');
STATUS_MESSAGE[false] = $T('Rejected');

var bookings = ${ jsonEncode (InitialBookings) };
var nBookings = ${ InitialNumberOfBookings }
var totalInIndex = ${ InitialTotalInIndex }
var nPages = ${ InitialNumberOfPages };

var indexNames = ${list(index for index in Indexes if index is not None) | n,j};
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
};

var dateParameterManager = new IndicoUtil.parameterManager();
var resultsPerPageParameterManager = new IndicoUtil.parameterManager();

var codes = {
${ ",\n". join(['"' + pluginName + '" \x3a ' + code for pluginName, code in JSCodes.items()]) }
};

var initialize_index_tabs = function() {
        $('ul.CAIndexList a').on('mouseover', function(event) {
            var index = $(this).data('index');
            IndicoUI.Widgets.Generic.tooltip(this, event, '<div style="padding:5px">' + $T("Plugins in this index:") + '<br \/>' +
                    indexInformation[index].plugins.join(", ") +
                    '<\/div>');
        }).click(function(){
            var index = $(this).data('index');
            indexSelectedObs(index, false);
        });
};

var alertNoIndexSelected = function() {
    new AlertPopup($T("No index selected"), $T("Please select an index name")).open();
};

var indexSelectedObs = function(selectedIndexName, firstTime) {
    $('.CAIndexList a').removeClass("CAIndexSelected");
    $(".CAIndexList a[data-index='" + selectedIndexName + "']").addClass("CAIndexSelected");

    $E('indexPluginTypes').set(indexInformation[selectedIndexName].plugins.join(", "));
    queryParams.indexName = selectedIndexName;

    var hasViewByStartDate = indexInformation[selectedIndexName].hasViewByStartDate;
    var hasShowOnlyPending = indexInformation[selectedIndexName].hasShowOnlyPending;

    if (hasViewByStartDate || selectedIndexName == 'RecordingRequest' || selectedIndexName == 'WebcastRequest' || selectedIndexName == 'All Requests') {
        $('#startDateViewBy').fadeIn();
            set_view_by('startDate');
    } else {
        $('#startDateViewBy').fadeOut();
        set_view_by('conferenceStartDate');
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
    }
};

function set_view_by(viewBy) {
    $('.CAViewByLink').removeClass("CAViewBySelected");
    $('#' + viewBy + 'ViewBy').addClass("CAViewBySelected");

    queryParams.viewBy = viewBy;
}

var viewByObs = function(viewBySelected, firstTime) {
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

    if (viewBySelected == 'startDate') {
        // startDate view does not support "only pending"
        queryParams.showOnlyPending = false;
        $('#pendingCB').prop('checked', false);
    }

    set_view_by(viewBySelected);

    if (!firstTime) {
        refresh();
    }
};

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
};

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
    }
};

var confIdObs = function() {
    $E('categoryId').dom.disabled = ($E('conferenceId').get() != '')
};

var updateFilterButton = function() {
    $('#filterButton').val($T("Apply Filter"));
    if ($('#pendingCB').prop('checked') && queryParams.viewBy == 'startDate') {
        // startDate view does not support "only pending"
        set_view_by('modificationDate');
    }
};

var refresh = function() {
    if (!queryParams.indexName) {
        alertNoIndexSelected();
    } else {
        applyFilter();
        query();
    }
};

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
};

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
};

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

    $('#staticURL').val(url);
    $('#staticURLLink').attr('href', url);
};

/** Static URL qTip event handler **/
$('#CAStaticURLLink').qtip({
    content: {
        text: function() { return $('#CAStatucURLContentContainer'); }
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
        classes: 'qtip-rounded qtip-shadow qtip-light'
    }
}, {
    beforeRender: updateStaticURL()
});

var buildVideoServicesDisplayUrl = function(conference){
    var urlTemplate = conference.type === 'conference' ? (${ ConfCollaborationDisplay.js_router | j,n }) : Indico.Urls.ConferenceDisplay;
    return build_url(urlTemplate, {confId: conference.id});
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
};

var confTitleBookingTemplate = function(booking) {
    var row = Html.tr("ACBookingLine");

    var cell = Html.td('ACBookingFirstCell', Html.span('', booking.type));
    row.append(cell);

    var cell = Html.td('ACBookingCellNoWrap', Html.span(booking.statusClass, booking.hasAcceptReject?STATUS_MESSAGE[booking.acceptRejectStatus]:""));
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
};

var dateBookingTemplate = function(booking, viewBy) {
    var row = $('<tr class="ACBookingLine"></tr>');

    var time = null;
    if (viewBy === "creationDate") {
        time = booking.creationDate.time.substring(0,5);
    } else if (viewBy == "modificationDate") {
        time = booking.modificationDate.time.substring(0,5);
    } else if (viewBy == "startDate" && (booking.type == "RecordingRequest" || booking.type == "WebcastRequest")) {
        time = booking.instanceDate.time.substring(0, 5);
    } else if (viewBy == "startDate" || viewBy == "conferenceStartDate") {
        time = (booking.bookingParams.startDate.length === 0)
               ? '' : Util.parseDateTime(booking.bookingParams.startDate,
                       IndicoDateTimeFormats.Default).time.substring(0, 5);
    }

    row.data('time', time);
    row.append($('<td class="ACBookingFirstCell ACBookingTime"></td>').html(time)).
        append($('<td class="ACBookingCellNoWrap"><span>' + booking.type + '</span></td>')).
        append($('<td class="ACBookingCellNoWrap"></td>').append($('<span/>').
               addClass(booking.statusClass).html(booking.hasAcceptReject?STATUS_MESSAGE[booking.acceptRejectStatus]:""))).
        append($('<td class="ACBookingCell"></td>').html(booking.talk ? booking.talk.room : booking.conference.room)).
        append($('<td class="ACBookingCell"></td>').append($('<span/>').html(booking.conference.title +
                                                          (booking.talk ? (': <em>' + booking.talk.title + '</em>') : ''))));

    if (pluginHasFunction(booking.type, 'customText')) {
        row.append($('<td class="ACBookingCell"></td>').append(codes[booking.type].customText(booking, viewBy)));
    } else {
        row.append($('<td></td>'));
    }

    row.append($('<td class="ACBookingCellNoWrap"></td>').append(
        $('<a></a>').html($T('Change')).attr('href', booking.modificationURL),
        $('<span class="horizontalSeparator">|</span>'),
        $('<a></a>').html($T('Event Display')).attr('href', buildVideoServicesDisplayUrl(booking.conference))
    ));
    return row;
};

var dateGroupTemplate = function(group, isFirst, viewBy) {
    var date = group[0];
    var bookings = group[1];

    var result = $('<tbody/>').append($('<tr/>').append(
      $('<td class="ACBookingGroupTitle" colspan=11 />').append(
        $('<span/>').html(date)
    )));
    var rows = []
    $.each(bookings, function(i, booking) {
        rows.push(dateBookingTemplate(booking, viewBy));
    });
    rows.sort(function(a, b) {
        a = $(a).data('time');
        b = $(b).data('time');
        return a > b ? 1 : (a < b ? -1 : 0);
    });
    result.append(rows);
    return result;
};

var updateList = function() {
    updateResults();
    updatePageNumberList();
};

var updateResults = function() {

    $E('results').clear();

    if (nBookings < 1) {
        $('#resultsMessage').html($T("No results found"));
        $('#resultsMessage').show();
        $('#resultsInfo').hide();
    } else {
        $('#resultsMessage').hide();
        $('#resultsInfo').show();

        $('#totalInIndex').html(totalInIndex);
        $('#nBookings').html(nBookings);
        for (var i = 0; i < bookings.length; i++) {
            group = bookings[i];
            if (queryParams.viewBy == 'conferenceTitle') {
                $E('results').append(confTitleGroupTemplate(group, i == 0))
            } else {
                $('#results').append(dateGroupTemplate(group, i == 0, queryParams.viewBy))
            }
        }
    }
};

var updatePageNumberList = function() {
    pf.setNumberOfPages(nPages);
    pf.selectPage(queryParams.page);
};

var pageSelectedHandler = function(page) {
    queryParams.page = page;
    query();
};

var pf = new PageFooter('${ InitialNumberOfPages }', '${ InitialPage }', 4, pageSelectedHandler)

$(function(){

    $('#today_button').click(function(){
        var now = new Date();
        var today_text = Util.formatDateTime(now, IndicoDateTimeFormats.ServerHourless);
        $('#sinceDate').val(today_text);
        $('#toDate').val(today_text);
        refresh();
        return false;
    });

    $('#sinceDate').datepicker({ dateFormat: "yy/mm/dd" }).on('keypress', function (e) { updateFilterButton(); });
    $('#toDate').datepicker({ dateFormat: "yy/mm/dd" }).on('keypress', function (e) { updateFilterButton(); });

    initialize_index_tabs();
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

    dateParameterManager.add($E('sinceDate'), 'date', true);
    dateParameterManager.add($E('toDate'), 'date', true);

    resultsPerPageParameterManager.add($E('resultsPerPage'), 'int', false, function(value) {
        if (value < 1) {
            return $T("Please input number higher than 0");
        }
    });

    if (bookings) {
        updateResults();
    }
    $('body').delegate('#staticURL', 'click', function(e){
        $(this).select();});
});
</script>
