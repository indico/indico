<%page args="video"/>
<span class="videoServiceWrapperInline">
    <span class="videoServiceType">
        <img src="images/video_${video.getType()}.png" border="0" alt="locked" style="margin-left: 3px;"/>
    </span>
    <span class="videoServiceLinks">
        <% launchInfo = video._getLaunchDisplayInfo() %>
        <a target="_blank" href="${launchInfo['launchLink']}" class="bookingLaunchLinkInline" data-id="${video.getId()}">
            ${_("Join Vidyo")}
            <!--${launchInfo['launchText']}-->
        </a>
        % if video.canBeConnected() and self_._rh._getUser() and (conf.canModify(self_._rh._aw) or video.getOwner()["id"] == self_._rh._getUser().getId()):
        <span style="margin-left:3px;margin-right:3px;">|</span>
        <script type="text/javascript">
            var booking${video.getId()} = ${jsonEncode(fossilize(video))};
        </script>
        <a href="#" style="font-size:12px" onClick="connectBookingRoom(booking${video.getId()},'${conf.getId()}')">${_("Connect")} ${video.getLinkVideoRoomLocation()}</a>
        <span style="display:inline; vertical-align:middle" id="connectProgress${video.getId()}"></span>
        % endif

    </span>
</span>
<script type="text/javascript">
    videoServiceInfo["${video.getId()}"] = drawBookingPopup(${jsonEncode(video.getBookingInformation())}, ${conf.getId()},'${video.getId()}', ${jsonEncode(conf.canModify(self_._rh._aw) and video.getOwner()["id"] != self_._rh._getUser().getId())});
</script>