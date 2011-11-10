<%page args="video, videoId=''"/>
<span class="videoServiceWrapperInline">
    <span class="videoServiceType">
        <img src="images/video_${video.getType()}.png" border="0" alt="locked" style="margin-left: 3px;"/>
    </span>
    <span class="videoServiceLinks">
        <% launchInfo = video._getLaunchDisplayInfo() %>
        <a target="_blank" href="${launchInfo['launchLink']}" class="bookingLaunchLinkInline" data-id="${videoId}">
            ${launchInfo['launchText']}
        </a>
    </span>
</span>
% if video.hasBookingInformation():
<script type="text/javascript">
<% 
    tempString = '<div class="videoServiceInlinePopup">'

    for section in video.getBookingInformation():
        tempString += '<span class="lineWrapper"><span class="leftCol">'
        tempString += _(section['title']) + '</span><span class="rightCol">'

        for line in section.get('lines', []):
            tempString += '<span>' + _(line) + '</span>'
        for caption, href in section.get('linkLines', []):
            tempString += '<span><a href="' + href + '">' + _(caption) + '</a></span>'

        tempString += '</span>'
%>
videoServiceInfo["${videoId}"] = ${jsonEncode(tempString)};
</script>
% endif