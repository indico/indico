<div class="container">
<% from MaKaC.common.PickleJar import DictPickler %>

<div class="categoryTitle"><%= _("Video Services Overview")%></div>

<ul class="CAIndexList">
<% lastIndex = len(Indexes) - 1 %>
<% for i, index in enumerate(Indexes): %>
    <% indexName = index.getName() %>
    <li>
        <% if i == lastIndex: %>
            <% additionalStyle = 'style="border-right\x3a 0px;"' %>
        <% end %>
        <% else: %>
            <% additionalStyle = '' %>
        <% end %>

        <a id="index_<%=indexName%>" onclick="indexSelectedObs('<%=indexName%>', false)" class="CAIndexUnselected" <%=additionalStyle%> >
            <%= indexName[0].upper() + indexName[1:] %>
        </a>
    </li>
<% end %>
</ul>

<div class="CADiv">
    <div id="pendingCategoryFilteringDiv">
        <div id="CAShowOnlyPendingDiv" class="CAShowOnlyPendingDiv" style="display:inline;">
            <% if InitialOnlyPending: %>
                <% checked = 'checked' %>
            <% end %>
            <% else: %>
                 <% checked = '' %>
            <% end %>
            <input type="checkbox" id="pendingCB" onchange="updateFilterButton()" <%=checked %>/>
            <label for="pendingCB"><%= _("Show only pending")%></label>
        </div>
        <div class="CAFilterByCategoryDiv" id="CAFilterByCategoryDiv" style="display:inline;">
            <span><%= _("Restrict to category id:")%></span>
            <input type="text" size="5" id="categoryId" onkeypress="updateFilterButton()" value="<%= InitialCategoryId %>"/>
        </div>
        <div class="CAFilterByCategoryDiv" id="CAFilterByCategoryDiv" style="display:inline;">
            <span><%= _("Restrict to conference id:")%></span>
            <input type="text" size="5" id="conferenceId" onkeyup="confIdObs()" onkeypress="updateFilterButton()" value="<%= InitialConferenceId %>"/>
        </div>
        <div class="CAResultsPerPageDiv">
            <%= _("Results per page:")%> <input type="text" id="resultsPerPage" size="5" onkeypress="updateFilterButton()" value="<%= InitialResultsPerPage %>"/>
        </div>
    </div>

    <div id="dateFilter" style="padding-top: 10px">
        <div>
            <% if InitialFromDays: %>
                <% checked1 = '' %>
                <% checked2 = 'checked' %>
            <% end %>
            <% else: %>
                <% checked1 = 'checked' %>
                <% checked2 = '' %>
            <% end %>
            <input type="radio" name="dateFilterType" id="sinceToDateRadio" onclick="updateDateFilterType()" class="CARadio" <%= checked1 %> />
            <%= _("Since")%> <input type="text" size="16" id="sinceDate" onkeypress="updateFilterButton()" value="<%= InitialSinceDate %>"/>
            <%= _("to")%> <input type="text" size="16" id="toDate" onkeypress="updateFilterButton()" value="<%= InitialToDate %>"/>
            <span class="CAMinMaxKeySuggestion"><%= _("Please input dates") %></span>
        </div>
        <div style="padding-top: 5px">
            <input type="radio" name="dateFilterType" id="fromToDaysRadio" onclick="updateDateFilterType()" class="CARadio" <%= checked2 %> />
            <%= _("From")%> <input type="text" size="3" id="fromDays" onkeypress="updateFilterButton()" value="<%= InitialFromDays %>"/>
            <%= _("days ago to")%> <input type="text" size="3" id="toDays" onkeypress="updateFilterButton()" value="<%= InitialToDays %>"/>
            <%= _("days in the future") %>
            <span class="CAMinMaxKeySuggestion"><%= _("Please input integers") %></span>
        </div>
    </div>
    <div id="titleFilter" style="padding-top: 10px">
        <div>
            <%= _("From")%> <input type="text" size="16" id="fromTitle" onkeypress="updateFilterButton()" value="<%= InitialFromTitle %>"/>
            <%= _("to")%> <input type="text" size="16" id="toTitle" onkeypress="updateFilterButton()" value="<%= InitialToTitle %>"/>
            <span class="CAMinMaxKeySuggestion"><%= _("Please input a conference title or the beginning of it") %></span>
        </div>
    </div>

    <div style="padding-top: 10px">
        <input type="button" id="filterButton" value="<%= _("Refresh")%>" onclick="refresh()"/>
    </div>
</div>

<div class="CADiv">
    <div class="CAOrderByDiv">
        <span class="CAViewBySpan"><%= _("Order:")%> </span>
        <a class="CAViewByLink" id="ascendingViewBy" onclick="orderByObs('ascending')"><%= _("Ascending")%></a>
        <a class="CAViewByLink" id="descendingViewBy" onclick="orderByObs('descending')" ><%= _("Descending")%></a>
    </div>
    <div class="CAViewByDiv">
        <span class="CAViewBySpan"><%= _("View by:")%> </span>
        <a class="CAViewByLink" id="conferenceTitleViewBy" onclick="viewByObs('conferenceTitle')"><%= _("Event Title")%></a>
        <a class="CAViewByLink" id="conferenceStartDateViewBy" onclick="viewByObs('conferenceStartDate')"><%= _("Event Start Date")%></a>
        <a class="CAViewByLink" id="creationDateViewBy" onclick="viewByObs('creationDate')"><%= _("Creation Date")%></a>
        <a class="CAViewByLink" id="modificationDateViewBy" onclick="viewByObs('modificationDate')"><%= _("Modification Date")%></a>
        <a class="CAViewByLink" id="startDateViewBy" onclick="viewByObs('startDate')"><%= _("Start Date")%></a>
    </div>

    <div class="CAInfoDiv">
        <div class="CATypesDiv">
            <%= _("This list can have bookings of the following type(s):")%> <span class="pluginNames" id="indexPluginTypes"></span>
        </div>

        <div class="CAStaticURLDiv">
            <a class="CAStaticURLSwitch" onclick="staticURLSwitch()"><%= _("Static URL for this result")%></a> <%= _("(Use it for bookmarks)")%><br />
            <input type="text" id="staticURL" style="width: 50%%; display: none; margin-top: 5px;"/>
            <a id="staticURLLink" style="display: none;  margin-left: 5px;" href="<%= BaseURL %>"><%= _("Go to URL")%></a>
        </div>
    </div>
</div>

<div>
    <div class = "CAResultsDiv">
        <span id="resultsMessage"><%= _("(Results will appear here)")%></span>
        <div id="resultsInfo" style="display:none;">
            <div class="CATotalInIndexDiv">
                <span id="totalInIndex"></span><span>&nbsp;<%= _("bookings in this index.") %></span>
            </div>
            <div class="CANResultsDiv">
                <span>Query returned&nbsp;</span><span id="nBookings"></span><span>&nbsp;<%= _("bookings.") %></span>
            </div>
        </div>
        <table cellpadding="0" cellspacing="0" class="CAResultsTable" id ="results">
        </table>
    </div>
    <div id="pageNumberList">
    </div>
</div>
<script type="text/javascript">

var bookings = <%= jsonEncode (InitialBookings) %>;
var nBookings = <%= InitialNumberOfBookings %>
var totalInIndex = <%= InitialTotalInIndex %>
var nPages = <%= InitialNumberOfPages %>;

var indexNames = <%=[index.getName() for index in Indexes]%>;
var indexInformation = <%= jsonEncode(DictPickler.pickle(dict([(i.getName(), i) for i in Indexes])))%>
var viewBy = ['conferenceTitle','conferenceStartDate', 'creationDate','modificationDate','startDate'];

var queryParams = {
    indexName: '',
    showOnlyPending: <%= jsonEncode(InitialOnlyPending) %>,
    filterByOnlyPending: true,
    conferenceId: '<%= InitialConferenceId %>',
    categoryId: '<%= InitialCategoryId %>',
    sinceDate: '<%= InitialSinceDate %>',
    toDate: '<%= InitialToDate %>',
    fromDays: '<%= InitialFromDays %>',
    toDays: '<%= InitialToDays %>',
    fromTitle: '<%= InitialFromTitle %>',
    toTitle: '<%= InitialToTitle %>',
    viewBy: '',
    orderBy: '',
    resultsPerPage: '<%= InitialResultsPerPage %>',
    page: '<%= InitialPage %>'
}

var dateParameterManager = new IndicoUtil.parameterManager();
var resultsPerPageParameterManager = new IndicoUtil.parameterManager();

var codes = {
<%= ",\n". join(['"' + pluginName + '" \x3a ' + code for pluginName, code in JSCodes.items()]) %>
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

    if (hasViewByStartDate) {
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
    $E('filterButton').dom.value = $T("Apply Filter");
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
    var url = '<%= BaseURL %>' +
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

    $E('staticURL').set(url);
    $E('staticURLLink').dom.href = url;
}

var staticURLState = false;
var staticURLSwitch = function() {
    if (staticURLState) {
        IndicoUI.Effect.disappear($E('staticURL'));
        IndicoUI.Effect.disappear($E('staticURLLink'));
    } else {
        IndicoUI.Effect.appear($E('staticURL'));
        IndicoUI.Effect.appear($E('staticURLLink'));
        $E('staticURL').dom.select();
    }
    staticURLState = !staticURLState;
}

var confTitleGroupTemplate = function(group, isFirst){
    var conference = group[0];
    var bookings = group[1];

    var result = Html.tbody({},
        Html.tr({}, Html.td({className : 'ACBookingGroupTitle', colspan: 10, colSpan: 10},
            Html.a({className : 'ACConfLink', href : conference.videoServicesDisplayURL},
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
    var row = Html.tr();

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
                                              Html.a({href: booking.conference.videoServicesDisplayURL}, 'Event Display'));
    row.append(cell);

    IndicoUI.Effect.mouseOver(row.dom);

    return row;
}

var dateBookingTemplate = function(booking, viewBy) {
    var row = Html.tr();

    var time = booking[viewBy].time.substring(0,5) // we can do this because viewBy will be creationDate, etc. which are the same
                                                   // names of the fields of the booking

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
            Html.a({href: booking.conference.videoServicesDisplayURL}, $T('Event Display')));
    row.append(cell);

    IndicoUI.Effect.mouseOver(row.dom);

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
            if (queryParams.viewBy == 'conferenceTitle' || queryParams.viewBy == 'conferenceStartDate') {
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

var pf = new PageFooter('<%= InitialNumberOfPages %>', '<%= InitialPage %>', 4, pageSelectedHandler)

IndicoUI.executeOnLoad(function(){
    buildIndexTooltips();
    confIdObs();
    viewByObs('<%=InitialViewBy %>', true);
    updateDateFilterType();
    <% if InitialOrderBy: %>
        orderByObs('<%= InitialOrderBy %>', true);
    <% end %>
    <% if InitialIndex: %>
        indexSelectedObs('<%= InitialIndex %>', true);
    <% end %>
    updateStaticURL();

    $E('pageNumberList').set(pf.draw());

    dateParameterManager.add($E('sinceDate'), 'datetime', true);
    dateParameterManager.add($E('toDate'), 'datetime', true);
    IndicoUI.Widgets.Generic.input2dateField($E('sinceDate'), true, null);
    IndicoUI.Widgets.Generic.input2dateField($E('toDate'), true, null);

    resultsPerPageParameterManager.add($E('resultsPerPage'), 'int', false, function(value) {
        if (value < 1) {
            return $T("Please input number higher than 0");
        }
    })

    if (bookings) {
        updateResults();
    }
});
</script>
