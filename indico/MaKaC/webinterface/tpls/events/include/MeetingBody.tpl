<%page args="minutes='off'"/>
<%namespace name="common" file="include/Common.tpl"/>

<div class="meetingEventSubHeader">
    <%include file="EventDetails.tpl" args="minutes=minutes"/>
</div>

<div class="meetingEventBody">
    <div style="position: absolute; right: 50px; top: 3px;"><span class="fakeLink dropDownMenu" id="goToDayLink"><strong>Go to day</strong></span></div>
    <script type="text/javascript">
        var goToDayMenuItems = {};

        <% addedDates = set() %>
        % for item in iconf.findall('session|contribution|break'):
            <% startDate = item.startDate.text[:10] %>
            % if date not in addedDates:
                goToDayMenuItems['${prettyDate(startDate)}'] = '#${startDate}';
                <% addedDates.add(startDate) %>
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
        <% items = iconf.findall('session|contribution|break') %>
        % for index, item in enumerate(items):
            <%
            startDate = item.startDate.text[:10]
            previousItem = items[index - 1] if index - 1 >= 0 else None
            nextItem = items[index + 1] if index + 1 < len(items) else None
            %>
            % if not previousItem or startDate != previousItem.startDate.text[:10]:
                <li>
                <div style="width: 100%;">
                    <a name="${startDate}"></a>
                    <span class="day">${prettyDate(startDate)}</span>
                </div>
                <ul class="meetingTimetable">
            % endif

            <%include file="${item.tag.capitalize()}.tpl" args="item=item, minutes=minutes"/>

            % if not nextItem or startDate != nextItem.startDate.text[:10]:
                </ul>
                </li>
            % endif
        % endfor
    </ul>
</div>
