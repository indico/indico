<div id="icalExportPopup${session.getUniqueId()}" class="icalExportPopup">

    <div class="iCalExportSection">
         <a href="${ urlHandlers.UHSessionToiCal.getURL(session) }">
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
             ${_("Download ICS file")}
        </a>
    </div>

    <div id="iCalSeparator${session.getUniqueId()}" class="icalSeparator" style="display:none" ></div>
    <%include file="ICalExportCommon.tpl" args="id=session.getUniqueId()"/>
    <div style="display:none">
        <div id="extraInformation${session.getUniqueId()}">
            <div class="note">Please use <strong>CTRL + C</strong> to copy this URL</div>
        </div>
    </div>

</div>
<script type="text/javascript">

var setURLs = function(urls){
    $('#publicLink${session.getUniqueId()}').attr('value', urls["publicRequestURL"]);
    $('#publicLink${session.getUniqueId()}').attr('title', urls["publicRequestURL"]);
    $('#authLink${session.getUniqueId()}').attr('value', urls["authRequestURL"]);
    $('#authLink${session.getUniqueId()}').attr('title', urls["authRequestURL"]);
};

exportPopups["${session.getUniqueId()}"] = new ExportIcalInterface(${apiMode}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'schedule.api.getSessionExportURLs', {confId:"${session.getConference().getId()}", sessionId:"${session.getId()}"}, ${requestURLs | n,j}, "${session.getUniqueId()}");

</script>

