<%inherit file="ICalExportBase.tpl"/>
<%block name="downloadText">${_('Download current event:')}</%block>
<%block name="downloadTextFile">  ${_("Event calendar file")}</%block>
<%block name="extraDownload">
    <div class="iCalExportSection">
         <a href='${ urlHandlers.UHConferenceToiCal.getURL(target, detailLevel = "contributions") }'>
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
             ${_("Detailed timetable calendar file")}
         </a>
    </div>
</%block>
<%block name="extraInfo">
    <input type="checkbox" id="detailExport${target.getUniqueId()}"> ${("Detailed timetable")}
</%block>

<%block name="script">
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

    exportPopups["${self_._conf.getUniqueId()}"] = new ExportIcalInterface(${apiMode}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'event.api.getExportURLs', {confId:"${self_._conf.getId()}"}, ${requestURLs | n,j}, "${self_._conf.getUniqueId()}", "${currentUser.getId() if currentUser else ''}");

    $("body").delegate('#detailExport${self_._conf.getUniqueId()}', "click", function(e) {
        setURLs(exportPopups["${self_._conf.getUniqueId()}"].getRequestURLs());
    });

    </script>
</%block>
