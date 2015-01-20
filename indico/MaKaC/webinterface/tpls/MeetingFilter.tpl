<%
if filterActive == "1":
    filterActiveStyle = "color:#D7FF99; font-weight: bold;"
else:
    filterActiveStyle = ""
%>

<a id="filterLink" href="#" style="${ filterActiveStyle }">${ _('Filter') }<div class="leftCorner"></div></a>

    <div id="filterDiv" class="filterDiv">
        <form id="filterForm" style="margin: 0pt;">


        <input type="hidden" id="filterActive" name="filterActive" value="1" />

        <div style="float: right;">
            <input type="submit" class="btn" value="Apply filter" />&nbsp;
            <input type="button" id="removeFilterButton" class="btn" value="Remove filter">
        </div>


        <strong>${ _("Focus on:")}&nbsp;</strong>

        <select id="datesSelect" name="showDate" style="font-size:8pt;">
            ${ datesMenu }
        </select>

        <select id="showSessionSelect" name="showSession" style="font-size:8pt;">
            ${ sessionsMenu }
        </select>

        <span style="white-space: nowrap; margin-left: 65px;">
            <input id="hideContributionsCheckbox" style="margin-right: 5px;" type="checkbox" name="detailLevel" value="session" ${ hideContributions }></input>
            <strong id="hideContributionsLabel">${ _("Hide Contributions")}</strong>
        </span>

        </form>
    </div>

<script type="text/javascript">
    var filterButtonClicked = false;
    var filterButtonState = false;
    var filterLink = $('#filterLink');

    var filterToggle = function() {
        if (!filterButtonClicked) {
            // When clicked for the first time append the div to the correct
            // container
            $E('pageSubHeader').append($E('filterDiv'));
            filterButtonClicked = true;
        }

        if (!filterButtonState) {
            $E('filterDiv').dom.style.display = 'block';
        }
        else {
            $E('filterDiv').dom.style.display = 'none';
        }
        filterButtonState = !filterButtonState;
    };

    // Setup the filter button in the toolbar
    filterLink.on('click', function(e) {
        e.preventDefault();
        filterToggle();
    });

    // When remove filter button clicked, if needed reset the form and do submit otherwise
    // just hide the filter div
    $E('removeFilterButton').observeClick(function() {
        // Reset the form
        $E('hideContributionsCheckbox').dom.checked = false;
        $E('datesSelect').dom.selectedIndex = "0";
        $E('showSessionSelect').dom.selectedIndex = "0";

        % if filterActive == "1":
            $E('filterActive').dom.value = "0";
            $E('filterForm').dom.submit();
        % else:
            filterToggle();
        % endif
    });

    // Tooltip on filter icon
    filterLink.on('mouseover', function(event) {
        IndicoUI.Widgets.Generic.tooltip(this, event,
            '<ul style="list-style-type:none;padding:3px;margin:0px">'+
            '<li>'+
                % if filterActive != "1":
                    'Add a filter'+
                % else:
                    'The filtering is <strong>activated</strong>'+
                    '<\/li>'+
                    '<li>'+
                        '${ _("Click on Remove filter to deactivate it")}'+
                % endif
            '<\/li>'+
            '<\/ul>'
        );
    });

    // Setup the hide contributions checkbox
    % if hideContributions == None:
        $E('hideContributionsLabel').dom.style.display = 'none';
        $E('hideContributionsCheckbox').dom.style.display = 'none'
    % endif

    // Make the hide contributions label clickable
    $E('hideContributionsLabel').dom.style.cursor='pointer'
    $E('hideContributionsLabel').observeClick(function() {$E('hideContributionsCheckbox').dom.checked = !$E('hideContributionsCheckbox').dom.checked;});

</script>
