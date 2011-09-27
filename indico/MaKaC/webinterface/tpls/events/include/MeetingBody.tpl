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
