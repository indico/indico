% if iconf.find('plugins/collaboration/booking'):
<tr>
<td class="leftCol">Video Services</td>
<td>
<div>
% for position, booking in enumerate(iconf.plugins.collaboration.booking):

    % if position == 2:
        <div id="collShowBookingsDiv">
            <span class="collShowHideBookingsText">
                <%
                moreOngoing = len(booking.findall("following-sibling::booking[kind = 'ongoing']"))
                moreScheduled = len(booking.findall("following-sibling::booking[kind = 'scheduled']"))
                %>
                There are
                % if booking.kind == 'ongoing':
                    ${ 1 + moreOngoing } more ongoing bookings
                    % if moreScheduled > 0:
                        and ${moreScheduled} more scheduled bookings.
                    % endif
                % elif booking.kind == 'scheduled':
                    ${ 1 + moreScheduled } more scheduled bookings.
                % endif
            </span>
            <span id="collShowBookings" class="fakeLink collShowBookingsText">Show</span>
        </div>
    </div>

    <div id="collHiddenBookings" style="visibility: hidden; overflow: hidden;">
    % endif

    <!-- Start of a booking line -->
    <div class="collaborationDisplayBookingLine">
    <span class="collaborationDisplayBookingType">${booking.typeDisplayName}</span>\
    % if booking.find('startDate'):
        <%
        collaborationToday = iconf.plugins.collaboration.todayReference
        collaborationTomorrow = iconf.plugins.collaboration.tomorrowReference
        startDate, endDate = booking.startDate.text, booking.endDate.text
        %>
        <%def name="shortDate(dateTime)">
            <% date = dateTime[:10] %>
            % if date == collaborationToday:
                today
            % elif date == collaborationTomorrow:
                tomorrow
            % else:
                <% date = parseDate(dateTime[:10], format('%Y-%m-%d')) %>
                ${ formatDate(date, format='%a %d/%m') }
            % endif
        </%def>
        % if booking.kind == 'scheduled' and startDate[:10] == endDate[:10]:
            % if startDate[:10] not in (collaborationToday, collaborationTomorrow):
                on
            % endif
            ${shortDate(startDate)} from ${extractTime(startDate)} to ${extractTime(endDate)}\
        % else:
            % if booking.kind == 'scheduled':
                from ${shortDate(startDate)} at ${extractTime(startDate)} until
            % elif booking.kind == 'ongoing':
                ongoing until
            % endif
            ${shortDate(endDate)} at ${extractTime(endDate)}\
        % endif
    % endif
    % if booking.find('firstLineInfo'):
: ${booking.firstLineInfo}\
    % else:
.\
% endif
<span style="margin-left:20px;"></span>\
    % if booking.find('information'):
<span class="collaborationDisplayMoreInfo" id="collaborationBookingMoreInfo${booking.id}">More Info</span>
    % endif

    % if booking.find('information') and booking.find('launchInfo'):
    <span style="margin-left:8px;margin-right:8px;">|</span>
    % endif

    % if booking.find('launchInfo'):
    <a target="_blank" href="${booking.launchInfo.launchLink}" id="bookingLaunchLink${booking.id}">
        ${booking.launchInfo.launchText}
    </a>
    <script type="text/javascript">
        $E('bookingLaunchLink${booking.id}').dom.onmouseover = function (event) {
            IndicoUI.Widgets.Generic.tooltip($E('bookingLaunchLink${booking.id}').dom, event,
                '<div class="collaborationLinkTooltipMeetingLecture">${booking.launchInfo.launchTooltip}</div>');
        }
    </script>
    % endif

    % if booking.find('information'):
    <!-- Start of a booking info line -->
    <div id="collaborationInfoLine${booking.id}" style="visibility: hidden; overflow: hidden;">
        <div class="collaborationDisplayInfoLine">
            <table>
                <tbody>
                % for section in booking.findall('information/section'):
                <tr>
                    <td class="collaborationDisplayInfoLeftCol">
                        <span>${section.title}</span>
                    </td>
                    <td class="collaborationDisplayInfoRightCol">
                        % for line in section.findall('line'):
                        <div>${line}</div>
                        % endfor
                        % for linkLine in section.findall('linkLine'):
                        <div><a href="${linkLine.href}">${linkLine.caption}</a></div>
                        % endfor
                    </td>
                </tr>
                % endfor
                </tbody>
            </table>
        </div>
    </div>

    <script type="text/javascript">
        $E('collaborationBookingMoreInfo${booking.id}').dom.onmouseover = function (event) {
            IndicoUI.Widgets.Generic.tooltip($E('collaborationBookingMoreInfo${booking.id}').dom, event,
                '<div class="collaborationLinkTooltipMeetingLecture">Click here to show / hide detailed information.</div>');
        }
        var bookingInfoState${booking.id} = false;
        var height${booking.id} = IndicoUI.Effect.prepareForSlide('collaborationInfoLine${booking.id}', true);

        $E('collaborationBookingMoreInfo${booking.id}').observeClick(function() {
            if (bookingInfoState${booking.id}) {
                IndicoUI.Effect.slide('collaborationInfoLine${booking.id}', height${booking.id});
                $E('collaborationBookingMoreInfo${booking.id}').set('More Info');
                $E('collaborationBookingMoreInfo${booking.id}').dom.className = "collaborationDisplayMoreInfo";
            } else {
                IndicoUI.Effect.slide('collaborationInfoLine${booking.id}', height${booking.id});
                $E('collaborationBookingMoreInfo${booking.id}').set('Hide Info');
                $E('collaborationBookingMoreInfo${booking.id}').dom.className = "collaborationDisplayHideInfo";
            }
            bookingInfoState${booking.id} = !bookingInfoState${booking.id}
        });
    </script>

    % endif
    <!-- End of a booking info line -->

    </div>
    <!-- End of a booking line -->
% endfor

% if len(iconf.plugins.collaboration.booking) > 2:
    <div class="collHideBookingsDiv">
      <span class="fakeLink collHideBookingsText" id="collHideBookings">Hide additional bookings</span>
    </div>
% endif
</div>
</td>
</tr>

<script type="text/javascript">
    var hideHook = function() {
        IndicoUI.Effect.appear($E('collShowBookingsDiv'));
    }
    if (exists($E('collHiddenBookings'))) {
        var height = IndicoUI.Effect.prepareForSlide('collHiddenBookings', true);
        $E('collShowBookings').observeClick(function() {
            IndicoUI.Effect.disappear($E('collShowBookingsDiv'));
            IndicoUI.Effect.slide('collHiddenBookings', height);
            IndicoUI.Effect.appear($E('collHideBookings'));
        });
        $E('collHideBookings').observeClick(function() {
            height = $E('collHiddenBookings').dom.offsetHeight;
            IndicoUI.Effect.slide('collHiddenBookings', height, null, hideHook);
        });
    }
</script>
% endif