<%inherit file="ICalExportBase.tpl"/>
<%block name="downloadText">${_('Download current event:')}</%block>
<%block name="downloadTextFile">  ${_("Event calendar file")}</%block>

<%block name="extraDownload" args="item">
    % if item.getType() != "simple_event":
    <div class="iCalExportSection">
         <a href='${ urlHandlers.UHConferenceToiCal.getURL(item, detail = "contributions") }'>
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
             ${_("Detailed timetable calendar file")}
         </a>
    </div>
    % endif
</%block>
<%block name="extraInfo" args="item">
    % if item.getType() != "simple_event":
        <input type="checkbox" id="detailExport${item.getUniqueId()}"> ${_("Detailed timetable")}
    % endif
</%block>

<%block name="script" args="item">
    ${parent.script(item)}
    <script type="text/javascript">
    exportPopups["${item.getUniqueId()}"] = new ExportIcalInterface(${apiMode | n,j}, ${persistentUserEnabled | n,j}, ${persistentAllowed | n,j}, ${apiActive | n,j}, ${userLogged | n,j}, setURLs, 'event.api.getExportURLs', {confId:"${item.getId()}"}, ${requestURLs | n,j}, "${item.getUniqueId()}", "${currentUser.getId() if currentUser else ''}");

    $("body").delegate('#detailExport${item.getUniqueId()}', "click", function(e) {
        setURLs(exportPopups["${item.getUniqueId()}"].getRequestURLs());
    });

    </script>
</%block>
