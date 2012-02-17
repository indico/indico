<div id="icalExportPopup${target.getUniqueId()}" style="display:none" class="icalExportPopup">
    <div class="iCalExportSection">
        <div class="exportIcalHeader"><%block name="downloadText"></%block></div>
         <a href="${ urlICSFile }">
            <img src="${icsIconURL}" border="0" style="vertical-align: middle">
            <%block name="downloadTextFile">  ${_("Calendar file")}</%block>
        </a>
    </div>
    <%block name="extraDownload">
    </%block>

    <div id="iCalSeparator${target.getUniqueId()}" class="icalSeparator" style="display:none"></div>
    <%include file="ICalExportCommon.tpl" args="id=target.getUniqueId()"/>
    <div style="display:none">
        <div id="extraInformation${target.getUniqueId()}">
            <div class="note">Please use <strong>CTRL + C</strong> to copy this URL</div>
            <%block name="extraInfo"></%block>
        </div>
    </div>

</div>

<%block name="script">
</%block>