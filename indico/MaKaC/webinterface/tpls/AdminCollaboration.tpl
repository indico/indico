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
        
        <a id="index_<%=indexName%>" onclick="indexSelectedObs('<%=indexName%>', false)" <%=additionalStyle%> >
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
    
    <div style="padding-top: 5px">
        <%= _("Since")%> <input type="text" size="16" id="minKey" onkeypress="updateFilterButton()" value="<%= InitialMinKey %>"/>
        <%= _("to")%> <input type="text" size="16" id="maxKey" onkeypress="updateFilterButton()" value="<%= InitialMaxKey %>"/>
        <span class="CAMinMaxKeySuggestion" id="minMaxKeySuggestion"></span>
    </div>
    
    <div style="padding-top: 5px">
        <input type="button" id="filterButton" value="<%= _("Refresh")%>" onclick="applyFilter(); query();"/>
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

<div class="CADiv">
    <div class = "CAResultsDiv">
        <span id="resultsMessage"><%= _("(Results will appear here)")%></span>
        <table class="CAResultsTable" id ="results">
        </table>
    </div>
    <div id="pageNumberList">
    </div>
</div>
</div>
<script type="text/javascript">

var nPages = <%= InitialNumberOfPages %>;
var bookings = <%= jsonEncode (InitialBookings) %>;

var indexNames = <%=[index.getName() for index in Indexes]%>;
var indexInformation = <%= jsonEncode(DictPickler.pickle(dict([(i.getName(), i) for i in Indexes])))%>
var viewBy = ['conferenceTitle','conferenceStartDate', 'creationDate','modificationDate','startDate'];

var queryParams = {
    indexName: '',
    showOnlyPending: <%= jsonEncode(InitialOnlyPending) %>,
    filterByOnlyPending: true,
    conferenceId: '<%= InitialConferenceId %>',
    categoryId: '<%= InitialCategoryId %>',
    minKey: '<%= InitialMinKey %>',
    maxKey: '<%= InitialMaxKey %>',
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
            IndicoUI.Widgets.Generic.tooltip(this, event, '<div style="padding:5px">Plugins in this index:<br \/>' +
                    indexInformation[this.id.substring(6)].plugins.join(", ") +
                    '<\/div>');
        }
    }    
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
        applyFilter();
        query()
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

    var clearKeys = function(){
    	$E('minKey').set('');
        $E('maxKey').set('');
        queryParams.minKey = '';
        queryParams.maxKey = '';
    }

    if ((endsWith(queryParams.viewBy, 'Date') || firstTime) && viewBySelected == 'conferenceTitle') {
    	clearKeys();
    	IndicoUI.Widgets.Generic.removeCalendar($E('minKey'));
        IndicoUI.Widgets.Generic.removeCalendar($E('maxKey'));
        $E('minMaxKeySuggestion').set('<%= _("Please input a conference title or the beginning of it")%>');
        orderByObs('ascending', true); // we put true because we don't want to trigger another request
    }
    if (endsWith(viewBySelected, 'Date') && (queryParams.viewBy == 'conferenceTitle' || firstTime)) {
    	clearKeys();
    	IndicoUI.Widgets.Generic.input2dateField($E('minKey'), true, null);
        IndicoUI.Widgets.Generic.input2dateField($E('maxKey'), true, null);
        $E('minMaxKeySuggestion').set('<%= _("Please input dates")%>');
        orderByObs('descending', true); // we put true because we don't want to trigger another request
    }
    

    queryParams.viewBy = viewBySelected;

    if (!firstTime) {
        applyFilter();
        query()
    };
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
        applyFilter();
        query();
    };

}

var confIdObs = function() {
	$E('categoryId').dom.disabled = ($E('conferenceId').get() != '') 
}

var updateFilterButton = function() {
    $E('filterButton').dom.value = '<%= _("Apply Filter")%>';   
}

var applyFilter = function(){
    queryParams.showOnlyPending = $E('pendingCB').dom.checked;
    queryParams.conferenceId = $E('conferenceId').get();
    queryParams.categoryId = $E('categoryId').get();
    queryParams.minKey = $E('minKey').get();
    queryParams.maxKey = $E('maxKey').get();
    queryParams.resultsPerPage = $E('resultsPerPage').get();
    queryParams.page = 1;
    $E('filterButton').dom.value = '<%= _("Refresh")%>';
}

var query = function() {

    if (endsWith(queryParams.viewBy, 'Date') && !dateParameterManager.check()) {
        return;
    }
    if (!resultsPerPageParameterManager.check()) {
        return;
    }

    var killProgress = IndicoUI.Dialogs.Util.progress("<%= _("Retrieving the data...")%>");
    updateStaticURL();

    indicoRequest(
        'collaboration.bookingIndexQuery',
        {
            indexName : queryParams.indexName,
            viewBy : queryParams.viewBy,
            orderBy : queryParams.orderBy,
            minKey : queryParams.minKey,
            maxKey : queryParams.maxKey,
            onlyPending : queryParams.filterByOnlyPending && queryParams.showOnlyPending,
            conferenceId : queryParams.conferenceId,
            categoryId : queryParams.categoryId,
            page: queryParams.page,
            resultsPerPage: queryParams.resultsPerPage
        },
        function(result,error) {
            if (!error) {
                bookings = result[0];
                nPages = result[1];
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
              '&minKey=' + queryParams.minKey +
              '&maxKey=' + queryParams.maxKey +
              '&viewBy=' + queryParams.viewBy +
              '&orderBy=' + queryParams.orderBy;

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

    var result = Html.tbody('',
        Html.tr('', Html.td({className : !isFirst? 'ACBookingGroupTitle' : '', colspan: 10, colSpan: 10}, 
            Html.a({className : 'ACConfLink', href : conference.displayURL},
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

    var cell = Html.td('ACBookingFirstCell', Html.a({href: booking.modificationURL}, booking.type));
    row.append(cell);

    var cell = Html.td('ACBookingCell', Html.span(booking.statusClass, booking.statusMessage));
    row.append(cell);

    var cell = Html.td('ACBookingCell', '<%= _("Last modification:")%> ' + formatDateTimeCS(booking.modificationDate) );
    row.append(cell);

    if (pluginHasFunction(booking.type, 'customText')) {
        var cell = Html.td('ACBookingCell', codes[booking.type].customText(booking, 'conferenceTitle') );
        row.append(cell);
    }

    return row;
}

var dateBookingTemplate = function(booking, viewBy) {
    var row = Html.tr();

    var time = booking[viewBy].time.substring(0,5) // we can do this because viewBy will be creationDate, etc. which are the same
                                                   // names of the fields of the booking
    
    var cell = Html.td('ACBookingFirstCell ACBookingTime', time);
    row.append(cell);

    var cell = Html.td('ACBookingCell', Html.a({href: booking.modificationURL}, booking.type));
    row.append(cell);

    var cell = Html.td('ACBookingCell', Html.span(booking.statusClass, booking.statusMessage));
    row.append(cell);

    var cell = Html.td('ACBookingConference', Html.span('', '<%= _("In event:")%> '), Html.a({className : 'ACBookingConferenceLink', href:booking.conference.displayURL}, booking.conference.title));
    row.append(cell);

    if (pluginHasFunction(booking.type, 'customText')) {
        var cell = Html.td('ACBookingCell', codes[booking.type].customText(booking, viewBy) );
        row.append(cell);
    }

    return row;
}

var dateGroupTemplate = function(group, isFirst, viewBy) {
    var date = group[0];
    var bookings = group[1];

    var result = Html.tbody('',
            Html.tr('', Html.td({className : !isFirst? 'ACBookingGroupTitle' : '', colspan: 10, colSpan: 10}, 
                Html.span('ACGroupDate', date)
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

    if (nPages == 0) {
        $E('resultsMessage').set('<%= _("No results found")%>');
        IndicoUI.Effect.appear($E('resultsMessage'));
    } else {
        IndicoUI.Effect.disappear($E('resultsMessage'));
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
    indexSelectedObs('<%=InitialIndex%>', true);
    confIdObs();
    viewByObs('<%=InitialViewBy %>', true);
    <% if InitialOrderBy: %>
        orderByObs('<%= InitialOrderBy %>', true);
    <% end %>
    updateStaticURL();
    
    $E('pageNumberList').set(pf.draw());

    dateParameterManager.add($E('minKey'), 'datetime', true);
    dateParameterManager.add($E('maxKey'), 'datetime', true);

    resultsPerPageParameterManager.add($E('resultsPerPage'), 'int', false, function(value) {
        if (value < 1) {
            return "<%= _("Please input number higher than 0")%>";
        }
    })
    
    if (bookings) {
        updateResults();
    }
});
</script>