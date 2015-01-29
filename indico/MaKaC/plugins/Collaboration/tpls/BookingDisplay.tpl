<%page args="Booking=None, Kind=None, Timezone=None"/>
<% from MaKaC.common.timezoneUtils import isToday, isTomorrow, isSameDay %>
<% from MaKaC.plugins.Collaboration.Vidyo.common import VidyoTools %>

<%
id = Booking.getId()
firstLineInfo = Booking._getFirstLineInfo(Timezone)
%>

<div class="event-service-row">
    <div class="event-service-row-collapsed clearfix">
        <div class="event-service-info left event-service-row-toggle">
            <img src="${Config.getInstance().getBaseURL()}/images/video_Vidyo.png" border="0" alt="locked" />
            <span class="event-service-title">
                % if Booking.getStartDate():
                    <span>
                        % if Kind == 'scheduled' and isSameDay(Booking.getStartDate(), Booking.getEndDate(), Timezone):
                            <span>
                                % if isToday(Booking.getStartDate(), Timezone) :
                                    today
                                % elif isTomorrow(Booking.getStartDate(), Timezone) :
                                    tomorrow
                                % else:
                                    ${ formatDate(Booking.getAdjustedStartDate(Timezone).date(), format="EEE d/MMM") }
                                % endif
                            </span>
                            from
                        ${ formatTime(Booking.getAdjustedStartDate(Timezone).time()) }
                            to
                        ${ formatTime(Booking.getAdjustedEndDate(Timezone).time()) }
                        % else:
                            % if Kind == 'scheduled' :
                                from
                            % if isToday(Booking.getStartDate(), Timezone) :
                                today at
                            % elif isTomorrow(Booking.getStartDate(), Timezone) :
                                tomorrow at
                            % else:
                            ${ formatDate(Booking.getAdjustedStartDate(Timezone).date(), format="EEE d/MMM") } at
                            % endif

                            ${ formatTime(Booking.getAdjustedStartDate(Timezone).time()) }

                                until

                            % else:
                                ongoing until
                            % endif



                            % if isToday(Booking.getEndDate(), Timezone) :
                                today at
                            % elif isTomorrow(Booking.getEndDate(), Timezone) :
                                tomorrow at
                            % else:
                            ${ formatDate(Booking.getAdjustedEndDate(Timezone).date(), format="EEE d/MMM") } at
                            % endif

                            ${ formatTime(Booking.getAdjustedEndDate(Timezone).time()) }
                        % endif
                        ${":" if firstLineInfo else "."}
                    </span>
                % endif
                % if firstLineInfo:
                    <strong>${ firstLineInfo }</strong>
                % endif

                <% displayInfo = Booking._getInformationDisplay(Timezone) %>
                <% launchInfo = Booking._getLaunchDisplayInfo() %>
            </span>
        </div>
        <div class="event-service-toolbar toolbar right">
            % if (Kind in ['ongoing', 'scheduled'] and launchInfo) or Booking.getType()=="Vidyo":
                <div class="group">
                    % if Kind == 'ongoing' or Booking.getType()=="Vidyo":
                        <a href="${ launchInfo['launchLink'] }" id="bookingLink${id}" class="i-button i-button-small highlight join-button">
                            ${ launchInfo['launchText'] }
                        </a>
                    % else:
                        <span style="color:#888" id="bookingLink${id}" class="i-button i-button-small highlight join-button">${launchInfo['launchText']}</span>
                    % endif
                </div>

                <script type="text/javascript">
                    $E('bookingLink${id}').dom.onmouseover = function (event) {
                        IndicoUI.Widgets.Generic.tooltip($E('bookingLink${id}').dom, event,
                                '<div class="collaborationLinkTooltipConference">${ launchInfo["launchTooltip"] }<\/div>');
                    }
                </script>
            % endif
            % if displayInfo and Booking.getType() == "Vidyo" and (Booking.hasConnect() or Booking.hasDisconnect()) and Booking.isLinkedToEquippedRoom() and self_._rh._getUser() and (conf.canModify(self_._rh._aw) or Booking.getOwner()["id"] == self_._rh._getUser().getId() or _request.remote_addr == VidyoTools.getLinkRoomAttribute(Booking.getLinkObject(), attName='ip')):
                <div class="group">
                    <a style="font-size:12px" data-booking-id="${Booking.getId()}" data-location="${Booking.getLinkVideoRoomLocation()}" data-event="${conf.getId()}" class="fakeLink connect_room">
                        <span style="vertical-align: middle;" class="button-text"/>${_("Connect")} ${Booking.getLinkVideoRoomLocation()}</span>
                        <span style="padding-left: 3px; vertical-align: middle;" class="progress"></span>
                    </a>
                </div>
            % endif
        </div>
    </div>
    % if displayInfo:
        <div class="event-service-details">
            <div class="collaborationDisplayInfoLine">
                ${ Booking._getInformationDisplay(Timezone) }
            </div>
        </div>
        <a class="trigger icon-expand" title='${_("More info")}'></a>
    % endif
</div>
