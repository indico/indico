<% declareTemplate(newTemplateStyle=True) %>

<%!
owner = conf.getOwnerList()[0]

prev = owner.getPreviousEvent(conf)
next = owner.getNextEvent(conf)
first = owner.getFirstEvent(conf)
last = owner.getLastEvent(conf)

# If printURL is set then show the print button
try:
	printURL
	showPrintButton = True
except NameError:
	showPrintButton = False

# Check if the header should be in dark colors
try:
    dark
except NameError:
    dark = False;

%>

<% includeTpl('Announcement') %>

<div class="pageHeader <% if dark: %>pageHeaderDark<% end %>">

    <% includeTpl('SessionBar', dark=dark) %>

    <div class="eventHeaderButtonBar" >

    <% if 'needsBackButton' in locals() and needsBackButton: %>
        <a href="<%= urlHandlers.UHConferenceDisplay.getURL(self._conf) %>" style=class="eventHeaderButtonBar"><%= _('Go back to Conference') %><div class="leftCorner"></div></a>
    <% end %>
    <% else: %>
        <a id="homeButton" href="<%= urlHandlers.UHWelcome.getURL() %>"
           style="background-image: url(<%= systemIcon('home') %>); margin-left: 10px"></a>

        <div class="separator"></div>

        <%if first != None: %>
            <a id="firstEventButton" href="<%= urlHandlers.UHConferenceDisplay.getURL(first) %>"
               style="background-image: url(<%= systemIcon('first_arrow') %>)"></a>
        <% end %>

        <%if prev != None: %>
            <a id="previousEventButton" href="<%= urlHandlers.UHConferenceDisplay.getURL(prev) %>"
               style="background-image: url(<%= systemIcon('left_arrow') %>)"></a>
        <% end %>

        <a id="upToCategoryButton" href="<%= categurl %>"
           style="background-image: url(<%= systemIcon('upCategory') %>)"></a>

        <%if next != None: %>
            <a id="nextEventButton" href="<%= urlHandlers.UHConferenceDisplay.getURL(next) %>"
               style="background-image: url(<%= systemIcon('right_arrow') %>)"></a>
        <% end %>

        <%if last != None: %>
            <a id="lastEventButton" href="<%= urlHandlers.UHConferenceDisplay.getURL(last) %>"
               style="background-image: url(<%= systemIcon('last_arrow') %>)"></a>
        <% end %>

    <% end %>

		<% if showPrintButton or showMoreButton or showFilterButton: %>
            <div class="separator"></div>
        <% end %>

        <% if showPrintButton : %>
            <a id="printButton" href="<%= printURL %>"
               style="background-image: url(<%= systemIcon('printer') %>)"></a>
		<% end %>

        <% if showFilterButton: %>
            <% includeTpl('MeetingFilter') %>
        <% end %>

		<% if showMoreButton: %>
            <% includeTpl('HeaderMoreMenu', viewoptions = viewoptions, \
                SelectedStyle = SelectedStyle, pdfURL=pdfURL, \
                showExportToICal=showExportToICal, showExportToPDF=showExportToPDF, \
                showDLMaterial=showDLMaterial, showLayout=showLayout) %>
		<% end %>

        <div class="separator"></div>

        <a id="manageEventButton" href="<% if usingModifKey: %><%= urlHandlers.UHConferenceModification.getURL(conf) %><%end%><%else:%><%= urlHandlers.UHConfManagementAccess.getURL(conf) %><%end%>"
           style="background-image: url(<%= systemIcon('manage') %>)"></a>
        <% if usingModifKey: %><a href="<%= urlHandlers.UHConfCloseModifKey.getURL(self._conf) %>" style=class="eventHeaderButtonBar"><%= _('exit manage') %><div class="leftCorner"></div></a><% end %>
    </div>


    <!-- This div is used for inserting content under the header
         such as the filtering optionsfor meetings -->
    <div id="pageSubHeader"></div>

    <% if showFilterButton and filterActive == "1": %>
        <script type="text/javascript">
            // If the filter is active show the div.
            // This is done here since it has to be
            // done after the declaration of pageSubHeader
            filterToggle();
        </script>
    <% end %>

</div>


<script type="text/javascript">

    function setMouseEvents(element, tooltipText) {
        var tooltipText = "<span style='padding:3px'>" + tooltipText + "</span>";
        element.dom.onmouseover = function(event) {
            IndicoUI.Widgets.Generic.tooltip(element.dom, event, tooltipText);
        }
    }

    setMouseEvents($E('homeButton'), '<%= _("Go to Indico Home Page")%>');

    if (exists($E('firstEventButton'))) {
        setMouseEvents($E('firstEventButton'), '<%= _("Oldest event")%>');
    }

    if (exists($E('previousEventButton'))) {
        setMouseEvents($E('previousEventButton'), '<%= _("Older event")%>');
    }

    setMouseEvents($E('upToCategoryButton'), '<%= _("Up to category")%>');

    if (exists($E('nextEventButton'))) {
        setMouseEvents($E('nextEventButton'), '<%= _("Newer event")%>');
    }

    if (exists($E('lastEventButton'))) {
        setMouseEvents($E('lastEventButton'), '<%= _("Newest event")%>');
    }

    if (exists($E('printButton'))) {
        setMouseEvents($E('printButton'), '<%= _("Printable version")%>');
    }

    setMouseEvents($E('manageEventButton'), '<%= _("Manage event")%>');

</script>

<%= errorMsg %>
<%= infoMsg %>


