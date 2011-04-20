% if bookings:
<tr>
<td class="leftCol">Video Services</td>
<td>
<div>
% for pos, booking in enumerate(bookings):
    <% bookingId = booking.getId() %>
    % if pos == 2:
        <div id="collShowBookingsDiv">
            <span class="collShowHideBookingsText">
                <%
                moreOngoing = sum(1 for b in bookings[pos + 1:] if getBookingKind(b) == 'ongoing')
                moreScheduled = sum(1 for b in bookings[pos + 1:] if getBookingKind(b) == 'scheduled')
                %>
                There are
                % if getBookingKind(booking) == 'ongoing':
                    ${ 1 + moreOngoing } more ongoing bookings
                    % if moreScheduled > 0:
                        and ${moreScheduled} more scheduled bookings.
                    % endif
                % elif getBookingKind(booking) == 'scheduled':
                    ${ 1 + moreScheduled } more scheduled bookings.
                % endif
            </span>
            <span id="collShowBookings" class="fakeLink collShowBookingsText">Show</span>
        </div>
    </div>

    <div id="collHiddenBookings" style="visibility: hidden; overflow: hidden;">
    % endif

    <!-- Start of a booking line -->
    <% data = bookingData[booking.getType()] %>
    <% launchInfo = data.getLaunchInfo(booking) %>
    <% bookingInfo = data.getInformation(booking) %>
    <div class="collaborationDisplayBookingLine">
    <span class="collaborationDisplayBookingType">${data.getDisplayName()}</span>\
    % if booking.hasStartDate():
        ${getBookingKind(booking)}
        ${formatTwoDates(booking.getAdjustedStartDate(timezone),
                         booking.getAdjustedEndDate(timezone),
                         useToday=True, useTomorrow=True, dayFormat='%a %d/%m', capitalize=False)}\
    % endif
    % if data.getFirstLineInfo(booking):
: ${data.getFirstLineInfo(booking)}\
    % else:
.\
% endif
<span style="margin-left:20px;"></span>\
    % if bookingInfo:
<span class="collaborationDisplayMoreInfo" id="collaborationBookingMoreInfo${bookingId}">More Info</span>
    % endif

    % if bookingInfo and launchInfo:
    <span style="margin-left:8px;margin-right:8px;">|</span>
    % endif

    % if launchInfo:
    <a target="_blank" href="${launchInfo['launchLink']}" id="bookingLaunchLink${bookingId}">
        ${launchInfo['launchText']}
    </a>
    <script type="text/javascript">
        $E('bookingLaunchLink${bookingId}').dom.onmouseover = function (event) {
            IndicoUI.Widgets.Generic.tooltip($E('bookingLaunchLink${bookingId}').dom, event,
                '<div class="collaborationLinkTooltipMeetingLecture">${launchInfo['launchTooltip']}</div>');
        }
    </script>
    % endif

    % if bookingInfo:
    <!-- Start of a booking info line -->
    <div id="collaborationInfoLine${bookingId}" style="visibility: hidden; overflow: hidden;">
        <div class="collaborationDisplayInfoLine">
            <table>
                <tbody>
                % for section in bookingInfo:
                <tr>
                    <td class="collaborationDisplayInfoLeftCol">
                        <span>${section['title']}</span>
                    </td>
                    <td class="collaborationDisplayInfoRightCol">
                        % for line in section.get('lines', []):
                        <div>${line}</div>
                        % endfor
                        % for caption, href in section.get('linkLines', []):
                        <div><a href="${href}">${caption}</a></div>
                        % endfor
                    </td>
                </tr>
                % endfor
                </tbody>
            </table>
        </div>
    </div>

    <script type="text/javascript">
        $E('collaborationBookingMoreInfo${bookingId}').dom.onmouseover = function (event) {
            IndicoUI.Widgets.Generic.tooltip($E('collaborationBookingMoreInfo${bookingId}').dom, event,
                '<div class="collaborationLinkTooltipMeetingLecture">Click here to show / hide detailed information.</div>');
        }
        var bookingInfoState${bookingId} = false;
        var height${bookingId} = IndicoUI.Effect.prepareForSlide('collaborationInfoLine${bookingId}', true);

        $E('collaborationBookingMoreInfo${bookingId}').observeClick(function() {
            if (bookingInfoState${bookingId}) {
                IndicoUI.Effect.slide('collaborationInfoLine${bookingId}', height${bookingId});
                $E('collaborationBookingMoreInfo${bookingId}').set('More Info');
                $E('collaborationBookingMoreInfo${bookingId}').dom.className = "collaborationDisplayMoreInfo";
            } else {
                IndicoUI.Effect.slide('collaborationInfoLine${bookingId}', height${bookingId});
                $E('collaborationBookingMoreInfo${bookingId}').set('Hide Info');
                $E('collaborationBookingMoreInfo${bookingId}').dom.className = "collaborationDisplayHideInfo";
            }
            bookingInfoState${bookingId} = !bookingInfoState${bookingId}
        });
    </script>

    % endif
    <!-- End of a booking info line -->

    </div>
    <!-- End of a booking line -->
% endfor

% if len(bookings) > 2:
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