<%page args="minutes=False"/>
<%namespace name="common" file="include/Common.tpl"/>

<div class="meetingEventSubHeader">
    <table class="eventDetails">
        <tbody>
            <%include file="${INCLUDE}/EventDetails.tpl" args="minutes=minutes"/>
        </tbody>
    </table>
</div>

<div class="meetingEventBody">
    <div style="position: absolute; right: 50px; top: 3px;"><span class="fakeLink dropDownMenu" id="goToDayLink"><strong>Go to day</strong></span></div>
    <script type="text/javascript">
        var goToDayMenuItems = $D(${dict((prettyDate(item.getAdjustedStartDate(timezone)),
                                       '#%s' % getDate(item.getAdjustedStartDate(timezone))) for item in entries)| n,j});

        goToDayMenuItems.sort(function(val1, val2){
           return SortCriteria.Default(goToDayMenuItems.get(val1), goToDayMenuItems.get(val2));
        });

        var goToDayLink = $E('goToDayLink');
        var goToDayMenu = null;
        if (keys(goToDayMenuItems).length < 2) {
            goToDayLink.dom.style.display = 'none';
        }
        goToDayLink.observeClick(function(e) {
            // Close the menu if clicking the link when menu is open
            if (goToDayMenu != null && goToDayMenu.isOpen()) {
                goToDayMenu.close();
                goToDayMenu = null;
                return;
            }
            // build a dictionary that represents the menu
            goToDayMenu = new PopupMenu(goToDayMenuItems, [goToDayLink], null, true, true);
            var pos = goToDayLink.getAbsolutePosition();
            goToDayMenu.open(pos.x + goToDayLink.dom.offsetWidth + 10, pos.y + goToDayLink.dom.offsetHeight + 3);
            return false;
        });

        ## dict to store inline video service popup information, populated in VideoService.tpl
        var videoServiceInfo = {};
    </script>

    <ul class="dayList">
        <% previousDate = None %>
        % for index, item in enumerate(entries):
            <%
                date = getDate(item.getAdjustedStartDate(timezone))
            %>

            % if previousDate and previousDate != date:
                </ul>
                </li>
            % endif

            % if not previousDate or date != previousDate:
                <li>
                <div style="width: 100%;">
                    <a name="${getDate(item.getAdjustedStartDate(timezone))}"></a>
                    <span class="day">${prettyDate(item.getAdjustedStartDate(timezone))}</span>
                </div>
                <ul class="meetingTimetable">
            % endif

            <%include file="${getItemType(item)}.tpl" args="item=item, parent=conf, minutes=minutes"/>

            <% previousDate = date %>
        % endfor
        % if entries:
            </ul>
            </li>
        % endif
    </ul>
</div>
<script type="text/javascript">
    var slideSpeed = 'fast';
    var tooltipMsgs = {moreinfo : $T('Click here to show / hide detailed information'),
                       morebookings : $T('There are more bookings than is currently shown.<br /> ' +
                                         'Click here to show / hide more information.')};

    $('#collShowBookings').qtip({
        content: tooltipMsgs["morebookings"],
        position: {
            my: 'bottom middle',
            at: 'top middle'
        },
        style: {
            classes: 'ui-tooltip-rounded ui-tooltip-shadow ui-tooltip-light'
        }
    });

    $('.collaborationDisplayMoreInfo').click(function() {
        var newText = ($(this).text() == $T("More Info")) ? $T("Hide info") : $T("More Info");
        var textNode = $(this);
        $(this).closest('.videoServiceWrapper').next('.collabInfoInline').slideToggle(slideSpeed, function() {
            textNode.text(newText);
        });
    });

    $('#collShowBookings').click(function() {
        var newText = ($(this).text() == $T("Show")) ? $T("Hide additional bookings") : $T("Show");
        var textNode = $(this);
        $('#collHiddenBookings').slideToggle(slideSpeed, function() {
            textNode.text(newText);
        });
    });

    $('.bookingLaunchLinkInline').qtip({
        content: {
            text: function() { return videoServiceInfo[$(this).data('id')]; }
        },
        position: {
            my: 'top middle',
            at: 'bottom middle'
        },
        show: {
            solo: true
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
    });

    $('.bookingLaunchLink').qtip({
        content: {
            text: function() { return videoServiceLaunchInfo[$(this).data('id')]; }
        },
        position: {
            my: 'bottom middle',
            at: 'top middle'
        },
        style: {
            classes: 'ui-tooltip-rounded ui-tooltip-shadow ui-tooltip-light'
        }
    });
</script>
