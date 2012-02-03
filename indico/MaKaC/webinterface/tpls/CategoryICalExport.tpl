<div id="icalExportPopup" style="display:none" class="icalExportPopup">

    <div id="downloadICS" class="iCalExportSection">
         <a href="${ urlHandlers.UHCategoryToiCal.getURL(categ) }">
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
             ${_("Download ICS file")}
        </a>
    </div>

    <div id="iCalSeparator" class="icalSeparator" style="display:none" ></div>
    <%include file="ICalExportCommon.tpl"/>
    <div style="display:none">
        <div id="extraInformation">
            <div class="note">Please use <strong>CTRL + C</strong> to copy this URL</div>
        </div>
    </div>

</div>
<script type="text/javascript">

var setURLs = function(urls){
    $('#publicLink').attr('value', urls["publicRequestURL"]);
    $('#publicLink').attr('title', urls["publicRequestURL"]);
    $('#authLink').attr('value', urls["authRequestURL"]);
    $('#authLink').attr('title', urls["authRequestURL"]);
};

var exportIcal = new ExportIcalInterface(${apiMode}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'category.api.getExportURLs', {categId:"${categ.getId()}"}, ${requestURLs | n,j});

</script>

