<%page args="video"/>
<% from MaKaC.plugins.Collaboration.Vidyo.common import VidyoTools %>
<span class="videoServiceWrapperInline">
    <span class="videoServiceType">
        <img src="${Config.getInstance().getBaseURL()}/images/video_${video.getType()}.png" border="0" alt="locked" style="margin-left: 3px;"/>
    </span>
    <span class="videoServiceLinks">
        <% launchInfo = video._getLaunchDisplayInfo() %>
        <a target="_blank" href="${launchInfo['launchLink']}" class="bookingLaunchLinkInline" data-id="${video.getId()}">
            ${_("Join Vidyo")}
            <!--${launchInfo['launchText']}-->
        </a>

        % if video.getType() == "Vidyo" and (video.hasConnect() or video.hasDisconnect()) and video.isLinkedToEquippedRoom() and aw.getUser() and (conf.canModify(aw) or video.getOwner()["id"] == aw.getUser().getId() or _request.remote_addr == VidyoTools.getLinkRoomAttribute(video.getLinkObject(), attName='IP')):
          <span style="margin-left:3px;margin-right:3px;">|</span>
          <a href="#" class="connect_room" data-booking-id="${video.getId()}"
             data-event="${conf.getId()}" data-location="${video.getLinkVideoRoomLocation()}">${_("Connect")} ${video.getLinkVideoRoomLocation()}</a>
          <span style="display:inline; vertical-align:middle" class="progress"></span>
        % endif
    </span>
</span>

<script type="text/javascript">
    videoServiceInfo["${video.getId()}"] = drawBookingPopup(${jsonEncode(video.getBookingInformation())}, ${conf.getId()},'${video.getId()}', ${jsonEncode(conf.canModify(aw) and video.getOwner()["id"] != aw.getUser().getId())});
</script>
