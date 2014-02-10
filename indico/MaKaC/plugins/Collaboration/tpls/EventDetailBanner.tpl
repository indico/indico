<script type="text/javascript">
  var bookings = ${dict((b['id'], b) for b in fossilize(bookings))|n,j};
</script>

<% from MaKaC.plugins.Collaboration.Vidyo.common import VidyoTools %>
<%
    ## Only show event-level video services.
    event_bookings = filter(lambda x: x.hasSessionOrContributionLink() != True and x.canBeDisplayed(), bookings)
%>
% if event_bookings:
<tr>
<td class="leftCol">Video Services</td>
<td>
<div>
% for pos, booking in enumerate(event_bookings):
    <% bookingId = booking.getId() %>
    % if pos == 2:
        <div id="collShowBookingsDiv" class="collaborationDisplayInfoLine">
            <span class="collShowHideBookingsText">
                <%
                moreOngoing = sum(1 for b in bookings[pos + 1:] if getBookingType(b) == 'ongoing')
                moreScheduled = sum(1 for b in bookings[pos + 1:] if getBookingType(b) == 'scheduled')
                %>
                There are
                % if getBookingType(booking) == 'ongoing':
                    ${ 1 + moreOngoing } more ongoing bookings
                    % if moreScheduled > 0:
                        and ${moreScheduled} more scheduled bookings.
                    % endif
                % elif getBookingType(booking) == 'scheduled':
                    ${ 1 + moreScheduled } more scheduled bookings.
                % endif
            </span>
            <span id="collShowBookings" class="fakeLink italic">Show</span>
        </div>
    </div>

    <div id="collHiddenBookings" style="display:none; overflow: hidden;">
    % endif

    <!-- Start of a booking line -->
    <% data = bookingData[booking.getType()] %>
    <% launchInfo = data.getLaunchInfo(booking) %>
    <% bookingInfo = data.getInformation(booking) %>
    <div class="collaborationDisplayBookingLine">
    <span class="videoServiceWrapper">
        <span class="collaborationDisplayBookingType">${data.getDisplayName()}</span>
        <span class="collaborationDisplayBookingTitle">
        % if booking.hasStartDate():
            ${getBookingType(booking)}
            ${formatTwoDates(booking.getAdjustedStartDate(timezone),
                             booking.getAdjustedEndDate(timezone),
                             useToday=True, useTomorrow=True, dayFormat='EEE d/MMM', capitalize=False)}\
        % endif
        % if data.getFirstLineInfo(booking):
    : ${data.getFirstLineInfo(booking)}\
        % else:
    .\
    % endif
    </span>
    <!-- <span style="margin-left:20px;"></span>  -->

        % if bookingInfo:
        <span class="collaborationDisplayMoreInfo">More Info</span>
        % endif

        % if bookingInfo and launchInfo:
        <span style="margin-left:3px;margin-right:3px;">|</span>
        % endif

        % if launchInfo:
            % if launchInfo['launchLink']:
                <a target="_blank" href="${launchInfo['launchLink']}" class="bookingLaunchLink" data-id="${bookingId}">
                    ${launchInfo['launchText']}
                </a>
            % else:
                <span style="font-weight:bold; color:#888" class="bookingLaunchLink"  data-id="${bookingId}" >${launchInfo['launchText']}</span>
            % endif
        <script type="text/javascript">
            videoServiceLaunchInfo["${bookingId}"] = ${jsonEncode(launchInfo['launchTooltip'])};
        </script>
        % endif

        % if (bookingInfo or launchInfo) and booking.getType() == "Vidyo" and self_._rh._getUser() and booking.isLinkedToEquippedRoom():
          % if conf.canModify(self_._rh._aw) or booking.getOwner()["id"] == self_._rh._getUser().getId() or \
               (_request.remote_addr == VidyoTools.getLinkRoomAttribute(booking.getLinkObject(), attName='IP')):
            <span style="margin-left:3px;margin-right:3px;">|</span>
            <a class="fakeLink connect_room" data-booking-id="${booking.getId()}"
               data-event="${conf.getId()}" data-location="${booking.getLinkVideoRoomLocation()}">
               <span style="vertical-align: middle;" class="button-text"/>${_("Connect")} ${booking.getLinkVideoRoomLocation()}</span>
               <span style="padding-left: 3px; vertical-align:middle" class="progress"></span></a>
          % endif
        % endif

    </span>

    % if bookingInfo:
    <!-- Start of a booking info line -->
    <div class="collabInfoInline" style="overflow: hidden; display: none;">
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
                        <div style="display:inline">${line}</div>
                        % endfor
                        % if section['title'] == _("Moderator") and self_._rh._getUser() and conf.canModify(self_._rh._aw) and booking.getOwner()["id"] != self_._rh._getUser().getId():
                        <div style="display:inline; vertical-align:bottom"><a href="#" style="font-size:12px" onClick= "makeMeModerator(this,${conf.getId()},${booking.getId()}, successMakeEventModerator)">${_("Make me moderator")}</a></div>
                        % endif
                        % for caption, href in section.get('linkLines', []):
                        <div style="display:inline"><a href="${href}" target="_blank">${caption}</a></div>
                        % endfor
                    </td>
                </tr>
                % endfor
                </tbody>
            </table>
        </div>
    </div>
    % endif
    <!-- End of a booking info line -->
    </div>
    <!-- End of a booking line -->
% endfor
</div>
</td>
</tr>

% endif
