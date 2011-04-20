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
        var goToDayMenuItems = {};

        <% addedDates = set() %>
        % for item in entries:
            % if item.getAdjustedStartDate(timezone):
                <% date = getDate(item.getAdjustedStartDate(timezone)) %>
                % if date not in addedDates:
                    goToDayMenuItems['${prettyDate(item.getAdjustedStartDate(timezone))}'] = '#${date}';
                    <% addedDates.add(date) %>
                % endif
            % endif
        % endfor

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
    </script>

    <ul class="dayList">
        % for index, item in enumerate(entries):
            <%
                date = getDate(item.getAdjustedStartDate(timezone))
                previousItem = entries[index - 1] if index - 1 >= 0 else None
                nextItem = entries[index + 1] if index + 1 < len(entries) else None
            %>
            % if not previousItem or date != getDate(previousItem.getAdjustedStartDate(timezone)):
                <li>
                <div style="width: 100%;">
                    <a name="${getDate(item.getAdjustedStartDate(timezone))}"></a>
                    <span class="day">${prettyDate(item.getAdjustedStartDate(timezone))}</span>
                </div>
                <ul class="meetingTimetable">
            % endif

            <%include file="${getItemType(item)}.tpl" args="item=item, parent=conf, minutes=minutes"/>

            % if not nextItem or date != getDate(nextItem.getAdjustedStartDate(timezone)):
                </ul>
                </li>
            % endif
        % endfor
    </ul>
</div>
