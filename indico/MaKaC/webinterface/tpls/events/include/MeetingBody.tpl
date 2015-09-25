<%page args="minutes=False"/>
<%namespace name="common" file="include/Common.tpl"/>
<div class="meetingEventSubHeader">
    <table class="eventDetails">
        <tbody>
            <%include file="${INCLUDE}/EventDetails.tpl" args="minutes=minutes"/>
        </tbody>
    </table>
</div>

% if conf.note or conf.canModify(user):
    ${ render_template('events/notes/note_event.html', note=conf.note, hidden=not minutes, can_edit=conf.canModify(user), for_event=conf) }
% endif

<div class="meetingEventBody">
    <div style="position: absolute; right: 50px; top: 3px;"><span class="fakeLink dropDownMenu" id="goToDayLink"><strong>Go to day</strong></span></div>
    <script type="text/javascript">
        var goToDayMenuDays = $D(${dict((getDate(item.getAdjustedStartDate(timezone)),prettyDate(item.getAdjustedStartDate(timezone))
                                       ) for item in entries)| n,j});

        var goToDayMenuDaysKeys = [];
        for(var key in goToDayMenuDays.getAll()) {
            goToDayMenuDaysKeys.push(key);
        }
        goToDayMenuDaysKeys.sort();

        var goToDayMenuItems = {};
        for(var i in goToDayMenuDaysKeys){
            goToDayMenuItems[goToDayMenuDaysKeys[i]] = {action:"#"+goToDayMenuDaysKeys[i] , display:goToDayMenuDays.get(goToDayMenuDaysKeys[i])};
        }

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
