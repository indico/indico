<div id="icalExportPopup${categ.getUniqueId()}" style="display:none" class="icalExportPopup">

    <div class="iCalExportSection">
         <a href="${ urlHandlers.UHCategoryToiCal.getURL(categ) }">
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
             ${_("Download ICS file")}
        </a>
    </div>

    <div id="iCalSeparator${categ.getId()}" class="icalSeparator" style="display:none" ></div>
    <%include file="ICalExportCommon.tpl" args="id=categ.getUniqueId()"/>
    <div style="display:none">
        <div id="extraInformation${categ.getUniqueId()}">
            <div class="note">Please use <strong>CTRL + C</strong> to copy this URL</div>
        </div>
    </div>

</div>
<script type="text/javascript">

var setURLs = function(urls){
    $('#publicLink${categ.getUniqueId()}').attr('value', urls["publicRequestURL"]);
    $('#publicLink${categ.getUniqueId()}').attr('title', urls["publicRequestURL"]);
    $('#authLink${categ.getUniqueId()}').attr('value', urls["authRequestURL"]);
    $('#authLink${categ.getUniqueId()}').attr('title', urls["authRequestURL"]);
};

exportPopups["${categ.getUniqueId()}"] = new ExportIcalInterface(${apiMode}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'category.api.getExportURLs', {categId:"${categ.getId()}"}, ${requestURLs | n,j}, "${categ.getUniqueId()}");

</script>

