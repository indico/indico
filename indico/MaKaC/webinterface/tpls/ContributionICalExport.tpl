<div id="icalExportPopup${Contribution.getUniqueId()}" class="icalExportPopup" style="display:none">

    <div class="iCalExportSection">
         <a href="${ urlHandlers.UHContribToiCal.getURL(Contribution) }">
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
             ${_("Download ICS file")}
        </a>
    </div>

    <div id="iCalSeparator${Contribution.getUniqueId()}" class="icalSeparator" style="display:none" ></div>
    <%include file="ICalExportCommon.tpl" args="id=Contribution.getUniqueId()"/>
    <div style="display:none">
        <div id="extraInformation${Contribution.getUniqueId()}">
            <div class="note">Please use <strong>CTRL + C</strong> to copy this URL</div>
        </div>
    </div>

</div>
<script type="text/javascript">

var setURLs = function(urls){
    $('#publicLink${Contribution.getUniqueId()}').attr('value', urls["publicRequestURL"]);
    $('#publicLink${Contribution.getUniqueId()}').attr('title', urls["publicRequestURL"]);
    $('#authLink${Contribution.getUniqueId()}').attr('value', urls["authRequestURL"]);
    $('#authLink${Contribution.getUniqueId()}').attr('title', urls["authRequestURL"]);
};

exportPopups["${Contribution.getUniqueId()}"] = new ExportIcalInterface(${apiMode}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'schedule.api.getContribExportURLs', {confId:"${Contribution.getConference().getId()}", contribId:"${Contribution.getId()}"}, ${requestURLs | n,j}, "${Contribution.getUniqueId()}");

</script>

