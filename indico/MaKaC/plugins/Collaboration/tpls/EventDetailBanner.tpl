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
    <div class="event-service-row">
        <div class="event-service-row-collapsed clearfix">
            <div class="event-service-info left event-service-row-toggle">
                <img src="${Config.getInstance().getBaseURL()}/images/video_Vidyo.png" border="0" alt="locked" />
                <span class="event-service-title">
                    % if booking.hasStartDate():
                    ${getBookingType(booking)}
                    ${formatTwoDates(booking.getAdjustedStartDate(timezone),
                    booking.getAdjustedEndDate(timezone),
                    useToday=True, useTomorrow=True, dayFormat='EEE d/MMM', capitalize=False)}\
                    % endif
                    % if data.getFirstLineInfo(booking):
                    ${data.getFirstLineInfo(booking)}\
                    % else:
                        .\
                    % endif
                </span>
            </div>
            <div class="event-service-toolbar toolbar right">

                % if launchInfo:
                    <script type="text/javascript">
                        videoServiceLaunchInfo["${bookingId}"] = ${jsonEncode(launchInfo['launchTooltip'])};
                    </script>
                    <div class="group">
                        % if launchInfo['launchLink']:
                            <a target="_blank" href="${launchInfo['launchLink']}" class="bookingLaunchLink i-button i-button-small highlight join-button" data-id="${bookingId}">
                                ${launchInfo['launchText']}
                            </a>
                        % else:
                            <span class="bookingLaunchLink i-button i-button-small highlight join-button"  data-id="${bookingId}" >${launchInfo['launchText']}</span>
                        % endif
                    </div>
                % endif
                % if (bookingInfo or launchInfo) and booking.getType() == "Vidyo" and self_._rh._getUser() and booking.isLinkedToEquippedRoom():
                    % if conf.canModify(self_._rh._aw) or booking.getOwner()["id"] == self_._rh._getUser().getId() or \
                                 (_request.remote_addr == VidyoTools.getLinkRoomAttribute(booking.getLinkObject(), attName='ip')):
                        <div class="group">
                            <a class="fakeLink connect_room i-button i-button-mini" data-booking-id="${booking.getId()}" data-event="${conf.getId()}" data-location="${booking.getLinkVideoRoomLocation()}">
                                <span style="vertical-align: middle;" class="button-text"/>${_("Connect")} ${booking.getLinkVideoRoomLocation()}</span>
                                <span style="padding-left: 3px; vertical-align:middle" class="progress"></span>
                            </a>
                        </div>
                    % endif
                % endif
            </div>
        </div>

        % if bookingInfo:
        <!-- Start of a booking info line -->
        <div class="event-service-details">
            <dl>
                % for section in bookingInfo:
                    <dt>${section['title']}</dt>
                    <dd>
                        % for line in section.get('lines', []):
                            <div style="display:inline">${line}</div>
                        % endfor
                        % if section['title'] == _("Moderator") and self_._rh._getUser() and conf.canModify(self_._rh._aw) and booking.getOwner()["id"] != self_._rh._getUser().getId():
                            <div style="display:inline; vertical-align:bottom"><a href="#" style="font-size:12px" onClick= "makeMeModerator(this,${conf.getId()},${booking.getId()}, successMakeEventModerator)">${_("Make me moderator")}</a></div>
                        % endif
                        % for caption, href in section.get('linkLines', []):
                            <div style="display:inline"><a href="${href}" target="_blank">${caption}</a></div>
                        % endfor
                    </dd>
                % endfor
            </dl>
        </div>
        <a class="trigger icon-expand" title='${_("More info")}'></a>
        % endif
    <!-- End of a booking info line -->
    </div>
    <!-- End of a booking line -->
% endfor
</div>
</td>
</tr>

% endif
