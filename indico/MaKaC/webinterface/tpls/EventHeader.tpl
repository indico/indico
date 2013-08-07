<%
owner = conf.getOwnerList()[0]

first = owner.getRelativeEvent('first')
last = owner.getRelativeEvent('last')

if first == conf:
   first = None
if last == conf:
   last = None

# If printURL is set then show the print button
if printURL is not UNDEFINED:
    showPrintButton = True
    printURL_ = printURL
else:
    showPrintButton = False

# Check if the header should be in dark colors
if dark is not UNDEFINED:
    dark_ = dark
else:
    dark_ = False;
%>
% if Config.getInstance().getMobileURL():
    <%include file="MobileDetection.tpl" args="conf=conf"/>
% endif
<%include file="Announcement.tpl"/>

<div class="pageHeader ${"pageHeaderDark" if dark_ else ""}">

    <%include file="SessionBar.tpl" args="dark=dark_"/>

    <div class="eventHeaderButtonBar" >

    % if 'needsBackButton' in locals() and needsBackButton:
        <a href="${ urlHandlers.UHConferenceDisplay.getURL(self_._conf) }" style=class="eventHeaderButtonBar">${ _('Go back to Conference') }<div class="leftCorner"></div></a>
    % elif conf.getType() != "conference" or displayNavigationBar:
        <a id="homeButton" href="${ urlHandlers.UHWelcome.getURL() }"
           style="background-image: url(${ systemIcon('home') }); margin-left: 10px"></a>

        <div class="separator"></div>

        %if first != None:
            <a id="firstEventButton" href="${ urlHandlers.UHConferenceDisplay.getURL(first) }"
               style="background-image: url(${ systemIcon('first_arrow') })"></a>
            <a id="previousEventButton" href="${ urlHandlers.UHPreviousEvent.getURL(conf) }"
               style="background-image: url(${ systemIcon('left_arrow') })"></a>
        % endif

        <a id="upToCategoryButton" href="${ categurl }"
           style="background-image: url(${ systemIcon('upCategory') })"></a>

        %if last != None:
            <a id="nextEventButton" href="${ urlHandlers.UHNextEvent.getURL(conf) }"
               style="background-image: url(${ systemIcon('right_arrow') })"></a>
            <a id="lastEventButton" href="${ urlHandlers.UHConferenceDisplay.getURL(last) }"
               style="background-image: url(${ systemIcon('last_arrow') })"></a>
        % endif

        % if showPrintButton or showMoreButton or showFilterButton:
            <div class="separator"></div>
        % endif

    % endif

        % if showPrintButton :
            <a id="printButton" href="${ printURL_ }"
               style="background-image: url(${ systemIcon('printer') })"></a>
        % endif

        % if showFilterButton:
            <%include file="MeetingFilter.tpl"/>
        % endif
        % if showExportToICal:
            <a id="exportIcal${self_._conf.getUniqueId()}" href="#" class="exportIcal" data-id="${self_._conf.getUniqueId()}">
                ${ _("iCal export") }
                <div class="leftCorner"></div>
            </a>
                <%include file="ConferenceICalExport.tpl" args="item=self_._conf"/>
        % endif

        % if showMoreButton:
            <%include file="HeaderMoreMenu.tpl" args="viewoptions = viewoptions,
                SelectedStyle = SelectedStyle, pdfURL=pdfURL,
                showExportToPDF=showExportToPDF,
                showDLMaterial=showDLMaterial, showLayout=showLayout,
                displayURL=displayURL"/>
        % endif

        <div class="separator"></div>

        <a id="manageEventButton" href="${ urlHandlers.UHConferenceModification.getURL(conf)  if usingModifKey else  urlHandlers.UHConfManagementAccess.getURL(conf) }"
           style="background-image: url(${ systemIcon('manage') })"></a>
        % if usingModifKey:
            <a href="${urlHandlers.UHConfCloseModifKey.getURL(self_._conf)}" style=class="eventHeaderButtonBar"> ${_('exit manage')} <div class="leftCorner"></div></a>
        % endif
    </div>


    <!-- This div is used for inserting content under the header
         such as the filtering optionsfor meetings -->
    <div id="pageSubHeader"></div>

    % if showFilterButton and filterActive == "1":
        <script type="text/javascript">
            // If the filter is active show the div.
            // This is done here since it has to be
            // done after the declaration of pageSubHeader
            filterToggle();
        </script>
    % endif

</div>


<script type="text/javascript">
$(function() {
    function createTooltip(element, tooltipText) {
        element.qtip({
            content: {
                text: $("<span style='padding:3px' />").append(tooltipText)
            }
        });
    }

    createTooltip($('#homeButton'), '${ _("Go to Indico Home Page")}');
    createTooltip($('#firstEventButton'), '${ _("Oldest event")}');
    createTooltip($('#previousEventButton'), '${ _("Older event")}');
    createTooltip($('#upToCategoryButton'), '${ _("Up to category")}');
    createTooltip($('#nextEventButton'), '${ _("Newer event")}');
    createTooltip($('#lastEventButton'), '${ _("Newest event")}');
    createTooltip($('#printButton'), '${ _("Printable version")}');
    createTooltip($('#manageEventButton'), '${ _("Switch to management area for this event")}');

    $(".exportIcal").click(function(){
        $(this).trigger('menu_select');
    });

});

</script>
