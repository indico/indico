<div id="icalExportPopup${self_._conf.getUniqueId()}" style="display:none" class="icalExportPopup">

    <div class="iCalExportSection">
         <a href='${ urlHandlers.UHConferenceToiCal.getURL(self_._rh._conf, detailLevel = "top") }'>
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
             ${_("Download event ICS file")}
         </a>
    </div>

    <div class="iCalExportSection">
         <a href='${ urlHandlers.UHConferenceToiCal.getURL(self_._rh._conf, detailLevel = "contributions") }'>
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
             ${_("Download timetable ICS file")}
         </a>
    </div>

    <div id="iCalSeparator${self_._conf.getUniqueId()}" class="icalSeparator" style="display:none"></div>

    <%include file="ICalExportCommon.tpl" args="id=self_._conf.getUniqueId()"/>
    <div style="display:none">
        <div id="extraInformation${self_._conf.getUniqueId()}" class="iCalExportSection">
            <div class="note">Please use <strong>CTRL + C</strong> to copy this URL</div>
            <input type="checkbox" id="detailExport${self_._conf.getUniqueId()}"> ${("Detailed timetable")}
        </div>
    </div>



</div>
<script type="text/javascript">
var setURLs = function(urls){
    if($('#detailExport${self_._conf.getUniqueId()}')[0].checked){
        $('#publicLink${self_._conf.getUniqueId()}').attr('value', urls["publicRequestAllURL"]);
        $('#publicLink${self_._conf.getUniqueId()}').attr('title', urls["publicRequestAllURL"]);
        $('#authLink${self_._conf.getUniqueId()}').attr('value', urls["authRequestAllURL"]);
        $('#authLink${self_._conf.getUniqueId()}').attr('title', urls["authRequestAllURL"]);
    }else{
        $('#publicLink${self_._conf.getUniqueId()}').attr('value', urls["publicRequestTopURL"]);
        $('#publicLink${self_._conf.getUniqueId()}').attr('title', urls["publicRequestTopURL"]);
        $('#authLink${self_._conf.getUniqueId()}').attr('value', urls["authRequestTopURL"]);
        $('#authLink${self_._conf.getUniqueId()}').attr('title', urls["authRequestTopURL"]);
    }
}

exportPopups["${self_._conf.getUniqueId()}"] = new ExportIcalInterface(${apiMode}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'event.api.getExportURLs', {confId:"${self_._conf.getId()}"}, ${requestURLs | n,j}, "${self_._conf.getUniqueId()}");

$("body").delegate('#detailExport${self_._conf.getUniqueId()}', "click", function(e) {
    setURLs(exportPopups["${self_._conf.getUniqueId()}"].getRequestURLs());
});

</script>

