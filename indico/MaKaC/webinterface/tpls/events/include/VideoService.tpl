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
    </span>
</span>
<script type="text/javascript">
    videoServiceInfo["${video.getId()}"] = drawBookingPopup(${jsonEncode(video.getBookingInformation())}, ${conf.getId()},'${video.getId()}', ${jsonEncode(conf.canModify(self_._rh._aw) and video.getOwner()["id"] != self_._rh._getUser().getId())});
</script>