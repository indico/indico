<div id="icalExportPopup" style="display:none" class="icalExportPopup">

    <div id="downloadICS" class="iCalExportSection">
         <a href='${ urlHandlers.UHConferenceToiCal.getURL(self_._rh._conf, detailLevel = "top") }'>
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
             ${_("Download event ICS file")}
         </a>
    </div>

    <div id="downloadTimetableICS" class="iCalExportSection">
         <a href='${ urlHandlers.UHConferenceToiCal.getURL(self_._rh._conf, detailLevel = "contributions") }'>
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
             ${_("Download timetable ICS file")}
         </a>
    </div>

    <div id="iCalSeparator" class="icalSeparator" style="display:none"></div>

    <%include file="ICalExportCommon.tpl"/>
    <div style="display:none">
        <div id="extraInformation" class="iCalExportSection">
            <div class="note">Please use <strong>CTRL + C</strong> to copy this URL</div>
            <input type="checkbox" id="detailExport"> ${("Detailed timetable")}
        </div>
    </div>



</div>
<script type="text/javascript">
var setURLs = function(urls){
    if($('#detailExport')[0].checked){
        $('#publicLink').attr('value', urls["publicRequestAllURL"]);
        $('#publicLink').attr('title', urls["publicRequestAllURL"]);
        $('#authLink').attr('value', urls["authRequestAllURL"]);
        $('#authLink').attr('title', urls["authRequestAllURL"]);
    }else{
        $('#publicLink').attr('value', urls["publicRequestTopURL"]);
        $('#publicLink').attr('title', urls["publicRequestTopURL"]);
        $('#authLink').attr('value', urls["authRequestTopURL"]);
        $('#authLink').attr('title', urls["authRequestTopURL"]);
    }
}

var exportIcal = new ExportIcalInterface(${apiMode}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'event.api.getExportURLs', {confId:"${self_._conf.getId()}"}, ${requestURLs | n,j});

$('#detailExport').click(function(e) {
    setURLs(exportIcal.getRequestURLs());
});

</script>

