<%
rel = conf.as_event.get_relative_event_ids()
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
${ template_hook('global-announcement') }

<div class="page-header ${"page-header-dark" if dark_ else ""}">

    <%include file="SessionBar.tpl" args="dark=dark_"/>

    <div class="eventHeaderButtonBar" >

    % if 'needsBackButton' in locals() and needsBackButton:
        <a href="${ urlHandlers.UHConferenceDisplay.getURL(self_._conf) }" style=class="eventHeaderButtonBar">${ _('Go back to Conference') }<div class="leftCorner"></div></a>
    % elif conf.as_event.type != "conference" or displayNavigationBar:
        <a id="homeButton" href="${ url_for_index() }"
           style="background-image: url(${ systemIcon('home') }); margin-left: 10px"></a>

        <div class="separator"></div>

        %if rel['first'] is not None:
            <a id="firstEventButton" href="${ url_for('event.conferenceDisplay', confId=rel['first']) }"
               style="background-image: url(${ systemIcon('first_arrow') })"></a>
        % endif
        % if rel['prev'] is not None:
        <a id="previousEventButton" href="${ url_for('event.conferenceDisplay', confId=rel['prev']) }"
               style="background-image: url(${ systemIcon('left_arrow') })"></a>
        % endif

        <a id="upToCategoryButton" href="${ categurl }"
           style="background-image: url(${ systemIcon('upCategory') })"></a>

        %if rel['next'] is not None:
            <a id="nextEventButton" href="${ url_for('event.conferenceDisplay', confId=rel['next']) }"
               style="background-image: url(${ systemIcon('right_arrow') })"></a>
        % endif
        % if rel['last'] is not None:
            <a id="lastEventButton" href="${ url_for('event.conferenceDisplay', confId=rel['last']) }"
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
            <a id="exportIcal${self_._conf.as_event.id}" href="#" class="js-export-ical"
               data-id="${self_._conf.as_event.id}">
                ${ _("iCal export") }
                <div class="leftCorner"></div>
            </a>
            ${ template_hook('event-ical-export', event=self_._conf.as_event) }
        % endif

        % if showMoreButton:
            <%include file="HeaderMoreMenu.tpl" args="viewoptions = viewoptions,
                SelectedStyle = SelectedStyle, pdfURL=pdfURL,
                showExportToPDF=showExportToPDF,
                showDLMaterial=showDLMaterial, showLayout=showLayout,
                displayURL=displayURL"/>
        % endif

        <div class="separator"></div>

        <a id="manageEventButton" href="${ url_for('event_management.settings', conf) }"
           style="background-image: url(${ systemIcon('manage') })"></a>
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

% if conf.as_event.type != 'conference':
    ${ render_template('flashed_messages.html') }
% endif

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

    $('.js-export-ical').on('click', function(evt) {
        evt.preventDefault();
        $(this).trigger('menu_select');
    });

});

</script>
